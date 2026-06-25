from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import os

def drop_expired_table():
    print("[Data Lifecycle]開始執行每日分表清理任務...")
    
    # 從環境變數讀取連線資訊
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)
    
    # 精確計算「7天前」的日期字串
    target_date = datetime.now() - timedelta(days=7)
    date_str = target_date.strftime("%Y%m%d")
    
    # 組裝動態資料表名稱
    table_name = f"ptt_stock_articles{date_str}"
    print(f"預計刪除的過期資料表名稱為: {table_name}")
    
    # 執行DROP TABLE
    query = text(f"DROP TABLE IF EXISTS {table_name};")
    
    try:
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(query)
                print(f"成功將舊資料表{table_name}移出資料庫")
    except Exception as e:
        print(f"刪除資料表失敗, 錯誤訊息: {e}")

if __name__ == "__main__":
    drop_expired_table()