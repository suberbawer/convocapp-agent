from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class Parameters(BaseModel):
    type: Literal["object"]
    properties: Dict[Literal["type"], Any]
    required: List[str]


class ToolDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Parameters


class Context(BaseModel):
    messages: List[Message]
    task: Optional[str] = None
    tools: Optional[List[ToolDefinition]] = []
    metadata: Optional[Dict[str, Any]] = {}


class MCPInput(BaseModel):
    context: Context


class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]


class MCPResponse(BaseModel):
    content: str = Field(..., description="Natural language response from the agent")
    tool: Optional[ToolCall] = None
    reasoning: Optional[List[str]] = None


class LLMClassifyResponse(BaseModel):
    intent: int
    tool_call: Optional[ToolCall] = None
    response: Optional[str] = None
