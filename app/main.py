import os
import io
import pandas as pd
from typing import Optional, List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .predictor import get_predictor

app = FastAPI(
    title="p38α MAPK Hybrid Activity & AD Predictor",
    description="Machine learning inference API and Web UI for hybrid RF molecular activity and applicability domain predictions.",
    version="1.0.0"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class SinglePredictRequest(BaseModel):
    smiles: str
    code: Optional[str] = "COMP-001"

class ExportRequest(BaseModel):
    results: List[dict]
    filename: Optional[str] = "Predictions_Result.xlsx"

@app.on_event("startup")
def startup_event():
    # Warm up model and featurizers
    get_predictor()

@app.get("/", response_class=HTMLResponse)
def serve_home():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h2>Predictor API is running. UI not found.</h2>")

@app.get("/api/health")
def health_check():
    predictor = get_predictor()
    return {
        "status": "online",
        "model_ready": predictor.is_ready,
        "model_type": type(predictor.model).__name__ if predictor.model else None,
        "n_features": getattr(predictor.model, "n_features_in_", None),
        "ad_threshold": predictor.ad_threshold
    }

@app.post("/api/predict")
def predict_single(req: SinglePredictRequest):
    predictor = get_predictor()
    result = predictor.predict_single(smiles=req.smiles, code=req.code or "COMP-001")
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid input"))
    return result

@app.get("/api/structure")
def get_structure_svg(smiles: str):
    predictor = get_predictor()
    mol = predictor.smiles_to_mol(smiles)
    if mol is None:
        raise HTTPException(status_code=400, detail="Invalid SMILES")
    svg = predictor.get_mol_svg(mol, width=320, height=220)
    return Response(content=svg, media_type="image/svg+xml")

@app.post("/api/predict-batch")
async def predict_batch(file: UploadFile = File(...)):
    filename = file.filename.lower()
    contents = await file.read()
    
    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(contents))
        elif filename.endswith(".csv") or filename.endswith(".txt"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .xlsx or .csv")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read spreadsheet: {str(e)}")

    # Standardize columns
    df.columns = [str(c).strip() for c in df.columns]
    smiles_candidates = [c for c in df.columns if "smiles" in c.lower()]
    code_candidates = [c for c in df.columns if any(k in c.lower() for k in ["code", "id", "name", "compound"])]

    if not smiles_candidates:
        raise HTTPException(status_code=400, detail="File must contain a column for SMILES (e.g. 'SMILES' or 'Ligand SMILES')")

    smiles_col = smiles_candidates[0]
    code_col = code_candidates[0] if code_candidates else None

    items = []
    for idx, row in df.iterrows():
        code_val = str(row[code_col]) if code_col else f"MOL_{idx+1}"
        smiles_val = str(row[smiles_col]) if pd.notna(row[smiles_col]) else ""
        items.append({"CODE": code_val, "SMILES": smiles_val})

    predictor = get_predictor()
    batch_res = predictor.predict_batch(items)
    return batch_res

@app.post("/api/export")
def export_predictions(req: ExportRequest):
    if not req.results:
        raise HTTPException(status_code=400, detail="No prediction data to export")
    
    df = pd.DataFrame(req.results)
    # Reorder columns standardly if present
    desired_order = ["CODE", "SMILES", "Activity", "Probability", "Confidence", "AD_Status", "AD_Distance"]
    cols = [c for c in desired_order if c in df.columns] + [c for c in df.columns if c not in desired_order]
    df = df[cols]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Predictions")
    output.seek(0)

    filename = req.filename if req.filename.endswith(".xlsx") else f"{req.filename}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
