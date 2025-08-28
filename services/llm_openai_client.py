from http.client import HTTPException
from httpx import request
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from typing import cast, Dict, Any
from pydantic import ValidationError
from config import get_settings

from models.schemas import ConversationStatus, LLMToolReturn, ODataParams, validate_spec
import json

from services.llm_tools import PARAMS_SCHEMA, TOOLS
from services.sap_client import aps_get
from services.sap_odata_builder import build_query

s = get_settings()
client = AsyncOpenAI(api_key=s.API_KEY_GPT)


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
    tools: list[ChatCompletionToolParam] = [
        {
            "type": "function",
            "function": {
                "name": "build_odata",
                "description": "Build OData v2 query",
                "parameters": cast(Dict[str, Any], PARAMS_SCHEMA),
            },
        }
    ]

    r = await client.chat.completions.create(
        model=s.OPENAI_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=s.TEMPERATURE,
    )
    print("r: ", r)
    choice = r.choices[0]
    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        tool_call = choice.message.tool_calls[0]
        if tool_call.function.name != "build_odata":
            raise HTTPException(500, detail="Unexpected tool name")
        args = json.loads(tool_call.function.arguments)

        ready = bool(args.get("ready", False))
        spec_dict = args.get("spec") or {}
        try:
            spec = ODataParams(**spec_dict)
        except Exception as e:
            return LLMToolReturn(
                ready=False,
                spec=state.spec,
                clarifying_question="Invalid spec format from tool.",
                reason=str(e),
            )
        errors = validate_spec(spec)
        if errors:
            state.last_validation_errors = errors
            return LLMToolReturn(
                ready=False,
                spec=state.spec,
                clarifying_question="; ".join(errors)[:500],
                reason="Spec validation failed",
            )
        if ready:
            state.spec = spec
            state.status = "READY"
            return LLMToolReturn(
                ready=True,
                spec=spec,
                reason="OK",
                clarifying_question=None,
            )
        return LLMToolReturn(
            ready=False,
            spec=state.spec,
            clarifying_question=args.get("clarifying_question"),
            reason=args.get("reason"),
        )
    return LLMToolReturn(
        ready=False,
        spec=state.spec,
        clarifying_question="No tool call produced.",
        reason="LLM did not call the tool",
    )
