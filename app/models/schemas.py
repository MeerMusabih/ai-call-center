from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class Language(str, Enum):
    ENGLISH = "en"
    ARABIC = "ar"


class CallState(str, Enum):
    IVR = "ivr"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptEntry(BaseModel):
    role: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)
    language: Language | None = None


class CallSession(BaseModel):
    call_id: str
    phone_number: str
    language: Language | None = None
    state: CallState = CallState.IVR
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = None
    transcript: list[TranscriptEntry] = Field(default_factory=list)
    recording_url: str | None = None
    metadata: dict = Field(default_factory=dict)


class FAQItem(BaseModel):
    id: str
    question: str
    answer: str
    category: str = ""
    language: Language = Language.ENGLISH


class IngestFAQRequest(BaseModel):
    file_path: str | None = None
    raw_text: str | None = None
    format: str = "json"


class CallLogResponse(BaseModel):
    call_id: str
    phone_number: str
    language: str
    state: str
    started_at: datetime
    ended_at: datetime | None
    transcript: list[TranscriptEntry]
    recording_url: str | None


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
