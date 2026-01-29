from datetime import datetime, timedelta
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query, status

from database import users_col, predictions_col, reports_col, chat_col
from dependencies import get_current_admin
from utils.email_service import send_email_async
from routes.notifications import notify_user_event

router = APIRouter(prefix="/admin", tags=["Admin"])

SYMPTOM_KEYWORDS = [
    "chest pain",
    "chest",
    "heart",
    "shortness of breath",
    "breath",
    "difficulty breathing",
    "memory",
    "forget",
    "confusion",
    "headache",
    "dizziness",
    "fatigue",
    "pressure",
    "fever",
    "cough",
    "nausea",
    "vomiting",
    "diarrhea",
    "anxiety",
    "stress",
    "sleep",
    "insomnia",
]


def _derive_symptoms_from_messages(messages: List[str]) -> List[str]:
    """
    Lightweight symptom extraction from free-text messages.
    This is intentionally simple: it surfaces common keywords so the
    Admin 'Symptoms' column stays populated and updates as users chat.
    """
    found: List[str] = []
    for m in messages:
        if not m:
            continue
        txt = m.lower()
        for kw in SYMPTOM_KEYWORDS:
            if kw in txt and kw not in found:
                found.append(kw)
    return found


# ============================
# DASHBOARD OVERVIEW
# ============================
@router.get("/overview")
async def admin_overview(admin: dict = Depends(get_current_admin)):
    total_users = await users_col.count_documents({})
    total_patients = await users_col.count_documents({"is_admin": {"$ne": True}})
    total_predictions = await predictions_col.count_documents({})
    total_chats = await chat_col.count_documents({})

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = datetime.utcnow() - timedelta(days=7)

    active_today = await chat_col.count_documents({"timestamp": {"$gte": today}})
    new_this_week = await users_col.count_documents(
        {"created_at": {"$gte": week_ago}, "is_admin": {"$ne": True}}
    )

    return {
        "total_users": total_users,
        "total_patients": total_patients,
        "total_predictions": total_predictions,
        "active_today": active_today,
        "new_this_week": new_this_week,
    }


# ============================
# GET ALL USERS
# ============================
@router.get("/users")
async def get_users(admin: dict = Depends(get_current_admin)):
    users: List[Dict[str, Any]] = []
    # Exclude sensitive hashes by default
    projection = {"_id": 0, "password": 0, "hashed_password": 0}
    async for u in users_col.find({}, projection):
        users.append(u)
    return {"users": users}


# ============================
# GET PATIENT SUMMARY TABLE
# ============================
@router.get("/patients")
async def get_patients(
    admin: dict = Depends(get_current_admin),
    days_active_threshold: int = Query(30, ge=1, le=365),
):
    """
    Returns one row per user with their latest heart & Alzheimer’s risks.

    - Aggregates latest prediction per condition.
    - Computes a single `max_risk_percentage` used for DESC sorting.
    - Marks patients as Active/Inactive based on recent prediction activity.
    """
    now = datetime.utcnow()
    active_cutoff = now - timedelta(days=days_active_threshold)

    patients: List[Dict[str, Any]] = []

    async for u in users_col.find({}, {"_id": 0, "password": 0, "hashed_password": 0}):
        email = u.get("email")
        if not email:
            continue

        # Latest heart prediction
        latest_heart = await predictions_col.find_one(
            {"user_email": email, "type": "heart"},
            sort=[("timestamp", -1)],
        )

        # Latest Alzheimer prediction
        latest_alz = await predictions_col.find_one(
            {"user_email": email, "type": "alzheimer"},
            sort=[("timestamp", -1)],
        )

        def _get_risk(doc, default=0):
            if not doc:
                return default
            v = doc.get("risk_percentage")
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
            details = doc.get("details") or {}
            v = details.get("risk_percentage") or details.get("disease_probability")
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
            return default

        heart_risk_pct = _get_risk(latest_heart, 0)
        alz_risk_pct = _get_risk(latest_alz, 0)

        last_ts_candidates = [
            latest_heart.get("timestamp") if latest_heart else None,
            latest_alz.get("timestamp") if latest_alz else None,
        ]
        last_prediction_at = max(
            [ts for ts in last_ts_candidates if ts is not None],
            default=None,
        )
        last_assessment_iso = last_prediction_at.isoformat() if hasattr(last_prediction_at, "isoformat") else (str(last_prediction_at) if last_prediction_at else None)

        max_risk_percentage = max(heart_risk_pct, alz_risk_pct)
        is_active = bool(last_prediction_at and last_prediction_at >= active_cutoff)

        # Pull a small window of recent medical chat messages to derive symptoms
        recent_user_msgs: List[str] = []
        async for c in (
            chat_col.find(
                {"user_email": email, "type": "chat_interaction"},
                {"_id": 0, "user_message": 1},
            )
            .sort("timestamp", -1)
            .limit(25)
        ):
            msg = c.get("user_message")
            if msg:
                recent_user_msgs.append(msg)

        all_symptoms = _derive_symptoms_from_messages(recent_user_msgs)

        # Heuristic "primary_disease" for UI purposes (heart vs alzheimer)
        primary_disease = "heart" if heart_risk_pct >= alz_risk_pct else "alzheimer"
        if any(k in ["memory", "forget", "confusion"] for k in all_symptoms):
            primary_disease = "alzheimer"
        if any(k in ["chest pain", "chest", "heart", "shortness of breath", "breath"] for k in all_symptoms):
            primary_disease = "heart"

        patients.append(
            {
                "email": email,
                "name": u.get("name", ""),
                "created_at": u.get("created_at"),
                "last_login": u.get("last_login"),
                "is_admin": u.get("is_admin", False),
                "is_active": u.get("is_active", False),
                "heart_risk_percentage": heart_risk_pct,
                "heart_risk": heart_risk_pct,
                "heart_risk_level": (latest_heart or {}).get("risk_level"),
                "alzheimer_risk_percentage": alz_risk_pct,
                "alzheimer_risk": alz_risk_pct,
                "alzheimer_risk_level": (latest_alz or {}).get("risk_level"),
                "max_risk_percentage": max_risk_percentage,
                "status": "Active" if is_active else "Inactive",
                "last_prediction_at": last_prediction_at,
                "last_assessment": last_assessment_iso,
                "symptoms": {
                    "symptom_count": len(all_symptoms),
                    "primary_disease": primary_disease,
                    "all_symptoms": all_symptoms,
                },
            }
        )

    # Sort so highest-risk patients appear at the top
    patients.sort(key=lambda p: p.get("max_risk_percentage", 0), reverse=True)

    return {"patients": patients}


