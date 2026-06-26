import streamlit as st# 網頁框架
import pandas as pd# 資料分析套件
import plotly.express as px# 互動式圖表套件
from wordcloud import WordCloud# 文字雲套件
import matplotlib.pyplot as plt# 繪圖套件
from datetime import datetime, timedelta
from pathlib import Path
import os
from wordcloud import WordCloud

# 網頁基本設定(頁面標題、Icon)
page_title = "PTT股版輿情監測與AI情緒分析儀表板"
page_icon = "📈"
st.set_page_config(
    page_title=page_title,
    page_icon=page_icon,
    layout="wide"
)

st.title(page_icon+page_title)
st.markdown("本儀表板展示了從PTT Stock版爬取的即時數據, 並透過BERT深度學習模型進行情緒標籤與信心分數分析")

# 利用Cache機制安全載入資料
@st.cache_data(ttl=60)# ttl=60代表每60秒會自動過期重新讀取, 達到即時更新效果
def load_data():
    try:
        # 動態取得app.py所在的資料夾路徑
        current_dir = Path(__file__).parent
        csv_path = current_dir / 'ptt_stock_analyzed.csv'
        
        # 讀取分析後的 CSV
        df = pd.read_csv(csv_path)
        
        # 重新命名為程式後續要使用的date
        if 'created_at' in df.columns:
            df = df.rename(columns={'created_at': 'date'})
        
        # 將時間字串轉為Python datetime物件
        df['date'] = pd.to_datetime(df['date'])

        return df
    except Exception as e:
        st.error(f"載入資料失敗, 請確認ptt_stock_analyzed.csv是否存在, 錯誤原因: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("目前沒有可顯示的數據, 請先運行爬蟲與分析腳本")
    st.stop()

# 側邊欄(Sidebar)-互動式時間與關鍵字篩選器
st.sidebar.header("🔍數據篩選面板")

# 時間維度篩選
time_option = st.sidebar.selectbox(
    "選擇時間範圍：",
    ["全部數據", "過去24小時", "過去7天", "過去30天"]
)

# 計算篩選時間起點（模擬當前系統時間為2026-06-18）
current_time = datetime(2026, 6, 3, 0, 0, 0)# 實務上可用datetime.now()
if time_option == "過去24小時":
    start_time = current_time - timedelta(days=1)
    df_filtered = df[df['date'] >= start_time]
elif time_option == "過去7天":
    start_time = current_time - timedelta(days=7)
    df_filtered = df[df['date'] >= start_time]
elif time_option == "過去30天":
    start_time = current_time - timedelta(days=30)
    df_filtered = df[df['date'] >= start_time]
else:
    df_filtered = df.copy()

# 個股/關鍵字搜尋
search_keyword = st.sidebar.text_input("輸入個股或標題關鍵字（如：台積電、航運）：", "")
if search_keyword:
    df_filtered = df_filtered[df_filtered['title'].str.contains(search_keyword, case=False, na=False)]

# 主要區塊(Main Body)-關鍵數據卡片(Metrics)
total_articles = len(df_filtered)
pos_count = len(df_filtered[df_filtered['sentiment_label'].str.contains('Positive')])
neg_count = len(df_filtered[df_filtered['sentiment_label'].str.contains('Negative')])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊總討論聲量", f"{total_articles}篇")
with col2:
    st.metric("🚀樂觀看多文章", f"{pos_count}篇", delta=f"{pos_count/max(1, total_articles)*100:.1f}%")
with col3:
    st.metric("😡悲觀看空文章", f"{neg_count}篇", delta=f"-{neg_count/max(1, total_articles)*100:.1f}%", delta_color="inverse")

st.markdown("---")

# 焦點圖表區(Charts-左右排版)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈聲量走勢與情緒分佈圖")
    if not df_filtered.empty:
        # 按日期(天)分組統計文章數量
        df_trend = df_filtered.groupby([df_filtered['date'].dt.date, 'sentiment_label']).size().reset_index(name='文章數量')
        # 使用Plotly畫出動態折線圖
        fig_trend = px.line(
            df_trend, 
            x='date', 
            y='文章數量', 
            color='sentiment_label',
            labels={'date': '日期', 'sentiment_label': 'AI情緒傾向'},
            markers=True
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.write("目前範圍內無走勢數據")

with chart_col2:
    st.subheader("🍩市場樂觀/悲觀比例")
    if total_articles > 0:
        # 統計標籤比例
        df_pie = df_filtered['sentiment_label'].value_counts().reset_index()
        # 使用Plotly畫出互動圓餅甜甜圈圖
        fig_pie = px.pie(
            df_pie, 
            values='count', 
            names='sentiment_label', 
            hole=0.4,
            color_discrete_map={'🚀正向(看多/樂觀)': '#ff4b4b', '😡負向(看空/崩潰)': '#1c83e1', '😐中立(無內容)': '#7d7d7d'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.write("目前範圍內無情緒數據")

# 文字雲區(WordCloud)
st.subheader("☁️當前熱門竄升關鍵字（文字雲）")
if total_articles > 0:
    # 將第二階段Jieba切好的tokens重新組合起來做文字雲
    # tokens欄位讀出來時是字串格式的"['台積電', '多']", 要轉回純文字
    all_words = []
    for t_str in df_filtered['tokens'].dropna():
        # 清理字串, 轉換成純文字空白相連的格式
        words = t_str.replace("[", "").replace("]", "").replace("'", "").replace(",", "")
        all_words.append(words)
    
    text_for_cloud = " ".join(all_words)
    
    if text_for_cloud.strip():
        # 讀取自定義的停用詞清單
        try:
            with open('stopwords.txt', 'r', encoding='utf-8') as f:
                custom_stopwords = set([line.strip() for line in f.readlines() if line.strip()])
        except FileNotFoundError:
            custom_stopwords = set() # 萬一沒讀到檔案就用空的set

        # # 設定微軟正黑體微字型路徑, 否則中文會變框框死碼
        # font_path = "C:\\Windows\\Fonts\\msjh.ttc"  # Windows預設正黑體路徑

        # 取得目前 app.py 的目錄路徑
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(BASE_DIR, "msjh.ttf")
        
        wc = WordCloud(
            font_path=font_path,
            background_color="white",
            width=1000,
            height=400,
            max_words=80,
            stopwords=custom_stopwords
        ).generate(text_for_cloud)
        
        # 使用Matplotlib渲染文字雲並丟給Streamlit顯示
        fig_wc, ax = plt.subplots(figsize=(10, 4))
        ax.imshow(wc, interpolation="hermite")# 文字雲的邊緣和像素平滑化
        ax.axis("off")
        st.pyplot(fig_wc)
    else:
        st.write("文字不足以生成文字雲")
else:
    st.write("目前範圍內無資料可生成文字雲")

# 原始數據抽查明細
st.subheader("📋輿情數據明細抽查")
st.dataframe(df_filtered[['date', 'title', 'sentiment_label', 'sentiment_score']].head(20), use_container_width=True)