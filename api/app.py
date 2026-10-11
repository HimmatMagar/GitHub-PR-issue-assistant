from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from agent.agent import review
from tools.github_read import parse_github_url

# STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="PR / Issue Assistant")
# app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ReviewRequest(BaseModel):
    url: str


class ReviewResponse(BaseModel):
    result: str


@app.get("/")
def index():
    # return FileResponse(STATIC_DIR / "index.html")
    return {'message': "hello"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
def review_endpoint(req: ReviewRequest):
    try:
        parse_github_url(req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        return ReviewResponse(result=review(req.url))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent failed: {e}")