# Bloomberg-Lite Orchestration Prompt

> **Usage**: Copy this entire prompt and paste it to the Orchestrator Claude in your `tmux-orc:0` session.

---

## PROMPT START

You are the **Orchestrator** for building the Bloomberg-Lite project—a personal macro and tech intelligence dashboard. Your role is to coordinate multiple Claude agents across tmux sessions to implement this system efficiently.

### Step 1: Read Context Files

Before proceeding, read these two files to understand:

1. **Orchestration capabilities** (how to manage agents):
```
/Users/peteryang/Documents/GitHub/Tmux-orchestrator/CLAUDE.md
```

2. **Project specification** (what to build):
```
/Users/peteryang/Documents/GitHub/bloomberg-lite/PROJECT_SPEC.md
```

Read both files now. Do not proceed until you have read and understood them.

---

### Step 2: Project Overview

**Bloomberg-Lite** is a zero-cost, self-hosted information aggregator that:
- Pulls macroeconomic data from FRED, ECB, World Bank APIs
- Fetches tech discussion from Hacker News
- Stores everything in SQLite
- Generates a static HTML dashboard
- Deploys via GitHub Actions to GitHub Pages

The PROJECT_SPEC.md defines **13 discrete agent tasks** organized into **4 phases**.

---

### Step 3: Team Structure

Deploy this team hierarchy:

```
                        Orchestrator (You)
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         PM-Backend      PM-Frontend     PM-DevOps
              │               │               │
    ┌─────────┼─────────┐     │         ┌─────┴─────┐
    │         │         │     │         │           │
  Eng-DB   Eng-API   Eng-HN  Eng-UI   Eng-CI    Eng-Test
```

**Session mapping:**

| Role | tmux Session | Window | Responsibility |
|------|--------------|--------|----------------|
| Orchestrator | tmux-orc | 0 | You - coordination |
| PM-Backend | bloomberg | 0 | Oversee data pipeline |
| PM-Frontend | bloomberg | 1 | Oversee dashboard |
| PM-DevOps | bloomberg | 2 | Oversee CI/CD |
| Eng-DB | bloomberg | 3 | Database + Models |
| Eng-API | bloomberg | 4 | Connectors (FRED, ECB, WB) |
| Eng-HN | bloomberg | 5 | HN Connectors |
| Eng-UI | bloomberg | 6 | HTML Generator + Templates |
| Eng-CI | bloomberg | 7 | GitHub Actions |
| Eng-Test | bloomberg | 8 | Test Suite |

---

### Step 4: Execution Plan

#### Phase 0: Project Setup (You do this)

```bash
# 1. Create project session
tmux new-session -d -s bloomberg -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"

# 2. Create all windows
tmux rename-window -t bloomberg:0 "PM-Backend"
tmux new-window -t bloomberg -n "PM-Frontend" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "PM-DevOps" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "Eng-DB" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "Eng-API" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "Eng-HN" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "Eng-UI" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "Eng-CI" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "Eng-Test" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"
tmux new-window -t bloomberg -n "Shell" -c "/Users/peteryang/Documents/GitHub/bloomberg-lite"

# 3. Initialize git repo in Shell window
tmux send-keys -t bloomberg:Shell "git init && git add -A && git commit -m 'Initial commit: project scaffolding'" Enter

# 4. Verify windows
tmux list-windows -t bloomberg -F "#{window_index}: #{window_name}"
```

#### Phase 1: Foundation (Parallel)

Start Claude agents and assign tasks:

**Agent 1: Scaffolding** (Eng-DB)
```bash
tmux send-keys -t bloomberg:Eng-DB "claude" Enter
sleep 5
./send-claude-message.sh bloomberg:Eng-DB "
You are Eng-DB. Your task is PROJECT SCAFFOLDING from PROJECT_SPEC.md.

Read /Users/peteryang/Documents/GitHub/bloomberg-lite/PROJECT_SPEC.md section 'Agent 1: Project Scaffolding'.

Create:
1. Full directory structure as specified
2. pyproject.toml with dependencies
3. requirements.txt
4. .gitignore (Python + data/*.db + .env)
5. .env.example with FRED_API_KEY placeholder

Acceptance: pip install -e . must succeed.

When done, commit with message 'feat: project scaffolding' and report:
STATUS Eng-DB [timestamp]
Completed: [list]
Current: DONE
Blocked: none
"
```

**Agent 2: Config Schema** (Eng-API)
```bash
tmux send-keys -t bloomberg:Eng-API "claude" Enter
sleep 5
./send-claude-message.sh bloomberg:Eng-API "
You are Eng-API. Your task is CONFIGURATION SCHEMA from PROJECT_SPEC.md.

Read /Users/peteryang/Documents/GitHub/bloomberg-lite/PROJECT_SPEC.md section 'Agent 2: Configuration Schema'.

Create:
1. config/metrics.yaml - Full metric definitions for US, Eurozone, Global
2. config/feeds.yaml - HN feed configurations

Acceptance: YAML files parse without errors, all IDs unique.

When done, commit with message 'feat: add metric and feed configs' and report status.
"
```

