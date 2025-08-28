from ast import List
from typing import Dict

from modols.schemas import ODataParams

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
    "Address",  # שים לב: לא Address/City ב-$select!
}
ADDRESS_SUBFIELDS = {
    "Address/City",
    "Address/PostalCode",
    "Address/Street",
    "Address/Building",
    "Address/Country",
}


# def validate_spec(spec: ODataParams) -> List[str]:
#     errors: List[str] = []
#     raise NotImplementedError

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
