import feedparser
import json
import os
import re  # 新增：用來處理正規表達式，過濾檔名特殊字元
import google.generativeai as genai

# ==========================================
# 1. 設定你的 Gemini API Key
# ==========================================

# 統一設定資料夾名稱
# 統一設定資料夾名稱
OUTPUT_DIR = "data_english"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(title):
    """
    過濾標題中不能作為檔名的特殊字元 (Windows/Mac/Linux 通用)
    """
    # 移除 \ / * ? : " < > | 等字元
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
    return safe_title.strip()

def fetch_and_process_articles(API,model_name,number):
    API_KEY = API # 請記得換成新的 Key！
    genai.configure(api_key=API_KEY)
# 這裡使用 2.5-flash，速度與效能極佳
    model = genai.GenerativeModel(model_name)
    # 改用紐約時報 (NYT) 健康版的 RSS，穩定且不擋爬蟲
    feed_url = "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml"
    
    print(f"🔄 正在從 {feed_url} 抓取最新醫學文章...")
    
    # 加上一個假的 User-Agent，讓網站以為我們是正常的瀏覽器
    feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    feed = feedparser.parse(feed_url)
    
    # --- 防呆：檢查是否真的有抓到文章 ---
    if len(feed.entries) == 0:
        print("⚠️ 警告：無法從該 RSS 取得任何文章，請檢查網路連線或更換 feed_url。")
        return
    else:
        print(f"📡 成功抓取到 {len(feed.entries)} 篇文章！開始檢查並交給 AI 分析...")
        
    success_count = 0
    skip_count = 0
    
    # 只抓取最新的 5 篇文章來生成題庫
    for entry in feed.entries[:number]:
        title = entry.title
        link = entry.link
        summary = entry.summary if 'summary' in entry else entry.title
        
        # 1. 預先產生安全的檔名與路徑
        safe_title = sanitize_filename(title)
        file_path = os.path.join(OUTPUT_DIR, f"{safe_title}.json")
        
        # 2. 🔥 新增：檢查檔案是否已經存在 🔥
        if os.path.exists(file_path):
            print(f"⏩ 已存在，跳過處理: {safe_title}.json")
            skip_count += 1
            continue # 直接跳到下一篇文章，不呼叫 API
        
        print(f"⏳ 處理中: {title}")
        
        prompt = f"""
        你是一位醫學系英文面試官。請閱讀以下醫學新聞的標題與摘要，並將其轉化為一道「英文面試題」。
        
        新聞標題: {title}
        新聞摘要: {summary}
        
        請以 JSON 格式輸出，必須包含以下三個 key:
        1. "background": 根據內容轉譯成一篇英文閱讀長文。
        2. "question": 提出一個具備批判性思考的英文面試問題 (例如詢問倫理困境、對未來醫療的影響、或個人看法)。
        3. "vocabulary": 列出 3 個這篇文章中重要的進階醫學/科學英文單字 (包含中文翻譯)。
        
        不要輸出任何 markdown 標記 (如 ```json)，直接輸出乾淨的 JSON 字串。
        """
        
        try:
            response = model.generate_content(prompt)
            # 使用 .strip() 預防 AI 輸出前後多餘的空白或反引號
            cleaned_response = response.text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:-3].strip()
                
            ai_data = json.loads(cleaned_response)
            
            ai_data["title"] = title
            ai_data["link"] = link
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(ai_data, f, ensure_ascii=False, indent=4)
                
            print(f"✅ 已存檔: {file_path}")
            success_count += 1
            
        except Exception as e:
            # 如果 Gemini 解析失敗，把錯誤印出來讓我們好除錯
            print(f"❌ 處理失敗 ({title}): \n原因：{e}")
            
    print(f"\n🎉 執行完畢！共成功生成 {success_count} 篇新題庫，跳過 {skip_count} 篇既有題庫。")

if __name__ == "__main__":
    fetch_and_process_articles()