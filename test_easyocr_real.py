import fitz
import easyocr
import time

print("Loading EasyOCR...")
reader = easyocr.Reader(['ko', 'en'], gpu=False)

doc = fitz.open('/Users/heebonpark/Downloads/서울항공윤거점.pdf')
images = doc[0].get_images(full=True)
xref = images[0][0]
base_image = doc.extract_image(xref)
image_bytes = base_image["image"]

print("Running OCR on image 0...")
start = time.time()
res = reader.readtext(image_bytes, detail=0)
end = time.time()

print(f"OCR Time: {end-start:.2f}s")
print("Result:", res)
