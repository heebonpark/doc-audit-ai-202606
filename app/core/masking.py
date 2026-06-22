import re

def mask_sensitive_data(text: str) -> str:
    """
    Masks sensitive information in the given text using regular expressions.
    Currently supports:
    - 주민등록번호 (Resident Registration Number): 123456-1234567 -> 123456-*******
    - 휴대전화번호 (Phone Number): 010-1234-5678 -> 010-****-5678
    """
    
    # 주민등록번호 마스킹 (YYMMDD-[1-4]\d{6})
    # 패턴 설명: 생년월일 6자리 - 성별(1~4) + 나머지 6자리
    ssn_pattern = r'(\d{6})\s*-\s*([1-4]\d{6})'
    
    def ssn_repl(match):
        front = match.group(1)
        # 뒷자리는 모두 * 로 치환 (혹은 성별 숫자 1개만 남기고 치환)
        # return f"{front}-*******"
        back_first_digit = match.group(2)[0]
        return f"{front}-{back_first_digit}******"
        
    masked_text = re.sub(ssn_pattern, ssn_repl, text)
    
    # 전화번호 마스킹 (010-XXXX-XXXX)
    phone_pattern = r'(01[016789])\s*-\s*(\d{3,4})\s*-\s*(\d{4})'
    
    def phone_repl(match):
        prefix = match.group(1)
        middle = match.group(2)
        suffix = match.group(3)
        return f"{prefix}-{'*' * len(middle)}-{suffix}"
        
    masked_text = re.sub(phone_pattern, phone_repl, masked_text)
    
    # 계좌번호, 이메일 등 추가 마스킹 패턴은 여기에 구현
    
    return masked_text

def apply_masking_to_pages(pages_content: list) -> list:
    """
    Applies masking to a list of page dictionaries containing 'text'.
    """
    masked_pages = []
    for page in pages_content:
        masked_text = mask_sensitive_data(page.get("text", ""))
        masked_pages.append({
            "page": page.get("page"),
            "text": masked_text
        })
    return masked_pages
