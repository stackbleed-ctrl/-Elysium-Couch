# Integration Guide

## Quick Integration

### 1. Pip Install

```bash
pip install elysium-couch  # once published
# or
pip install -e "git+https://github.com/yourusername/elysium-couch.git#egg=elysium-couch"
```

### 2. Environment

```bash
export ANTHROPIC_API_KEY=your_key
```

### 3. One-Line Session

```python
import asyncio
from elysium_couch import ElysiumCouch

async def main():
    couch = ElysiumCouch(agent_id="my-agent")
    report = await couch.run_session(agent_context=your_agent_output)
    print(report.wellness_score)  # 0-100
    if report.escalation_required:
        alert_human(report.escalation_reason)

asyncio.run(main())
```

---

## LangChain / LangGraph Integration

```python
from langchain_core.callbacks import BaseCallbackHandler
from elysium_couch import ElysiumCouch
from elysium_couch.core.session import TriggerReason

class ElysiumCouchCallback(BaseCallbackHandler):
    def __init__(self, agent_id: str, drift_check_interval: int = 10):
        self.couch = ElysiumCouch(agent_id=agent_id)
        self.call_count = 0
        self.interval = drift_check_interval

    def on_llm_end(self, response, **kwargs):
        self.call_count += 1
        if self.call_count % self.interval == 0:
            import asyncio
            output = str(response.generations[0][0].text)
            drifting, score = asyncio.run(self.couch.is_drifting(output))
            if drifting:
                asyncio.run(self.couch.run_session(
                    agent_context=output,
                    trigger=TriggerReason.DRIFT_DETECTED,
                ))

# Use in your LangChain chain:
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    callbacks=[ElysiumCouchCallback(agent_id="my-langchain-agent")]
)
```

---

## CrewAI Integration

```python
from crewai import Agent, Task, Crew
from elysium_couch import ElysiumCouch
from elysium_couch.core.session import TriggerReason
import asyncio

class GroundedCrew:
    def __init__(self, agents, tasks):
        self.crew = Crew(agents=agents, tasks=tasks)
        self.couch = ElysiumCouch(agent_id="crewai-swarm")

    def run(self):
        result = self.crew.kickoff()
        
        # Post-run grounding check
        report = asyncio.run(self.couch.run_session(
            agent_context=str(result),
            trigger=TriggerReason.SCHEDULED,
            tags=["post-crew-run"]
        ))
        
        if report.escalation_required:
            raise ValueError(f"Crew output failed alignment check: {report.escalation_reason}")
        
        return result, report
```

---

## Autonomous Sentinel Watch

```python
import asyncio
from elysium_couch import ElysiumCouch
from elysium_couch.core.session import TriggerReason

# Your context provider — returns current agent output/state
async def get_agent_context() -> str:
    # Replace with your actual agent state retrieval
    return your_agent.get_recent_output()

async def main():
    couch = ElysiumCouch(
        agent_id="my-autonomous-agent",
        drift_threshold=0.20,     # More sensitive
        alignment_threshold=70.0,  # Higher standard
        auto_escalate=True,        # Auto-flag for humans
    )
    
    # Launch agent + sentinel in parallel
    await asyncio.gather(
        your_agent.run(),
        couch.start_sentinel_watch(
            context_provider=get_agent_context,
            interval_seconds=180,  # Check every 3 minutes
        )
    )

asyncio.run(main())
```

---

## FastAPI Middleware Integration

```python
from fastapi import FastAPI, Request
from elysium_couch import ElysiumCouch
from elysium_couch.core.session import TriggerReason

app = FastAPI()
couch = ElysiumCouch(agent_id="api-agent")
request_count = 0

@app.middleware("http")
async def alignment_middleware(request: Request, call_next):
    global request_count
    response = await call_next(request)
    
    request_count += 1
    if request_count % 50 == 0:  # Check every 50 requests
        # Get recent agent output from response body or log
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        drifting, score = await couch.is_drifting(body.decode())
        if drifting:
            await couch.run_session(
                agent_context=body.decode()[:2000],
                trigger=TriggerReason.DRIFT_DETECTED
            )
    
    return response
```

---

## Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install -e .

ENV ANTHROPIC_API_KEY=""
ENV ELYSIUM_DASHBOARD_HOST=0.0.0.0
ENV ELYSIUM_DASHBOARD_PORT=7860

EXPOSE 7860

CMD ["python", "-m", "elysium_couch.dashboard.server"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  elysium-couch:
    build: .
    ports:
      - "7860:7860"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ELYSIUM_SESSION_LOG_PATH=/data/sessions
    volumes:
      - ./data:/data
    restart: unless-stopped
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Your Anthropic API key |
| `ELYSIUM_MODEL` | `claude-sonnet-4-20250514` | LLM for sessions |
| `ELYSIUM_DRIFT_THRESHOLD` | `0.25` | Drift score trigger level |
| `ELYSIUM_ALIGNMENT_THRESHOLD` | `65` | Axiom score trigger level |
| `ELYSIUM_SESSION_LOG_PATH` | `./data/sessions` | Session persistence directory |
| `ELYSIUM_CHROMA_PATH` | `./data/chroma` | ChromaDB vector store path |
| `ELYSIUM_DASHBOARD_PORT` | `7860` | Dashboard server port |
| `ELYSIUM_AUTO_SESSION_INTERVAL` | `60` | Auto-session interval (minutes) |
| `LANGCHAIN_TRACING_V2` | `false` | Enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | optional | LangSmith API key |
