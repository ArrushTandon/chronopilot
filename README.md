# 🧭 ChronoPilot — Autonomous AI Productivity Co-Pilot

> **Gen AI Academy APAC Edition Hackathon Submission**  
> Multi-Agent AI System · Google Cloud · AlloyDB · Gemini 3 Flash Preview

---

## 🚀 Live Demo

🔗 **[chronopilot-754173513004.asia-south1.run.app](https://chronopilot-754173513004.asia-south1.run.app/)**  
📊 **[/status](https://chronopilot-754173513004.asia-south1.run.app/status)** — Live system health check

---

## 🧠 What is ChronoPilot?

ChronoPilot is an autonomous multi-agent AI system that helps students and professionals survive deadline crises. Unlike a regular chatbot that just suggests actions, ChronoPilot **autonomously plans, prioritises, schedules, and saves tasks** — and gets smarter about you with every session through persistent memory.

**The problem:** Students and professionals drown in deadline chaos. Most AI tools give advice. ChronoPilot acts.

**The solution:** A coordinated team of 5 AI agents that decompose your goals, rank your tasks, build a schedule, save everything to a database, and learn your work patterns over time.

---

## ✨ Key Features

- **Multi-Agent Orchestration** — 5 specialised agents coordinated by an Orchestrator
- **Persistent Memory** — Learns your productive hours, estimation accuracy, and completion rate across sessions
- **Smart Routing** — Fast-path keyword routing saves quota; Gemini decides routing for ambiguous messages
- **Conversational Mode** — Casual messages get a direct reply without triggering the full agent pipeline
- **Multi-User Support** — Email-based identity, each user gets their own memory profile in AlloyDB
- **Real-Time UI** — Agent status animations, execution log streaming, and task board update live

---

## 🤖 The 5 Agents

| Agent | Role |
|-------|------|
| **Orchestrator** | Reads user message, decides which agents to invoke, generates final reply |
| **Planner** | Decomposes goals into 3–8 tasks, adjusts time estimates using your historical accuracy |
| **Priority** | Scores tasks using urgency × importance × effort formula (0.0 to 1.0) |
| **Scheduler** | Assigns time blocks within your productive hours with 15-min breaks |
| **Executor** | Saves tasks and session logs to AlloyDB |
| **Memory** | Updates your profile after every session — completion rate, estimation accuracy, underestimate factor |

---

## 🏗️ Architecture

```
User (Browser)
      │ HTTPS
      ▼
FastAPI on Cloud Run  ←──────────────────────────────┐
      │                                              │
      │ Private IP (easy-alloydb-vpc)      Gemini 3 Flash Preview
      ▼                                    (Google AI Studio API)
AlloyDB for PostgreSQL                              │
  ├── users (memory profiles)          ┌────────────┴────────────┐
  ├── tasks                            │         Agents          │
  ├── sessions                         │  Orchestrator           │
  ├── execution_logs                   │  Planner                │
  └── negotiations                     │  Priority               │
                                       │  Scheduler              │
                                       │  Memory                 │
                                       │  Executor ──► AlloyDB   │
                                       └─────────────────────────┘
```

**GCP Services Used:**
- **Cloud Run** — Backend hosting (asia-south1)
- **AlloyDB for PostgreSQL** — Persistent storage with pgvector
- **VPC / Private Networking** — Secure Cloud Run → AlloyDB connection
- **Google AI Studio API** — Gemini 3 Flash Preview (competition-exclusive model)

---

## 🗄️ Database Schema

| Table | Purpose |
|-------|---------|
| `users` | Profile + learned memory (productive hours, completion rate, estimation accuracy) |
| `tasks` | All tasks with priority scores, deadlines, time estimates |
| `sessions` | Every conversation session with agent invocation log |
| `execution_logs` | Granular action log per agent per session |
| `negotiations` | Multi-user conflict resolution (future feature) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Vanilla HTML/CSS/JS (served by FastAPI) |
| AI Model | Gemini 3 Flash Preview via Google AI Studio |
| Database | AlloyDB for PostgreSQL + pgvector |
| Deployment | Google Cloud Run (asia-south1) |
| Networking | GCP VPC with private service access |

---

## ⚙️ Running Locally

### Prerequisites
- Python 3.11+
- Google AI Studio API key with `gemini-3-flash-preview` access
- AlloyDB instance (or any PostgreSQL database)

### Setup

```bash
git clone https://github.com/ArrushTandon/chronopilot.git
cd chronopilot

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file:

```bash
GEMINI_API_KEY=your_google_ai_studio_api_key
DB_HOST=your_alloydb_public_ip
DB_PORT=5432
DB_NAME=deadline_survival
DB_USER=postgres
DB_PASS=your_password
```

### Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Visit `http://localhost:8080`

---

## ☁️ Cloud Run Deployment

```bash
gcloud beta run deploy chronopilot \
  --source . \
  --region=asia-south1 \
  --network=easy-alloydb-vpc \
  --subnet=easy-alloydb-subnet \
  --allow-unauthenticated \
  --vpc-egress=all-traffic \
  --set-env-vars GEMINI_API_KEY=YOUR_KEY,DB_HOST=YOUR_PRIVATE_IP,DB_PORT=5432,DB_NAME=deadline_survival,DB_USER=postgres,DB_PASS=alloydb
```

---

## 📁 Project Structure

```
chronopilot/
├── app/
│   ├── main.py              # FastAPI entry point + API routes
│   ├── config.py            # Environment variables
│   ├── database.py          # AlloyDB connection + queries
│   ├── models.py            # Pydantic request/response models
│   └── agents/
│       ├── orchestrator.py  # Master coordinator agent
│       ├── planner.py       # Goal decomposition agent
│       ├── priority.py      # Task ranking agent
│       ├── scheduler.py     # Time block assignment agent
│       ├── executor.py      # Task saving agent
│       ├── memory_agent.py  # User profile learning agent
│       └── utils.py         # Shared Gemini call with retry logic
├── static/
│   ├── index.html           # Frontend UI
│   └── Logo.png             # ChronoPilot logo
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 📊 Diagrams

### Process Flow
![ChronoPilot Process Flow](diagrams/ChronoPilot_Process_Flow_Diagram.png)

### Architecture
![ChronoPilot Architecture](diagrams/ChronoPilot_Architecture_Diagram.png)

---

## 🎯 What Makes This Different

1. **It acts, not advises** — Tasks are written to AlloyDB, not just suggested in chat
2. **Persistent memory** — The system genuinely learns your patterns across sessions
3. **Quota-efficient** — Fast-path routing and conversational mode avoid unnecessary Gemini calls
4. **Real multi-agent coordination** — Each agent has a distinct role; the Orchestrator decides the pipeline dynamically per message

---

## 👤 Author

**Arrush** — Final Year B.Tech Computer Science, SRMIST (NIRF Engineering Rank #14)  
Built for the **Gen AI Academy APAC Edition Hackathon**

---

*Built with ❤️ on Google Cloud Platform*