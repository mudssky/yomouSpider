# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class top2000spiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title=scrapy.Field()
    author=scrapy.Field()
    ncode=scrapy.Field()
    desp=scrapy.Field()
    genre=scrapy.Field()
    keywords=scrapy.Field()
    startTime=scrapy.Field()
    lastmodified=scrapy.Field()
    readtime=scrapy.Field()
    weeklyUniqueUser=scrapy.Field()
    reviewcounts=scrapy.Field()
    overallpoint=scrapy.Field()
    bookmarkcounts=scrapy.Field()
    commentUserCounts=scrapy.Field()
    evaluationponit=scrapy.Field()
    completeStatus=scrapy.Field()
    wordCounts=scrapy.Field()
    contentList=scrapy.Field()


