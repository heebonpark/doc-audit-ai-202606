import streamlit as st
import pandas as pd
import time
import io
import os
import glob

from app.ui.styles import inject_premium_css
from app.core.pdf_processor import process_pdf_stream, get_highlighted_pdf_page_image
from app.core.masking import apply_masking_to_pages
from app.core.vision_detector import SignatureDetector
from app.core.llm_verifier import LocalLLMVerifier
from app.core.ml_analyzer import MLAnomalyDetector
from app.core.drm_helper import find_and_unlock_drm_pdf

# Page configuration
st.set_page_config(
    page_title="Data Intel PRO - PDF Verification",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS
inject_premium_css()

def main():
    st.markdown("<h1>Data Intel PRO - 지능형 PDF 자동 검증 시스템</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <p style='color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem;'>
        초고속 인메모리 스트림 처리 및 로컬 AI 기반의 변경/해지/신규 계약서 자동 검증 파이프라인
        </p>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🔒 사내 DRM 파일 로드 지원")
        st.caption("MS Word 백그라운드 제어를 통해 DRM 암호화를 조용하게 자동 해제하고 즉시 검증 파이프라인에 로드합니다.")
        drm_keyword = st.text_input("검색할 파일 키워드", placeholder="예: sample_anomaly")
        drm_path = st.text_input("검색 대상 폴더 경로", value="data/hot_folder")
        
        load_drm_btn = st.button("파일 검색 및 자동 검증 시작", type="primary")
        
        st.divider()
        st.markdown("##### 메뉴")
        st.button("⚙️ 설정")
        st.button("📊 대시보드")
        st.button("🚪 로그아웃")

    # Dashboard Metrics (Traffic Light System)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="오늘 누적 처리", value="142 건")
    with col2:
        st.markdown("<div class='status-green' style='display:inline-block; margin-bottom: 5px;'>정상 (Normal)</div>", unsafe_allow_html=True)
        st.metric(label="", value="128 건")
    with col3:
        st.markdown("<div class='status-yellow' style='display:inline-block; margin-bottom: 5px;'>의심 (Suspicious)</div>", unsafe_allow_html=True)
        st.metric(label="", value="11 건")
    with col4:
        st.markdown("<div class='status-red' style='display:inline-block; margin-bottom: 5px;'>반려 (Rejected)</div>", unsafe_allow_html=True)
        st.metric(label="", value="3 건")

    st.markdown("<hr style='border-color: #334155; margin: 30px 0;'>", unsafe_allow_html=True)
    
    # Common variables for the pipeline
    file_bytes_to_process = None
    
    # 1. DRM Loader Logic
    if load_drm_btn:
        with st.spinner("DRM 파일을 찾고 보안을 해제하는 중입니다... (MS Word 백그라운드 구동 중)"):
            drm_result = find_and_unlock_drm_pdf(drm_keyword, drm_path)
            if drm_result["success"]:
                st.success(drm_result["message"])
                file_bytes_to_process = drm_result["file_bytes"]
            else:
                st.error(drm_result["message"])

    # 2. Standard Upload Logic
    st.markdown("### 📄 계약서/신청서 단일 파일 검증 (테스트)")
    uploaded_file = st.file_uploader("검증할 PDF 파일을 드래그 앤 드롭 하세요 (일반 파일용)", type=['pdf'])
    
    if uploaded_file is not None:
        file_bytes_to_process = uploaded_file.read()
        
    if file_bytes_to_process is not None:
        st.info("파일이 메모리에 로드되었습니다. 자동 검증 파이프라인을 시작합니다...")
        
        # This is a placeholder for the actual processing logic
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1 & 2: Load and Extract
        status_text.text("1/5: 메모리 스트림 로딩 및 텍스트 추출 중 (PyMuPDF)...")
        progress_bar.progress(20)
        time.sleep(0.5) # UX delay
        
        pdf_result = process_pdf_stream(file_bytes_to_process)
        
        if not pdf_result["success"]:
            st.error(f"PDF 로딩 실패: {pdf_result.get('error', '알 수 없는 오류')}")
            st.stop()
            
        # Step 3: Masking
        status_text.text("2/5: 정규식 기반 민감정보(주민번호 등) 마스킹 처리 중...")
        progress_bar.progress(40)
        masked_pages = apply_masking_to_pages(pdf_result["text_content"])
        time.sleep(0.5)
        
        # Step 4: Signature Detection (Mocked)
        status_text.text("3/5: 인감/서명(YOLOv8) 탐지 중 (로컬 모델)...")
        progress_bar.progress(60)
        vision_engine = SignatureDetector()
        vision_result = vision_engine.detect_signature(file_bytes_to_process)
        time.sleep(0.5)
        
        # Step 5: LLM Verification (Mocked)
        status_text.text("4/5: 로컬 LLM 논리 모순(의미론적 검증) 분석 중...")
        progress_bar.progress(80)
        llm_engine = LocalLLMVerifier()
        # combine text for llm
        full_text = "\n".join([p["text"] for p in masked_pages])
        llm_result = llm_engine.verify_document_logic(full_text)
        time.sleep(0.5)
            
        status_text.text("5/5: 최종 신뢰도 점수 산출 중...")
        progress_bar.progress(100)
        time.sleep(0.5)
        status_text.text("✅ 검증 완료!")
        
        st.markdown("### 📊 검증 결과 리포트")
        
        if llm_result["status"] == "정상":
            status_html = "<div class='status-green' style='display:inline-block; font-size: 18px; margin-bottom: 15px;'>결과: 정상 (Normal)</div>"
        elif llm_result["status"] == "의심":
            status_html = f"<div class='status-yellow' style='display:inline-block; font-size: 18px; margin-bottom: 15px;'>결과: 의심 (Suspicious) - {llm_result['reason']}</div>"
        else:
            status_html = "<div class='status-red' style='display:inline-block; font-size: 18px; margin-bottom: 15px;'>결과: 반려 (Rejected)</div>"
            
        st.markdown(status_html, unsafe_allow_html=True)
        
        # Suspicious Highlight Preview (Phase 3)
        if llm_result["status"] != "정상" and "evidence_snippet" in llm_result:
            st.markdown("#### 🔍 의심 영역 원본 미리보기 (시각적 하이라이트)")
            evidence = llm_result["evidence_snippet"]
            
            # Text based preview
            preview_text = masked_pages[0]["text"][:500] if masked_pages else "텍스트 없음"
            if evidence and evidence in preview_text:
                highlighted = preview_text.replace(evidence, f"<mark style='background-color: #facc15; color: #000; padding: 0 4px; border-radius: 4px; font-weight: bold;'>{evidence}</mark>")
            else:
                highlighted = f"... <mark style='background-color: #facc15; color: #000; padding: 0 4px; border-radius: 4px; font-weight: bold;'>{evidence}</mark> ..."
                
            st.markdown(f"<div style='background-color: rgba(30,41,59,0.5); padding: 15px; border-radius: 10px; border-left: 4px solid #facc15; margin-bottom: 20px;'>{highlighted}</div>", unsafe_allow_html=True)
            
            # Visual PDF Image Preview
            img_bytes = get_highlighted_pdf_page_image(file_bytes_to_process, evidence, page_num=0)
            if img_bytes:
                st.image(img_bytes, caption="원본 문서 내 의심 영역 자동 하이라이팅", use_container_width=True)
        
        # Display extracted and masked text summary
        with st.expander("📄 추출 및 마스킹된 텍스트 확인 (1페이지 미리보기)"):
            if masked_pages:
                st.text(masked_pages[0]["text"][:1000] + "... (생략)")
            else:
                st.text("추출된 텍스트가 없습니다.")
        
        # Result data
        result_data = {
            "검증 항목": ["문서 포맷 확인", "주민등록번호 마스킹", "인감/서명 존재 여부", "논리/의미론적 검증"],
            "상태": ["🟢 정상", "🟢 완료", "🟢 감지됨" if vision_result["has_signature"] else "🔴 미감지", "🟡 의심" if llm_result["status"] == "의심" else "🟢 정상"],
            "세부 내용": [f"총 {pdf_result['page_count']}페이지 추출 성공", "정규식 패턴 적용 완료", f"신뢰도 {vision_result['confidence']*100:.1f}%", llm_result["reason"]]
        }
        
        df = pd.DataFrame(result_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("단일 검증 결과 엑셀로 다운로드"):
            excel_io = io.BytesIO()
            df.to_excel(excel_io, index=False, engine='openpyxl')
            excel_io.seek(0)
            
            st.download_button(
                label="다운로드 클릭",
                data=excel_io,
                file_name="single_verification_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.markdown("<hr style='border-color: #334155; margin: 30px 0;'>", unsafe_allow_html=True)
    
    # Hot Folder Batch Processing Section
    st.markdown("### 📁 핫폴더(Hot Folder) 일괄 검증")
    st.markdown("<p style='color: #94a3b8;'>지정된 핫폴더 내의 모든 PDF 문서를 일괄 검증합니다. (경로: <code>data/hot_folder/</code>)</p>", unsafe_allow_html=True)
    
    hot_folder_path = "data/hot_folder"
    if not os.path.exists(hot_folder_path):
        os.makedirs(hot_folder_path)
        
    pdf_files = glob.glob(os.path.join(hot_folder_path, "*.pdf"))
    
    if len(pdf_files) == 0:
        st.info("핫폴더에 대기 중인 PDF 파일이 없습니다. 파일을 추가해 주세요.")
    else:
        st.write(f"대기 중인 파일: **{len(pdf_files)}** 건")
        
        if st.button("일괄 검증 및 머신러닝 이상 탐지 시작", type="primary"):
            batch_results = []
            extracted_texts = []
            
            progress_bar_batch = st.progress(0)
            status_text_batch = st.empty()
            
            for idx, file_path in enumerate(pdf_files):
                file_name = os.path.basename(file_path)
                status_text_batch.text(f"처리 중: {file_name} ({idx+1}/{len(pdf_files)})")
                
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                    
                # Process
                pdf_result = process_pdf_stream(file_bytes)
                if not pdf_result["success"]:
                    batch_results.append({
                        "파일명": file_name,
                        "상태": "🔴 오류",
                        "LLM 의심사유": "N/A",
                        "의심영역(미리보기)": "N/A",
                        "ML_이상여부": "N/A",
                        "ML_이상점수": 0
                    })
                    extracted_texts.append("")
                    continue
                    
                masked_pages = apply_masking_to_pages(pdf_result["text_content"])
                full_text = "\\n".join([p["text"] for p in masked_pages])
                extracted_texts.append(full_text)
                
                llm_engine = LocalLLMVerifier()
                llm_result = llm_engine.verify_document_logic(full_text)
                
                # Determine final status
                final_status = "🟢 정상" if llm_result["status"] == "정상" else ("🟡 의심" if llm_result["status"] == "의심" else "🔴 반려")
                
                batch_results.append({
                    "파일명": file_name,
                    "상태": final_status,
                    "LLM 의심사유": llm_result["reason"],
                    "의심영역(미리보기)": llm_result.get("evidence_snippet", ""),
                    "ML_이상여부": False, # Will be filled later
                    "ML_이상점수": 0
                })
                
                progress_bar_batch.progress((idx + 1) / len(pdf_files) * 0.7) # 70% progress for individual processing
                
            # Phase 5: Machine Learning Anomaly Detection
            status_text_batch.text("🤖 ML/DL 다중 문서 패턴 분석 중 (Isolation Forest)...")
            ml_analyzer = MLAnomalyDetector()
            ml_results = ml_analyzer.analyze_batch(extracted_texts)
            
            # Combine ML results into batch results
            for i, res in enumerate(ml_results):
                if batch_results[i]["상태"] != "🔴 오류":
                    batch_results[i]["ML_이상여부"] = "🚨 이상치 감지" if res["is_anomaly"] else "✅ 패턴 정상"
                    batch_results[i]["ML_이상점수"] = f"{res['score']:.1f}"
                    
                    # If ML detects an anomaly, upgrade status to Suspicious/Rejected if it was normal
                    if res["is_anomaly"] and batch_results[i]["상태"] == "🟢 정상":
                        batch_results[i]["상태"] = "🟡 의심(ML탐지)"
            
            progress_bar_batch.progress(100)
            status_text_batch.text("✅ 일괄 검증 및 머신러닝 분석 완료!")
            
            st.markdown("### 📊 통합 검증 리포트 (LLM + ML)")
            df_batch = pd.DataFrame(batch_results)
            st.dataframe(df_batch, use_container_width=True, hide_index=True)
            
            # Batch Excel Download
            batch_excel_io = io.BytesIO()
            df_batch.to_excel(batch_excel_io, index=False, engine='openpyxl')
            batch_excel_io.seek(0)
            
            st.download_button(
                label="일괄 검증 결과 엑셀 다운로드",
                data=batch_excel_io,
                file_name="batch_verification_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
