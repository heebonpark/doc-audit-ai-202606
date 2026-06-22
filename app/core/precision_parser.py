import re
import json
from typing import Dict

# Placeholder for a more advanced LLM‑based parsing.
# In a production setting we could call an LLM with a prompt like:
# "Extract the following fields from the given Korean contract text: 고객명, 상호(법인명), 작성 일자, 신청 사유. Return a JSON object."
# For now we implement a fuzzy‑regex based fallback that is more tolerant to OCR noise.

def _fuzzy_search(patterns, text):
    """Return the first match for any of the supplied regex patterns.
    Patterns are tried in order; the function stops at the first successful match.
    """
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(2).strip()
    return None


def parse_document_precise(text: str) -> Dict[str, str]:
    """Parse key fields from a contract document with tolerance for OCR errors.

    Returns a dictionary that may contain the following keys (if detected):
    - "고객명(계약자)"
    - "상호(법인명)"
    - "작성 일자"
    - "신청 사유"
    """
    result = {}

    # 1️⃣ 고객명 / 계약자
    name_patterns = [
        r"(Name|성명|계약자|섬명)[:\s]+([^\n]+)",
        r"(고객명)[:\s]+([^\n]+)"
    ]
    name = _fuzzy_search(name_patterns, text)
    if name:
        result["고객명(계약자)"] = name

    # 2️⃣ 상호 (법인명 / 가맹점명)
    company_patterns = [
        r"(Company|상호|상호명|가맹점명|법인명|상호명)[:\s]+([^\n]+)",
        r"(상호)[:\s]+([^\n]+)"
    ]
    company = _fuzzy_search(company_patterns, text)
    if company:
        result["상호(법인명)"] = company
    else:
        result["상호(법인명)"] = "미기재"

    # 3️⃣ 작성 일자
    date_patterns = [
        r"(Date|일자|날짜)[:\s]+([\d\-/.]+)",
        r"(작성일)[:\s]+([\d\-/.]+)"
    ]
    date = _fuzzy_search(date_patterns, text)
    if date:
        result["작성 일자"] = date

    # 4️⃣ 신청 사유 (reason)
    reason_patterns = [
        r"(Reason|사유|신청 사유)[:\s]+([^\n]+)"
    ]
    reason = _fuzzy_search(reason_patterns, text)
    if reason:
        result["신청 사유"] = reason
    else:
        result["신청 사유"] = "N/A"

    # Optional: add raw JSON for debugging
    result["_raw"] = json.dumps({"extracted": result}, ensure_ascii=False)
    return result
