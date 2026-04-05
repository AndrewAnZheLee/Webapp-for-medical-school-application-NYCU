import streamlit as st
import google.generativeai as genai

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="個人面試專區 | 醫學系面試 AI", page_icon="👤", layout="wide")

# 隱藏預設選單讓畫面保持乾淨
hide_st_style = """<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. 系統狀態檢查 (防呆機制) ---
# 確保使用者有先在首頁輸入 API Key，否則阻擋執行
if "gemini_api_key" not in st.session_state or not st.session_state["gemini_api_key"]:
    st.warning("⚠️ 尚未偵測到 API Key！請先回到 **首頁 (app.py)** 的左側欄位完成設定。")
    st.stop()

# --- 3. 初始化 AI 模型 ---
genai.configure(api_key=st.session_state["gemini_api_key"])

# 讀取使用者在首頁選擇的模型，若無則預設為 flash
selected_model = st.session_state.get("gemini_model", "gemini-1.5-flash")
model = genai.GenerativeModel(selected_model)

def ask_professor(prompt):
    """呼叫 Gemini API 的輔助函數"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 教授的大腦暫時連線失敗，請檢查 API Key 或網路狀態：\n{e}"

# --- 4. 頁面 UI 與互動設計 ---
st.title("👤 個人面試專區")
st.caption(f"🧠 目前負責面試的 AI 考官模型：`{selected_model}`")

st.markdown("""
醫學系教授在看備審資料時，最喜歡針對**「動機的真實性」**與**「遇到挫折的反應」**進行深挖。
請在下方貼上你的一段備審資料或自我介紹，讓 AI 教授對你進行壓力測試。
""")

st.divider()

# 使用 columns 讓版面更有條理
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📄 你的自我介紹")
    bg_info = st.text_area(
        "請貼上片段 (建議 300-500 字)：", 
        height=300, 
        placeholder="例如：我從小看著爺爺深受慢性病折磨，因此立志成為一名家醫科醫師...\n(或者貼上你的社團幹部經驗、科展經歷)"
    )
    
    submit_btn = st.button("🎯 送出資料，請教授提問", use_container_width=True)

with col2:
    st.subheader("👨‍⚕️ 教授的靈魂拷問")
    
    if submit_btn:
        if not bg_info.strip():
            st.error("請先在左側輸入你的備審資料喔！")
        else:
            with st.spinner("教授正在眉頭深鎖地閱讀你的資料..."):
                # --- 🔥 進階版 Prompt：同時生成提問與心法 ---
                system_prompt = f"""
                你現在要完成兩項任務。
                
                【第一部分：教授提問】
                扮演台灣頂尖醫學系的資深面試教授，風格嚴厲、講求實證邏輯。
                閱讀以下考生資料後，給出：
                1. 一句犀利的開場白。
                2. 針對內容提出 2 個具深度的追問，帶有壓力測試的意味。
                
                【第二部分：專屬答題心法】
                跳脫教授角色，改以「面試教練」的視角，針對你剛剛提的問題，給予該考生 3 點具體且客製化的「答題心法」或「攻防建議」。告訴他該如何化解這個壓力題。
                
                ⚠️ 輸出格式要求：請務必用 ===TIPS=== 這個字串將兩部分隔開。
                例如：
                (教授的提問內容)
                ===TIPS===
                (教練的答題心法)
                
                【考生資料開始】
                {bg_info}
                【考生資料結束】
                """
                
                raw_feedback = ask_professor(system_prompt)
                
                # --- 解析 AI 的回覆 ---
                # 用我們自訂的分隔符號把字串切成兩半
                if "===TIPS===" in raw_feedback:
                    questions, tips = raw_feedback.split("===TIPS===")
                else:
                    # 防呆機制：萬一 AI 沒有乖乖輸出分隔線
                    questions = raw_feedback
                    tips = "教練暫時想不到完美的破解法，請保持冷靜、誠實作答！"
                
                # --- 顯示 UI ---
                st.info("教授推了一下眼鏡，看著你說：")
                st.markdown(questions.strip()) # strip() 用來清除前後多餘的空白或換行
                
                st.markdown("---")
                
                # 將動態生成的專屬心法放入摺疊面板中
                with st.expander("💡 專屬答題心法提示 (作答前請先想想)"):
                    st.markdown(tips.strip())
    else:
        st.write("等待考生提交資料中...")