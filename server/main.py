from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .actions import ActionService
from .config import load_settings
from .nostr_pub import RelayPublisher
from .storage import Storage

settings = load_settings()
storage = Storage(settings.db_path)
publisher = RelayPublisher()
service = ActionService(storage, settings, publisher)

app = FastAPI(title="PanchoBot MVP0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ProposeReq(BaseModel):
    content: str
    pubkey: str = Field(min_length=64, max_length=64)
    tags: list = []
    relays: list[str] | None = None


class ApproveReq(BaseModel):
    action_id: str
    approval_event: dict
    note_event: dict


class ExecuteReq(BaseModel):
    action_id: str


@app.post("/actions/propose")
def propose(req: ProposeReq):
    return service.propose(req.content, req.tags, req.relays, req.pubkey)


@app.post("/actions/approve")
def approve(req: ApproveReq):
    return service.approve(req.action_id, req.approval_event, req.note_event)


@app.post("/actions/execute")
async def execute(req: ExecuteReq):
    return await service.execute(req.action_id)


@app.get("/actions/{action_id}/audit")
def audit(action_id: str):
    return {"entries": storage.list_audit(action_id)}


web_dir = Path(__file__).resolve().parent.parent / "web"
app.mount("/web", StaticFiles(directory=web_dir), name="web")


@app.get("/")
def index():
    return FileResponse(web_dir / "index.html")
