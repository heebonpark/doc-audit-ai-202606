import os
import sys
import shutil
import webbrowser
import fitz  # PyMuPDF

class SmartDRMEngine:
    def __init__(self, primary_strategy="Acrobat"):
        self.primary_strategy = primary_strategy

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

    def _strategy_acrobat(self, target_file: str, unlocked_path: str) -> dict:
        """Strategy 2: Adobe Acrobat COM Automation"""
        if sys.platform != "win32":
            return {"success": False, "message": "Acrobat COM은 Windows에서만 지원됩니다."}
        try:
            import win32com.client
            app = win32com.client.DispatchEx("AcroExch.App")
            av_doc = win32com.client.DispatchEx("AcroExch.AVDoc")
            
            # Hide app
            app.Hide()
            
            if av_doc.Open(target_file, "Temp"):
                pd_doc = av_doc.GetPDDoc()
                # 1 = PDSaveFull
                if pd_doc.Save(1, unlocked_path):
                    pd_doc.Close()
                    av_doc.Close(1)
                    app.Exit()
                    with open(unlocked_path, "rb") as f:
                        file_bytes = f.read()
                    os.remove(unlocked_path)
                    return {"success": True, "file_bytes": file_bytes, "message": "Acrobat COM으로 DRM 해제 성공."}
                pd_doc.Close()
                av_doc.Close(1)
            app.Exit()
        except Exception as e:
            pass
        return {"success": False, "message": "Acrobat COM 연동 실패 또는 권한 없음."}

    def _strategy_word(self, target_file: str, unlocked_path: str) -> dict:
        """Strategy 3: MS Word COM Automation"""
        if sys.platform != "win32":
            return {"success": False, "message": "Word COM은 Windows에서만 지원됩니다."}
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0 # 0 = wdAlertsNone (prevents hanging on dialogs)
            doc = word.Documents.Open(target_file, ConfirmConversions=False)
            doc.SaveAs(unlocked_path, FileFormat=17) # 17 = PDF
            doc.Close()
            word.Quit()
            
            with open(unlocked_path, "rb") as f:
                file_bytes = f.read()
            os.remove(unlocked_path)
            return {"success": True, "file_bytes": file_bytes, "message": "MS Word COM으로 DRM 해제 성공."}
        except Exception as e:
            try:
                word.Quit()
            except:
                pass
        return {"success": False, "message": "MS Word COM 연동 실패."}

    def _strategy_guided_manual(self, target_file: str) -> dict:
        """Strategy 4: Guided Manual Fallback"""
        try:
            webbrowser.open(target_file)
            return {"success": False, "requires_manual": True, "message": f"자동 우회 실패. 뷰어가 열렸습니다. 수동으로 '다른 이름으로 저장'을 통해 보안을 해제해주세요. ({os.path.basename(target_file)})"}
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
        
        # Temp dir prep
        temp_dir = os.path.join(os.getcwd(), "data", "hot_folder", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        unlocked_path = os.path.join(temp_dir, "unlocked_" + os.path.basename(target_file))

        # Mac Fallback
        if sys.platform != "win32":
            return self._strategy_pymupdf(target_file)
            
        # Strategy Pipeline
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
