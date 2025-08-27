from typing import Any, Dict, Optional, Sequence, Union
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator
from config import get_settings

import logging
logger = logging.getLogger("app.es5")

JSONDict = Dict[str, Any]
MAX_TOP = 50
StrOrSeq = Union[str, Sequence[str]]

class ODataParams(BaseModel):
    top: Optional[int] = None
    skip: Optional[int] = None
    select: StrOrSeq = None
    orderby: StrOrSeq = None
    expand: StrOrSeq = None
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

    def to_query(self) -> Dict[str, str]:
        q: Dict[str, str] = {}

        if self.top is not None:
            q["$top"] = str(self.top)
        if self.skip is not None:
            q["$skip"] = str(self.skip)
        if self.select is not None:
            q["$select"] = ",".join(self.select)
        if self.orderby is not None:
            q["$orderby"] = ",".join(self.orderby)
        if self.expand is not None:
            q["$expand"] = ",".join(self.expand)
        if self.filter:
            q["$filter"] = self.filter
        if self.format:
            q["$format"] = self.format

        for k, v in self.extra.items():
            q.setdefault(k, v)
        return q


async def aps_get(
    client: httpx.AsyncClient, resource_url: str, params: Optional[ODataParams] = None
) -> JSONDict:
    s = get_settings()
    base_params: Dict[str, str] = {
        "sap-client": s.SAP_CLIENT,
        "$format": "json", 
    }
    if params:
        base_params.update(params.to_query())
    print("***************************")

    logger.info("ES5 Request URL: %s", resource_url)
    logger.info("ES5 Request Params: %s", base_params)

    try:
        r = await client.get(resource_url, params=base_params)

        logger.info("ES5 Full Request URL: %s", r.url)
        logger.info("ES5 GET: %s | Status: %s", r.url, r.status_code)

        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502, detail=f"Upstream status error: {e}"
        ) from e
    except httpx.HTTPError as e:
        raise HTTPException(
            
            status_code=502, detail=f"Upstream network error: {e}"
        ) from e


async def fetch_business_partners(
    client: httpx.AsyncClient, *, p: Optional[ODataParams]  = None,
) -> JSONDict:
    s = get_settings()
    return await aps_get(client, s.ES5_BPSET, params=p)
