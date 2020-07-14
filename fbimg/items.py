# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FbimgItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    url = scrapy.Field()
    width = scrapy.Field()
    height = scrapy.Field()
    alt = scrapy.Field()
    uid = scrapy.Field()
