import json
from app.agents.utils import generate_with_retry

def run_planner(user_message: str, memory: dict) -> dict:
    system = f"""You are the Planner Agent in a multi-agent productivity system.
Your job is to decompose the user's goal into concrete, actionable tasks.

User memory profile:
- Productive hours: {memory.get('productive_hours_start', 10)}AM to {memory.get('productive_hours_end', 22)}
- Estimation accuracy: {memory.get('estimation_accuracy', 1.0)} (multiply all estimates by this)
- Underestimate factor: {memory.get('underestimate_factor', 1.0)}
- Past completion rate: {memory.get('completion_rate', 1.0)}

Rules:
- Break the goal into 3-8 specific tasks
- Adjust time estimates using the user's underestimate_factor
- Assign priority: high / medium / low
- Return ONLY a JSON object, no markdown, no explanation

JSON format:
{{
  "tasks": [
    {{
      "title": "task name",
      "description": "what exactly to do",
      "estimated_hours": 2.0,
      "priority_label": "high",
      "priority_score": 0.9,
      "deadline": null
    }}
  ],
  "summary": "one line summary of the plan"
}}"""

    text = generate_with_retry(f"{system}\n\nUser goal: {user_message}")

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        return {
            "tasks": [{
                "title": "Complete the described goal",
                "description": user_message,
                "estimated_hours": 2.0,
                "priority_label": "high",
                "priority_score": 0.8,
                "deadline": None
            }],
            "summary": "Task created from user input"
        }