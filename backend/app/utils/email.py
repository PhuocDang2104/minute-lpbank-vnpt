import logging
import re
import smtplib
import ssl
from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, List, Tuple

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_valid_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email))


def _build_welcome_email_html() -> str:
    try:
        template_path = Path(__file__).parent.parent / "templates" / "welcome_email.html"
        return template_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to load email template: {e}")
        # Fallback to simple HTML if template fails
        return """
        <html><body>
            <h2>Welcome to MeetMate</h2>
            <p>Admin has updated the template but it failed to load. Please contact support.</p>
        </body></html>
        """


def _build_welcome_email_text() -> str:
    return (
        "Xin chào,\n\n"
        "Cảm ơn bạn đã đăng ký nhận thông tin từ MeetMate — trợ lý AI hỗ trợ chuẩn hóa quy trình họp "
        "và chuyển kết quả cuộc họp thành hành động có trách nhiệm.\n\n"
        "MeetMate giúp bạn:\n"
        "- Pre-meeting: chuẩn bị agenda, tài liệu, nhắc lịch theo ngữ cảnh.\n"
        "- In-meeting: ghi nhận nội dung theo thời gian thực, phân tách người nói.\n"
        "- Post-meeting: tạo minutes có cấu trúc, trích xuất Action Items/Decisions, gửi và đồng bộ sang công cụ quản trị.\n\n"
        "Tài liệu & liên kết:\n"
        "- Giới thiệu: https://vnpt-ai-hackathon-meetmate.vercel.app/about\n"
        "- Demo (sắp ra mắt): https://vnpt-ai-hackathon-meetmate.vercel.app/demo\n"
        "- Website: https://vnpt-ai-hackathon-meetmate.vercel.app/\n\n"
        "Nếu bạn muốn team demo theo quy trình thực tế của đội mình, hãy reply email này và cho biết ngữ cảnh sử dụng.\n\n"
        "Trân trọng,\n"
        "MeetMate Team\n"
    )


def _pitch_template_context() -> dict:
    """Default placeholders for the pitch minutes HTML."""
    return {
        "meeting_ref": "DEMO-2024-09",
        "minutes_url": "https://vnpt-ai-hackathon-meetmate.vercel.app/demo-minutes",
        "recording_url": "https://vnpt-ai-hackathon-meetmate.vercel.app/demo-recording",
        "delivery_seconds": "42",
        "meeting_title": "MeetMate Demo cùng VNPT",
        "meeting_datetime": "09/2024",
        "meeting_location": "Online",
        "participants_count": "5",
        "organizer_name": "MeetMate Team",
        "objective": "Trình diễn luồng Pre/In/Post-meeting, khả năng ghi nhận real-time và xuất minutes chuẩn doanh nghiệp.",
        "key_points_html": "<ul style='padding-left:18px;margin:0;'><li>AI ghi âm, tách người nói và highlight Action/Decision/Risk.</li><li>Minutes chuẩn hóa, có người phụ trách và deadline.</li><li>Sẵn sàng tích hợp SmartVoice và GoMeet.</li></ul>",
        "highlight_refs": "00:05:12, 00:12:40",
        "decisions_rows_html": """
        <tr>
          <td class="small text" style="padding:10px 12px; border-top:1px solid #EEF0F3;">Chuẩn hóa minutes theo mẫu VNPT</td>
          <td class="small text" style="padding:10px 12px; border-top:1px solid #EEF0F3;">MeetMate</td>
          <td class="small text" style="padding:10px 12px; border-top:1px solid #EEF0F3;">Tuần này</td>
        </tr>
        <tr>
          <td class="small text" style="padding:10px 12px; border-top:1px solid #EEF0F3;">Kết nối SmartVoice/GoMeet</td>
          <td class="small text" style="padding:10px 12px; border-top:1px solid #EEF0F3;">Tech team</td>
          <td class="small text" style="padding:10px 12px; border-top:1px solid #EEF0F3;">Đang tiến hành</td>
        </tr>
        """,
        "followups_html": "<ul style='padding-left:18px;margin:0;'><li>Chốt API SmartVoice & GoMeet.</li><li>Test minutes trên dữ liệu nội bộ VNPT.</li><li>Chuẩn bị demo end-to-end với phòng ban.</li></ul>",
        "pending_count": "3",
        "next_review_date": "Tuần tới",
        "attachments_note": "Link minutes, transcript, demo deck và prompt tham khảo.",
        "attachments_rows_html": """
        <tr>
          <td class="text small" style="padding:10px 12px; border-bottom:1px solid #EEF0F3;">Minutes</td>
          <td class="text small" style="padding:10px 12px; border-bottom:1px solid #EEF0F3;"><a href="https://vnpt-ai-hackathon-meetmate.vercel.app/demo-minutes">Mở file</a></td>
        </tr>
        <tr>
          <td class="text small" style="padding:10px 12px; border-bottom:1px solid #EEF0F3;">Transcript</td>
          <td class="text small" style="padding:10px 12px; border-bottom:1px solid #EEF0F3;"><a href="https://vnpt-ai-hackathon-meetmate.vercel.app/demo-transcript">Mở file</a></td>
        </tr>
        <tr>
          <td class="text small" style="padding:10px 12px;">Deck</td>
          <td class="text small" style="padding:10px 12px;"><a href="https://vnpt-ai-hackathon-meetmate.vercel.app/demo-deck">Xem deck</a></td>
        </tr>
        """,
        "project_name": "MeetMate Demo",
        "kb_updated_at": "Hôm qua",
        "transcript_url": "https://vnpt-ai-hackathon-meetmate.vercel.app/demo-transcript",
        "year": str(datetime.utcnow().year),
    }


