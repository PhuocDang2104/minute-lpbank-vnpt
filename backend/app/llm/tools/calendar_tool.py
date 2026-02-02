from datetime import datetime

def schedule_meeting(title: str, when: datetime) -> dict:
    return {"title": title, "scheduled": when.isoformat()}