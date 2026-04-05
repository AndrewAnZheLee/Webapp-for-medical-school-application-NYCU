import streamlit as st
import google.generativeai as genai
from generate_pbl import generate_pbl_cases
from generate_english_data import fetch_and_process_articles
import os
# --- 1. 頁面基本設定 (升級為 wide 寬版配置，看起來更專業) ---
st.set_page_config(
    page_title="醫學系面試 AI 訓練營",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 隱藏預設的 Streamlit 選單和 Footer 讓畫面更乾淨 ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
#st.markdown(hide_st_style, unsafe_allow_html=True)
def count_english_json():
    folder_path = "data_english"
    if os.path.exists(folder_path):
        # 列出所有檔案，並篩選出以 .json 結尾的
        files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        return len(files)
    return 0

# 在 Streamlit 中顯示
count = count_english_json()
# --- 2. 側邊欄：系統設定與 API Key 管理 ---
with st.sidebar:
    st.header("⚙️ 系統核心設定")
    st.markdown("請先在此輸入您的 Gemini API Key 來啟動 AI 考官。")
    
    # API Key 輸入框
    api_key = st.text_input("🔑 Gemini API Key:", type="password", placeholder="AIzaSy...")
    
    if api_key:
        st.session_state["gemini_api_key"] = api_key
        genai.configure(api_key=api_key)
        
        # 動態抓取模型
        try:
            with st.spinner("🔄 連線中..."):
                available_models = [
                    m.name.replace("models/", "") 
                    for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods
                ]
                
                if available_models:
                    # 預設尋找 flash 模型
                    default_index = next((i for i, name in enumerate(available_models) if "flash" in name.lower()), 0)
                    
                    model_choice = st.selectbox(
                        "🧠 選擇 AI 考官大腦:",
                        available_models,
                        index=default_index,
                        help="Flash 反應快，Pro 邏輯推演更深。"
                    )
                    st.session_state["gemini_model"] = model_choice
                    st.success("✅ 系統已就緒！")
                    # 🔥 新增：題庫後台管理功能 🔥
                    st.divider()
                    st.subheader("🛠️ 題庫後台管理")
                    if st.button("🚀 執行 PBL 題庫生成"):
                        with st.spinner("正在生成新題庫..."):
                            generate_pbl_cases(api_key, model_choice)
                            st.success("✅ 題庫擴充完成！")
                            st.cache_data.clear() # 強制網頁重新讀取檔案
                     # 🔥 新增：題庫後台管理功能 🔥
                    
                    num_to_gen = st.number_input("總共要抓幾題英文？", value=count)
                    if st.button("🚀 執行英文題庫生成"):
                        with st.spinner("正在生成新題庫..."):
                            fetch_and_process_articles(api_key, model_choice,num_to_gen)
                            st.success("✅ 題庫擴充完成！")
                            st.cache_data.clear() # 強制網頁重新讀取檔案
        except Exception as e:
            st.error("❌ API Key 無效或連線失敗，請檢查設定。")
    else:
        st.warning("⚠️ 等待輸入 API Key...")
        
    st.markdown("---")
    st.markdown("[👉 點此免費獲取 Gemini API Key](https://aistudio.google.com/app/apikey)")
    st.caption("🔒 您的 API Key 僅會暫存於本次瀏覽器對話中，重整後即會清除，請安心使用。")

# --- 3. 主頁面：視覺化儀表板 ---
st.title("🩺 醫學系面試 AI 訓練營 (Pro Version)")
st.markdown("### 打造你的專屬面試教練，隨時隨地展開高強度模擬面試。")

st.divider() # 分隔線

# --- 4. 使用 columns 排版，讓 4 個專區變成網格狀 (Grid) 的卡片設計 ---
st.markdown("#### 🎯 核心訓練模組總覽")
col1, col2 = st.columns(2)

with col1:
    st.info("""
    #### 👤 個人面試專區
    **【核心目標】深挖個人特質、報考動機與抗壓性**
    
    上傳你的自傳或備審資料片段，AI 教授將針對細節進行「靈魂拷問」，找出邏輯漏洞並測試你的臨場反應。
    """)
    
    st.success("""
    #### 🤝 PBL 討論專區
    **【核心目標】團隊合作、議題分析與領導力**
    
    模擬 Problem-Based Learning 流程。包含社會議題成因分析、解法提案，並為你提供「引言人 (Moderator)」的控場策略與突發狀況應對。
    """)

with col2:
    st.warning("""
    #### 🗣️ 英文面試專區
    **【核心目標】醫學文獻閱讀與英文邏輯表達**
    
    閱讀前沿醫療科普文章或倫理案例，用英文回答教授的提問。AI 將針對你的文法、詞彙與論述邏輯給予專業評分。
    """)
    
    st.error("""
    #### 📊 MMI 微型面試專區
    **【核心目標】圖表判讀、倫理兩難與綜合評估**
    
    挑戰多站式面試 (Multiple Mini Interview)！包含流行病學圖表分析、急診室倫理困境模擬，並提供高分答題架構解析。
    """)

st.divider()

# --- 5. 使用指引 ---
st.markdown("### 🚀 如何開始？")
st.markdown("""
1. 確保您已經在 **左側面板** 貼上您的 Gemini API Key。
2. 等待系統顯示「✅ 系統已就緒」。
3. 從網頁左側的 **Pages 導覽列** 點選您想練習的專區（例如 `1_個人面試專區`）。
4. 開始與您的專屬 AI 教授對話！
""")