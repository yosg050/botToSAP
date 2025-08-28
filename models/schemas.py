from typing_extensions import Literal
from pydantic import BaseModel

from typing import Any, Dict, Optional, Sequence, Union
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from config import get_settings


StrOrSeq = Union[str, Sequence[str]]


class ODataParams(BaseModel):
    top: Optional[int] = None
    skip: Optional[int] = None
    select: Optional[StrOrSeq] = None
    orderby: Optional[StrOrSeq] = None
    expand: Optional[StrOrSeq] = None
    filter: Optional[str] = None
    format: Optional[str] = "json"

    extra: Dict[str, str] = Field(default_factory=dict)

    @field_validator("top", "skip")
    @classmethod
    def _validate_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("top/skip must be non-negative")
        return v

    @staticmethod
    def _normalize_str_or_seq(v: StrOrSeq) -> Optional[list[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",")]
            return [p for p in parts if p]
        return [s.strip() for s in v if isinstance(s, str) and s.strip()]

    @field_validator("select", "orderby", "expand", mode="before")
    @classmethod
    def _normalize_fields(cls, v):
        return cls._normalize_str_or_seq(v)

class AskBody(BaseModel):
    user_id: str
    conversation_id: str
    message: str

# LLM response
class LLMToolReturn(BaseModel):
    ready: bool = False
    spec: ODataParams
    clarifying_question: Optional[str] = None
    reason: Optional[str] = None

class ConversationStatus(BaseModel):
    user_id: str
    conversation_id: str
    spec: ODataParams = Field(default_factory=ODataParams)
    status: Literal["DRAFT", "NEEDS_INFO", "READY", "SENT"] = "DRAFT"
    last_validation_errors: list[str] = Field(default_factory=list)
    history: list[Dict[str, Any]] = Field(default_factory=list)


def validate_spec(spec: ODataParams) -> list[str]:
    errors: list[str] = []
    if spec.top is not None and not (1 <= spec.top <= 100):
        errors.append("top must be between 1 and 100.")

    if spec.select and any("/" in f for f in spec.select):
        errors.append(
            "Do not select sub-fields like Address/City; select 'Address' or omit."
        )
    if spec.filter:
        bal = 0
        for ch in spec.filter:
            if ch == "(":
                bal += 1
            elif ch == ")":
                bal -= 1
                if bal < 0:
                    break
        if bal != 0:
            errors.append("Unbalanced parentheses in $filter.")
    return errors
