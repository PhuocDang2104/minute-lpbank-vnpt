from typing import List, Dict, Any


def call_smartbot_llm(messages: List[Dict[str, str]], model: str = "smartbot-recap-fast") -> Dict[str, Any]:
    """Stub for VNPT SmartBot LLM. Replace with real HTTP call."""
    content = " ".join(m.get("content", "") for m in messages)
    return {"content": f"[SmartBot stub:{model}] {content}"}
