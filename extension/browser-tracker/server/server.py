from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from models import EventPayload
from logger import log_event
import uvicorn

app = FastAPI(title="Browser Tracker Server")

# Allow requests from the Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Since it's a local extension without a standard origin sometimes, or we can specify the extension ID later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
async def get_status():
    """Endpoint for the extension popup to check if server is running."""
    return {"status": "ok"}

@app.post("/api/events")
async def receive_event(payload: EventPayload, background_tasks: BackgroundTasks):
    """Endpoint to receive events from the extension."""
    # Process the logging in the background so we don't block the extension
    background_tasks.add_task(log_event, payload.type, payload.timestamp, payload.data)
    return {"status": "received"}

if __name__ == "__main__":
    print("Starting Browser Tracker Server on http://localhost:8000")
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
