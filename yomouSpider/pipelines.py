# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import os
import pymongo
class YomouspiderPipeline(object):
    def process_item(self, item, spider):
        spider.logger.debug('final item:'+str(item))
        return item

class SavefilePipeline(object):
    def save_text(self,textStr,path):
        with open(path,'w',encoding='utf8')as f:
            f.write(textStr)
        f.close()
    def convert_windowsFileName(self,filename):
        return  re.sub(r'[\/:*?"<>|]', " ",filename)

    def process_item(self,item,spider):
        textStr=''
        for section in item['contentList']:
            textStr+=section['chapter_title']+'\n'+section['pageTitle']+'\n'+section['content']
        filename='{title}[{author}][{pt}][{ncode}].txt'.format(title=item.get('title'),author=item.get('author'),pt=item.get('overallpoint'),ncode=item.get('ncode'))
        if not os.path.exists('syosetu'):
            os.mkdir('syosetu')
        filename=self.convert_windowsFileName(filename)
        path=os.path.join('syosetu',filename)
        self.save_text(textStr,path)
        spider.logger.info('save file succeed:'+path)
        return item

class InnsertMongodbPipeline(object):
    collection_name='top2000'
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )
    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
    def process_item(self, item, spider):
        insert_result=self.db[self.collection_name].insert_one(dict(item))
        spider.logger.info('insert completed'+str(insert_result))
        return item
    def close_spider(self, spider):
        self.client.close()
    def has_ncode(self,ncode):
        count=self.self.db[self.collection_name].find({'ncode':ncode}).count()
        if count==0:
            return False
        return True