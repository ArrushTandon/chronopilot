import json
from app.agents.utils import generate_with_retry
from app.database import update_user_memory

def run_memory_agent(user_id: str, session_data: dict, memory: dict):
    system = f"""You are the Memory Agent in a multi-agent productivity system.
Your job is to analyze what happened this session and update the user's memory profile.

Current memory profile:
{json.dumps(memory, indent=2)}

This session:
- Tasks created: {session_data.get('tasks_created', 0)}
- Tasks completed: {session_data.get('tasks_completed', 0)}
- User message: {session_data.get('summary', '')}

Based on this session, compute updated memory values.
Return ONLY a JSON object, no markdown, no explanation.

Format:
{{
  "estimation_accuracy": 1.0,
  "underestimate_factor": 1.0,
  "completion_rate": 1.0,
  "notes": "what changed and why"
}}"""

    try:
        text = generate_with_retry(system)

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        delta = json.loads(text)
        update_user_memory(user_id, delta)
        return delta
    except Exception as e:
        return {"notes": f"Memory update skipped: {str(e)}"}