from typing import Dict, Any
import datetime


def execute_planner_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": "planner",
        "status": "created",
        "task_id": f"planner-{int(datetime.datetime.utcnow().timestamp())}",
        "payload": payload,
    }


def execute_jira_issue(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": "jira",
        "status": "created",
        "issue_key": f"LPB-{int(datetime.datetime.utcnow().timestamp())}",
        "payload": payload,
    }


def execute_calendar_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "provider": "calendar",
        "status": "scheduled",
        "event_id": f"cal-{int(datetime.datetime.utcnow().timestamp())}",
        "payload": payload,
    }


def dispatch_tool_execution(tool_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if tool_type == "task":
        return execute_planner_task(payload)
    if tool_type == "jira":
        return execute_jira_issue(payload)
    if tool_type == "schedule":
        return execute_calendar_event(payload)
    return {"provider": tool_type, "status": "ignored", "payload": payload}
