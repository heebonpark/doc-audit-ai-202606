import fitz
import os

def create_sample(file_name, text_content):
    doc = fitz.open()
    page = doc.new_page()
    font = fitz.Font("helv")
    p = fitz.Point(50, 70)
    page.insert_text(p, text_content, fontname="helv", fontsize=12)
    doc.save(file_name)
    doc.close()

if __name__ == "__main__":
    os.makedirs("data/hot_folder", exist_ok=True)
    # Generate 5 normal samples
    for i in range(1, 6):
        sample_text = f"Normal Contract\n\nName: User {i}\nSSN: 800101-123456{i}\nReason: Standard registration."
        create_sample(f"data/hot_folder/sample_normal_{i}.pdf", sample_text)
        
    # Generate 1 anomalous sample
    anomaly_text = "Urgent Cancellation\n\nName: Unknown\nSSN: 000000-0000000\nReason: null\nERROR_CODE_99"
    create_sample("data/hot_folder/sample_anomaly_1.pdf", anomaly_text)
    
    print("Created 6 sample PDFs in data/hot_folder/")
