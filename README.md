# PTT股版輿情監測與AI情緒分析系統

本專案是一個全棧式的大數據輿情分析平台。系統能自動採集PTT Stock版的即時文章，串接關聯式資料庫進行落庫儲存，並整合資料清洗管道、Jieba中文斷詞以及Hugging Face BERT深度學習模型，最終透過Streamlit打造出互動式的財經輿情儀表板。

---

## 核心功能

1. **自動化數據採集(Scrapy)**：定時高效爬取PTT股版文章（包含標題、作者、時間、內文與推文數），具備連線池管理。
2. **安全數據落庫(PostgreSQL + SQLAlchemy)**：利用環境變數隔離機密資訊，透過ORM架構與資料庫對話，防止SQL注入。
3. **動態資料清洗管道(Regex + StopWords)**：精準剃除BBS顏色碼、網址及系統罐頭文字，整合自定義停用詞清單（`stopwords.txt`）過濾文本雜訊。
4. **台灣股市專用斷詞(Jieba)**：匯入PTT社群網路術語自定義詞庫（`mydict.txt`），精準鎖定「割韭菜」、「台積電」等核心財經關鍵字。
5. **AI深度學習情緒分析(Hugging Face BERT)**：採用Transformer架構的繁體中文情緒分類模型，捕捉上下文的因果關係與反諷語意，產出精準的情緒標籤與信心分數。
6. **互動式網頁儀表板(Streamlit + Plotly)**：
   - **時間維度篩選**：自由切換「24小時/7天/30天」數據。
   - **聲量走勢與市場比例**：動態折線圖與甜甜圈圖即時連動。
   - **熱門關鍵字文字雲**：自動過濾停用詞，萃取當前市場最高頻的焦點主題。

---

## 專案目錄結構

```text
scrapy_project/              # 專案總根目錄
├── crawler_project/         # 主要工作空間(在此目錄執行指令)
│   ├── crawler_project/     # Scrapy程式核心模組
│   │   ├── spiders/         # 爬蟲程式庫
│   │   │   └── ptt_stock.py # PTT股版爬蟲核心邏輯
│   │   ├── items.py         # 定義資料結構(Data Model)
│   │   ├── pipelines.py     # 資料庫寫入邏輯(PostgreSQL)
│   │   └── settings.py      # 爬蟲系統設定(含加載.env)
│   ├── .env                 # 資料庫密碼環境變數(本地私有)
│   ├── .env.example         # 環境變數範本(上傳GitHub用)
│   ├── .gitignore           # Git忽略清單(封鎖.env, venv)
│   ├── analyze.py           # NLP資料清洗與AI情緒分析腳本
│   ├── app.py               # Streamlit互動式輿情儀表板
│   ├── mydict.txt           # 台灣股市社群自定義詞庫
│   ├── stopwords.txt        # 文字雲雜訊過濾停用詞清單
│   ├── scrapy.cfg           # Scrapy專案部署配置文件
│   ├── README.md            # 本專案說明文件
│   └── ptt_stock_analyzed.csv # 分析後的結構化數據(暫存檔)
└── venv/                    # Python虛擬環境(獨立套件空間)
```

## 環境建置與安裝步驟
1. 複製專案並進入目錄
```bash
git clone <你的專案倉庫網址>
cd scrapy_project
```
2. 啟動虛擬環境並安裝相依套件
```bash
# 啟動你的虛擬環境(Windows範例)
venv\Scripts\activate

# 安裝所有必要的第三方套件
pip install scrapy pandas sqlalchemy psycopg2-binary jieba transformers torch streamlit plotly wordcloud python-dotenv
```
3. 配置環境變數.env: 請在專案根目錄下建立.env檔案，並填入你的PostgreSQL資料庫連線資訊：
```text
DB_USER=你的資料庫帳號
DB_PASSWORD=你的資料庫密碼
DB_HOST=localhost
DB_PORT=5432
DB_NAME=你的資料庫名稱
```

## 系統執行步驟
本系統採模組化設計，請依序執行以下三個階段：
1. 啟動爬蟲採集數據: 執行以下指令，系統會自動前往PTT抓取資料並寫入PostgreSQL資料庫
```bash
scrapy crawl ptt_stock
```
2. 執行AI輿情與情緒分析: 執行分析腳本，系統會從資料庫撈出原始資料，進行清洗、斷詞與BERT AI情緒標記，最後產出ptt_stock_analyzed.csv分析結果
```bash
python analyze.py
```
3. 開啟互動式儀表板網頁: 執行Streamlit服務，系統會自動彈開瀏覽器並呈現視覺化數據監測網頁
```bash
streamlit run app.py
```
網頁啟動成功後，預設可透過瀏覽本地網址：http://localhost:8501

DEMO網址:https://scrapyproject-3s6zq4g7qurl5uqfep8ypq.streamlit.app/