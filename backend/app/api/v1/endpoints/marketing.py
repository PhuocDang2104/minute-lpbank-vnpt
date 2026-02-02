from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.marketing import MarketingLead
from app.schemas.marketing import (
    BroadcastPitchMinutesRequest,
    BroadcastPitchMinutesResponse,
    MarketingLead as MarketingLeadSchema,
    MarketingLeadCreate,
)
from app.utils.email import send_pitch_minutes_email, send_welcome_email

router = APIRouter()
settings = get_settings()
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates"


@router.post("/join", response_model=MarketingLeadSchema)
def join_mailing_list(
    lead: MarketingLeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Join the mailing list.
    """
    existing_lead = db.query(MarketingLead).filter(MarketingLead.email == lead.email).first()
    if existing_lead:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_lead = MarketingLead(email=lead.email)
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)

    background_tasks.add_task(send_welcome_email, lead.email)
    return db_lead


@router.get("/landing", response_class=HTMLResponse)
def get_landing_page():
    """
    Serve the landing page HTML.
    """
    template_path = TEMPLATES_DIR / "landing.html"
    if not template_path.exists():
        return HTMLResponse(content="<h1>Landing page not found</h1>", status_code=404)

    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


@router.get("/pitch-broadcast", response_class=HTMLResponse)
def get_pitch_broadcast_page():
    """
    Serve the hidden broadcast page with a manual trigger button.
    """
    template_path = TEMPLATES_DIR / "pitch_broadcast.html"
    if not template_path.exists():
        return HTMLResponse(content="<h1>Broadcast page not found</h1>", status_code=404)

    return HTMLResponse(content=template_path.read_text(encoding="utf-8"))


@router.post("/broadcast-pitch", response_model=BroadcastPitchMinutesResponse)
def broadcast_pitch_minutes(
    payload: BroadcastPitchMinutesRequest,
    db: Session = Depends(get_db),
):
    """
    Broadcast the pitch minutes email to all marketing leads.
    """
    if settings.marketing_broadcast_token:
        if payload.token != settings.marketing_broadcast_token:
            raise HTTPException(status_code=403, detail="Invalid token")

    leads = db.query(MarketingLead).all()
    total = len(leads)
    sent = 0
    failed = []

    for lead in leads:
        if send_pitch_minutes_email(lead.email):
            sent += 1
        else:
            failed.append(lead.email)

    return BroadcastPitchMinutesResponse(total=total, sent=sent, failed=failed)
