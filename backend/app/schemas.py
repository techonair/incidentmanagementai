from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    email: str
    password: str


class IncidentIn(BaseModel):
    title: str
    summary: str = ""
    severity: str = "sev3"
    service: str
    team_id: str | None = None
    assignee_id: str | None = None


class IncidentPatch(BaseModel):
    status: str | None = None
    severity: str | None = None
    team_id: str | None = None
    assignee_id: str | None = None
    summary: str | None = None


class AlertIn(BaseModel):
    fingerprint: str
    service: str
    title: str
    summary: str = ""
    severity: str = "sev3"


class CommentIn(BaseModel):
    body: str


class TaskIn(BaseModel):
    title: str
    status: str = "todo"
    assignee_id: str | None = None


class TaskPatch(BaseModel):
    title: str | None = None
    status: str | None = None
    assignee_id: str | None = None


class AiActionDecision(BaseModel):
    note: str = Field(default="")
