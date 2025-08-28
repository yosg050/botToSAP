from ast import List
from typing import Dict

from models.schemas import ODataParams

LEGAL_FIELDS = {
    "BusinessPartnerID",
    "CompanyName",
    "WebAddress",
    "EmailAddress",
    "PhoneNumber",
    "FaxNumber",
    "LegalForm",
    "CurrencyCode",
    "BusinessPartnerRole",
    "Address",
}
ADDRESS_SUBFIELDS = {
    "Address/City",
    "Address/PostalCode",
    "Address/Street",
    "Address/Building",
    "Address/Country",
}

def build_query(p: ODataParams | None) -> Dict[str, str]:
    if p is None:
        return {}
    q: Dict[str, str] = {}

    if p.top is not None:
        q["$top"] = str(p.top)
    if p.skip is not None:
        q["$skip"] = str(p.skip)
    if p.select is not None:
        q["$select"] = ",".join(p.select)
    if p.orderby is not None:
        q["$orderby"] = ",".join(p.orderby)
    if p.expand is not None:
        q["$expand"] = ",".join(p.expand)
    if p.filter:
        q["$filter"] = p.filter
    if p.format:
        q["$format"] = p.format

    for k, v in p.extra.items():
        q.setdefault(k, v)
    print("q: ", q)
    return q



