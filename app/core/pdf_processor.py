import fitz  # PyMuPDF
import io
import re

def process_pdf_stream(file_bytes: bytes, password: str = None, max_pages: int = None) -> dict:
    """
    Process PDF from a memory stream using PyMuPDF.
    Handles decryption if a password is provided or if it has a known standard password.
    Optionally limit processing to the first `max_pages` pages for faster preview.
    """
    result = {
        "success": False,
        "is_encrypted": False,
        "page_count": 0,
        "metadata": {},
        "text_content": [],
        "error": None
    }

    try:
        # Load PDF from memory stream
        pdf_stream = io.BytesIO(file_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        # Check encryption
        if doc.needs_pass:
            result["is_encrypted"] = True
            if password:
                doc.authenticate(password)
            else:
                result["error"] = "Password required to decrypt the PDF."
                return result

        result["metadata"] = doc.metadata
        result["page_count"] = doc.page_count
        total_pages = doc.page_count if max_pages is None else min(doc.page_count, max_pages)

        # Extract text (with optional OCR on short/low‑info pages)
        for page_num in range(total_pages):
            page = doc[page_num]
            # Get plain text
            text = page.get_text("text").strip()

            # Heuristic: run OCR only on short text or watermark pages *and* when total pages are small
            if len(text) < 50 or "지원팀" in text or "워터마크" in text or "박희본" in text:
                # If the document is large (>10 pages) we limit OCR to first few pages to avoid slowdown
                if doc.page_count <= 10 or page_num < 5:
                    try:
                        import easyocr, logging, io
                        logging.getLogger('easyocr').setLevel(logging.ERROR)
                        reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)
                        ocr_text = []
                        for img_info in page.get_images(full=True):
                            xref = img_info[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            res = reader.readtext(image_bytes, detail=0)
                            ocr_text.extend(res)
                        text += "\n" + " ".join(ocr_text)
                    except ImportError:
                        text += "\n[OCR 엔진(easyocr)이 설치되지 않아 이미지 텍스트를 읽을 수 없습니다]"

            result["text_content"].append({
                "page": page_num + 1,
                "text": text
            })
            # Heuristic detection of handwritten snippets
            if len(text) < 30 and re.search(r"[가-힣]{2,}", text):
                result.setdefault("handwritten_blocks", []).append({
                    "page": page_num + 1,
                    "text": text
                })
            # Detect checkbox symbols
            if re.search(r"[□☐☑■]", text):
                result.setdefault("checkbox_blocks", []).append({
                    "page": page_num + 1,
                    "text": text
                })

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)
    finally:
        if 'doc' in locals():
            doc.close()

    return result
    """
    Process PDF from a memory stream using PyMuPDF.
    Handles decryption if a password is provided or if it has a known standard password.
    
    Returns a dictionary containing metadata, extracted text per page, and success status.
    """
    result = {
        "success": False,
        "is_encrypted": False,
        "page_count": 0,
        "metadata": {},
        "text_content": [],
        "error": None
    }
    
    try:
        # Load PDF from memory stream
        pdf_stream = io.BytesIO(file_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        # Check encryption
        if doc.needs_pass:
            result["is_encrypted"] = True
            if password:
                # Try to decrypt
                doc.authenticate(password)
            else:
                # In a real system, you might try a list of known default passwords here
                # Or return indicating password is required
                result["error"] = "Password required to decrypt the PDF."
                return result
                
        result["metadata"] = doc.metadata
        result["page_count"] = doc.page_count
        
        # Extract text
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Get plain text
            text = page.get_text("text").strip()
            
            # If text is too short or looks like a typical watermark, run OCR on images
            if len(text) < 50 or "지원팀" in text or "워터마크" in text or "박희본" in text:
                image_list = page.get_images(full=True)
                if image_list:
                    try:
                        import easyocr
                        # Suppress verbose output
                        import logging
                        logging.getLogger('easyocr').setLevel(logging.ERROR)
                        
                        reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)
                        ocr_text = []
                        for img_info in image_list:
                            xref = img_info[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            res = reader.readtext(image_bytes, detail=0)
                            ocr_text.extend(res)
                        
                        text += "\n" + " ".join(ocr_text)
                    except ImportError:
                        text += "\n[OCR 엔진(easyocr)이 설치되지 않아 이미지 텍스트를 읽을 수 없습니다]"
            
            result["text_content"].append({
                "page": page_num + 1,
                "text": text
            })
            
        result["success"] = True
        
    except Exception as e:
        result["error"] = str(e)
    finally:
        if 'doc' in locals():
            doc.close()
            
    return result

def get_highlighted_pdf_page_image(file_bytes: bytes, search_text: str, page_num: int = 0) -> bytes:
    """
    Loads a PDF from memory, searches for 'search_text' on 'page_num',
    adds a highlight annotation, and renders the page as an image (PNG).
    Returns the image bytes.
    """
    try:
        pdf_stream = io.BytesIO(file_bytes)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        
        if page_num >= len(doc):
            return None
            
        page = doc[page_num]
        
        # Search for the text and add highlight annotations
        if search_text and search_text != "해당 사유 텍스트":
            text_instances = page.search_for(search_text)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.update()
                
        # Render page to an image (Pixmap)
        # matrix zoom scales up the resolution
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        img_bytes = pix.tobytes("png")
        doc.close()
        return img_bytes
        
    except Exception as e:
        print(f"Error generating preview image: {e}")
        return None
