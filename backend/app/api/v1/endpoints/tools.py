from fastapi import APIRouter
from pydantic import BaseModel
from app.services.tool_executor import dispatch_tool_execution


router = APIRouter()


class ToolExecutionRequest(BaseModel):
    type: str
    payload: dict


@router.post("/execute")
def execute_tool(req: ToolExecutionRequest):
    return dispatch_tool_execution(req.type, req.payload)
