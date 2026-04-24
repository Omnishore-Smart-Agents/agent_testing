import sys
import asyncio
import io
import json

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from agent.core_agent import CoreAgent
from tools.docx_generator import create_test_report_docx

app = FastAPI(title="AI QA Agent MVP")

# Mount static files
import os
os.makedirs("frontend", exist_ok=True)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

class RunRequest(BaseModel):
    url: str
    browser: str = "chromium"

@app.get("/")
async def serve_ui():
    return FileResponse("frontend/index.html")

@app.post("/api/run-agent")
async def run_agent(req: RunRequest):
    if not req.url:
         raise HTTPException(status_code=400, detail="Missing url")
    
    # Store logs for streaming
    logs = []
    
    def log_callback(message: str):
        logs.append(message)
    
    # Run the core agent logic
    agent = CoreAgent(browser_type=req.browser, log_callback=log_callback)
    
    result = await agent.run(req.url)
    
    # Include logs in response
    result["logs"] = logs
    
    return result

@app.get("/api/logs")
async def get_logs():
    async def generate():
        yield "data: waiting for logs\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/export-word")
async def export_word(req: RunRequest):
    if not req.url:
         raise HTTPException(status_code=400, detail="Missing url")
    
    # Run the agent to get fresh data
    logs = []
    agent = CoreAgent(browser_type=req.browser, log_callback=lambda m: logs.append(m))
    result = await agent.run(req.url)
    result["logs"] = logs
    result["target_url"] = req.url
    
    # Generate Word document
    doc_bytes = create_test_report_docx(result)
    
    # Return as downloadable file
    import time
    filename = f"rapport_test_{int(time.time())}.docx"
    
    return StreamingResponse(
        io.BytesIO(doc_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
