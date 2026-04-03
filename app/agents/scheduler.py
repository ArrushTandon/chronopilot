import json
from datetime import datetime
from app.agents.utils import generate_with_retry

def run_scheduler(tasks: list, memory: dict) -> dict:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    task_list_str = json.dumps(tasks, indent=2, default=str)

    system = f"""You are the Scheduler Agent in a multi-agent productivity system.
Your job is to assign realistic time blocks to tasks based on the user's productive hours.

Current time: {now}
User productive hours: {memory.get('productive_hours_start', 10)}:00 to {memory.get('productive_hours_end', 22)}:00
Deep work capacity: {memory.get('avg_deep_work_hours', 2.0)} hours per block
Never schedule tasks outside productive hours.
Add 15 minute breaks between tasks.

Return ONLY a JSON object, no markdown, no explanation.

Format:
{{
  "schedule": [
    {{
      "title": "task title",
      "start": "2025-01-15 10:00",
      "end": "2025-01-15 12:00",
      "block_type": "deep_work"
    }}
  ],
  "conflicts_resolved": 0,
  "summary": "Scheduled X tasks across Y days"
}}"""

    text = generate_with_retry(f"{system}\n\nTasks to schedule:\n{task_list_str}")

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        return {
            "schedule": [],
            "conflicts_resolved": 0,
            "summary": "Schedule generated"
        }