# ============================
# RAW PREDICTIONS TABLE
# ============================
@router.get("/predictions")
async def get_all_predictions(
    admin: dict = Depends(get_current_admin),
    limit: int = Query(500, ge=1, le=5000),
):
    """
    Returns a flat, prediction-level table for admin visualization.
    Sorted by `risk_percentage` DESC so the riskiest events are first.
    """
    cursor = (
        predictions_col.find({}, {"_id": 0})
        .sort("risk_percentage", -1)
        .limit(limit)
    )

    predictions: List[Dict[str, Any]] = []
    async for p in cursor:
        # Add a pre-formatted label like "75% Moderate Risk"
        risk_pct = p.get("risk_percentage", 0)
        risk_level = p.get("risk_level", "Unknown")
        p["risk_label"] = f"{risk_pct}% {risk_level}"
        predictions.append(p)

    return {"predictions": predictions}


# ============================
# UPDATE USER
# ============================
@router.put("/users/{email}")
async def update_user(
    email: str,
    data: dict,
    admin: dict = Depends(get_current_admin),
):
    if not await users_col.find_one({"email": email}):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await users_col.update_one({"email": email}, {"$set": data})
    return {"status": "updated"}


# ============================
# DELETE USER
# ============================
@router.delete("/users/{email}")
async def delete_user(
    email: str,
    admin: dict = Depends(get_current_admin),
):
    await users_col.delete_one({"email": email})
    await predictions_col.delete_many({"user_email": email})
    await chat_col.delete_many({"user_email": email})
    await reports_col.delete_many({"user_email": email})
    return {"status": "deleted"}


# ============================
# CHAT HISTORY
# ============================
@router.get("/user/chat-history")
async def chat_history(
    user_email: str,
    admin: dict = Depends(get_current_admin),
):
    return [
        c
        async for c in chat_col.find(
            {
                "user_email": user_email,
                "type": {"$in": ["admin_message", "user_message"]},
            },
            {"_id": 0},
        ).sort("timestamp", -1)
    ]


