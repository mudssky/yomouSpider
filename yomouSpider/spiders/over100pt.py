# -*- coding: utf-8 -*-
import scrapy


class Over100ptSpider(scrapy.Spider):
    name = 'over100pt'
    allowed_domains = ['yomou.syosetu.com']
    start_urls = ['http://yomou.syosetu.com/']

    def parse(self, response):
        pass
