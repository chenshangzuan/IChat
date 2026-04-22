from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    demo_id: str = "deepagents"
    user_id: str = ""


class EditMessageRequest(BaseModel):
    session_id: str
    demo_id: str = "deepagents"
    message_index: int


class ApprovalDecision(BaseModel):
    type: str  # "approve" | "reject"
    message: str = ""


class ApprovalRequest(BaseModel):
    session_id: str
    demo_id: str = "deepagents"
    user_id: str = ""
    decisions: list[ApprovalDecision]


class AgentMetadata(BaseModel):
    agent_type: str | None = None
    delegations: int = 0
    tool_calls: int = 0
    duration: float = 0.0


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_metadata: AgentMetadata | None = None


class DemoInfo(BaseModel):
    id: str
    name: str
    description: str
    category: str
    coming_soon: bool = False


class DemosResponse(BaseModel):
    demos: list[DemoInfo]
