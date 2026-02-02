"""
Email Service - Send emails via SMTP (UTF-8 safe)
"""
import smtplib
import logging
from email.message import EmailMessage
from email.policy import SMTPUTF8
from email.header import Header
from email.utils import formataddr
from typing import Optional, List
from app.core.config import get_settings
from app.utils.markdown_utils import render_markdown_to_html

logger = logging.getLogger(__name__)
settings = get_settings()


def is_email_enabled() -> bool:
    """Check if email sending is configured"""
    return (
        settings.email_enabled and 
        bool(settings.smtp_user) and 
        bool(settings.smtp_password)
    )


def send_email(
    to_emails: List[str],
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachment_content: Optional[bytes] = None,
    attachment_filename: Optional[str] = None,
) -> dict:
    """
    Send email via SMTP (UTF-8 safe, cleans NBSP).
    """
    def _clean(s: Optional[str]) -> str:
        return s.replace("\xa0", " ").strip() if s else ""

    to_emails = [_clean(e) for e in to_emails if _clean(e)]
    subject = _clean(subject)
    body_text = _clean(body_text)
    body_html = _clean(body_html) if body_html else None
    smtp_host = _clean(settings.smtp_host)
    smtp_user = _clean(settings.smtp_user)
    smtp_pass = _clean(settings.smtp_password)

    if not is_email_enabled():
        logger.warning("Email sending is not enabled. Set SMTP credentials and EMAIL_ENABLED=true")
        return {
            'success': False,
            'error': 'Email not configured',
            'sent_to': [],
            'failed': to_emails
        }
    
    try:
        msg = EmailMessage(policy=SMTPUTF8)
        from_name = _clean(settings.email_from_name) or smtp_user
        from_email = smtp_user

        msg['From'] = formataddr((str(Header(from_name, 'utf-8')), from_email))
        msg['To'] = ", ".join([formataddr((str(Header('', 'utf-8')), e)) for e in to_emails])
        msg['Subject'] = str(Header(subject, 'utf-8'))

        # Plain text
        msg.set_content(body_text or " ", subtype='plain', charset='utf-8')
        # HTML
        if body_html:
            msg.add_alternative(body_html, subtype='html', charset='utf-8')

        # Attachment (optional)
        if attachment_content and attachment_filename:
            msg.add_attachment(
                attachment_content,
                maintype='application',
                subtype='octet-stream',
                filename=str(Header(_clean(attachment_filename), 'utf-8')),
            )

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(from_email, smtp_pass)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {len(to_emails)} recipients")
        return {'success': True, 'sent_to': to_emails, 'failed': []}

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        return {'success': False, 'error': 'SMTP authentication failed. Check email/password.', 'sent_to': [], 'failed': to_emails}
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return {'success': False, 'error': f'SMTP error: {str(e)}', 'sent_to': [], 'failed': to_emails}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        return {'success': False, 'error': str(e), 'sent_to': [], 'failed': to_emails}


def send_meeting_minutes_email(
    to_emails: List[str],
    meeting_title: str,
    meeting_date: str,
    meeting_time: str,
    meeting_location: str,
    executive_summary: str,
    minutes_content: Optional[str] = None,
) -> dict:
    """
    Send meeting minutes email with formatted content
    """
    subject = f"[MeetMate] Bien ban cuoc hop: {meeting_title} - {meeting_date}"
    
    body_text = f"""Kinh gui Quy dong nghiep,

Bien ban cuoc hop "{meeting_title}" da duoc hoan thanh.

Thoi gian: {meeting_date} - {meeting_time}
Dia diem: {meeting_location}

TOM TAT:
{executive_summary}

---
Day la email tu dong tu MeetMate AI Assistant.
Vui long khong tra loi email nay.
"""

    minutes_html_section = ""
    if minutes_content:
        rendered_minutes = render_markdown_to_html(minutes_content)
        minutes_html_section = f"""
            <div class="summary" style="margin-top: 20px; border-left-color: #f59e0b;">
                <h3 style="color: #f59e0b;">Chi tiết biên bản</h3>
                <div class="minutes-body" style="font-size: 14px; color: #1f2937; line-height: 1.6; word-break: break-word;">{rendered_minutes}</div>
            </div>
        """

    body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #5b5fc7, #7b7fd7); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 20px; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #e0e0e0; }}
        .meta {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .meta-item {{ display: flex; align-items: center; gap: 8px; font-size: 14px; color: #666; }}
        .summary {{ background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #5b5fc7; }}
        .summary h3 {{ margin-top: 0; color: #5b5fc7; }}
        .summary ul {{ padding-left: 18px; margin: 8px 0; }}
        .summary ol {{ padding-left: 18px; margin: 8px 0; }}
        .summary table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
        .summary th, .summary td {{ border: 1px solid #e5e7eb; padding: 8px; text-align: left; }}
        .summary blockquote {{ margin: 10px 0; padding-left: 12px; border-left: 3px solid #e5e7eb; color: #4b5563; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Bien ban cuoc hop</h1>
            <p style="margin: 5px 0 0; opacity: 0.9;">{meeting_title}</p>
        </div>
        <div class="content">
            <div class="meta">
                <div class="meta-item">Ngay: {meeting_date}</div>
                <div class="meta-item">Gio: {meeting_time}</div>
                <div class="meta-item">Dia diem: {meeting_location}</div>
            </div>
            <div class="summary">
                <h3>Tom tat cuoc hop</h3>
                <p>{executive_summary.replace(chr(10), '<br>')}</p>
            </div>
            {minutes_html_section}
        </div>
        <div class="footer">
            <p>Day la email tu dong tu <strong>MeetMate AI Assistant</strong></p>
            <p>Vui long khong tra loi email nay.</p>
        </div>
    </div>
</body>
</html>
"""

    return send_email(
        to_emails=to_emails,
        subject=subject,
        body_text=body_text + (f"\n\nCHI TIET:\n{minutes_content}" if minutes_content else ""),
        body_html=body_html,
    )


# Test function
def test_email_config() -> dict:
    """Test email configuration by sending a test email"""
    if not is_email_enabled():
        return {
            'success': False,
            'message': 'Email not configured. Set SMTP_USER, SMTP_PASSWORD, EMAIL_ENABLED=true'
        }
    
    try:
        result = send_email(
            to_emails=[settings.smtp_user],
            subject='[MeetMate] Test Email',
            body_text='This is a test email from MeetMate. Email configuration is working!',
        )
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
