import fitz
import easyocr
from PIL import Image
import io

print("Initializing EasyOCR...")
reader = easyocr.Reader(['ko', 'en'], gpu=False)

doc = fitz.open('/Users/heebonpark/Downloads/서울항공윤거점.pdf')
page = doc[0]
image_list = page.get_images(full=True)
if image_list:
    xref = image_list[0][0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]
    
    print("Running OCR on first image...")
    result = reader.readtext(image_bytes, detail=0)
    print("OCR Text:", " ".join(result))
else:
    print("No images found.")
