import pandas as pd
import re# Regular Expression（正規表示式/正則表達式）
import jieba
import os
from sqlalchemy import create_engine
from transformers import pipeline# Hugging Face Transformers的pipeline API, 可以輕鬆使用預訓練模型進行情緒分析
from dotenv import load_dotenv

# 安全加載環境變數
# 自動讀取同目錄底下的.env檔案, 並把設定暫存到系統記憶體中
load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# 從PostgreSQL撈取資料(使用Pandas)
print("正在從PostgreSQL讀取數據...")
db_url = f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(db_url)

from datetime import datetime, timedelta
from sqlalchemy import inspect# 確認DB元數據MetaData

# 產生過去7天的後綴(包含今天)
today = datetime.now()
past_7_days = [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(7)]
target_tables = [f"ptt_stock_articles{date_suffix}" for date_suffix in past_7_days]

# 線上檢查資料庫, 過濾掉「不存在」的資料表（防呆, 避免假日沒爬資料噴錯）
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
valid_tables = [table for table in target_tables if table in existing_tables]

if not valid_tables:
    print("過去7天的動態資料表皆不存在於資料庫中, 請確認爬蟲是否有正常運作")
    exit()

# 組裝UNION ALL SQL語法
sql_queries = [f"SELECT * FROM {table}" for table in valid_tables]
combined_query = " UNION ALL ".join(sql_queries)

print(f"準備讀取的資料表有: {', '.join(valid_tables)}")

# 透過Pandas執行合併查詢
df = pd.read_sql(combined_query, engine)

# df = pd.read_sql('SELECT * FROM ptt_stock_articles', engine)

if df.empty:
    print("資料庫裡面沒有資料, 請先跑爬蟲")
    exit()

print(f"成功載入{len(df)}筆文章")

# 資料清洗(Data Cleaning)函數
# def clean_text(text):
#     if not text:
#         return ""
#     # 移除PTT系統罐頭文字(發信站、文章網址)
#     text = re.sub(r'※ 發信站:.*|※ 文章網址:.*|※ 編輯:.*', '', text)
#     # 移除引言回信(以>開頭的行)
#     text = re.sub(r'(^|\n)>.*', '', text)
#     # 移除網址URL
#     text = re.sub(r'https?://\S+|www\.\S+', '', text)
#     # 只保留中文字、英文字母與數字, 去除奇怪的BBS符號碼
#     text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
#     return text.strip()

# print("開始進行資料清洗...")
# df['clean_content'] = df['content'].apply(clean_text)

# 資料清洗(Data Cleaning)函數
def clean_ptt_content(text):
    if not text:
        return ""
    
    # 智能簽名檔辨識與切除
    lines = text.split('\n')
    split_index = None
    
    # 倒著看回來（由下往上搜尋分隔線）, 通常簽名檔分隔線只會出現在最後幾行
    # 設定只在文章「最後 15 行」內搜尋標準簽名檔特徵
    search_range = max(0, len(lines) - 15)
    
    for i in range(len(lines) - 1, search_range, -1):
        current_line = lines[i].strip()
        # 嚴格匹配PTT的標準簽名檔分隔線符號
        if current_line == '--' or current_line.startswith('-- '):
            # 檢查這個分隔線下方是否真的有其他文字（確認不是正文的結尾裝飾）
            remaining_text = "".join(lines[i+1:]).strip()
            if remaining_text: 
                split_index = i
                break# 找到了最上面的那條簽名檔分隔線, 停止搜尋
                
    # 如果符合嚴格特徵, 才進行局部切除
    if split_index is not None:
        text = "\n".join(lines[:split_index])
        
    # 移除PTT系統罐頭文字(發信站、文章網址)
    text = re.sub(r'※ 發信站:.*|※ 文章網址:.*|※ 編輯:.*', '', text)
    # 移除引言回信(以>開頭的行)
    text = re.sub(r'(^|\n)>.*', '', text)
    # 移除網址URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # 只保留中文字、英文字母與數字, 去除奇怪的BBS符號碼
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', text)
    return text.strip()

print("開始進行資料清洗...")
df['clean_content'] = df['content'].apply(clean_ptt_content)

# 斷詞與關鍵字萃取(Jieba)
print("載入台灣股市自定義詞庫...")
jieba.load_userdict('mydict.txt')

def segment_text(text):
    # 這裡順便過濾掉長度小於2的單字（如:的、了、在等停用詞）
    words = jieba.cut(text)
    return [w for w in words if len(w) >= 2 and not w.isspace()]

df['tokens'] = df['clean_content'].apply(segment_text)

# Hugging Face BERT情緒分析(Sentiment Analysis)
print("正在載入Hugging Face BERT繁體中文情緒模型(第一次載入需要下載, 請稍候)...")
# 使用適合中文情緒二分類的模型
classifier = pipeline('sentiment-analysis', model='IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment')

# 信心分數（Score）通常介於0.0到1.0之間
def get_bert_sentiment(text):
    if not text:
        return "NEUTRAL", 0.5
    try:
        # BERT有長度限制（通常最大512字）, 擷取前300個字做代表即可
        truncated_text = text[:300]
        result = classifier(truncated_text)[0]
        # classifier(truncated_text)回傳結果通常是個列表, 裡面包含一個字典, 格式如下：
        # [
        #     {'label': 'POSITIVE', 'score': 0.9876}
        # ]
        # 回傳標籤(例如'POSITIVE'或'NEGATIVE')與信心分數
        return result['label'], result['score']
    except Exception as e:
        return "ERROR", 0.0

print("開始實作AI情緒分析...")
# 為了方便儲存, 把結果拆成標籤與分數兩欄
df['sentiment_results'] = df['clean_content'].apply(get_bert_sentiment)
df['sentiment_label'] = df['sentiment_results'].apply(lambda x: x[0])
df['sentiment_score'] = df['sentiment_results'].apply(lambda x: x[1])

# 刪除暫存的欄位
df = df.drop(columns=['sentiment_results'])

# 將分析結果寫回資料庫, 或存成CSV
print("\n--- 分析完成範例 ---")
print(df[['title', 'sentiment_label', 'sentiment_score']].head())# head(): 只顯示最前面的5筆

# 儲存成CSV做為後續資料視覺化(第三階段)的輸入源
df.to_csv('ptt_stock_analyzed.csv', index=False, encoding='utf-8-sig')
print("\n分析結果已成功儲存至ptt_stock_analyzed.csv檔案中")