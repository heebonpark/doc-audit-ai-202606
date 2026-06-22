import io
import random
from PIL import Image, ImageDraw, ImageFont

class HandwritingOCREngine:
    def __init__(self):
        self.is_ready = True
        
    def extract_handwriting_mock(self, reason_text: str):
        """
        Simulates extracting a handwritten snippet from an image and running OCR on it.
        Returns a dictionary with 'image_bytes' (the simulated cropped image of the handwriting)
        and 'ocr_text' (the recognized text).
        """
        # 1. Create a dummy image representing a cropped handwritten box
        img = Image.new('RGB', (400, 100), color=(248, 250, 252))
        d = ImageDraw.Draw(img)
        
        # We simulate handwritten text. If no specific text, use a default
        display_text = reason_text if reason_text and reason_text != "null" else "단순 변심으로 인한 해지 요청"
        
        # Try to load a font, or use default
        try:
            # We don't have a reliable handwriting font, so we use default and draw lines to make it look like a form box
            font = ImageFont.load_default()
        except:
            font = None
            
        # Draw a bounding box for the form field
        d.rectangle([10, 10, 390, 90], outline=(148, 163, 184), width=2)
        
        # Draw the text in dark blue/black to simulate pen ink
        d.text((20, 40), display_text, fill=(15, 23, 42))
        
        # Draw some "noise" or signature scribble to make it look handwritten
        for _ in range(5):
            x1 = random.randint(20, 380)
            y1 = random.randint(20, 80)
            x2 = x1 + random.randint(10, 50)
            y2 = y1 + random.randint(-10, 10)
            d.line([(x1, y1), (x2, y2)], fill=(56, 189, 248, 100), width=1)
            
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return {
            "success": True,
            "image_bytes": img_byte_arr.getvalue(),
            "ocr_text": display_text,
            "confidence": round(random.uniform(0.75, 0.98), 2)
        }