def _build_pitch_minutes_email_html() -> str:
    try:
        # Prefer Canva template if present
        canva_template = Path(__file__).parent / "pitching mail" / "email.html"
        template_path = canva_template if canva_template.exists() else Path(__file__).parent.parent / "templates" / "pitch_minutes_email.html"
        html = template_path.read_text(encoding="utf-8")
        ctx = _pitch_template_context()
        for key, val in ctx.items():
            html = html.replace(f"{{{{{key}}}}}", val)
        return html
    except Exception as e:
        logger.error(f"Failed to load pitch minutes template: {e}")
        return """
        <html><body>
            <h2>Biên bản pitching MeetMate</h2>
            <p>Chúng tôi gặp lỗi khi tải template HTML. Vui lòng xem phiên bản text đính kèm.</p>
        </body></html>
        """


def _build_pitch_minutes_email_text() -> str:
    ctx = _pitch_template_context()
    return (
        "Chào bạn,\n\n"
        "Đây là biên bản tóm tắt buổi demo MeetMate.\n\n"
        f"Biên bản đầy đủ: {ctx['minutes_url']}\n"
        f"Recording: {ctx['recording_url']}\n"
        f"Mục tiêu: {ctx['objective']}\n"
        "Quyết định chính:\n"
        "- Chuẩn hóa minutes theo mẫu VNPT (MeetMate, tuần này)\n"
        "- Kết nối SmartVoice/GoMeet (Tech team, đang tiến hành)\n"
        "Follow-ups: Chốt API, test dữ liệu VNPT, chuẩn bị demo end-to-end.\n\n"
        "Nếu bạn muốn nhận file minutes chi tiết hoặc book buổi demo theo quy trình của đội mình, hãy reply email này.\n\n"
        "Trân trọng,\n"
        "MeetMate Team\n"
    )


