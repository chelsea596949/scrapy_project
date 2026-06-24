# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class PttStockItem(scrapy.Item):
    article_id = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    content = scrapy.Field()
    push_count = scrapy.Field()
    url = scrapy.Field()