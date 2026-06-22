class LocalOCRProcessor:
    def __init__(self):
        """
        Initializes the local OCR engine (e.g., EasyOCR or Tesseract).
        In a real scenario, this loads the models.
        """
        self.is_loaded = True
        
    def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Mocks OCR extraction.
        """
        # TODO: Implement actual easyocr or tesseract extraction
        return "[OCR 추출 텍스트: 본 문서는 스캔본 테스트입니다.]"
