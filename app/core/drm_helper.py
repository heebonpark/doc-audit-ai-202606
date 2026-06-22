import os
import sys
import shutil

def find_and_unlock_drm_pdf(keyword: str, path: str = "data/hot_folder") -> dict:
    """
    Searches for a PDF file containing the given keyword in the filename within the specified path.
    Uses MS Word COM automation (Option A) on Windows to silently open the DRM-encrypted PDF
    and save it as an unencrypted PDF in a temp directory.
    
    Returns a dictionary with success status, extracted file bytes, and error messages.
    """
    result = {"success": False, "file_bytes": None, "message": ""}
    
    if not keyword:
        result["message"] = "키워드를 입력해주세요."
        return result
        
    if not os.path.exists(path):
        result["message"] = f"경로가 존재하지 않습니다: {path}"
        return result
        
    found_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if keyword in file and file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                found_files.append(full_path)
                
    if not found_files:
        result["message"] = f"'{keyword}' 키워드가 포함된 PDF 파일을 찾을 수 없습니다."
        return result
        
    target_file = found_files[0]
    
    # If not on Windows, we cannot use win32com. We just read it normally.
    if sys.platform != "win32":
        try:
            with open(target_file, "rb") as f:
                result["file_bytes"] = f.read()
            result["success"] = True
            result["message"] = f"(Mac 환경) 파일 로드 성공: {os.path.basename(target_file)}"
            return result
        except Exception as e:
            result["message"] = f"파일 읽기 실패: {e}"
            return result
            
    # Windows DRM Automation using MS Word COM
    try:
        import win32com.client
    except ImportError:
        result["message"] = "pywin32 패키지가 설치되지 않았습니다. pip install pywin32 를 실행하세요."
        return result
        
    temp_dir = os.path.join(os.getcwd(), "data", "hot_folder", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    unlocked_path = os.path.join(temp_dir, "unlocked_" + os.path.basename(target_file))
    
    # Normalize paths for Windows COM
    target_file = os.path.abspath(target_file)
    unlocked_path = os.path.abspath(unlocked_path)
    
    try:
        # Start MS Word in the background
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False # Run silently
        
        # Open the PDF (Word automatically converts/decrypts whitelisted PDFs)
        doc = word.Documents.Open(target_file, ConfirmConversions=False)
        
        # Save As PDF (FileFormat=17 represents PDF in Word COM)
        doc.SaveAs(unlocked_path, FileFormat=17)
        doc.Close()
        word.Quit()
        
        # Read the unlocked bytes
        with open(unlocked_path, "rb") as f:
            result["file_bytes"] = f.read()
            
        # Clean up the temp file
        os.remove(unlocked_path)
        
        result["success"] = True
        result["message"] = f"✅ DRM 해제 및 로드 성공: {os.path.basename(target_file)}"
        
    except Exception as e:
        # Try to quit word application to prevent hanging background processes
        try:
            word.Quit()
        except:
            pass
        result["message"] = f"DRM 해제 중 오류 발생 (MS Word 연동 실패): {e}"
        
    return result