def _send_email(*, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    """Shared email sender using SMTP settings."""
    if not settings.email_enabled:
        logger.info("Email sending is disabled. Skipping email [%s].", subject)
        return False

    if not _is_valid_email(to_email):
        logger.warning("Invalid email address: %r. Skipping email [%s].", to_email, subject)
        return False

    from_addr = settings.smtp_user
    from_name = getattr(settings, "email_from_name", None) or "MeetMate"
    reply_to = getattr(settings, "email_reply_to", None)  # optional in settings

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    text_part = MIMEText(text_body, "plain", "utf-8")
    html_part = MIMEText(html_body, "html", "utf-8")
    msg.attach(text_part)
    msg.attach(html_part)

    return _smtp_send_message(msg, subject=subject, to_email=to_email)


def _smtp_send_message(msg, *, subject: str, to_email: str) -> bool:
    """Send a prepared email message via SMTP."""
    timeout = getattr(settings, "smtp_timeout_sec", 15)
    use_starttls = getattr(settings, "smtp_starttls", True)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as server:
            server.ehlo()

            if use_starttls:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()

            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("Email [%s] sent to %s", subject, to_email)
        return True

    except Exception:
        logger.exception("Failed to send email [%s] to %s", subject, to_email)
        return False


def _load_pitch_images() -> List[Tuple[str, bytes, str]]:
    """Load images from the Canva export folder for inline embedding.

    Returns list of (cid, content, subtype).
    """
    images_dir = Path(__file__).parent / "pitching mail" / "images"
    if not images_dir.exists():
        return []

    assets = []
    for path in images_dir.glob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower().lstrip(".")
        if suffix not in {"png", "jpg", "jpeg", "gif"}:
            continue
        try:
            data = path.read_bytes()
            cid = path.name  # use filename as cid
            assets.append((cid, data, suffix))
        except Exception as e:
            logger.warning("Skip inline image %s: %s", path, e)
    return assets


def _inject_inline_cids(html: str, assets: List[Tuple[str, bytes, str]]) -> str:
    """Replace image src references to use cid."""
    if not assets:
        return html
    for cid, _, _ in assets:
        html = html.replace(f"images/{cid}", f"cid:{cid}")
    return html

    timeout = getattr(settings, "smtp_timeout_sec", 15)
    use_starttls = getattr(settings, "smtp_starttls", True)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as server:
            server.ehlo()

            if use_starttls:
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()

            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info("Email [%s] sent to %s", subject, to_email)
        return True

    except Exception:
        logger.exception("Failed to send email [%s] to %s", subject, to_email)
        return False


def send_welcome_email(to_email: str, *, subject: Optional[str] = None) -> bool:
    """
    Send a welcome email to a subscriber.

    Returns:
        True if sent successfully, False otherwise.
    """
    subj = subject or "Chào mừng bạn đến với MeetMate"
    return _send_email(
        to_email=to_email,
        subject=subj,
        text_body=_build_welcome_email_text(),
        html_body=_build_welcome_email_html(),
    )


def send_pitch_minutes_email(to_email: str, *, subject: Optional[str] = None) -> bool:
    """
    Send the pitch minutes email to a subscriber.

    Returns:
        True if sent successfully, False otherwise.
    """
    subj = subject or "Biên bản pitching MeetMate - VNPT AI Hackathon"
    if not settings.email_enabled:
        logger.info("Email sending is disabled. Skipping email [%s].", subj)
        return False

    if not _is_valid_email(to_email):
        logger.warning("Invalid email address: %r. Skipping email [%s].", to_email, subj)
        return False

    html_body = _build_pitch_minutes_email_html()
    text_body = _build_pitch_minutes_email_text()

    # Prepare message with inline images for Canva template
    msg_root = MIMEMultipart("related")
    msg_root["Subject"] = subj
    from_addr = settings.smtp_user
    from_name = getattr(settings, "email_from_name", None) or "MeetMate"
    reply_to = getattr(settings, "email_reply_to", None)
    msg_root["From"] = f"{from_name} <{from_addr}>"
    msg_root["To"] = to_email
    if reply_to:
        msg_root["Reply-To"] = reply_to

    alt_part = MIMEMultipart("alternative")
    alt_part.attach(MIMEText(text_body, "plain", "utf-8"))

    # Inline images
    assets = _load_pitch_images()
    html_with_cid = _inject_inline_cids(html_body, assets)
    alt_part.attach(MIMEText(html_with_cid, "html", "utf-8"))
    msg_root.attach(alt_part)

    for cid, content, subtype in assets:
        try:
            img = MIMEImage(content, _subtype=subtype)
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=cid)
            msg_root.attach(img)
        except Exception as e:
            logger.warning("Failed to attach inline image %s: %s", cid, e)

    return _smtp_send_message(msg_root, subject=subj, to_email=to_email)
