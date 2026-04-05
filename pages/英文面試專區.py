import streamlit as st
import google.generativeai as genai
import json
import os
import glob

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="英文面試專區 | 醫學系面試 AI", page_icon="🗣️", layout="wide")

# 隱藏預設選單
hide_st_style = """<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. 系統狀態檢查 (防呆機制) ---
if "gemini_api_key" not in st.session_state or not st.session_state["gemini_api_key"]:
    st.warning("⚠️ 尚未偵測到 API Key！請先回到 **首頁 (app.py)** 的左側欄位完成設定。")
    st.stop()

# 初始化 AI 模型
genai.configure(api_key=st.session_state["gemini_api_key"])
selected_model = st.session_state.get("gemini_model", "gemini-1.5-flash")
model = genai.GenerativeModel(selected_model)

# --- 3. 讀取獨立的 JSON 題庫檔案 ---
@st.cache_data
def load_english_topics():
    topics = []
    folder_path = "data_english"
    
    # 檢查資料夾是否存在
    if not os.path.exists(folder_path):
        return topics
        
    # 抓取資料夾內所有的 .json 檔案
    for file_path in glob.glob(os.path.join(folder_path, "*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                topics.append(data)
        except Exception as e:
            st.toast(f"讀取檔案失敗: {file_path}")
            
    return topics

topics = load_english_topics()

# --- 4. 頁面 UI 與互動設計 ---
st.title("🗣️ 英文面試專區 (Medical English Interview)")
st.caption(f"🧠 目前負責評分的 AI 考官模型：`{selected_model}`")

if not topics:
    st.error("❌ 找不到題庫資料！請先在終端機執行 `python generate_english_data.py` 來抓取最新醫學新聞。")
    st.stop()

st.markdown("""
醫學系的英文面試通常會要求你閱讀一段最新的醫學文獻或新聞，並測試你的**閱讀理解、批判性思考與英文口語/寫作表達能力**。
請從下方選擇一篇本週最新的醫學時事，並用英文回答教授的問題。
""")

st.divider()

# 讓使用者選擇一篇文章 (提取標題作為選單選項)
topic_titles = [t.get("title", "Unknown Title") for t in topics]
selected_title = st.selectbox("📰 選擇本週熱門醫學時事：", topic_titles)

# 抓出選定的文章資料
current_topic = next(t for t in topics if t.get("title") == selected_title)

# --- 5. 左右分欄：左邊題目，右邊作答 ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📝 Article Background")
    # 顯示背景知識
    st.info(current_topic.get("background", "No background provided."))
    
    # 提供原文連結
    link = current_topic.get("link", "#")
    st.markdown(f"[🔗 Read Full Source Article on NYT Health]({link})")
    
    # 將單字表隱藏在摺疊面板中，避免畫面太雜亂
    with st.expander("📚 Key Vocabulary (點擊展開字彙表)"):
        vocab_list = current_topic.get("vocabulary", [])
        
        if isinstance(vocab_list, list) and len(vocab_list) > 0:
            # 方式 A：使用漂亮的 Markdown 列表顯示
            for item in vocab_list:
                word = item.get("word", "N/A")
                translation = item.get("translation", "N/A")
                st.markdown(f"**{word}** : {translation}")
                
            # 或者 方式 B：如果你想要呈現像表格一樣整齊，可以使用 st.table
            # st.table(vocab_list) 
        else:
            st.write("No vocabulary provided.")
            
    st.subheader("❓ Interview Question")
    # 把問題用醒目的紅色框標示
    st.error(f"**{current_topic.get('question', 'No question provided.')}**")

with col2:
    st.subheader("🎤 Your Response")
    st.write("請以英文回答左側的問題 (Please respond in English)：")
    
    user_answer = st.text_area(
        "Type your answer here...", 
        height=250,
        placeholder="Well, from my perspective, this new development in medical technology implies that..."
    )
    
    submit_btn = st.button("💯 Submit for Grading (送出評分)", use_container_width=True)
    
    if submit_btn:
        if len(user_answer.strip()) < 30:
            st.warning("⚠️ Your answer is too short. Please elaborate more to get a proper evaluation.")
        else:
            with st.spinner("🧑‍🏫 Professor is evaluating your response..."):
                # --- AI 評分 Prompt ---
                grading_prompt = f"""
                You are a strict but fair Native English medical professor conducting an interview for a top medical school in Taiwan.
                
                Article Title: {current_topic.get('title')}
                Question asked: {current_topic.get('question')}
                Student's answer: {user_answer}
                
                Please evaluate the student's answer and provide feedback. 
                Your feedback MUST be entirely in Traditional Chinese (繁體中文), EXCEPT for English medical terms or specific grammar corrections.
                
                Please structure your response exactly as follows (use Markdown):
                
                ### 🎯 整體評分: [給予 1 到 10 的分數]/10
                
                ### 📝 文法與詞彙 (Grammar & Vocabulary)
                (指出文法錯誤，並建議可以替換的「更專業的高階醫學單字」)
                
                ### 🧠 邏輯結構與醫學洞察 (Logical Structure & Insight)
                (評估他們的論點是否合理？是否有展現同理心或批判性思考？邏輯上有沒有漏洞？)
                
                ### ✨ 高分範例回答 (Example Answer)
                (提供一段約 100 字的 Native Speaker 高分示範回答，全英文)
                """
                
                try:
                    response = model.generate_content(grading_prompt)
                    st.success("✅ Evaluation Complete!")
                    
                    # 將評分結果包在一個漂亮的框裡面
                    with st.container(border=True):
                        st.markdown(response.text)
                        
                except Exception as e:
                    st.error(f"❌ API 連線錯誤：{e}")