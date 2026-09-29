"""
Production Model Server and REST API Router for ExactorAccelerator (.ej models).
Provides standalone microservice deployment via FastAPI and Docker.
"""

from typing import Dict, Any, Optional, List
import argparse
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from exactor_accelerator.model_persistence import load_model


def create_model_app(model_path: str) -> FastAPI:
    """Creates an optimized FastAPI application serving an ExactorAccelerator model."""
    model = load_model(model_path)
    
    app = FastAPI(
        title="ExactorAccelerator Model Server",
        description=f"Neuro-Symbolic Inference Microservice serving: {model_path}",
        version="1.0.0"
    )

    class PredictionRequest(BaseModel):
        event: Dict[str, Any]
        fast_path: Optional[bool] = True
        include_explanation: Optional[bool] = False

    class BatchPredictionRequest(BaseModel):
        events: List[Dict[str, Any]]
        fast_path: Optional[bool] = True

    @app.get("/health")
    def health():
        return {
            "status": "HEALTHY",
            "model_type": model.__class__.__name__,
            "model_path": model_path
        }

    @app.get("/schema")
    def schema():
        formula = None
        if hasattr(model, "formula_expr_"):
            formula = model.formula_expr_
        elif hasattr(model, "runtime") and model.runtime.current_rule:
            formula = model.runtime.current_rule.formula_expr
        return {
            "model_type": model.__class__.__name__,
            "boolean_formula": formula,
            "formula_booleana": formula,
        }

    @app.post("/predict")
    def predict(req: PredictionRequest):
        try:
            if hasattr(model, "evaluate"):
                # ExactorAccelerator SDK
                res = model.evaluate(req.event, fast_path=req.fast_path)
                resp_data = res
                if req.include_explanation and hasattr(model, "explain"):
                    resp_data["explicacion"] = model.explain(req.event)
                return resp_data
            elif hasattr(model, "predict"):
                # ExactorAcceleratorClassifier
                import pandas as pd
                df = pd.DataFrame([req.event])
                pred = int(model.predict(df)[0])
                proba = [float(p) for p in model.predict_proba(df)[0]]
                resp_data = {
                    "prediction": pred,
                    "probabilities": proba,
                    "decision": "CRITICAL" if pred == 1 else "SAFE"
                }
                if req.include_explanation and hasattr(model, "explain"):
                    resp_data["explicacion"] = model.explain(req.event)
                return resp_data
            else:
                raise HTTPException(status_code=500, detail="Modelo cargado no tiene interfaz de predicción.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/predict/batch")
    def predict_batch(req: BatchPredictionRequest):
        try:
            results = []
            if hasattr(model, "evaluate"):
                for evt in req.events:
                    results.append(model.evaluate(evt, fast_path=req.fast_path))
                return {"count": len(results), "predictions": results}
            elif hasattr(model, "predict"):
                import pandas as pd
                df = pd.DataFrame(req.events)
                preds = [int(p) for p in model.predict(df)]
                probas = [[float(p[0]), float(p[1])] for p in model.predict_proba(df)]
                return {
                    "count": len(preds),
                    "predictions": preds,
                    "probabilities": probas
                }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return app


def main():
    parser = argparse.ArgumentParser(description="ExactorAccelerator Production Model Server")
    parser.add_argument("--model", type=str, required=True, help="Ruta al archivo de modelo .ej")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Puerto de escucha (default: 8000)")
    parser.add_argument("--workers", type=int, default=1, help="Number of uvicorn workers")
    
    args = parser.parse_args()
    app = create_model_app(args.model)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
