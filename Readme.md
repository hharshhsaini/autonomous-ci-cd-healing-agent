#  RIFT Healing Agent - Autonomous DevOps AI

An intelligent multi-agent system that automatically fixes code errors, runs tests, and ensures CI/CD pipeline success.

##  Features

- **Autonomous Error Detection**: Automatically discovers and runs all test files
- **Intelligent Fixing**: Uses GPT-4o to generate targeted fixes for failures
- **CI/CD Integration**: Monitors pipeline and iterates until all tests pass
- **Multi-Language Support**: Python, JavaScript, TypeScript, Java, Go, Rust
- **Production Dashboard**: Real-time React dashboard with comprehensive analytics

##  Architecture

### Multi-Agent System (LangGraph)
1. **Clone Agent** - Clones repository
2. **Copybara Transform** - Normalizes code format
3. **Test Agent** - Runs language-specific tests
4. **Analyze Agent** - Parses errors and categorizes
5. **Fix Agent** - Generates fixes using GPT-4o
6. **Verify Agent** - Re-runs tests to confirm fixes
7. **Push Agent** - Commits and pushes to new branch

### Tech Stack
- **Backend**: FastAPI + LangGraph + OpenAI GPT-4o
- **Frontend**: React + Vite + Recharts
- **Deployment**: Docker + Docker Compose

##  Dashboard Features

### 1. Input Section
- GitHub Repository URL
- Team Name (e.g., "RIFT ORGANISERS")
- Team Leader Name (e.g., "Saiyam Kumar")
- Run Agent button with loading indicator

### 2. Run Summary Card
- Repository URL analyzed
- Team name and leader
- Branch created: `TEAMNAME_LEADERNAME_AI_Fix`
- Total failures detected and fixes applied
- CI/CD status badge: **PASSED** (green) / **FAILED** (red)
- Total time taken

### 3. Score Breakdown Panel
- **Base Score**: 100 points
- **Speed Bonus**: +10 if completed < 5 minutes
- **Efficiency Penalty**: -2 per commit over 20
- **Final Total Score** with visual progress bars

### 4. Fixes Applied Table
Columns: File | Bug Type | Line Number | Commit Message | Status

Bug Types:
- `LINTING` (green)
- `SYNTAX` (red)
- `LOGIC` (purple)
- `TYPE_ERROR` (orange)
- `IMPORT` (cyan)
- `INDENTATION` (yellow)

Status: ✓ Fixed (green) | ✗ Failed (red)

### 5. CI/CD Status Timeline
- Visual timeline showing each iteration
- Pass/fail badge for each run
- Iteration count (e.g., "3/5")
- Timestamps for each run

##  Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key
- GitHub Personal Access Token

### Setup

1. **Clone Repository**
```bash
git clone <your-repo-url>
cd rift-healing-agent
```

2. **Configure Environment**
```bash
# backend/.env
OPENAI_API_KEY=sk-proj-your-key-here
GITHUB_TOKEN=ghp_your-token-here
```

3. **Start Services**
```bash
docker-compose up -d
```

4. **Access Dashboard**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

##  Branch Naming Convention

**Format**: `TEAMNAME_LEADERNAME_AI_Fix`

Rules:
- All UPPERCASE
- Replace spaces with underscores (_)
- End with `_AI_Fix`
- No special characters except underscores

Examples:
- Team: "RIFT ORGANISERS", Leader: "Saiyam Kumar" → `RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix`
- Team: "Code Warriors", Leader: "John Doe" → `CODE_WARRIORS_JOHN_DOE_AI_Fix`

##  API Endpoints

### POST `/api/run-agent`
Start a new healing agent run

**Request:**
```json
{
  "github_url": "https://github.com/user/repo",
  "team_name": "RIFT ORGANISERS",
  "leader_name": "Saiyam Kumar",
  "branch_name": "RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix"
}
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "branch_name": "RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix"
}
```

### GET `/api/stream/{job_id}`
Server-Sent Events stream for real-time updates

### GET `/api/results/{job_id}`
Get final results including `results.json`

### GET `/api/health`
Health check endpoint

##  Test Case Format

The agent outputs match this EXACT format:

```
LINTING error in src/utils.py line 15 → Fix: remove the import statement
SYNTAX error in src/validator.py line 8 → Fix: add the colon at the correct position
LOGIC error in src/models.py line 42 → Fix: fix the logic error causing test failure
TYPE_ERROR error in src/auth.py line 19 → Fix: fix the type annotation
IMPORT error in src/db.py line 3 → Fix: fix missing import path
INDENTATION error in src/config.py line 27 → Fix: fix indentation block
```

##  Scoring System

- **Base Score**: 100 points
- **Speed Bonus**: +10 points if completed in < 5 minutes
- **Commit Penalty**: -2 points per commit over 20
- **Maximum Score**: 110 points

##  Security

- Sandboxed code execution with timeouts
- No Docker-in-Docker (direct subprocess execution)
- Environment variable isolation
- GitHub token with minimal required scopes

##  Project Structure

```
rift-healing-agent/
├── backend/
│   ├── agent/
│   │   ├── nodes/          # Agent nodes
│   │   ├── orchestrator.py # LangGraph workflow
│   │   ├── parsers.py      # Error parsers
│   │   └── state.py        # State management
│   ├── main.py             # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Dashboard, Run, Results
│   │   ├── hooks/          # Custom hooks
│   │   └── utils/          # Utilities
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

##  Testing

```bash
# Test with a sample repository
curl -X POST http://localhost:8000/api/run-agent \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/user/buggy-repo",
    "team_name": "RIFT ORGANISERS",
    "leader_name": "Saiyam Kumar"
  }'
```

##  Deployment

### Frontend (Vercel/Netlify)
```bash
cd frontend
npm run build
# Deploy dist/ folder
```

### Backend (Railway/Render)
```bash
# Set environment variables
OPENAI_API_KEY=your-key
GITHUB_TOKEN=your-token

# Deploy using Docker
```

##  License

MIT License

##  Team Name - Room no.518

1. Harsh Saini (Leader)
2. Anurag Singh
3. Varun Yadav
4. Aditya Chauhan

Built for RIFT 2026 Hackathon

---

**Status**: Production Ready |  Competition Compliant |  Fully Functional
