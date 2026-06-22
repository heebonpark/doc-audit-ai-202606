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
from app.core.drm_helper import SmartDRMEngine
from app.core.live_capture import LiveVerifier

# Page configuration
st.set_page_config(
    page_title="Data Intel PRO - PDF Verification",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom CSS
inject_premium_css()

def init_session_state():
    if "drm_strategy" not in st.session_state:
        st.session_state.drm_strategy = "Acrobat"
    if "hot_folder_path" not in st.session_state:
        st.session_state.hot_folder_path = "data/hot_folder"
    if "drm_visible" not in st.session_state:
        st.session_state.drm_visible = False
    if "history_records" not in st.session_state:
        st.session_state.history_records = []
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

def process_single_file_logic(file_bytes_to_process=None, live_text=None, live_image=None, file_name="단일 캡처/업로드"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    is_live = (live_text is not None and live_image is not None)
    
    # Step 1 & 2: Load and Extract
    if not is_live:
        status_text.text("1/5: 메모리 스트림 로딩 및 텍스트 추출 중 (PyMuPDF)...")
        progress_bar.progress(20)
        time.sleep(0.5)
        pdf_result = process_pdf_stream(file_bytes_to_process)
        if not pdf_result["success"]:
            st.error(f"PDF 로딩 실패: {pdf_result.get('error', '알 수 없는 오류')}")
            st.stop()
        page_count = pdf_result["page_count"]
    else:
        status_text.text("1/5: 화면 메모리(Clipboard) 직접 후킹 및 텍스트 파싱 중...")
        progress_bar.progress(20)
        time.sleep(0.5)
        page_count = "Live Capture"

    # Step 3: Masking
    status_text.text("2/5: 정규식 기반 민감정보(주민번호 등) 마스킹 처리 중...")
    progress_bar.progress(40)
    if not is_live:
        masked_pages = apply_masking_to_pages(pdf_result["text_content"])
        full_text = "\n".join([p["text"] for p in masked_pages])
    else:
        masked_pages = apply_masking_to_pages([{"page": 1, "text": live_text}])
        full_text = "\n".join([p["text"] for p in masked_pages])
    time.sleep(0.5)
    
    # Step 4: Signature Detection
    status_text.text("3/5: 인감/서명(YOLOv8) 탐지 중 (로컬 모델)...")
    progress_bar.progress(60)
    vision_engine = SignatureDetector()
    vision_result = vision_engine.detect_signature(file_bytes_to_process if not is_live else live_image)
    time.sleep(0.5)
    
    # Step 5: LLM Verification
    status_text.text("4/5: 로컬 LLM 논리 모순(의미론적 검증) 분석 중...")
    progress_bar.progress(80)
    llm_engine = LocalLLMVerifier()
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
    
    # Show Extracted Data Dashboard
    if "extracted_data" in llm_result:
        st.markdown("#### 📋 AI 추출 문서 핵심 정보 (Data Extraction)")
        ext = llm_result["extracted_data"]
        
        col_ex1, col_ex2, col_ex3 = st.columns(3)
        with col_ex1:
            st.markdown(f"**문서 유형:** <span style='color:#38bdf8'>{ext.get('문서 유형', 'N/A')}</span>", unsafe_allow_html=True)
            st.markdown(f"**계약자(고객명):** <span style='color:#38bdf8'>{ext.get('고객명(계약자)', 'N/A')}</span>", unsafe_allow_html=True)
        with col_ex2:
            st.markdown(f"**작성 일자:** <span style='color:#38bdf8'>{ext.get('작성 일자', 'N/A')}</span>", unsafe_allow_html=True)
            st.markdown(f"**특이사항:** <span style='color:#fb7185'>{ext.get('특이사항', 'N/A')}</span>", unsafe_allow_html=True)
        with col_ex3:
            st.markdown(f"**신청 사유:**")
            st.markdown(f"<div style='background-color:#1e293b; padding:8px; border-radius:5px;'>{ext.get('신청 사유', 'N/A')}</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

    # Suspicious Highlight Preview
    if llm_result["status"] != "정상" and "evidence_snippet" in llm_result:
        st.markdown("#### 🔍 의심 영역 원본 미리보기 (시각적 하이라이트)")
        evidence = llm_result["evidence_snippet"]
        
        preview_text = masked_pages[0]["text"][:500] if masked_pages else "텍스트 없음"
        if evidence and evidence in preview_text:
            highlighted = preview_text.replace(evidence, f"<mark style='background-color: #facc15; color: #000; padding: 0 4px; border-radius: 4px; font-weight: bold;'>{evidence}</mark>")
        else:
            highlighted = f"... <mark style='background-color: #facc15; color: #000; padding: 0 4px; border-radius: 4px; font-weight: bold;'>{evidence}</mark> ..."
            
        st.markdown(f"<div style='background-color: rgba(30,41,59,0.5); padding: 15px; border-radius: 10px; border-left: 4px solid #facc15; margin-bottom: 20px;'>{highlighted}</div>", unsafe_allow_html=True)
        
        if not is_live:
            img_bytes = get_highlighted_pdf_page_image(file_bytes_to_process, evidence, page_num=0)
            if img_bytes:
                st.image(img_bytes, caption="원본 문서 내 의심 영역 자동 하이라이팅", use_container_width=True)
        else:
            st.image(live_image, caption="현재 화면 스크린샷 (라이브 캡처본)", use_container_width=True)
    
    with st.expander("📄 추출 및 마스킹된 텍스트 확인 (1페이지 미리보기)"):
        if masked_pages:
            st.text(masked_pages[0]["text"][:1000] + "... (생략)")
        else:
            st.text("추출된 텍스트가 없습니다.")
    
    result_data = {
        "검증 항목": ["문서 포맷 확인", "주민등록번호 마스킹", "인감/서명 존재 여부", "논리/의미론적 검증"],
        "상태": ["🟢 정상", "🟢 완료", "🟢 감지됨" if vision_result["has_signature"] else "🔴 미감지", "🟡 의심" if llm_result["status"] == "의심" else "🟢 정상"],
        "세부 내용": [f"총 {page_count}페이지 추출 성공" if not is_live else "라이브 메모리 스크래핑 성공", "정규식 패턴 적용 완료", f"신뢰도 {vision_result['confidence']*100:.1f}%", llm_result["reason"]]
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
        
    # Append to history
    from datetime import datetime
    st.session_state.history_records.append({
        "시간": datetime.now().strftime("%H:%M:%S"),
        "파일명": file_name,
        "상태": "🟢 정상" if llm_result["status"] == "정상" else ("🟡 의심" if llm_result["status"] == "의심" else "🔴 반려"),
        "사유": llm_result["reason"]
    })

def main():
    init_session_state()
    
    st.markdown("<h1>Data Intel PRO - 지능형 PDF 자동 검증 시스템</h1>", unsafe_allow_html=True)
    st.markdown("""
        <p style='color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem;'>
        초고속 인메모리 스트림 처리 및 로컬 AI 기반의 변경/해지/신규 계약서 자동 검증 파이프라인
        </p>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("##### 메뉴")
        st.button("📊 대시보드")
        st.button("🚪 로그아웃")
        
        st.markdown("---")
        st.markdown("##### 📜 검증 이력 (History)")
        if not st.session_state.history_records:
            st.info("오늘 수행된 검증 내역이 없습니다.")
        else:
            history_df = pd.DataFrame(st.session_state.history_records)
            st.dataframe(history_df, use_container_width=True, hide_index=True)
            
            excel_io = io.BytesIO()
            history_df.to_excel(excel_io, index=False, engine='openpyxl')
            excel_io.seek(0)
            
            st.download_button(
                label="📥 전체 이력 다운로드",
                data=excel_io,
                file_name="verification_history.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    # Dashboard Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(label="오늘 누적 처리", value="142 건")
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
    
    col_reset1, col_reset2 = st.columns([8, 2])
    with col_reset2:
        if st.button("🔄 화면 및 세션 초기화", use_container_width=True, help="현재 화면에 떠 있는 텍스트와 이미지, 결과표를 깔끔하게 지웁니다. (사이드바 이력은 보존됨)"):
            st.session_state.uploader_key += 1
            st.rerun()
            
    # UI Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔒 DRM/핫폴더 일괄 처리", "👁️ 화면 라이브 직접 검증", "📄 단일 파일 수동 검증", "⚙️ 환경 설정"])

    # --- TAB 1: DRM & BATCH ---
    with tab1:
        st.markdown("### 📁 스마트 DRM & 핫폴더 일괄 검증")
        st.markdown("<p style='color: #94a3b8;'>키워드로 암호화된 파일을 찾거나 지정된 핫폴더의 모든 파일을 검증합니다.</p>", unsafe_allow_html=True)
        
        # DRM keyword finder
        with st.container():
            st.markdown("#### 1. 특정 DRM 파일 자동 탐색 및 해제")
            col_k, col_b = st.columns([3, 1])
            with col_k:
                drm_keyword = st.text_input("검색할 파일 키워드", placeholder="예: sample_anomaly")
            with col_b:
                st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                load_drm_btn = st.button("파일 검색 및 자동 검증", type="primary")
                
            if load_drm_btn:
                drm_engine = SmartDRMEngine(
                    primary_strategy=st.session_state.drm_strategy,
                    visible=st.session_state.drm_visible
                )
                with st.status("DRM 우회 엔진 가동 중...", expanded=True) as status:
                    st.write(f"현재 선택된 전략: {st.session_state.drm_strategy} COM")
                    st.write("파일 스캔 및 백그라운드 해제 프로세스 시작...")
                    drm_result = drm_engine.process(drm_keyword, st.session_state.hot_folder_path)
                    
                    if drm_result.get("requires_manual"):
                        status.update(label="수동 해제 필요", state="error", expanded=True)
                        st.warning(drm_result["message"])
                    elif drm_result["success"]:
                        status.update(label=drm_result["message"], state="complete", expanded=False)
                        st.toast('DRM 해제 성공!', icon='✅')
                        # Start processing
                        st.info("파일이 준비되었습니다. 검증 파이프라인을 구동합니다.")
                        process_single_file_logic(file_bytes_to_process=drm_result["file_bytes"], file_name=drm_keyword)
                    else:
                        status.update(label="우회 실패", state="error", expanded=True)
                        st.error(drm_result["message"])

        st.divider()
        st.markdown("#### 2. 전체 핫폴더 일괄 분석 (머신러닝)")
        hot_folder_path = st.session_state.hot_folder_path
        if not os.path.exists(hot_folder_path):
            os.makedirs(hot_folder_path)
            
        pdf_files = glob.glob(os.path.join(hot_folder_path, "*.pdf"))
        if len(pdf_files) == 0:
            st.info("핫폴더에 대기 중인 PDF 파일이 없습니다.")
        else:
            st.write(f"현재 **{len(pdf_files)}** 개의 파일이 감지되었습니다. (암호화된 파일은 제외됨)")
            if st.button("일괄 검증 및 다중 문서 패턴 분석(ML) 시작"):
                # (Batch Logic copied and adapted here)
                batch_results = []
                extracted_texts = []
                
                progress_bar_batch = st.progress(0)
                status_text_batch = st.empty()
                
                for idx, file_path in enumerate(pdf_files):
                    file_name = os.path.basename(file_path)
                    status_text_batch.text(f"처리 중: {file_name} ({idx+1}/{len(pdf_files)})")
                    
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                        
                    pdf_result = process_pdf_stream(file_bytes)
                    if not pdf_result["success"]:
                        batch_results.append({"파일명": file_name, "상태": "🔴 오류", "LLM 의심사유": "N/A", "의심영역(미리보기)": "N/A", "ML_이상여부": "N/A", "ML_이상점수": 0})
                        extracted_texts.append("")
                        continue
                        
                    masked_pages = apply_masking_to_pages(pdf_result["text_content"])
                    full_text = "\n".join([p["text"] for p in masked_pages])
                    extracted_texts.append(full_text)
                    
                    llm_engine = LocalLLMVerifier()
                    llm_result = llm_engine.verify_document_logic(full_text)
                    final_status = "🟢 정상" if llm_result["status"] == "정상" else ("🟡 의심" if llm_result["status"] == "의심" else "🔴 반려")
                    
                    batch_results.append({"파일명": file_name, "상태": final_status, "LLM 의심사유": llm_result["reason"], "의심영역(미리보기)": llm_result.get("evidence_snippet", ""), "ML_이상여부": False, "ML_이상점수": 0})
                    progress_bar_batch.progress((idx + 1) / len(pdf_files) * 0.7)
                    
                status_text_batch.text("🤖 ML/DL 다중 문서 패턴 분석 중 (Isolation Forest)...")
                ml_analyzer = MLAnomalyDetector()
                ml_results = ml_analyzer.analyze_batch(extracted_texts)
                
                for i, res in enumerate(ml_results):
                    if batch_results[i]["상태"] != "🔴 오류":
                        batch_results[i]["ML_이상여부"] = "🚨 이상치 감지" if res["is_anomaly"] else "✅ 패턴 정상"
                        batch_results[i]["ML_이상점수"] = f"{res['score']:.1f}"
                        if res["is_anomaly"] and batch_results[i]["상태"] == "🟢 정상":
                            batch_results[i]["상태"] = "🟡 의심(ML탐지)"
                
                progress_bar_batch.progress(100)
                status_text_batch.text("✅ 일괄 검증 및 머신러닝 분석 완료!")
                
                df_batch = pd.DataFrame(batch_results)
                st.dataframe(df_batch, use_container_width=True, hide_index=True)
                
                batch_excel_io = io.BytesIO()
                df_batch.to_excel(batch_excel_io, index=False, engine='openpyxl')
                batch_excel_io.seek(0)
                
                st.download_button(
                    label="일괄 검증 결과 엑셀 다운로드",
                    data=batch_excel_io,
                    file_name="batch_verification_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Append batch results to history
                from datetime import datetime
                for res in batch_results:
                    st.session_state.history_records.append({
                        "시간": datetime.now().strftime("%H:%M:%S"),
                        "파일명": res["파일명"],
                        "상태": res["상태"],
                        "사유": res["LLM 의심사유"]
                    })

    # --- TAB 2: LIVE VERIFICATION ---
    with tab2:
        st.markdown("### 👁️ 현재 띄워진 문서 직접 검증 (Live Verification)")
        st.markdown("<p style='color: #94a3b8;'>파일 저장이 불가능한 강력한 보안 환경에서, 현재 열려있는 뷰어 화면의 텍스트와 이미지를 실시간으로 후킹하여 검증합니다.</p>", unsafe_allow_html=True)
        
        st.info("💡 **사용 방법:** 버튼을 누른 후, 3초 안에 사내 문서 뷰어(Acrobat 등) 창을 클릭하여 화면에 띄워주세요!")
        
        if st.button("현재 열린 문서 검증 시작", type="primary", use_container_width=True):
            with st.status("라이브 캡처 준비 중...", expanded=True) as status:
                for i in range(3, 0, -1):
                    st.write(f"⏳ {i}초 뒤 캡처가 시작됩니다. 아크로뱃 창을 활성화해주세요!")
                    time.sleep(1)
                    
                st.write("📸 화면 및 텍스트 데이터 추출 중...")
                live_verifier = LiveVerifier()
                cap_result = live_verifier.capture_live_state()
                
                if cap_result["success"]:
                    status.update(label="라이브 데이터 후킹 성공!", state="complete", expanded=False)
                    st.success("메모리에서 텍스트와 스크린샷 추출을 완료했습니다. 검증을 시작합니다.")
                    process_single_file_logic(live_text=cap_result["raw_text"], live_image=cap_result["image_bytes"])
                else:
                    status.update(label="라이브 캡처 실패", state="error", expanded=True)
                    st.error(cap_result.get("error", "캡처 도중 오류가 발생했습니다."))

    # --- TAB 3: SINGLE UPLOAD ---
    with tab3:
        st.markdown("### 📄 단일 파일 수동 업로드 검증")
        st.markdown("<p style='color: #94a3b8;'>DRM이 걸려있지 않은 일반 문서를 테스트합니다.</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("검증할 PDF 파일을 드래그 앤 드롭 하세요", type=['pdf'], key=f"single_uploader_{st.session_state.uploader_key}")
        if uploaded_file is not None:
            file_bytes_to_process = uploaded_file.read()
            st.info("메모리에 파일이 로드되었습니다. 검증을 시작합니다...")
            process_single_file_logic(file_bytes_to_process=file_bytes_to_process, file_name=uploaded_file.name)

    # --- TAB 4: SETTINGS ---
    with tab4:
        st.markdown("### ⚙️ 시스템 환경 설정")
        st.markdown("SaaS 운영자 및 로컬 시스템 설정을 관리합니다.")
        
        with st.container():
            st.subheader("1. 스마트 DRM 해제 엔진 설정")
            st.caption("문서 원본을 훼손하지 않으면서도 안정적으로 DRM을 우회하기 위한 1순위 타겟 엔진을 선택합니다.")
            
            selected_strategy = st.selectbox(
                "기본 DRM 우회 전략", 
                ["Acrobat", "Word (Print)", "Word"], 
                index=0 if st.session_state.drm_strategy == "Acrobat" else (1 if st.session_state.drm_strategy == "Word (Print)" else 2),
                help="Acrobat은 원본 유지가 잘 되지만 버전에 따라 백그라운드 저장이 막힐 수 있습니다. Word (Print)는 Microsoft Print to PDF 가상 프린터를 사용하여 강력한 화면 캡처 방지 및 재암호화를 완벽히 우회합니다. Word는 가장 확실하지만 레이아웃이 변형될 수 있습니다."
            )
            
            selected_visible = st.checkbox(
                "백그라운드 숨김 모드 해제 (디버깅 모드)", 
                value=st.session_state.drm_visible,
                help="체크하면 워드나 아크로뱃 창이 화면에 직접 보입니다. 엔진 가동 중 멈출 때 어떤 오류창(DRM 로그인 창 등)이 뜨는지 눈으로 확인할 수 있습니다."
            )
            
            st.subheader("2. 핫폴더(Hot Folder) 모니터링 경로")
            st.caption("자동 검증 대상이 모이는 드라이브 경로를 설정합니다.")
            selected_path = st.text_input("핫폴더 경로", value=st.session_state.hot_folder_path)
            
            if st.button("설정 저장"):
                st.session_state.drm_strategy = selected_strategy
                st.session_state.drm_visible = selected_visible
                st.session_state.hot_folder_path = selected_path
                st.toast('설정이 성공적으로 저장되었습니다.', icon='💾')
                st.success("새로운 환경설정이 적용되었습니다. DRM 탭으로 이동하여 테스트해보세요!")

if __name__ == "__main__":
    main()
