import time
import io
import pyautogui
import pyperclip

class LiveVerifier:
    def __init__(self):
        pass

    def capture_live_state(self) -> dict:
        """
        Captures the text and screenshot of the currently active window.
        Returns a dictionary with raw_text and image_bytes.
        """
        result = {
            "success": False,
            "raw_text": "",
            "image_bytes": None,
            "error": ""
        }
        try:
            # 1. Take a screenshot of the current screen
            screenshot = pyautogui.screenshot()
            
            # Save screenshot to bytes
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            result["image_bytes"] = img_byte_arr.getvalue()
            
            # 2. Extract text via Clipboard (Ctrl+A, Ctrl+C)
            # Clear clipboard first
            pyperclip.copy("")
            
            # Send Ctrl+A (Select All)
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            
            # Send Ctrl+C (Copy)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)
            
            # Deselect
            pyautogui.press('right')
            
            # Get text from clipboard
            copied_text = pyperclip.paste()
            
            if not copied_text or copied_text.strip() == "":
                result["error"] = "클립보드에서 텍스트를 추출할 수 없습니다. (보안 정책으로 클립보드가 막혔을 수 있습니다)"
                return result
                
            result["raw_text"] = copied_text
            result["success"] = True
            
        except Exception as e:
            result["error"] = f"라이브 캡처 중 오류 발생: {str(e)}"
            
        return result
