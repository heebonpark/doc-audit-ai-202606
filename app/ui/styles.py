import streamlit as st

def inject_premium_css():
    """
    Injects the custom Data Intel PRO Premium UI CSS into the Streamlit app.
    Features: Pretendard font, Dark Navy/Royal Blue palette, Glassmorphism, 
    and hides the default Streamlit header/footer.
    """
    st.markdown(
        """
        <style>
        /* Import Pretendard Font */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

        /* Global Font and Background */
        html, body, [class*="css"] {
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
            background-color: #0f172a; /* Dark Navy Background */
            color: #f8fafc; /* Light text */
        }

        /* Hide Streamlit Defaults */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}

        /* Premium Headers */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #ffffff;
        }

        h1 {
            background: linear-gradient(90deg, #60a5fa, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
        }

        /* Glassmorphism Cards for Containers */
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
            background: rgba(30, 41, 59, 0.7); /* Slate 800 with opacity */
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.6);
        }

        /* Primary Button Styling */
        div.stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 10px 24px;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
            width: 100%;
        }

        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            color: white;
            border: none;
        }

        div.stButton > button:active {
            transform: translateY(1px);
        }

        /* File Uploader Customization */
        div[data-testid="stFileUploader"] {
            background-color: rgba(30, 41, 59, 0.5);
            border: 2px dashed #475569;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }

        div[data-testid="stFileUploader"]:hover {
            border-color: #3b82f6;
            background-color: rgba(30, 41, 59, 0.8);
        }

        /* Metrics / Status Indicators */
        div[data-testid="stMetricValue"] {
            font-size: 32px;
            font-weight: 800;
        }

        /* Custom Status Badge Classes (Applied via HTML markdown) */
        .status-green {
            background-color: rgba(34, 197, 94, 0.2);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.5);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }
        
        .status-yellow {
            background-color: rgba(234, 179, 8, 0.2);
            color: #facc15;
            border: 1px solid rgba(234, 179, 8, 0.5);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }

        .status-red {
            background-color: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.5);
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }

        /* Dataframes & Tables */
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #334155;
        }

        /* Expander */
        .streamlit-expanderHeader {
            background-color: rgba(30, 41, 59, 0.8);
            border-radius: 12px;
            color: #e2e8f0;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
