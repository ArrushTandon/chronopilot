import pg8000.native
import json
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

def get_connection():
    return pg8000.native.Connection(
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

def fetch_user_memory(user_id: str) -> dict:
    conn = get_connection()
    try:
        rows = conn.run(
            """
            SELECT name, productive_hours_start, productive_hours_end,
                   estimation_accuracy, underestimate_factor,
                   completion_rate, avg_deep_work_hours,
                   total_sessions, preferred_reminder
            FROM users WHERE id = :uid
            """,
            uid=user_id
        )
        if not rows:
            return {}
        cols = [
            "name", "productive_hours_start", "productive_hours_end",
            "estimation_accuracy", "underestimate_factor",
            "completion_rate", "avg_deep_work_hours",
            "total_sessions", "preferred_reminder"
        ]
        return dict(zip(cols, rows[0]))
    finally:
        conn.close()

def parse_deadline(deadline_str) -> str | None:
    """Convert Gemini's deadline output to a valid timestamp string."""
    if not deadline_str:
        return None

    # Already a valid datetime string
    if isinstance(deadline_str, str) and len(deadline_str) > 10:
        try:
            datetime.fromisoformat(deadline_str)
            return deadline_str
        except ValueError:
            pass

    # Map day names to actual dates
    day_map = {
        "monday":    0, "tuesday": 1, "wednesday": 2,
        "thursday":  3, "friday":  4, "saturday":  5, "sunday": 6
    }

    if isinstance(deadline_str, str):
        lower = deadline_str.lower().strip()
        today = datetime.now()

        for day_name, day_num in day_map.items():
            if day_name in lower:
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target = today + timedelta(days=days_ahead)
                return target.strftime("%Y-%m-%d 23:59:00")

        # Try parsing common formats
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                return datetime.strptime(deadline_str, fmt).strftime("%Y-%m-%d 23:59:00")
            except ValueError:
                continue

    return None

def save_session(user_id: str, session_data: dict) -> str:
    conn = get_connection()
    try:
        # Use json.dumps for JSONB columns — never str()
        raw_conversation = json.dumps(session_data.get("conversation", []))
        memory_delta     = json.dumps(session_data.get("memory_delta", {}))
        agents_invoked   = session_data.get("agents_invoked", [])

        rows = conn.run(
            """
            INSERT INTO sessions
              (user_id, user_message_summary, agents_invoked,
               tasks_created, calendar_events_modified,
               raw_conversation, memory_delta)
            VALUES
              (:uid, :summary, :agents, :tc, :cem, :convo::jsonb, :delta::jsonb)
            RETURNING id
            """,
            uid=user_id,
            summary=session_data.get("summary", ""),
            agents=agents_invoked,
            tc=session_data.get("tasks_created", 0),
            cem=session_data.get("calendar_events_modified", 0),
            convo=raw_conversation,
            delta=memory_delta
        )
        return str(rows[0][0])
    finally:
        conn.close()

def save_task(user_id: str, task: dict) -> str:
    conn = get_connection()
    try:
        # Parse deadline safely
        raw_deadline = task.get("deadline")
        parsed_deadline = parse_deadline(raw_deadline)

        rows = conn.run(
            """
            INSERT INTO tasks
              (user_id, title, description, priority_label,
               priority_score, estimated_hours, deadline, status)
            VALUES
              (:uid, :title, :desc, :plabel, :pscore, :ehours, :dl, 'pending')
            RETURNING id
            """,
            uid=user_id,
            title=task.get("title", ""),
            desc=task.get("description", ""),
            plabel=task.get("priority_label", "medium"),
            pscore=float(task.get("priority_score", 0.5)),
            ehours=float(task.get("estimated_hours", 1.0)),
            dl=parsed_deadline
        )
        return str(rows[0][0])
    finally:
        conn.close()

def save_log(session_id: str, agent: str, action: str, status: str = "success"):
    conn = get_connection()
    try:
        conn.run(
            """
            INSERT INTO execution_logs (session_id, agent_name, action, status)
            VALUES (:sid, :agent, :action, :status)
            """,
            sid=session_id,
            agent=agent,
            action=action,
            status=status
        )
    finally:
        conn.close()

def update_user_memory(user_id: str, delta: dict):
    conn = get_connection()
    try:
        conn.run(
            """
            UPDATE users SET
              estimation_accuracy  = :ea,
              underestimate_factor = :uf,
              completion_rate      = :cr,
              total_sessions       = total_sessions + 1,
              last_session_at      = NOW()
            WHERE id = :uid
            """,
            ea=float(delta.get("estimation_accuracy", 1.0)),
            uf=float(delta.get("underestimate_factor", 1.0)),
            cr=float(delta.get("completion_rate", 1.0)),
            uid=user_id
        )
    finally:
        conn.close()

def fetch_user_tasks(user_id: str) -> list:
    conn = get_connection()
    try:
        rows = conn.run(
            """
            SELECT id, title, priority_label, priority_score,
                   estimated_hours, deadline, status
            FROM tasks
            WHERE user_id = :uid AND status != 'completed'
            ORDER BY priority_score DESC
            """,
            uid=user_id
        )
        cols = ["id", "title", "priority_label", "priority_score",
                "estimated_hours", "deadline", "status"]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()