from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from pydantic import ValidationError
from config import get_settings
from typing import Dict, Any

from modols.schemas import ConversationStatus, LLMToolReturn, ODataParams
import json

from servises.llm_tools import TOOLS

client = AsyncOpenAI()


SYSTEM_PROMPT = """אתה ממפה בקשות בשפה חופשית לעולם OData v2 מול BusinessPartnerSet.
כללים:
- תחזיר תמיד 'spec' מלא (לא patch חלקי).
- אם חסר מידע → ready=false + clarifying_question קצרה בשפת הפניה של המשתמש.
- ברירת מחדל: top=10.
- דוגמאות שדות: Address/City, Address/Country, EmailAddress, CompanyName, PhoneNumber, LegalForm, CurrencyCode, BusinessPartnerRole.
- ב-$select אין תת-שדות של Address/City — או Address מלא או בלי Address.
- שמור על $filter חוקי בלבד (and/or, סוגריים, startswith/endswith/substringof).
- קבל גם 'previous_spec' ו-'last_validation_errors' כדי לתקן ניסוח קודם.
"""
EXAMPLES = [
    {
        "ready": True,
        "intent": "list",
        "filters": ["Address/City eq 'Walldorf'", "endswith(EmailAddress,'@sap.com')"],
        "select": ["CompanyName", "EmailAddress"],
        "top": 5,
    },
    {"ready": True, "intent": "count", "filters": ["Address/Country ne 'DE'"]},
    {
        "ready": True,
        "intent": "list",
        "filters": ["startswith(PhoneNumber,'0622')"],
        "orderby": ["CompanyName desc"],
        "top": 3,
    },
]


async def ask_openai(user_text: str, state: ConversationStatus) -> LLMToolReturn:
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "developer",
            "content": json.dumps(
                {
                    "previous_spec": state.spec.model_dump(),
                    "last_validation_errors": state.last_validation_errors,
                },
                ensure_ascii=False,
            ),
        },
        {"role": "user", "content": user_text},
    ]

    s = get_settings()

    r = await client.chat.completions.create(
        model=s.OPENAI_MODEL,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=s.TEMPERATURE,
    )

    choice = r.choices[0]
    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        try:
            spec = ODataParams(**args.get("spec", {}))
            return LLMToolReturn(
                ready=bool(args.get("ready")),
                clarifying_question=args.get("clarifying_question"),
                reason=args.get("reason"),
                spec=spec,
            )
        except ValidationError as ve:
            return LLMToolReturn(
                ready=False,
                clarifying_question=str(ve),
                reason="Invalid OData spec",
                spec=state.spec,
            )

    return LLMToolReturn(
        ready=False,
        clarifying_question="Unknown error",
        reason="Failed to process request",
        spec=state.spec,
    )
