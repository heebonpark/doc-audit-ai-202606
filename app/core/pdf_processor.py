import fitz  # PyMuPDF
import io

def process_pdf_stream(file_bytes: bytes, password: str = None) -> dict:
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
            text = page.get_text("text")
            result["text_content"].append({
                "page": page_num + 1,
                "text": text
            })
            
        result["success"] = True
        
    except Exception as e:
        result["error"] = str(e)
    finally:
        if 'doc' in locals():
            
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
