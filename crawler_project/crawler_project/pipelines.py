import psycopg2
from datetime import datetime

class PostgresPipeline:
    def open_spider(self, spider):
        # 當爬蟲啟動時執行： 建立資料庫連線
        # 從 settings.py 中讀取連線設定
        db_settings = spider.settings.get('POSTGRES_SETTINGS')
        
        try:
            self.connection = psycopg2.connect(**db_settings)
            self.cursor = self.connection.cursor()# 在Python的資料庫規範中, 不能直接用連線本身去對資料庫下達SQL指令, 必須透過cursor()建立一個游標物件, 由它來負責發送SQL以及帶回查詢結果
            spider.logger.info("成功連線至PostgreSQL資料庫")

            self.created_tables = set()
        except Exception as e:
            spider.logger.error(f"資料庫連線失敗: {e}")
            raise e

    def close_spider(self, spider):
        # 當爬蟲結束時執行： 關閉資料庫連線
        if hasattr(self, 'cursor') and self.cursor:# 確認系統裡有沒有cursor且不是空的
            self.cursor.close()
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
            spider.logger.info("PostgreSQL資料庫連線已安全關閉")

    def _create_table_if_not_exists(self, table_name, spider):
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            article_id VARCHAR(50) PRIMARY KEY,
            title VARCHAR(255),
            author VARCHAR(100),
            created_at TIMESTAMP,
            push_count VARCHAR(10),
            url TEXT,
            content TEXT
        );
        """
        try:
            self.cursor.execute(create_table_query)
            self.connection.commit()
            # 成功建立或確認存在後, 加入快取, 之後同名稱的表就不再進來這裡
            self.created_tables.add(table_name)
            spider.logger.info(f"成功確認/建立資料表: {table_name}")
        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"建立資料表{table_name}失敗: {e}")
            raise e

    def process_item(self, item, spider):
        # 每當Spider yield一個item, 就會流進這裡寫入資料庫

        # 從item取得日期並轉換成YYYYMMDD後綴
        try:
            date_str = item.get('date', '')
            dt = datetime.strptime(date_str.split(' ')[0], "%Y-%m-%d")
                
            date_suffix = dt.strftime("%Y%m%d") # 轉成"20260623"
        except Exception as e:
            # 日期解析失敗, 給一個預設值（例如今天）, 避免爬蟲崩潰
            spider.logger.warning(f"日期解析失敗({item.get('date')}), 使用當前日期作為後綴, 錯誤: {e}")
            date_suffix = datetime.now().strftime("%Y%m%d")

        table_name = f"ptt_stock_articles{date_suffix}"

        if table_name not in self.created_tables:
                    self._create_table_if_not_exists(table_name, spider)

        # SQL語法： 使用ON CONFLICT實作Update / Insert邏輯
        insert_query = f"""
            INSERT INTO {table_name} (article_id, title, author, created_at, push_count, url, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (article_id) 
            DO UPDATE SET 
                push_count = EXCLUDED.push_count,  -- 如果文章重複, 更新最新的推文數
                title = EXCLUDED.title;             -- 如果標題有改（例如分類變更）, 也同步更新
        """
        
        # 要帶入SQL的資料數組
        data = (
            item.get('article_id'),
            item.get('title'),
            item.get('author'),
            item.get('date'),
            item.get('push_count'),
            item.get('url'),
            item.get('content')
        )
        
        try:
            self.cursor.execute(insert_query, data)
            self.connection.commit()# 提交事務, 正式寫入
        except Exception as e:
            self.connection.rollback()# 發生錯誤時倒帶（Rollback）, 防止資料庫死鎖
            spider.logger.error(f"資料寫入失敗, 表名 {table_name}, 文章ID {item.get('article_id')}: {e}")
            
        return item # 必須return item, 讓後續的其他Pipeline能繼續處理