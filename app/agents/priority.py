import json
from app.agents.utils import generate_with_retry

def run_priority(tasks: list, memory: dict) -> list:
    if not tasks:
        return []

    task_list_str = json.dumps(tasks, indent=2, default=str)

    system = f"""You are the Priority Agent in a multi-agent productivity system.
Your job is to rank tasks by urgency and assign final priority scores.

User memory profile:
- Completion rate: {memory.get('completion_rate', 1.0)}
- Avg deep work block: {memory.get('avg_deep_work_hours', 2.0)} hours

Scoring formula: urgency (deadline proximity) x importance x effort fit
Score must be between 0.0 and 1.0. Higher = do first.

Return ONLY a JSON array, no markdown, no explanation.

Format:
[
  {{
    "title": "task title",
    "priority_score": 0.95,
    "priority_label": "high",
    "reason": "due soonest and highest impact"
  }}
]"""

    text = generate_with_retry(f"{system}\n\nTasks to rank:\n{task_list_str}")

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        ranked = json.loads(text)
        score_map = {t["title"]: t for t in ranked}
        for task in tasks:
            if task["title"] in score_map:
                task["priority_score"] = score_map[task["title"]]["priority_score"]
                task["priority_label"] = score_map[task["title"]]["priority_label"]
        return tasks
    except Exception:
        return tasks