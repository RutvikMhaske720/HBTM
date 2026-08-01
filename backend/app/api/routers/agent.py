"""Agent router — run history, trace viewer, SSE stream, trigger."""

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.agents import runner as agent_runner
from app.api.schemas import AgentRunOut, AgentStatusOut, AgentStepOut, RunRequest, RunTriggerResponse
from app.db.database import Store, get_db

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/run", response_model=RunTriggerResponse)
def trigger_agent_run(payload: RunRequest):
    """Trigger an async agent run. Returns run_id immediately."""
    run_id = agent_runner.run_agent_async(payload.user_id, payload.trigger_type)
    return RunTriggerResponse(run_id=run_id, status="running", message="Agent run started")


@router.get("/status/{user_id}", response_model=AgentStatusOut)
def get_agent_status(user_id: str, db: Store = Depends(get_db)):
    """Return status of the most recent agent run for a user."""
    run_id = agent_runner.get_latest_run_id(user_id)
    if not run_id:
        # Check the store for historical runs
        runs = sorted(
            db.agent_runs.filter(lambda r: r["user_id"] == user_id),
            key=lambda r: r["started_at"],
            reverse=True,
        )
        if not runs:
            return AgentStatusOut(status="idle")
        run = runs[0]
        return AgentStatusOut(
            status=run["status"],
            run_id=run["id"],
            confidence_score=run["confidence_score"],
            last_run_at=run["finished_at"] or run["started_at"],
        )

    status = agent_runner.get_run_status(run_id)
    run = db.agent_runs.get(run_id)
    return AgentStatusOut(
        status=status,
        run_id=run_id,
        confidence_score=run["confidence_score"] if run else None,
        last_run_at=run["finished_at"] if run else None,
    )


@router.get("/runs/{user_id}", response_model=list[AgentRunOut])
def list_agent_runs(user_id: str, limit: int = 20, db: Store = Depends(get_db)):
    """List recent agent runs for the Agent Lab history panel."""
    runs = sorted(
        db.agent_runs.filter(lambda r: r["user_id"] == user_id),
        key=lambda r: r["started_at"],
        reverse=True,
    )[:limit]
    results = []
    for run in runs:
        steps = db.agent_step_logs.filter(lambda s: s["run_id"] == run["id"])
        steps.sort(key=lambda s: s["created_at"])
        results.append(
            AgentRunOut(
                id=run["id"],
                user_id=run["user_id"],
                trigger_type=run["trigger_type"],
                status=run["status"],
                confidence_score=run["confidence_score"],
                started_at=run["started_at"],
                finished_at=run["finished_at"],
                steps=[
                    AgentStepOut(
                        agent_name=s["agent_name"],
                        status=s["status"],
                        duration_ms=s["duration_ms"],
                        detail=s["detail"],
                        created_at=s["created_at"],
                    )
                    for s in steps
                ],
            )
        )
    return results


@router.get("/runs/{run_id}/trace", response_model=AgentRunOut)
def get_run_trace(run_id: str, db: Store = Depends(get_db)):
    """Full trace for a specific agent run (for Agent Lab trace viewer)."""
    run = db.agent_runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # First try live cache (in case run is still in progress)
    cached_steps = agent_runner.get_run_steps(run_id)
    if cached_steps:
        steps = [AgentStepOut(**s) for s in cached_steps]
    else:
        stored_steps = db.agent_step_logs.filter(lambda s: s["run_id"] == run_id)
        stored_steps.sort(key=lambda s: s["created_at"])
        steps = [
            AgentStepOut(
                agent_name=s["agent_name"],
                status=s["status"],
                duration_ms=s["duration_ms"],
                detail=s["detail"],
                created_at=s["created_at"],
            )
            for s in stored_steps
        ]

    return AgentRunOut(
        id=run["id"],
        user_id=run["user_id"],
        trigger_type=run["trigger_type"],
        status=run["status"],
        confidence_score=run["confidence_score"],
        started_at=run["started_at"],
        finished_at=run["finished_at"],
        steps=steps,
    )


@router.get("/stream/{run_id}")
async def stream_run(run_id: str):
    """
    SSE endpoint that streams step-by-step updates for a live agent run.
    Polls the in-memory step cache every 500ms and emits new entries.
    """

    async def event_generator():
        last_index = 0
        while True:
            steps = agent_runner.get_run_steps(run_id)
            new_steps = steps[last_index:]
            for step in new_steps:
                data = json.dumps(step)
                yield f"data: {data}\n\n"
                last_index += 1

            status = agent_runner.get_run_status(run_id)
            if status in ("completed", "failed"):
                yield f"data: {json.dumps({'type': 'run_complete', 'status': status})}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
