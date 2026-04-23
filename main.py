import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.core_agent import CoreAgent

app = FastAPI(title="AI QA Agent MVP")

# Mount static files
import os
os.makedirs("frontend", exist_ok=True)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

class RunRequest(BaseModel):
    url: str

@app.get("/")
async def serve_ui():
    return FileResponse("frontend/index.html")

@app.post("/api/run-agent")
async def run_agent(req: RunRequest):
    if not req.url:
         raise HTTPException(status_code=400, detail="Missing url")
    
    # Run the core agent logic
    agent = CoreAgent()
    
    # For a real system we would use SSE or websockets to stream logs to UI, 
    # but for simplicity in MVP we await result.
    result = await agent.run(req.url)
    
    return result

if __name__ == "__main__":
    import uvicorn
    # Start uvicorn programmatically without the auto-reloader to avoid asyncio loop policy reset on Windows
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
