from typing import Optional, List
from fastapi import FastAPI, Depends, Query, Request
import httpx
from config import get_settings
from models.schemas import ConversationStatus
from services.llm_openai_client import ask_openai
from services.sap_client import ODataParams, aps_get
import sys, logging
from routes.ask import AskBody, ask_get
# from services.sap_odata_builder import validate_spec


app_logger = logging.getLogger("app")
app_logger.setLevel(logging.DEBUG)  # או INFO
if not app_logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    app_logger.addHandler(h)
    app_logger.propagate = False

app = FastAPI(title="botToSAP – OData LLM Mapper")

_CONV: dict[str, ConversationStatus] = {}  # db test


async def get_http_client() -> httpx.AsyncClient:
    s = get_settings()
    async with httpx.AsyncClient(
        timeout=s.REQUEST_TIMEOUT,
        auth=(s.ES5_USERNAME, s.ES5_PASSWORD),
    ) as client:
        yield client


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/partners")
async def partners(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    s = get_settings()
    qp = dict(request.query_params)

    qp.setdefault("sap-client", s.SAP_CLIENT)
    qp.setdefault("$format", "json")
    return await aps_get(client, s.ES5_BPSET, params=ODataParams(extra=qp))


@app.post("/ask")
async def ask(
    body: AskBody,
):
    # s = await ask_get(body)
    state = _CONV.get(body.conversation_id) or ConversationStatus(conversation_id=body.conversation_id, user_id=body.user_id)
    tool_ret = await ask_openai(body.message, state)

    state.spec = tool_ret.spec

    # errors = validate_spec(state.spec)

    if tool_ret:
        state.status = "DRAFT"
        _CONV[state.conversation_id] = state
        return {
            "status": "DRAFT",
            "clarifying_question": tool_ret.clarifying_question
        }
