from fastapi import APIRouter, Depends
from dependencies import get_current_user
from database import reports_col

router = APIRouter()

@router.get("/")
async def get_reports(user: dict = Depends(get_current_user)):
    reports = await reports_col.find({"user": user["email"]}).to_list(100)
    return {"ok": True, "reports": reports}
