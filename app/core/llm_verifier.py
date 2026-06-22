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
        
        # Determine document type based on content
        doc_type_inferred = doc_type
        if "Normal Contract" in text_content or "Standard registration" in text_content:
            doc_type_inferred = "신규계약서"
        elif "Cancellation" in text_content or "null" in text_content or "ERROR_CODE" in text_content:
            doc_type_inferred = "해지신청서"
            
        # Mocking an evidence snippet based on the text content
        snippet = ""
        if "Reason:" in text_content:
            try:
                snippet = text_content.split("Reason:")[1].split("\\n")[0].strip()
            except:
                pass
                
        # Logic: If it's a new contract, it's normal. If cancellation and reason is suspicious, flag it.
        if doc_type_inferred == "신규계약서" and "ERROR_CODE" not in text_content:
            return {
                "status": "정상",
                "reason": "필수 기재 항목이 모두 정상적으로 작성되었습니다.",
                "confidence_score": 0.95,
                "evidence_snippet": ""
            }
            
        if not snippet or snippet.lower() == "null":
            snippet = "null" # suspicious reason
            
        return {
            "status": "의심",
            "reason": f"{doc_type_inferred} 내 필수 기재 항목(해지 사유)이 모호하거나 누락되었습니다.",
            "confidence_score": 0.85,
            "evidence_snippet": snippet
        }
