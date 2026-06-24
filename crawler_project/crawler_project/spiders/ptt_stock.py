import scrapy
from datetime import datetime, timedelta
from crawler_project.items import PttStockItem

class PttStockSpider(scrapy.Spider):
    name = "ptt_stock"
    allowed_domains = ["ptt.cc"]
    start_urls = ["https://www.ptt.cc/bbs/Stock/index.html"]

    def __init__(self, *args, **kwargs):
        super(PttStockSpider, self).__init__(*args, **kwargs)
        # 取得昨天的日期, 並動態計算出今年與這個月
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        self.current_year = yesterday.year
        self.current_month = yesterday.month
        self.current_day = yesterday.day

        # 標記：用來判斷這頁是否有任何一篇文章是屬於這個日期的
        self.has_this_day_data = True

    # PTT有滿18歲的確認頁面, 透過cookie繞過
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, cookies={'over18': '1'}, callback=self.parse)

    # 解析文章列表頁
    def parse(self, response):
        self.logger.info(f"目前使用的User-Agent是: {response.request.headers.get('User-Agent')}")

        has_newer_data = False# 這一頁是否有比目標日期「更新」的文章（例如今天）
        has_target_data = False# 這一頁是否有「符合目標日期」的文章（例如昨天）

        target_date = datetime(self.current_year, self.current_month, self.current_day)

        # 找到所有文章的區塊
        articles = response.css('div.r-ent')
        for art in articles:
            title_element = art.css('div.title a')
            if title_element:
                title = title_element.css('::text').get()
                url = response.urljoin(title_element.css('::attr(href)').get())
                author = art.css('div.meta div.author::text').get()
                date_str = art.css('div.meta div.date::text').get()# 格式例如: " 6/02" 或 "12/31"
                push_count = art.css('div.nrec span::text').get() or "0"

                # 月份判斷邏輯
                if date_str:
                    try:
                        # 移除前後空, 並用斜線切出月份和日期
                        article_month = int(date_str.strip().split('/')[0])
                        article_day = int(date_str.strip().split('/')[1])
                        # 建立文章的datetime物件（用來精準比大小）
                        article_date = datetime(self.current_year, article_month, article_day)
                    except(ValueError, IndexError):
                        continue
                    
                    if article_date > target_date:
                        # 如果文章比目標日期還要新（例如目標是昨天，這篇是今天），代表還沒翻到目標，記錄下來
                        has_newer_data = True
                        
                    elif article_date == target_date:
                        # 如果正好是目標日期（昨天），處理並下載
                        has_target_data = True

                        # 從URL萃取文章ID
                        article_id = url.split('/')[-1].replace('.html', '')

                        # 建立Item並帶到下一層
                        item = PttStockItem(
                            article_id=article_id, title=title, author=author, 
                            date=date_str.strip(), push_count=push_count, url=url
                        )

                        # 發送請求去抓取內文頁
                        yield scrapy.Request(url, cookies={'over18': '1'}, callback=self.parse_content, cb_kwargs={'item': item})

            # 只要這一頁有「今天的文章」(has_newer_data) 或者是「昨天的文章」(has_target_data)
            # 就代表需要繼續往前翻頁
            if has_target_data or has_newer_data:
                prev_page = response.css('div.btn-group-paging a:nth-child(2)::attr(href)').get()
                if prev_page:
                    self.logger.info(f"正在往前翻頁：{prev_page}")
                    yield response.follow(prev_page, cookies={'over18': '1'}, callback=self.parse)
            else:
                # 如果整頁文章的日期都不等於這個日期（代表已經翻到前天的舊文章了）
                self.logger.info("已經翻完這個日期的所有文章，爬蟲停止。")

    # 解析文章內文頁
    def parse_content(self, response, item):
        # 抓取文章上方的完整時間欄位
        # PTT的meta欄位順序通常是：作者、看板、標題、時間
        meta_values = response.css('span.article-meta-value::text').getall()
        
        if len(meta_values) >= 4:
            # 取得最後一個欄位，格式通常為"Tue Jun  2 12:34:56 2026"
            date_string = meta_values[3] 
            try:
                # 解析時間字串
                dt = datetime.strptime(date_string, "%a %b %d %H:%M:%S %Y")
                # 覆蓋原本只有月日的date
                item['date'] = dt.strftime("%Y-%m-%d %H:%M:%S") 
            except ValueError:
                # 遇到少數格式異常的文章, 保留原本的列表頁日期
                pass

        # 抓取主要內容區塊
        main_content = response.css('#main-content')
        
        # 移除內文中的meta資訊與推文區塊, 只保留純內文
        # 這裡用一個簡單的文本清洗, 過濾掉不需要的BBS資訊
        texts = main_content.xpath('./text()').getall()
        content = "".join(texts).strip()
        
        item['content'] = content
        yield item# 將完整的Item丟給Pipeline