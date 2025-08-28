PARAMS_SCHEMA = {
    "type": "object",
    "properties": {
        "ready": {"type": "boolean"},
        "clarifying_question": {"type": ["string", "null"]},
        "reason": {"type": ["string", "null"]},
        "spec": {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": ["list", "count", "get"]},
                "select": {"type": ["array", "null"], "items": {"type": "string"}},
                "filter": {"type": ["string", "null"]},
                "orderby": {"type": ["array", "null"], "items": {"type": "string"}},
                "top": {"type": "integer"},
                "skip": {"type": ["integer", "null"]},
                "inlinecount": {
                    "type": ["string", "null"],
                    "enum": ["allpages"], 
                },
            },
            "required": ["intent", "top"],
            "additionalProperties": False,
        },
    },
    "required": ["ready", "spec"],
    "additionalProperties": False,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "build_odata",
            "description": "Build an OData v2 request for GWSAMPLE_BASIC.BusinessPartnerSet. Return a FULL spec.",
            "parameters": PARAMS_SCHEMA,
            "strict": True,
        },
    }
]
