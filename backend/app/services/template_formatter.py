"""
Template-based Minutes Formatter
Format meeting minutes according to template structure
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services import template_service, meeting_service
from sqlalchemy.orm import Session


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
        
        # Skip empty required sections
        if section_required and not section_fields:
            continue
        
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
            if value:
                formatted_field = format_field(
                    field=field,
                    value=value,
                    format_type=format_type
                )
                if formatted_field:
                    lines.append(formatted_field)
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
            return context.get('decisions', [])
        elif field_id == 'action_items':
            return context.get('actions', [])
        elif field_id == 'risks_list':
            return context.get('risks', [])
        elif field_id == 'agenda_items':
            return context.get('agenda', [])
    
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

