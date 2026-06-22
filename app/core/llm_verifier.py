class LocalLLMVerifier:
    def __init__(self):
        """
        Initializes the connection to a local LLM (e.g., via Ollama).
        """
        self.is_connected = True
        
    def verify_document_logic(self, text_content: str, doc_type: str = "변경신청서") -> dict:
        """
        Uses Local LLM to verify semantic logic (e.g., dates, reasons).
        Returns a status, reason, confidence, and a snippet of the suspicious text.
        """
        # TODO: Implement actual langchain + ollama invocation
        
        import re
        from datetime import datetime
        
        # 1. Determine Document Type
        doc_type_inferred = doc_type
        if "Normal Contract" in text_content or "Standard registration" in text_content or "계약서" in text_content:
            doc_type_inferred = "신규계약서"
        elif "Cancellation" in text_content or "해지" in text_content or "null" in text_content or "ERROR_CODE" in text_content:
            doc_type_inferred = "해지신청서"
            
        # 2. Extract Data (Mocked but using basic parsing for realism)
        extracted_data = {
            "문서 유형": doc_type_inferred,
            "고객명(계약자)": "미상",
            "작성 일자": datetime.now().strftime("%Y-%m-%d"),
            "신청 사유": "N/A",
            "특이사항": "발견되지 않음"
        }
        
        # Parse Name
        name_match = re.search(r'(Name|성명|계약자)[:\s]+([^\n]+)', text_content, re.IGNORECASE)
        if name_match: extracted_data["고객명(계약자)"] = name_match.group(2).strip()
        
        # Parse Company Name
        company_match = re.search(r'(Company|상호|상호명|가맹점명|법인명)[:\s]+([^\n]+)', text_content, re.IGNORECASE)
        if company_match:
            extracted_data["상호(법인명)"] = company_match.group(2).strip()
        else:
            extracted_data["상호(법인명)"] = "미기재"
        
        # Parse Date
        date_match = re.search(r'(Date|일자|날짜)[:\s]+([\d\-/\.]+)', text_content, re.IGNORECASE)
        if date_match: extracted_data["작성 일자"] = date_match.group(2).strip()
        
        # Parse Reason
        reason_match = re.search(r'(Reason|사유)[:\s]+([^\n]+)', text_content, re.IGNORECASE)
        snippet = ""
        if reason_match:
            snippet = reason_match.group(2).strip()
            extracted_data["신청 사유"] = snippet
            
        # Parse Notes/Errors
        if "ERROR_CODE" in text_content:
            extracted_data["특이사항"] = "시스템 에러 코드(ERROR_CODE) 검출됨"
            
        # 3. Validation Logic (Detailed)
        status = "정상"
        reason_desc = "필수 기재 항목이 모두 정상적으로 작성되었습니다."
        
        if doc_type_inferred == "해지신청서":
            if not snippet or snippet.lower() in ["null", "n/a", "없음"]:
                status = "의심"
                reason_desc = "해지 사유가 누락되었거나 'null' 처리되었습니다."
                snippet = "null" if not snippet else snippet
            elif any(bad_word in snippet.replace(" ", "") for bad_word in ["단순변심", "몰라", "잘못눌러", "그냥"]):
                status = "의심"
                reason_desc = f"불성실한 해지 사유('{snippet}')가 감지되었습니다. 추가 확인이 필요합니다."
            elif "ERROR_CODE" in text_content:
                status = "의심"
                reason_desc = "문서 내부에 시스템 에러 코드가 포함되어 있습니다."
        elif doc_type_inferred == "신규계약서":
            if "ERROR_CODE" in text_content:
                status = "의심"
                reason_desc = "계약서 내부에 비정상적인 시스템 에러 코드가 인쇄되었습니다."
        
        return {
            "status": status,
            "reason": reason_desc,
            "confidence_score": 0.95 if status == "정상" else 0.85,
            "evidence_snippet": snippet,
            "extracted_data": extracted_data
        }
