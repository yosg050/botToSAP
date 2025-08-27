from typing import Optional, List
from fastapi import FastAPI, Depends, Query, Request
import httpx
from config import get_settings
from servises.sap_client import ODataParams, aps_get
import sys, logging

app_logger = logging.getLogger("app")
app_logger.setLevel(logging.DEBUG)  # או INFO
if not app_logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    )
    app_logger.addHandler(h)
    app_logger.propagate = False

app = FastAPI(title="SAP ES5 Proxy")


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
    qp = {
        "sap-client": s.SAP_CLIENT,
        "$format": "json",
        "$top": "5",
    }
    return await aps_get(client, s.ES5_BPSET, params=ODataParams(extra=qp))


# from fastapi import FastAPI, HTTPException, Query
# import httpx
# import os
# from dotenv import load_dotenv

# load_dotenv()

# es5_username = os.getenv("ES5_USERNAME")
# es5_password = os.getenv("ES5_PASSWORD")
# app = FastAPI(title="SAP ES5 Proxy")

# ES5_BPSET = "https://sapes5.sapdevcenter.com/sap/opu/odata/iwbep/GWSAMPLE_BASIC/BusinessPartnerSet"


# @app.get("/health")
# async def health():
#     return {"ok": True}


# @app.get("/partners")
# async def partners(
#     top: int = Query(20, ge=1, le=50),
#     city: str = Query("Walldorf"),
# ):
#     params = {
#         "$top": str(top),
#         "$filter": f"Address/City eq '{city}'",
#         # "$select": "BusinessPartnerID,CompanyName,Address",
#         "$orderby": "CompanyName asc",
#         "$format": "json",
#         "sap-client": "002",
#     }

#     try:
#         async with httpx.AsyncClient(
#             timeout=15.0, auth=(es5_username, es5_password)
#         ) as client:
#             r = await client.get(ES5_BPSET, params=params)
#             print("****************************")
#             print("Request URL:", r.url)
#             print("Response text:", r.text)
#             print("****************************")
#             r.raise_for_status()
#     except httpx.HTTPError as e:
#         raise HTTPException(status_code=502, detail=f"Upstream error: {e}")

#     return r.json()
