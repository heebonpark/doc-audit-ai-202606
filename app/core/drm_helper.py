import os
import sys
import shutil
import webbrowser
import fitz  # PyMuPDF
import multiprocessing

def _run_acrobat_com_process(target_file, unlocked_path, visible, result_dict):
    """
    Isolated process function for Acrobat COM.
    """
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        
        app = win32com.client.DispatchEx("AcroExch.App")
        av_doc = win32com.client.DispatchEx("AcroExch.AVDoc")
        
        if visible:
            app.Show()
        else:
            app.Hide()
            
        if av_doc.Open(target_file, "Temp"):
            pd_doc = av_doc.GetPDDoc()
            # 1 = PDSaveFull
            if pd_doc.Save(1, unlocked_path):
                pd_doc.Close()
                av_doc.Close(1)
                if not visible:
                    app.Exit()
                pythoncom.CoUninitialize()
                result_dict["success"] = True
                return
            pd_doc.Close()
            av_doc.Close(1)
        if not visible:
            app.Exit()
        pythoncom.CoUninitialize()
        result_dict["error"] = "Acrobat COM 문서 열기/저장 실패"
    except Exception as e:
        result_dict["error"] = str(e)


def _run_word_com_process(target_file, unlocked_path, visible, result_dict):
    """
    Isolated process function for MS Word COM.
    """
    try:
        import win32com.client
        import pythoncom
        pythoncom.CoInitialize()
        
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = visible
        # If visible is True, we allow alerts so the user can see what's wrong.
        # If visible is False, we strictly suppress alerts.
        word.DisplayAlerts = -1 if visible else 0 
        
        doc = word.Documents.Open(target_file, ConfirmConversions=False)
        doc.SaveAs(unlocked_path, FileFormat=17) # 17 = PDF
        doc.Close()
        if not visible:
            word.Quit()
            
        pythoncom.CoUninitialize()
        result_dict["success"] = True
    except Exception as e:
        result_dict["error"] = str(e)


class SmartDRMEngine:
    def __init__(self, primary_strategy="Acrobat", visible=False):
        self.primary_strategy = primary_strategy
        self.visible = visible
        self.timeout_seconds = 15

    def _strategy_pymupdf(self, target_file: str) -> dict:
        """Strategy 1: Check if it's already unencrypted or natively readable"""
        try:
            doc = fitz.open(target_file)
            if not doc.needs_pass:
                with open(target_file, "rb") as f:
                    file_bytes = f.read()
                doc.close()
                return {"success": True, "file_bytes": file_bytes, "message": "순수 PDF (암호화 안됨) 확인됨."}
            doc.close()
        except Exception:
            pass
        return {"success": False}

    def _run_with_timeout(self, target_function, target_file, unlocked_path) -> dict:
        if sys.platform != "win32":
            return {"success": False, "message": "Windows 환경이 아닙니다."}
            
        manager = multiprocessing.Manager()
        result_dict = manager.dict()
        result_dict["success"] = False
        result_dict["error"] = ""
        
        p = multiprocessing.Process(
            target=target_function,
            args=(target_file, unlocked_path, self.visible, result_dict)
        )
        
        p.start()
        p.join(self.timeout_seconds)
        
        if p.is_alive():
            # Process hung! Kill it forcefully.
            p.terminate()
            p.join()
            return {"success": False, "message": f"Timeout ({self.timeout_seconds}초) 초과. 숨겨진 보안 팝업이 대기 중일 수 있습니다."}
            
        if result_dict.get("success"):
            if os.path.exists(unlocked_path):
                with open(unlocked_path, "rb") as f:
                    file_bytes = f.read()
                os.remove(unlocked_path)
                return {"success": True, "file_bytes": file_bytes, "message": "COM 연동 성공."}
            else:
                return {"success": False, "message": "저장된 파일이 없습니다."}
                
        return {"success": False, "message": result_dict.get("error", "알 수 없는 오류")}

    def _strategy_acrobat(self, target_file: str, unlocked_path: str) -> dict:
        res = self._run_with_timeout(_run_acrobat_com_process, target_file, unlocked_path)
        if res["success"]:
            res["message"] = "Acrobat COM으로 DRM 해제 성공."
        else:
            res["message"] = f"Acrobat 실패: {res.get('message')}"
        return res

    def _strategy_word(self, target_file: str, unlocked_path: str) -> dict:
        res = self._run_with_timeout(_run_word_com_process, target_file, unlocked_path)
        if res["success"]:
            res["message"] = "MS Word COM으로 DRM 해제 성공."
        else:
            res["message"] = f"MS Word 실패: {res.get('message')}"
        return res

    def _strategy_guided_manual(self, target_file: str) -> dict:
        try:
            webbrowser.open(target_file)
            return {"success": False, "requires_manual": True, "message": f"자동 우회 실패. 뷰어가 열렸습니다. 수동으로 '다른 이름으로 저장'을 수행해 주세요."}
        except Exception as e:
            return {"success": False, "message": f"수동 열기 실패: {e}"}

    def process(self, keyword: str, path: str = "data/hot_folder") -> dict:
        result = {"success": False, "file_bytes": None, "message": "", "requires_manual": False}
        
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
                    found_files.append(os.path.abspath(os.path.join(root, file)))
                    
        if not found_files:
            result["message"] = f"'{keyword}' 키워드가 포함된 PDF 파일을 찾을 수 없습니다."
            return result
            
        target_file = found_files[0]
        
        temp_dir = os.path.join(os.getcwd(), "data", "hot_folder", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        unlocked_path = os.path.join(temp_dir, "unlocked_" + os.path.basename(target_file))

        if sys.platform != "win32":
            return self._strategy_pymupdf(target_file)
            
        # 1. Native PyMuPDF check
        res = self._strategy_pymupdf(target_file)
        if res["success"]:
            return res
            
        # 2. Priority Strategy
        strategies = []
        if self.primary_strategy == "Acrobat":
            strategies = [self._strategy_acrobat, self._strategy_word]
        else:
            strategies = [self._strategy_word, self._strategy_acrobat]
            
        for strategy_func in strategies:
            res = strategy_func(target_file, unlocked_path)
            if res.get("success"):
                return res
                
        # 3. Fallback Guided Manual
        return self._strategy_guided_manual(target_file)
