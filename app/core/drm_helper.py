import os
import webbrowser

def find_and_open_drm_pdf(keyword: str, path: str = "data/hot_folder") -> str:
    """
    Searches for a PDF file containing the given keyword in the filename
    within the specified path, and opens it using the default system viewer
    (webbrowser.open).
    
    This is specifically used to trigger the company's DRM decryption mechanism,
    which unencrypts the file in memory when opened by a whitelisted system viewer.
    
    Returns a status message.
    """
    if not keyword:
        return "키워드를 입력해주세요."
        
    if not os.path.exists(path):
        return f"경로가 존재하지 않습니다: {path}"
        
    found_files = []
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if keyword in file and file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                found_files.append(full_path)
                
    if not found_files:
        return f"'{keyword}' 키워드가 포함된 PDF 파일을 찾을 수 없습니다."
        
    # Open the first matched file to trigger DRM unlock
    target_file = found_files[0]
    try:
        webbrowser.open(target_file)
        return f"성공: '{os.path.basename(target_file)}' 파일을 열었습니다. 뷰어에서 '다른 이름으로 저장'을 통해 DRM을 해제해 주세요."
    except Exception as e:
        return f"파일 열기 실패: {e}"
