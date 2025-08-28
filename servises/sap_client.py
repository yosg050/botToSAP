from typing import Any, Dict, Optional
import httpx
from fastapi import HTTPException
import logging
from pydantic import BaseModel, Field, field_validator

from config import get_settings
from modols.schemas import ODataParams
from servises.sap_odata_builder import build_query


logger = logging.getLogger("app.es5")

JSONDict = Dict[str, Any]
MAX_TOP = 50

async def aps_get(
    client: httpx.AsyncClient, resource_url: str, params: Optional[ODataParams] = None
) -> JSONDict:
    s = get_settings()
    base_params: Dict[str, str] = {
        "sap-client": s.SAP_CLIENT,
        "$format": "json", 
    }
    if params:
        base_params.update(build_query(params))
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
