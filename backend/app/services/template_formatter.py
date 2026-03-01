"""
Template-based Minutes Formatter
Format meeting minutes according to template structure
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services import template_service, meeting_service
from sqlalchemy.orm import Session


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_is_non_empty(item) for item in value)
    if isinstance(value, dict):
        return any(_is_non_empty(item) for item in value.values())
    return True


def _md_cell(value: Any) -> str:
    text_val = str(value or "").replace("|", "\\|").replace("\n", " ").strip()
    return text_val or "-"


def _format_section_fallback(
    section_id: str,
    meeting: Any,
    context: Dict[str, Any],
    format_type: str = "markdown",
) -> str:
    sid = str(section_id or "").strip().lower()
    if not sid:
        return ""

    summary = str(context.get("summary") or "").strip()
    key_points = [str(item).strip() for item in _as_list(context.get("key_points")) if str(item).strip()]
    action_rows = [row for row in _as_list(context.get("action_items")) if isinstance(row, dict)]
    decision_rows = [row for row in _as_list(context.get("decision_items")) if isinstance(row, dict)]
    risk_rows = [row for row in _as_list(context.get("risk_items")) if isinstance(row, dict)]
    action_list = [str(item).strip() for item in _as_list(context.get("actions")) if str(item).strip()]
    decision_list = [str(item).strip() for item in _as_list(context.get("decisions")) if str(item).strip()]
    risk_list = [str(item).strip() for item in _as_list(context.get("risks")) if str(item).strip()]
    next_steps = [str(item).strip() for item in _as_list(context.get("next_steps")) if str(item).strip()]
    topic_tracker = [row for row in _as_list(context.get("topic_tracker")) if isinstance(row, dict)]
    ai_filters = [str(item).strip() for item in _as_list(context.get("ai_filters")) if str(item).strip()]

    if sid in {"header", "meeting_info", "meeting-information", "info"}:
        lines: List[str] = []
        if format_type == "markdown":
            lines.append(f"**Tên cuộc họp:** {meeting.title or context.get('title') or '-'}")
            lines.append(f"**Loại cuộc họp:** {meeting.meeting_type or context.get('type') or '-'}")
            lines.append(f"**Thời gian:** {context.get('time') or '-'}")
            lines.append(f"**Địa điểm:** {meeting.location or '-'}")
            return "\n".join(lines)
        if format_type == "html":
            return (
                f"<p><strong>Tên cuộc họp:</strong> {meeting.title or context.get('title') or '-'}</p>"
                f"<p><strong>Loại cuộc họp:</strong> {meeting.meeting_type or context.get('type') or '-'}</p>"
                f"<p><strong>Thời gian:</strong> {context.get('time') or '-'}</p>"
                f"<p><strong>Địa điểm:</strong> {meeting.location or '-'}</p>"
            )
        return (
            f"Tên cuộc họp: {meeting.title or context.get('title') or '-'}\n"
            f"Loại cuộc họp: {meeting.meeting_type or context.get('type') or '-'}\n"
            f"Thời gian: {context.get('time') or '-'}\n"
            f"Địa điểm: {meeting.location or '-'}"
        )

    if sid in {"participants", "participant", "attendees"}:
        participants = getattr(meeting, "participants", []) or []
        if not participants:
            return "- Chưa có danh sách người tham gia." if format_type == "markdown" else "Chưa có danh sách người tham gia."
        if format_type == "markdown":
            return "\n".join(
                [
                    f"- {(p.display_name or p.email or 'Unknown')} ({p.role or 'attendee'})"
                    for p in participants
                ]
            )
        if format_type == "html":
            items = "".join(
                [f"<li>{(p.display_name or p.email or 'Unknown')} ({p.role or 'attendee'})</li>" for p in participants]
            )
            return f"<ul>{items}</ul>"
        return "\n".join([f"• {(p.display_name or p.email or 'Unknown')} ({p.role or 'attendee'})" for p in participants])

    if sid in {"summary", "executive_summary"}:
        return summary or ("_Chưa có tóm tắt điều hành._" if format_type == "markdown" else "Chưa có tóm tắt điều hành.")

    if sid in {"key_points", "highlights"}:
        if not key_points:
            return "- Chưa có điểm chính." if format_type == "markdown" else "Chưa có điểm chính."
        if format_type == "markdown":
            return "\n".join([f"- {item}" for item in key_points])
        if format_type == "html":
            return "<ul>" + "".join([f"<li>{item}</li>" for item in key_points]) + "</ul>"
        return "\n".join([f"• {item}" for item in key_points])

    if sid in {"action_items", "actions"}:
        if action_rows and format_type == "markdown":
            lines = [
                "| Người phụ trách | Hạn chót | Mức ưu tiên | Trạng thái | Hành động |",
                "| --- | --- | --- | --- | --- |",
            ]
            for row in action_rows:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("owner")),
                            _md_cell(row.get("deadline")),
                            _md_cell(row.get("priority")),
                            _md_cell(row.get("status")),
                            _md_cell(row.get("description")),
                        ]
                    )
                    + " |"
                )
            return "\n".join(lines)
        if not action_list:
            action_list = [str(row.get("description") or "").strip() for row in action_rows if str(row.get("description") or "").strip()]
        if not action_list:
            return "- Chưa có hành động cần theo dõi." if format_type == "markdown" else "Chưa có hành động cần theo dõi."
        if format_type == "markdown":
            return "\n".join([f"{idx}. {item}" for idx, item in enumerate(action_list, start=1)])
        if format_type == "html":
            return "<ol>" + "".join([f"<li>{item}</li>" for item in action_list]) + "</ol>"
        return "\n".join([f"{idx}. {item}" for idx, item in enumerate(action_list, start=1)])

    if sid in {"decisions", "decision", "decisions_list"}:
        if decision_rows and format_type == "markdown":
            lines = [
                "| Quyết định | Lý do | Trạng thái | Người xác nhận |",
                "| --- | --- | --- | --- |",
            ]
            for row in decision_rows:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("description")),
                            _md_cell(row.get("rationale")),
                            _md_cell(row.get("status")),
                            _md_cell(row.get("confirmed_by")),
                        ]
                    )
                    + " |"
                )
            return "\n".join(lines)
        if not decision_list:
            decision_list = [str(row.get("description") or "").strip() for row in decision_rows if str(row.get("description") or "").strip()]
        if not decision_list:
            return "- Chưa ghi nhận quyết định." if format_type == "markdown" else "Chưa ghi nhận quyết định."
        if format_type == "markdown":
            return "\n".join([f"{idx}. {item}" for idx, item in enumerate(decision_list, start=1)])
        if format_type == "html":
            return "<ol>" + "".join([f"<li>{item}</li>" for item in decision_list]) + "</ol>"
        return "\n".join([f"{idx}. {item}" for idx, item in enumerate(decision_list, start=1)])

    if sid in {"risks", "risks_list", "risk_register"}:
        if risk_rows and format_type == "markdown":
            lines = [
                "| Rủi ro | Mức độ | Giảm thiểu | Người phụ trách | Trạng thái |",
                "| --- | --- | --- | --- | --- |",
            ]
            for row in risk_rows:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("description")),
                            _md_cell(row.get("severity")),
                            _md_cell(row.get("mitigation")),
                            _md_cell(row.get("owner")),
                            _md_cell(row.get("status")),
                        ]
                    )
                    + " |"
                )
            return "\n".join(lines)
        if not risk_list:
            risk_list = [str(row.get("description") or "").strip() for row in risk_rows if str(row.get("description") or "").strip()]
        if not risk_list:
            return "- Chưa ghi nhận rủi ro." if format_type == "markdown" else "Chưa ghi nhận rủi ro."
        if format_type == "markdown":
            return "\n".join([f"- {item}" for item in risk_list])
        if format_type == "html":
            return "<ul>" + "".join([f"<li>{item}</li>" for item in risk_list]) + "</ul>"
        return "\n".join([f"• {item}" for item in risk_list])

    if sid in {"next_steps", "follow_up"}:
        if not next_steps:
            return "- Chưa có bước tiếp theo." if format_type == "markdown" else "Chưa có bước tiếp theo."
        if format_type == "markdown":
            return "\n".join([f"{idx}. {item}" for idx, item in enumerate(next_steps, start=1)])
        if format_type == "html":
            return "<ol>" + "".join([f"<li>{item}</li>" for item in next_steps]) + "</ol>"
        return "\n".join([f"{idx}. {item}" for idx, item in enumerate(next_steps, start=1)])

    if sid in {"topic_tracker", "topics"} and topic_tracker and format_type == "markdown":
        lines = [
            "| Chủ đề | Bắt đầu | Kết thúc | Thời lượng (giây) |",
            "| --- | --- | --- | --- |",
        ]
        for row in topic_tracker:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(row.get("title")),
                        _md_cell(row.get("start_time")),
                        _md_cell(row.get("end_time")),
                        _md_cell(row.get("duration_seconds")),
                    ]
                )
                + " |"
            )
        return "\n".join(lines)

    if sid in {"ai_filters", "filters"}:
        if not ai_filters:
            return ""
        if format_type == "markdown":
            return "\n".join([f"- {item}" for item in ai_filters])
        if format_type == "html":
            return "<ul>" + "".join([f"<li>{item}</li>" for item in ai_filters]) + "</ul>"
        return "\n".join([f"• {item}" for item in ai_filters])

    return ""


def format_minutes_with_template(
    db: Session,
    template_id: str,
    meeting_id: str,
    context: Dict[str, Any],
    format_type: str = 'markdown'
) -> str:
    """
    Format minutes according to template structure.
    
    Args:
        db: Database session
        template_id: Template ID
        meeting_id: Meeting ID
        context: Context data (transcript, actions, decisions, risks, etc.)
        format_type: Output format (markdown/html/text)
    
    Returns:
        Formatted minutes string
    """
    # Get template
    template = template_service.get_template(db, template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")
    
    structure = template.structure
    sections = structure.get('sections', [])
    
    # Get meeting data
    meeting = meeting_service.get_meeting(db, meeting_id)
    if not meeting:
        raise ValueError(f"Meeting {meeting_id} not found")
    
    # Sort sections by order
    sections = sorted(sections, key=lambda x: x.get('order', 0))
    
    lines = []
    
    for section in sections:
        section_id = section.get('id')
        section_title = section.get('title', '')
        section_fields = section.get('fields', [])
        section_required = section.get('required', False)
        
        # Add section header
        if section_title:
            if format_type == 'markdown':
                lines.append(f"## {section_title}")
            elif format_type == 'html':
                lines.append(f"<h2>{section_title}</h2>")
            else:
                lines.append(f"\n{section_title}")
                lines.append("=" * len(section_title))
            lines.append("")
        
        section_has_content = False

        # Process fields
        for field in section_fields:
            field_id = field.get('id')
            field_label = field.get('label', '')
            field_type = field.get('type', 'text')
            field_source = field.get('source', '')
            field_required = field.get('required', False)
            
            # Get field value
            value = get_field_value(
                field_id=field_id,
                field_source=field_source,
                field_type=field_type,
                meeting=meeting,
                context=context
            )
            
            # Skip required fields with no value
            if field_required and not value:
                continue
            
            # Format field
            if _is_non_empty(value):
                formatted_field = format_field(
                    field=field,
                    value=value,
                    format_type=format_type
                )
                if formatted_field:
                    lines.append(formatted_field)
                    lines.append("")
                    section_has_content = True

        # Fallback: if template has no fields or fields resolve to empty,
        # auto-populate by section id from available AI context.
        if not section_has_content:
            fallback_block = _format_section_fallback(
                section_id=section_id,
                meeting=meeting,
                context=context,
                format_type=format_type,
            )
            if fallback_block:
                lines.append(fallback_block)
                lines.append("")
                section_has_content = True

        if section_required and not section_has_content:
            if format_type == "markdown":
                lines.append("_Chưa có dữ liệu cho mục này._")
            elif format_type == "html":
                lines.append("<p><em>Chưa có dữ liệu cho mục này.</em></p>")
            else:
                lines.append("Chưa có dữ liệu cho mục này.")
            lines.append("")
    
    return "\n".join(lines)


def get_field_value(
    field_id: str,
    field_source: str,
    field_type: str,
    meeting: Any,
    context: Dict[str, Any]
) -> Any:
    """Get field value from source"""
    
    # Map source to value
    if field_source.startswith('meeting.'):
        source_attr = field_source.replace('meeting.', '')
        
        if source_attr == 'title':
            return meeting.title
        elif source_attr == 'start_time':
            return meeting.start_time
        elif source_attr == 'end_time':
            return meeting.end_time
        elif source_attr == 'location':
            return meeting.location
        elif source_attr == 'description':
            return meeting.description
        elif source_attr == 'participants':
            # Return participants list
            participants = getattr(meeting, 'participants', [])
            return [{
                'name': p.display_name or p.email or 'Unknown',
                'role': p.role or 'attendee',
                'status': p.response_status or 'pending'
            } for p in participants]
    
    elif field_source == 'ai_generated':
        # Get from context
        if field_id == 'executive_summary':
            return context.get('summary', '')
        elif field_id == 'key_points':
            return context.get('key_points', [])
        elif field_id == 'decisions_list':
            return context.get('decision_items') or context.get('decisions', [])
        elif field_id == 'action_items':
            return context.get('action_items') or context.get('actions', [])
        elif field_id == 'risks_list':
            return context.get('risk_items') or context.get('risks', [])
        elif field_id == 'agenda_items':
            return context.get('agenda', [])
        elif field_id == 'next_steps':
            return context.get('next_steps', [])
        elif field_id == 'topic_tracker':
            return context.get('topic_tracker', [])
    
    return None


def format_field(
    field: Dict[str, Any],
    value: Any,
    format_type: str = 'markdown'
) -> str:
    """Format a single field"""
    field_id = field.get('id')
    field_label = field.get('label', '')
    field_type = field.get('type', 'text')
    
    lines = []
    
    # Format based on field type
    if field_type == 'text':
        if field_label:
            if format_type == 'markdown':
                lines.append(f"**{field_label}:** {value}")
            elif format_type == 'html':
                lines.append(f"<p><strong>{field_label}:</strong> {value}</p>")
            else:
                lines.append(f"{field_label}: {value}")
        else:
            lines.append(str(value))
    
    elif field_type == 'datetime':
        if isinstance(value, datetime):
            formatted_date = value.strftime('%d/%m/%Y %H:%M')
        else:
            formatted_date = str(value)
        
        if field_label:
            if format_type == 'markdown':
                lines.append(f"**{field_label}:** {formatted_date}")
            elif format_type == 'html':
                lines.append(f"<p><strong>{field_label}:</strong> {formatted_date}</p>")
            else:
                lines.append(f"{field_label}: {formatted_date}")
        else:
            lines.append(formatted_date)
    
    elif field_type == 'array':
        if not isinstance(value, list):
            value = [value] if value else []
        
        if field_label and value:
            if format_type == 'markdown':
                lines.append(f"**{field_label}:**")
            elif format_type == 'html':
                lines.append(f"<p><strong>{field_label}:</strong></p>")
                lines.append("<ul>")
            else:
                lines.append(f"{field_label}:")
        
        for item in value:
            if isinstance(item, dict):
                # Format structured item
                item_text = format_structured_item(item, field, format_type)
                lines.append(item_text)
            else:
                # Simple list item
                if format_type == 'markdown':
                    lines.append(f"- {item}")
                elif format_type == 'html':
                    lines.append(f"<li>{item}</li>")
                else:
                    lines.append(f"  • {item}")
        
        if format_type == 'html' and field_label and value:
            lines.append("</ul>")
    
    return "\n".join(lines)


def format_structured_item(
    item: Dict[str, Any],
    field: Dict[str, Any],
    format_type: str = 'markdown'
) -> str:
    """Format a structured item (for array fields with structure)"""
    structure = field.get('structure', {})
    
    if format_type == 'markdown':
        parts = []
        for key, field_type in structure.items():
            if key in item and item[key]:
                parts.append(f"{key}: {item[key]}")
        return f"- {' | '.join(parts)}" if parts else "- "
    
    elif format_type == 'html':
        parts = []
        for key, field_type in structure.items():
            if key in item and item[key]:
                parts.append(f"<strong>{key}:</strong> {item[key]}")
        return f"<li>{' | '.join(parts)}</li>" if parts else "<li></li>"
    
    else:
        parts = []
        for key, field_type in structure.items():
            if key in item and item[key]:
                parts.append(f"{key}: {item[key]}")
        return f"  • {' | '.join(parts)}" if parts else "  • "
