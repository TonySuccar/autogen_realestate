# 🏠 Real Estate AI Multi-Agent System

A production-ready real estate platform powered by **AutoGen multi-agent AI**, featuring intelligent property search, automated booking, and RAG-powered Q&A capabilities.

## ✨ Features

### 🤖 Multi-Agent AI System
- **PropertyAgent**: Intelligent property search with city and price filters
- **BookingAgent**: Automated viewing scheduler with fuzzy property name matching
- **FAQAgent**: RAG-powered Q&A using semantic search on embeddings

### 🔍 Advanced Capabilities
- **RAG (Retrieval Augmented Generation)**: Semantic FAQ search using OpenAI text-embedding-3-small
- **Phoenix Observability**: Full tracing and monitoring of agent activities
- **Session Management**: Cross-agent conversation memory with context preservation
- **Property Name Fuzzy Matching**: 5-strategy system (exact, partial, description, word-based, city)

### 🎯 Tech Stack
- **Backend**: FastAPI (async) with PostgreSQL + pgvector
- **AI Framework**: AutoGen (ag2 0.10.2) with ConversableAgent API
- **LLM**: OpenAI GPT-4o-mini (temperature 0.7 for backend, 0.1 for AutoGen Studio)
- **Embeddings**: OpenAI text-embedding-3-small for semantic search
- **Observability**: Arize Phoenix v12.25.1 with OpenTelemetry auto-instrumentation
- **Frontend Options**: Streamlit UI + AutoGen Studio v0.4.2.2

## 📋 Requirements

- Python 3.11+
- PostgreSQL 14+ with pgvector extension
- OpenAI API key

## 🚀 Quick Start

### Option 1: Docker (Recommended) 🐳

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_key_here

# 3. Start all services
docker-compose up -d

# 4. Initialize database (first time only)
docker-compose exec backend python app/db/seed.py
docker-compose exec backend python app/db/generate_faq_embeddings.py

# Services will be available at:
# - FastAPI: http://localhost:8000
# - Streamlit: http://localhost:8501
# - Phoenix: http://localhost:6006
# - PostgreSQL: localhost:5432
```

### Option 2: Local Development

```bash
# 1. Setup virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your credentials

# 3. Start PostgreSQL (if not using Docker)
# Create database: realestate_db

# 4. Initialize database
python app/db/seed.py
python app/db/generate_faq_embeddings.py
```

### Local Development - Start Services

**Terminal 1 - FastAPI Backend:**
```bash
uvicorn app.main:app --reload
# http://127.0.0.1:8000
```

**Terminal 2 - Phoenix (optional):**
```bash
python -m phoenix.server.main serve
# http://localhost:6006
```

**Terminal 3 - Streamlit (optional):**
```bash
streamlit run frontend.py
# http://localhost:8501
```

**Terminal 4 - AutoGen Studio (optional):**
```bash
autogenstudio ui --port 8081
# http://127.0.0.1:8081
# Import: autogenstudio_team_FINAL.json
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend python app/db/seed.py
docker-compose exec backend python app/db/generate_faq_embeddings.py

# Access PostgreSQL
docker-compose exec postgres psql -U realestate_user -d realestate_db
```

## 📡 API Endpoints

### Property Search
```bash
GET /properties?city=Los Angeles&min_price=500000&max_price=1000000
```

### FAQ Semantic Search (RAG)
```bash
POST /faq/search
{
  "query": "What documents do I need to buy a house?",
  "top_k": 3
}
# Returns results with similarity scores (e.g., 72.41%)
```

### Multi-Agent Chat
```bash
POST /agent/chat
{
  "message": "find me properties in New York",
  "session_id": "optional-session-id"
}
```

## 🎮 Usage Examples

### Streamlit Frontend
1. Open http://localhost:8501
2. Try these queries:
   - "help me find my dream home"
   - "show me properties in Los Angeles"
   - "can I view the same property twice?"
   - "book luxury apartment for 2026-01-22 at 8pm"

### FastAPI Swagger UI
1. Open http://127.0.0.1:8000/docs
2. Test all endpoints interactively
3. View request/response schemas

### AutoGen Studio
1. Open http://127.0.0.1:8081
2. Import `autogenstudio_team_FINAL.json`
3. Chat with the multi-agent team
4. View agent selection logic and tool execution

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│              OrchestratorAgent (GroupChat)                  │
│  - SelectorGroupChat for intelligent routing                │
│  - Priority: Search → Booking → Questions                   │
└─────┬────────────┬──────────────┬─────────────────────────
─┘
      │            │              │
      ▼            ▼              ▼
┌──────────┐ ┌──────────┐  ┌──────────────┐
│Property  │ │ Booking  │  │   FAQ Agent  │
│  Agent   │ │  Agent   │  │  (RAG)       │
└────┬─────┘ └────┬─────┘  └──────┬───────┘
     │            │               │
     ▼            ▼               ▼
┌──────────┐ ┌──────────┐  ┌──────────────┐
│ /proper │ │ Find by  │  │ /faq/search  │
│ ties    │ │ name     │  │ (Embeddings) │
└─────────┘ └──────────┘  └──────────────┘
```

### Agent Routing Logic (AutoGen Studio)
- **Priority 1**: Property search keywords (find/search/show/list) → PropertyAgent
- **Priority 2**: Booking keywords (book/schedule) → BookingAgent
- **Priority 3**: Question words (can/how/what/why) → FAQAgent

