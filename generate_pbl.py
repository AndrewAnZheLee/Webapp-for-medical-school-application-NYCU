import json
import os
import re
import google.generativeai as genai

# ==========================================
# 1. 設定你的 Gemini API Key
# ==========================================

OUTPUT_DIR = "data_pbl"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()

# 設定每個核心素養要「新增」幾題
QUESTIONS_PER_COMPETENCY = 1

def get_next_global_idx():
    """
    掃描資料夾，找出目前最大的編號並回傳下一個編號
    """
    files = os.listdir(OUTPUT_DIR)
    max_idx = 0
    for f in files:
        # 使用正規表達式搜尋檔名開頭的數字 (例如 001)
        match = re.match(r'^(\d{3})_', f)
        if match:
            idx = int(match.group(1))
            if idx > max_idx:
                max_idx = idx
    return max_idx + 1
def get_existing_contexts():
    existing_info = []
    if not os.path.exists(OUTPUT_DIR):
        return ""
    
    files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json')]
    for f in files:
        try:
            with open(os.path.join(OUTPUT_DIR, f), "r", encoding="utf-8") as file:
                data = json.load(file)
                # 記錄標題與核心衝突，讓 AI 避開
                existing_info.append(f"- 標題：{data.get('title')} (核心衝突：{data.get('core_conflict')})")
        except:
            continue
    
    if not existing_info:
        return "目前尚無既有題目。"
    return "\n".join(existing_info)
def generate_pbl_cases(API,model_name):
    API_KEY = API # ⚠️ 請記得換成你的新 Key！
    genai.configure(api_key=API_KEY.strip())
    model = genai.GenerativeModel(model_name)
    seed_competencies = [
        "倫理議題 (Ethics)",
        "專業素養與同理心 (Professionalism and Empathy)",
        "溝通技巧 (Communication Skills)",
        "團隊合作 (Teamwork)",
        "批判性思考與問題解決 (Critical Thinking and Problem Solving)",
        "健康政策與社會責任 (Health Policy and Social Responsibility)",
        "醫學知識應用 (Application of Medical Knowledge)",
        "壓力處理與情境應變 (Stress Management and Scenario Response)"
    ]
    
    # 🔥 取得起始編號
    current_idx = get_next_global_idx()
    
    print(f"📂 目前資料夾內最大編號為: {current_idx - 1}")
    print(f"🔄 將從 {current_idx:03d} 開始生成...")

    for competency in seed_competencies:
        comp_short = competency.split(" (")[0]
        past_cases = get_existing_contexts()
        for i in range(QUESTIONS_PER_COMPETENCY):
            print(f"⏳ 正在生成第 {current_idx:03d} 題：【{comp_short}】...")
            
            prompt = f"""
            你是一位台灣頂尖醫學系（如陽明交大）的小組討論面試出題委員。
            請以「{competency}」作為【最主要測試目標】，設計一個全新的考題。注意，不一定要與醫學有直接關係。
            
            陽明交大賽制：引言者(朗讀題目、控場)、一般組員(討論)、結論者(總結)。
            ⚠️【重要限制：避免重複】⚠️
            以下是目前資料夾中已經存在的題目清單，請絕對不要重複類似的情境或衝突點：
            {past_cases}
            
            請以 JSON 格式輸出：
            1. "title": 考題標題。
            2. "exam_paper_text": 考場發下的題目原文（含引言者需朗讀的段落與討論任務）。
            3. "core_conflict": 核心衝突點。
            4. "stakeholders": 利害關係人立場 (Array)。
            5. "moderator_twist": 給引言者的突發狀況。
            6. "concluder_twist": 給結論者的挑戰。
            7. "target_competency": "{comp_short}"。
            
            不要輸出 markdown 標記，直接輸出 JSON。
            """
            
            try:
                response = model.generate_content(prompt)
                cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
                ai_data = json.loads(cleaned_response)
                
                case_title = sanitize_filename(ai_data.get("title", "Topic"))
                filename = f"{current_idx:03d}_{comp_short}_{case_title}.json"
                file_path = os.path.join(OUTPUT_DIR, filename)
                
                ai_data["id"] = current_idx
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(ai_data, f, ensure_ascii=False, indent=4)
                
                print(f"✅ 已存檔: {filename}")
                current_idx += 1 # 流水號遞增
                
            except Exception as e:
                print(f"❌ 生成失敗: {e}")

    print(f"\n🎉 任務完成！目前的總題數已擴充。")

if __name__ == "__main__":
    generate_pbl_cases()