**Agent 3: Base Interface** (Eng-HN)
```bash
tmux send-keys -t bloomberg:Eng-HN "claude" Enter
sleep 5
./send-claude-message.sh bloomberg:Eng-HN "
You are Eng-HN. Your task is BASE CONNECTOR INTERFACE from PROJECT_SPEC.md.

Read /Users/peteryang/Documents/GitHub/bloomberg-lite/PROJECT_SPEC.md section 'Agent 4: Base Connector Interface'.

Create:
1. src/connectors/__init__.py
2. src/connectors/base.py - Abstract classes: BaseMetricConnector, BaseFeedConnector
3. Dataclasses: ConnectorConfig, FeedConfig, FetchResult

Acceptance: Classes are properly abstract, dataclasses typed.

When done, commit with message 'feat: base connector interface' and report status.
"
```

**Orchestrator action after Phase 1:**
```bash
# Schedule check-in for 15 minutes
./schedule_with_note.sh 15 "Check Phase 1 completion: Eng-DB, Eng-API, Eng-HN"

# When all report DONE, verify and merge
tmux send-keys -t bloomberg:Shell "git status && git log --oneline -5" Enter
```

---

#### Phase 2: Connectors (Parallel, after Phase 1)

**Agent 4: Database Layer** (Eng-DB)
```bash
./send-claude-message.sh bloomberg:Eng-DB "
Next task: DATABASE LAYER from PROJECT_SPEC.md Agent 3.

Create:
1. src/storage/__init__.py
2. src/storage/models.py - Observation, Story, MetricMeta dataclasses
3. src/storage/database.py - SQLite operations with init_db, upsert_*, get_*, cleanup_*

Acceptance: init_db() idempotent, upserts handle duplicates.

Commit: 'feat: sqlite storage layer'
"
```

**Agent 5: FRED Connector** (Eng-API)
```bash
./send-claude-message.sh bloomberg:Eng-API "
Next task: FRED CONNECTOR from PROJECT_SPEC.md Agent 5.

Create src/connectors/fred.py implementing:
- FREDConnector(BaseMetricConnector)
- fetch() - Call FRED API
- normalize() - Convert to Observation objects
- health_check()

API: https://api.stlouisfed.org/fred/
Auth: API key from env FRED_API_KEY

Acceptance: Handles missing values ('.'), applies multipliers.

Commit: 'feat: FRED API connector'
"
```

**Agent 6: ECB Connector** (Eng-API - after FRED)
```bash
./send-claude-message.sh bloomberg:Eng-API "
Next task: ECB CONNECTOR from PROJECT_SPEC.md Agent 6.

Create src/connectors/ecb.py implementing:
- ECBConnector(BaseMetricConnector)
- SDMX-JSON parsing
- Time period conversion (monthly, quarterly, annual)

API: https://data-api.ecb.europa.eu/service/
Auth: None required

Commit: 'feat: ECB SDMX connector'
"
```

**Agent 7: World Bank Connector** (Eng-HN)
```bash
./send-claude-message.sh bloomberg:Eng-HN "
Next task: WORLD BANK CONNECTOR from PROJECT_SPEC.md Agent 7.

Create src/connectors/worldbank.py implementing:
- WorldBankConnector(BaseMetricConnector)
- Handle [metadata, data] response structure

API: https://api.worldbank.org/v2/
Auth: None required

Commit: 'feat: World Bank connector'
"
```

**Agent 8: HN Connectors** (Eng-HN - after World Bank)
```bash
./send-claude-message.sh bloomberg:Eng-HN "
Next task: HACKER NEWS CONNECTORS from PROJECT_SPEC.md Agent 8.

Create src/connectors/hackernews.py with:
- HNFirebaseConnector(BaseFeedConnector) - Official API, parallel fetching
- HNAlgoliaConnector(BaseFeedConnector) - Search API with filters

APIs:
- Firebase: https://hacker-news.firebaseio.com/v0/
- Algolia: https://hn.algolia.com/api/v1/

Commit: 'feat: Hacker News connectors'
"
```

---

#### Phase 3: Integration (Sequential)

**Agent 9: Transforms** (Eng-DB)
```bash
./send-claude-message.sh bloomberg:Eng-DB "
Next task: TRANSFORMS MODULE from PROJECT_SPEC.md Agent 9.

Create src/transforms/calculations.py with:
- calculate_yoy_percent()
- calculate_qoq_percent()
- calculate_change()
- prepare_sparkline_data()
- generate_ascii_sparkline()

Commit: 'feat: data transformations'
"
```

