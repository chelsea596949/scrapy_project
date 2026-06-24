# Scrapy settings for crawler_project project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "crawler_project"

SPIDER_MODULES = ["crawler_project.spiders"]
NEWSPIDER_MODULE = "crawler_project.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "crawler_project (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Scrapy預設會將DOWNLOAD_DELAY乘以一個0.5~1.5的隨機數
# 例如設1秒, 實際延遲會在0.5到1.5秒之間隨機變動, 讓行為更像真人
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "crawler_project.middlewares.CrawlerProjectSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# 啟用隨機User-Agent中間件
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,# 必須先關閉Scrapy內建的預設User-Agent
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,# 啟用新安裝的隨機User-Agent套件
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "crawler_project.pipelines.PostgresPipeline": 300,# 必須確定名稱跟pipelines.py裡的class名稱一致, 數字300代表這個Pipeline的執行優先順序, 數字越小優先執行
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True# 啟用自動限速（預設是False）
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1# 初始下載延遲（秒）
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60# 在高延遲情況下的最大下載延遲（秒）, 防止卡死
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0# Scrapy應與遠端網站保持的平均平行請求數, 設為1.0代表溫和爬取, 對伺服器非常禮貌
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

# PostgreSQL資料庫連線設定(從環境變數安全讀取)
POSTGRES_SETTINGS = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'crawler_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD')
}