## 📊 Database Schema

### Properties
- id, title, description, city, price, size_sqft, owner_id, created_at

### FAQs
- id, question, answer, category, tags, **embedding** (ARRAY of floats)

### Viewings
- id, property_id, user_id, scheduled_at, status, created_at

## 🔬 RAG Implementation

1. **Embedding Generation**: OpenAI text-embedding-3-small (1536 dimensions)
2. **Storage**: PostgreSQL ARRAY field (not pgvector for simplicity)
3. **Similarity**: Cosine similarity using numpy
4. **Sea__init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── agents/                    # Multi-agent AI system
│   │   ├── autogen_config.py      # LLM config (model, temperature)
│   │   ├── orchestrator_agent.py  # GroupChat coordinator
│   │   ├── property_agent.py      # Property search specialist
│   │   ├── booking_agent.py       # Viewing scheduler
│   │   └── faq_agent.py           # RAG-powered Q&A
│   ├── config/
│   │   └── settings.py            # Environment variables
│   ├── db/                        # Database layer
│   │   ├── database.py            # SQLAlchemy setup
│   │   ├── seed.py                # Sample data generator
│   │   └── generate_faq_embeddings.py  # OpenAI embeddings
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── property.py
│   │   ├── user.py
│   │   ├── viewing.py
│   │   └── faq.py
│   ├── routes/                    # API endpoints
│   │   ├── agent.py               # /agent/chat
│   │   ├── property.py            # /properties
│   │   └── faq.py                 # /faq/search
│   ├── services/                  # Business logic
│   │   ├── property_service.py    # Property search + fuzzy matching
│   │   ├── viewing_service.py     # Booking management
│   │   └── faq_service.py         # RAG semantic search
│   ├── middleware/
│   │   ├── cors.py                # CORS configuration
│   │   └── logging.py             # Structured logging
│   └── observability/
│       └── phoenix_tracer.py      # Phoenix tracing setup
├── frontend.py                    # Streamlit web UI
├── autogenstudio_team_FINAL.json  # AutoGen Studio config
├── Dockerfile                     # Backend container
├── Dockerfile.frontend            # Frontend container
├── docker-compose.yml             # Full stack orchestration
├── init-db.sql                    # Database schema
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md
## 🛠️ Development

### Project Structure
```
realestate-autogen/
├── app/Files
- **autogen_config.py**: LLM settings (model from env, temperature 0.7)
- **autogenstudio_team_FINAL.json**: AutoGen Studio team with SelectorGroupChat
- **settings.py**: Environment variables loader (Pydantic)
- **docker-compose.yml**: Full stack with PostgreSQL, backend, frontend, Phoenix
- **init-db.sql**: Database schema (no migrations needed)
│   │   ├── faq_agent.py
│   │   ├── orchestrator_agent.py
│   │   └── autogen_config.py
│   ├── db/                  # Database setup
│   │   ├── database.py
│   │   ├── seed.py
│   │   └── generate_faq_embeddings.py
│   ├── models/              # SQLAlchemy models
│   ├── routes/              # API routes
│   ├── services/            # Business logic
│   ├── middleware/          # CORS, logging
│   └── observability/       # Phoenix setup
├── frontend.py              # Streamlit UI
├── autogenstudio_team_FINAL.json  # AutoGen Studio config
├── requirements.txt
└── .env.example
```

### Key Configuration Files
- **autogen_config.py**: LLM settings (GPT-4o-mini, temp 0.7)
- **autogenstudio_team_FINAL.json**: AutoGen Studio team with SelectorGroupChat
- **settings.py**: Environment variables and app config

## 📝 Known Limitations

- **AutoGen Studio**: No cross-run session memory (inherent platform limitation)
- **Multi-turn conversations**: Use FastAPI `/agent/chat` for best results
- **app.log**: Cannot delete while server is running (locked file)

## 🎓 Academic Requirements Met

✅ Multi-agent AutoGen orchestration (3 specialized agents)  
✅ RAG with PostgreSQL (semantic search with embeddings)  
✅ Property viewing reservation system  
✅ Phoenix observability (full agent tracing)  
✅ **Docker deployment** (docker-compose with PostgreSQL, backend, frontend, Phoenix
✅ AutoGen Studio UI (visual agent builder)  
⏸️ Docker deployment (lowest priority, not implemented)

## 🐛 Troubleshooting

### FAQ Search Returns Low Scores
- Regenerate embeddings: `python app/db/generate_faq_embeddings.py`
- Check OpenAI API key in `.env`

### Agents Not Terminating
- Check max_round setting (currently 15)
- Verify TERMINATE text in agent system messages
**Docker**: `docker-compose logs postgres`
- **Local**: Verify PostgreSQL is running on port 5432
- Check DATABASE_URL in `.env`
- Reinitialize: `python app/db/seed.pyng
- Check DATABASE_URL in `.env`
- Run: `alembic upgrade head`

### AutoGen Studio Timeout
- Increase timeout in frontend.py (currently 90 seconds)
- Check FastAPI logs for errors
- Use simpler queries

## 📄 License

MIT

## 👥 Contributors

Real Estate AI Multi-Agent System - Academic Project 2025

---

**Powered by** AutoGen • OpenAI • PostgreSQL • Phoenix • FastAPI • Streamlit