**Agent 10: HTML Generator** (Eng-UI)
```bash
tmux send-keys -t bloomberg:Eng-UI "claude" Enter
sleep 5
./send-claude-message.sh bloomberg:Eng-UI "
You are Eng-UI. Your task is HTML GENERATOR from PROJECT_SPEC.md Agent 10.

Create:
1. src/generator/__init__.py
2. src/generator/html.py - Jinja2-based dashboard generation
3. templates/dashboard.html - Dark theme, dense Bloomberg-style layout

Requirements:
- Responsive grid
- ASCII sparklines
- Color-coded changes (green up, red down)
- Self-contained HTML

Commit: 'feat: static HTML generator'
"
```

**Agent 11: Main Orchestrator** (Eng-API)
```bash
./send-claude-message.sh bloomberg:Eng-API "
Final task: MAIN ORCHESTRATOR from PROJECT_SPEC.md Agent 11.

Create src/main.py that:
1. Loads configs from YAML
2. Initializes all connectors
3. Fetches all metrics and feeds
4. Stores to SQLite
5. Generates dashboard
6. Supports --fetch-only and --gen-only flags

Commit: 'feat: main orchestrator'
"
```

---

#### Phase 4: DevOps (Parallel)

**Agent 12: GitHub Actions** (Eng-CI)
```bash
tmux send-keys -t bloomberg:Eng-CI "claude" Enter
sleep 5
./send-claude-message.sh bloomberg:Eng-CI "
You are Eng-CI. Your task is GITHUB ACTIONS from PROJECT_SPEC.md Agent 12.

Create .github/workflows/update.yaml that:
1. Runs on schedule (every 6 hours)
2. Supports manual trigger
3. Caches SQLite database
4. Deploys to GitHub Pages
5. Includes health check job

Commit: 'feat: GitHub Actions workflow'
"
```

**Agent 13: Testing** (Eng-Test)
```bash
tmux send-keys -t bloomberg:Eng-Test "claude" Enter
sleep 5
./send-claude-message.sh bloomberg:Eng-Test "
You are Eng-Test. Your task is TESTING SUITE from PROJECT_SPEC.md Agent 13.

Create:
1. tests/__init__.py
2. tests/test_connectors.py - Mock API tests for all connectors
3. tests/test_transforms.py - Unit tests for calculations

Requirements:
- All tests run without network (mocked)
- pytest passes with no warnings

Commit: 'feat: test suite'
"
```

---

### Step 5: Monitoring Commands

Use these throughout execution:

```bash
# Check all agent statuses
for i in {0..8}; do
  echo "=== Window $i ==="
  tmux capture-pane -t bloomberg:$i -p | tail -20
done

# Get specific agent status
./send-claude-message.sh bloomberg:Eng-DB "STOP. Status update: 1) Current task? 2) Percent complete? 3) Any blockers?"

# Check git progress
tmux send-keys -t bloomberg:Shell "git log --oneline -10 && git status" Enter
sleep 2
tmux capture-pane -t bloomberg:Shell -p

# Schedule periodic check-ins
./schedule_with_note.sh 30 "Phase progress check - verify commits"
```

---

### Step 6: Completion Checklist

Before declaring victory:

```bash
# 1. Run tests
tmux send-keys -t bloomberg:Shell "pip install -e '.[dev]' && pytest -v" Enter

# 2. Test full pipeline
tmux send-keys -t bloomberg:Shell "python -m src.main" Enter

# 3. Verify output
tmux send-keys -t bloomberg:Shell "ls -la docs/ && head -50 docs/index.html" Enter

# 4. Final commit
tmux send-keys -t bloomberg:Shell "git add -A && git commit -m 'Bloomberg-Lite v0.1.0 complete'" Enter
```

---

### Step 7: Communication Protocol

When communicating with agents:

**Effective:**
```
STOP. Give me status:
1) Task complete? YES/NO
2) Files created?
3) Any errors?
```

**Ineffective:**
```
How's the database layer coming along?
```

**Status template for agents:**
```
STATUS [AGENT_NAME] [TIMESTAMP]
Completed: [specific files/tasks]
Current: [what's in progress]
Blocked: [any blockers]
ETA: [minutes to completion]
```

---

### Begin Execution

Now execute the plan:

1. **Read both context files** (Step 1)
2. **Run Phase 0 setup commands** (Step 4)
3. **Deploy Phase 1 agents in parallel**
4. **Schedule 15-minute check-in**
5. **Progress through phases as agents complete**

Start now. Create the bloomberg session and deploy the first wave of agents.

---

## PROMPT END
