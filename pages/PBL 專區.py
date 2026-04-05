import streamlit as st
import google.generativeai as genai
import json
import os
import glob
import time

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="PBL 練習專區", page_icon="🤝", layout="wide")

# 隱藏預設選單
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# 檢查 API Key
if "gemini_api_key" not in st.session_state or not st.session_state["gemini_api_key"]:
    st.warning("⚠️ 尚未偵測到 API Key！請先回到 **首頁 (app.py)** 完成設定。")
    st.stop()

genai.configure(api_key=st.session_state["gemini_api_key"])
selected_model = st.session_state.get("gemini_model", "gemini-1.5-flash")
model = genai.GenerativeModel(selected_model)

# --- 2. 讀取陽明交大模擬題庫 ---
@st.cache_data
def load_nycu_cases():
    cases = []
    folder_path = "data_pbl"
    if not os.path.exists(folder_path):
        return cases
    for file_path in glob.glob(os.path.join(folder_path, "*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                cases.append(json.load(f))
        except Exception:
            pass
    return cases

cases = load_nycu_cases()

# --- 3. 側邊欄：角色選擇與規則說明 ---
with st.sidebar:
    st.header("🎭 考場角色設定")
    user_role = st.radio(
        "選擇你今天要練習的身分：",
        ["👨‍🏫 引言者 (Moderator)", "🧑‍🎓 一般組員 (Member)", "📝 結論者 (Concluder)"],
        help="不同角色在陽明交大賽制中有完全不同的權責。"
    )
    
    st.divider()
    st.markdown("### 🔔 考場鈴聲提醒")
    st.caption("一短聲：思考開始/結束")
    st.caption("一短聲：自由討論結束")
    st.caption("兩短聲：該題討論結束")
    
    if st.button("⏱️ 開始 1 分鐘思考計時"):
        with st.empty():
            for i in range(60, 0, -1):
                st.metric("思考剩餘時間", f"{i}s")
                time.sleep(1)
            st.success("🔔 第一次響鈴：思考時間結束！")

# --- 4. 主頁面 UI ---
st.title("🤝 PBL 練習專區")
st.caption(f"🧠 目前 AI 評分模型：`{selected_model}`")

if not cases:
    st.error("❌ 找不到題庫！請先執行 `generate_pbl_data.py`。")
    st.stop()

# 選擇教案
case_titles = [c.get("title", "Unknown") for c in cases]
selected_title = st.selectbox("📂 選擇練習題目：", case_titles)
current_case = next(c for c in cases if c.get("title") == selected_title)

st.divider()

# 顯示考卷內容
st.subheader("📜 考場題目 (請大聲朗讀)")
with st.container(border=True):
    st.markdown(f"### {current_case.get('title')}")
    st.write(current_case.get("exam_paper_text"))
    st.caption("⚠️ 擔任引言者需負責朗誦此段題目。")

# --- 5. 根據角色顯示不同練習區 ---
col_input, col_feedback = st.columns([1, 1])

with col_input:
    if "引言者" in user_role:
        st.subheader("🏁 引言者任務")
        st.markdown("""
        * **任務 1**：發表 1.5 分鐘引言。
        * **任務 2**：處理考場突發狀況 (程序控管)。
        * **注意**：不參與後續小組討論。
        """)
        
        intro_text = st.text_area("請輸入你的 1.5 分鐘引言講稿：", height=150)
        
        st.warning(f"🔥 **考場突發狀況：**\n{current_case.get('moderator_twist')}")
        twist_response = st.text_area("身為引言者，你會如何用台詞化解此狀況？", height=100)
        
        submit_btn = st.button("提交引言者評分")

    elif "一般組員" in user_role:
        st.subheader("🗣️ 一般組員任務")
        st.markdown("""
        * **任務 1**：發表 1.5 分鐘演說。
        * **任務 2**：參與自由討論與意見交流。
        """)
        
        member_speech = st.text_area("請輸入你的 1.5 分鐘個人演說講稿：", height=200)
        member_discussion = st.text_area("自由討論區：針對核心衝突點提出你的觀點或回應他人意見：", height=150)
        
        submit_btn = st.button("提交組員表現評分")

    elif "結論者" in user_role:
        st.subheader("📝 結論者任務")
        st.markdown("""
        * **任務**：在討論結束後進行 2 分鐘總結。
        * **注意**：不參與中間的小組討論。
        """)
        
        st.error(f"🚨 **討論現況 (由 AI 模擬)：**\n{current_case.get('concluder_twist')}")
        conclusion_text = st.text_area("請根據上述現況，輸入你的 2 分鐘總結講稿：", height=250)
        
        submit_btn = st.button("提交結論者評分")

# --- 6. AI 評分邏輯 (根據 8 大核心能力) ---
if submit_btn:
    with col_feedback:
        with st.spinner("🧑‍🏫 正在根據 8 大核心能力進行綜合評估..."):
            # 建立評分 Prompt
            role_context = f"考生選擇的角色是：{user_role}"
            user_inputs = ""
            if "引言者" in user_role:
                user_inputs = f"引言內容：{intro_text}\n突發狀況應對：{twist_response}"
            elif "一般組員" in user_role:
                user_inputs = f"演說內容：{member_speech}\n自由討論表現：{member_discussion}"
            else:
                user_inputs = f"總結內容：{conclusion_text}"

            prompt = f"""
            你是一位台灣醫學系（如陽明交大）小組討論面試官。
            請根據以下 8 大核心素養為考生的表現進行評分與建議：
            1. 倫理議題 (Ethics)
            2. 專業素養/同理心 (Professionalism/Empathy)
            3. 溝通技巧 (Communication Skills)
            4. 團隊合作 (Teamwork)
            5. 批判性思考/問題解決 (Critical Thinking/Problem Solving)
            6. 健康政策/社會責任 (Health Policy/Social Responsibility)
            7. 醫學知識應用 (Application of Medical Knowledge)
            8. 壓力處理/情境應變 (Stress Management/Scenario Response)

            【考題內容】：{current_case.get('exam_paper_text')}
            【{role_context}】
            【考生作答內容】：
            {user_inputs}

            請輸出：
            ### 🎯 綜合表現等第：[A/B/C]
            ### 📊 核心能力評析 (針對 8 項能力中有展現出的部分進行短評)
            ### 💡 針對該角色的具體優化建議
            """
            
            try:
                response = model.generate_content(prompt)
                st.subheader("📋 教授詳細評分報告")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"API 連線失敗：{e}")