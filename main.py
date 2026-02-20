from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List

from ocr import ocr_and_extract
from blueprint import generate_blueprint

app = FastAPI(title="WealthOS AI MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BlueprintRequest(BaseModel):
    profile: Dict[str, Any]
    parsed_docs: List[Dict[str, Any]] = []

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/upload")
async def upload(file: UploadFile = File(...), doc_type: str = Form("other")):
    data = await file.read()
    return ocr_and_extract(data, file.filename, doc_type)

@app.post("/blueprint")
def blueprint(req: BlueprintRequest):
    return generate_blueprint(req.profile, req.parsed_docs)

@app.post("/budget")
def budget(req: BudgetRequest):
    return compute_budget(req)
