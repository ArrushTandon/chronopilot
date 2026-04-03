import json
from app.database import fetch_user_memory, save_session, fetch_user_tasks
from app.agents.utils import generate_with_retry
from app.agents.planner import run_planner
from app.agents.priority import run_priority
from app.agents.scheduler import run_scheduler
from app.agents.executor import run_executor
from app.agents.memory_agent import run_memory_agent

def run_orchestrator(user_id: str, message: str, history: list) -> dict:
    execution_log = []

    # 1. Load user memory from AlloyDB
    memory = fetch_user_memory(user_id)
    execution_log.append(f"ORCHESTRATOR → loaded memory for {memory.get('name', 'user')}")

    # Conversational fast-path — no agents needed for casual messages
    casual_keywords = ["hi", "hello", "hey", "how are", "what is", "how does",
                       "who are", "thank", "thanks", "good morning", "good night",
                       "what can you", "help me understand", "explain"]
    if any(kw in message.lower() for kw in casual_keywords) and len(message.split()) < 12:
        reply = generate_with_retry(
            f"""You are ChronoPilot, a friendly AI productivity co-pilot.
Have a natural, warm conversation with the user. Keep it brief and helpful.
You help people manage deadlines, tasks, and schedules — but you can also just chat.
User said: {message}
Reply in 2-3 sentences max."""
        )
        return {
            "reply": reply,
            "agents_invoked": [],
            "tasks_created": [],
            "execution_log": ["CHRONOPILOT → conversational response (no planning needed)"],
            "session_id": ""
        }

    # 2. Fast-path routing for common patterns (saves a Gemini call)
    message_lower = message.lower()
    
    if any(w in message_lower for w in ["deadline", "behind", "haven't started", "overdue", "due"]):
        agents_to_invoke = ["planner", "priority", "scheduler", "executor", "memory"]
        execution_log.append("ORCHESTRATOR → fast-path: deadline crisis detected")
    
    elif any(w in message_lower for w in ["reschedule", "calendar", "meeting", "tomorrow", "schedule"]):
        agents_to_invoke = ["scheduler", "executor", "memory"]
        execution_log.append("ORCHESTRATOR → fast-path: scheduling request detected")
    
    elif any(w in message_lower for w in ["first", "priority", "what should", "focus", "work on"]):
        agents_to_invoke = ["priority", "executor", "memory"]
        execution_log.append("ORCHESTRATOR → fast-path: priority request detected")
    
    elif any(w in message_lower for w in ["all-nighter", "night", "8 hours", "sprint"]):
        agents_to_invoke = ["planner", "scheduler", "executor", "memory"]
        execution_log.append("ORCHESTRATOR → fast-path: sprint planning detected")
    
    else:
        # Fall back to Gemini routing only for ambiguous messages
        routing_prompt = f"""You are the Orchestrator of a multi-agent productivity system.
Given the user message, decide which agents to invoke.

Agents available:
- planner: breaks goals into tasks
- scheduler: assigns time blocks
- priority: ranks tasks by urgency
- executor: saves tasks and logs actions
- memory: updates user profile (always invoke last)

User message: {message}

Return ONLY a JSON array of agent names in order.
Example: ["planner", "priority", "scheduler", "executor", "memory"]
Always end with memory."""

        routing_text = generate_with_retry(routing_prompt)

        if routing_text.startswith("```"):
            routing_text = routing_text.split("```")[1]
            if routing_text.startswith("json"):
                routing_text = routing_text[4:]
        routing_text = routing_text.strip()

        try:
            agents_to_invoke = json.loads(routing_text)
        except Exception:
            agents_to_invoke = ["planner", "priority", "scheduler", "executor", "memory"]

    execution_log.append(f"ORCHESTRATOR → routing to: {agents_to_invoke}")

    # 3. Run agents in order
    tasks = []
    schedule = {}
    session_data = {
        "summary": message,
        "agents_invoked": agents_to_invoke,
        "tasks_created": 0,
        "tasks_completed": 0,
        "conversation": history
    }

    if "planner" in agents_to_invoke:
        execution_log.append("PLANNER → decomposing goal into tasks")
        plan = run_planner(message, memory)
        tasks = plan.get("tasks", [])
        execution_log.append(f"PLANNER → {len(tasks)} tasks decomposed")

    if "priority" in agents_to_invoke and tasks:
        execution_log.append("PRIORITY → scoring tasks by urgency x effort")
        tasks = run_priority(tasks, memory)
        execution_log.append("PRIORITY → tasks ranked")

    if "scheduler" in agents_to_invoke and tasks:
        execution_log.append("SCHEDULER → building time blocks")
        schedule = run_scheduler(tasks, memory)
        execution_log.append(f"SCHEDULER → {schedule.get('summary', 'done')}")

    if "executor" in agents_to_invoke:
        execution_log.append("EXECUTOR → saving tasks to AlloyDB")
        result = run_executor(user_id, tasks, schedule)
        session_data["tasks_created"] = result["tasks_created"]
        execution_log.extend(result["logs"])

    # 4. Save session to AlloyDB
    session_id = save_session(user_id, session_data)
    execution_log.append("ORCHESTRATOR → session saved")

    # 5. Run memory agent
    if "memory" in agents_to_invoke:
        execution_log.append("MEMORY → updating profile from session")
        run_memory_agent(user_id, session_data, memory)
        execution_log.append("MEMORY → profile updated ✓")

    # 6. Generate final natural language reply
    # Only call Gemini for reply if we have meaningful output
    if tasks:
        context = f"""You are the Deadline Survival AI — an autonomous productivity system.
You just completed these actions:
{chr(10).join(execution_log)}

Tasks created: {json.dumps([t['title'] for t in tasks], default=str)}
Schedule: {schedule.get('summary', 'No schedule generated')}

User said: {message}

Write a concise, confident reply summarizing what you did autonomously.
Be direct. Lead with actions taken. Max 100 words."""

        reply_text = generate_with_retry(context)
    else:
        # No tasks created — generate a lightweight reply without a Gemini call
        reply_text = (
            f"I've loaded your profile and I'm ready to act. "
            f"Tell me your deadlines, meetings, or what you're behind on — "
            f"and I'll autonomously plan, prioritize, and schedule everything. "
            f"What's your current situation?"
        )

    return {
        "reply": reply_text,
        "agents_invoked": agents_to_invoke,
        "tasks_created": tasks,
        "execution_log": execution_log,
        "session_id": session_id
    }


'''
    # 6. Generate final natural language reply
    context = f"""You are the Deadline Survival AI — an autonomous productivity system.
You just completed these actions:
{chr(10).join(execution_log)}

Tasks created: {json.dumps([t['title'] for t in tasks], default=str)}
Schedule: {schedule.get('summary', 'No schedule generated')}

User said: {message}

Write a concise, confident reply summarizing what you did autonomously.
Be direct. Lead with actions taken. Max 120 words."""

    reply_text = generate_with_retry(context)

    return {
        "reply": reply_text,
        "agents_invoked": agents_to_invoke,
        "tasks_created": tasks,
        "execution_log": execution_log,
        "session_id": session_id
    }

'''
