from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.models import OrchestrationRequest, OrchestrationResponse
from app.agents.orchestrator import run_orchestrator
from app.database import fetch_user_tasks
from pydantic import BaseModel as PydanticBase
import os

app = FastAPI(title="Deadline Survival AI", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

class LoginRequest(PydanticBase):
    name: str
    email: str

@app.post("/user/login")
def user_login(req: LoginRequest):
    conn = __import__('app.database', fromlist=['get_connection']).get_connection()
    try:
        # Check if user exists
        rows = conn.run(
            "SELECT id, name FROM users WHERE email = :email",
            email=req.email
        )
        if rows:
            return { "user_id": str(rows[0][0]), "name": rows[0][1], "returning": True }
        else:
            # Create new user
            new_rows = conn.run(
                "INSERT INTO users (name, email) VALUES (:name, :email) RETURNING id, name",
                name=req.name, email=req.email
            )
            return { "user_id": str(new_rows[0][0]), "name": new_rows[0][1], "returning": False }
    finally:
        conn.close()


@app.get("/", response_class=FileResponse)
def serve_frontend():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok", "service": "deadline-survival-ai"}

@app.post("/orchestrate", response_model=OrchestrationResponse)
def orchestrate(req: OrchestrationRequest):
    try:
        result = run_orchestrator(
            user_id=req.user_id,
            message=req.message,
            history=req.conversation_history or []
        )
        return OrchestrationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{user_id}")
def get_tasks(user_id: str):
    try:
        tasks = fetch_user_tasks(user_id)
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/{user_id}")
def get_memory(user_id: str):
    from app.database import fetch_user_memory
    try:
        return fetch_user_memory(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/model")
def health_model():
    try:
        from app.agents.utils import generate_with_retry
        result = generate_with_retry("Reply with only the word: OK", retries=2, delay=5)
        return {"model_status": "available", "response": result}
    except Exception as e:
        return {"model_status": "unavailable", "error": str(e)}

@app.get("/status")
def status():
    from app.database import get_connection
    try:
        conn = get_connection()
        conn.run("SELECT 1")
        conn.close()
        db = "connected"
    except:
        db = "error"
    return {
        "service": "ChronoPilot",
        "version": "1.0.0",
        "model": "gemini-3-flash-preview",
        "database": db,
        "agents": ["planner","priority","scheduler","executor","memory"],
        "status": "operational"
    }

@app.get("/")
def root():
    return {"message": "Deadline Survival AI is running"}