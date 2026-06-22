import fitz
import sys

doc = fitz.open('/Users/heebonpark/Downloads/서울항공윤거점.pdf')
print(f"Total pages: {len(doc)}")
for i in range(min(2, len(doc))):
    page = doc[i]
    images = page.get_images(full=True)
    print(f"Page {i} has {len(images)} images.")
    if images:
        print(f"Image 0 Info: {images[0]}")
