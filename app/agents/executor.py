from app.database import save_task

def run_executor(user_id: str, tasks: list, schedule: dict) -> dict:
    saved_tasks = []
    logs = []

    for task in tasks:
        try:
            task_id = save_task(user_id, task)
            saved_tasks.append({**task, "id": task_id})
            logs.append(f"EXECUTOR → created task: {task['title']}")
        except Exception as e:
            logs.append(f"EXECUTOR → failed: {task['title']} ({str(e)})")

    if schedule.get("schedule"):
        logs.append(f"EXECUTOR → scheduled {len(schedule['schedule'])} time blocks")

    if schedule.get("conflicts_resolved", 0) > 0:
        logs.append(f"EXECUTOR → resolved {schedule['conflicts_resolved']} conflicts")

    return {
        "saved_tasks": saved_tasks,
        "tasks_created": len(saved_tasks),
        "logs": logs
    }