# ============================
# SEND DIRECT MESSAGE + EMAIL
# ============================
@router.post("/send-message")
async def send_message(
    payload: dict,
    admin: dict = Depends(get_current_admin),
):
    """
    Send a direct message from Admin to a specific user.

    - Persists the message in `chat_history` for auditing.
    - Sends an email notification via SMTP so the user is alerted instantly.
    """
    user_email = payload.get("user_email")
    message = payload.get("message")
    subject = payload.get("subject") or "New message from Medical AI Admin"

    if not user_email or not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`user_email` and `message` are required",
        )

    db_user = await users_col.find_one({"email": user_email})
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    chat_entry = {
        "user_email": user_email,
        "admin_email": admin.get("email"),
        "admin_message": message,
        "subject": subject,
        "timestamp": datetime.utcnow(),
        "type": "admin_message",
        "is_admin": True,
    }
    await chat_col.insert_one(chat_entry)

    # Build a simple HTML body for the email
    body_html = f"""
        <p>Dear user,</p>
        <p>You have a new message from the Medical AI Admin dashboard:</p>
        <blockquote>{message}</blockquote>
        <p>If you have any questions, please log in to your account to reply.</p>
    """

    # Fire-and-forget style: if SMTP is misconfigured, we log but don't break the API
    try:
        await send_email_async(
            to_email=user_email,
            subject=subject,
            body_html=body_html,
            body_text=message,
        )
    except Exception as e:
        print(f"⚠️ Failed to send email notification to {user_email}: {e}")

    # Also push a WebSocket notification to the specific user
    try:
        await notify_user_event(
            user_email,
            "admin_message",
            {
                "subject": subject,
                "message": message,
                "timestamp": chat_entry["timestamp"].isoformat(),
                "admin_email": chat_entry["admin_email"],
            },
        )
    except Exception as e:
        print(f"⚠️ Failed to send WebSocket notification to {user_email}: {e}")

    return {"status": "success"}


# ============================
# ANALYTICS
# ============================
@router.get("/analytics")
async def admin_analytics(admin: dict = Depends(get_current_admin)):
    """
    Basic analytics grouped by heart risk percentage.
    Uses the normalized `risk_percentage` field from the predictions collection.
    """
    high = await predictions_col.count_documents({"risk_percentage": {"$gt": 70}})
    medium = await predictions_col.count_documents(
        {"risk_percentage": {"$gt": 40, "$lte": 70}}
    )
    low = await predictions_col.count_documents({"risk_percentage": {"$lte": 40}})

    # Additional aggregates used by the frontend
    heart_predictions = await predictions_col.count_documents({"type": "heart"})
    alzheimer_predictions = await predictions_col.count_documents(
        {"type": "alzheimer"}
    )
    total_assessments = heart_predictions + alzheimer_predictions

    # Simple engagement metrics based on chat timestamps
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(days=7)
    one_month_ago = now - timedelta(days=30)

    daily_active = await chat_col.distinct("user_email", {"timestamp": {"$gte": one_day_ago}})
    weekly_active = await chat_col.distinct("user_email", {"timestamp": {"$gte": one_week_ago}})
    monthly_active = await chat_col.distinct("user_email", {"timestamp": {"$gte": one_month_ago}})

    return {
        "high_risk_count": high,
        "medium_risk_count": medium,
        "low_risk_count": low,
        "heart_predictions": heart_predictions,
        "alzheimer_predictions": alzheimer_predictions,
        "total_assessments": total_assessments,
        "daily_active": len(daily_active),
        "weekly_active": len(weekly_active),
        "monthly_active": len(monthly_active),
        # Placeholders for system performance; can be wired to real metrics later
        "avg_response_time": None,
        "success_rate": None,
        "error_rate": None,
    }


@router.get("/mail")
async def admin_mailbox(
    admin: dict = Depends(get_current_admin),
    limit: int = Query(200, ge=1, le=1000),
):
    """
    Flattened view of admin messages across all users.

    Used by the Admin dashboard "Mail" view.
    """
    cursor = (
        chat_col.find({"type": "admin_message"})
        .sort("timestamp", -1)
        .limit(limit)
    )

    items: List[Dict[str, Any]] = []
    async for msg in cursor:
        items.append(
            {
                "user_email": msg.get("user_email"),
                "admin_email": msg.get("admin_email"),
                "subject": msg.get("subject", "Message from Admin"),
                "message": msg.get("admin_message") or msg.get("message", ""),
                "timestamp": msg.get("timestamp"),
            }
        )

    return {"items": items}


@router.get("/inbox")
async def admin_inbox(
    admin: dict = Depends(get_current_admin),
    limit: int = Query(200, ge=1, le=1000),
):
    """
    Incoming direct messages from users (user -> admin).

    Used by the Admin dashboard "Inbox" view.
    """
    cursor = (
        chat_col.find({"type": "user_message"})
        .sort("timestamp", -1)
        .limit(limit)
    )

    items: List[Dict[str, Any]] = []
    async for msg in cursor:
        items.append(
            {
                "user_email": msg.get("user_email"),
                "subject": msg.get("subject", "Message from user"),
                "message": msg.get("message") or msg.get("user_message") or "",
                "timestamp": msg.get("timestamp"),
            }
        )

    return {"items": items}
