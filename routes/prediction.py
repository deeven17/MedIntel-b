from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from typing import Dict, Any

import numpy as np

from database import predictions_col
from dependencies import get_current_user
from models.hybrid_heart_model import predict_heart_disease
from models.hybrid_alzheimer_model import predict_alzheimer_disease

router = APIRouter()


def _make_bson_safe(obj: Any) -> Any:
    """Convert numpy scalars and nested structures to BSON-serializable types."""
    if isinstance(obj, (np.floating, np.float16, np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.integer, np.int8, np.int16, np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, dict):
        return {k: _make_bson_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_bson_safe(v) for v in obj]
    return obj


def _normalize_payload(payload: dict) -> list[float]:
    """
    Convert incoming payload into feature list for the DL models.
    Assumes values are numeric or numeric strings.
    """
    try:
        return [float(v) for v in payload.values()]
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prediction payload must contain numeric values only",
        )


def _build_prediction_doc(
    user_email: str,
    pred_type: str,
    model_output: Dict[str, Any],
) -> Dict[str, Any]:
    """Map model output into a single, consistent prediction document."""
    risk_percentage = model_output.get("risk_percentage")
    if risk_percentage is None and "disease_probability" in model_output:
        risk_percentage = model_output["disease_probability"]

    risk_level = model_output.get("risk_level") or model_output.get("severity_level") or "Unknown"

    doc = {
        "user_email": user_email,
        "type": pred_type,
        "result": model_output.get("prediction", ""),
        "confidence": model_output.get("confidence", 0.0),
        "risk_level": risk_level,
        "risk_percentage": int(risk_percentage) if risk_percentage is not None else 0,
        "timestamp": datetime.utcnow(),
        "model_used": model_output.get("model_used", f"hybrid_{pred_type}_model"),
        "details": model_output,
    }
    return _make_bson_safe(doc)


@router.post("/heart")
async def heart(payload: dict, user: dict = Depends(get_current_user)):
    """
    Heart disease prediction using the HybridHeartDiseaseModel.

    The deep learning / ensemble model output is normalized and
    immediately persisted to the centralized `predictions` collection.
    """
    features = _normalize_payload(payload)
    model_output = predict_heart_disease(features)

    doc = _build_prediction_doc(
        user_email=user.get("email"),
        pred_type="heart",
        model_output=model_output,
    )

    await predictions_col.insert_one(doc)

    return {
        "type": "heart",
        "prediction": doc["result"],
        "risk_percentage": doc["risk_percentage"],
        "risk_level": doc["risk_level"],
        "confidence": doc["confidence"],
        "model_used": doc["model_used"],
    }


@router.post("/alzheimer")
async def alzheimer(payload: dict, user: dict = Depends(get_current_user)):
    """
    Alzheimer's prediction using the HybridAlzheimerModel.

    The deep learning / ensemble model output is normalized and
    immediately persisted to the centralized `predictions` collection.
    """
    features = _normalize_payload(payload)
    model_output = predict_alzheimer_disease(features)

    doc = _build_prediction_doc(
        user_email=user.get("email"),
        pred_type="alzheimer",
        model_output=model_output,
    )

    await predictions_col.insert_one(doc)

    return {
        "type": "alzheimer",
        "prediction": doc["result"],
        "risk_percentage": doc["risk_percentage"],
        "risk_level": doc["risk_level"],
        "confidence": doc["confidence"],
        "model_used": doc["model_used"],
    }
