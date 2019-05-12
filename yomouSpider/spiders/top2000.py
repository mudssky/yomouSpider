# -*- coding: utf-8 -*-
import scrapy
import logging
import time
import os
import pymongo
from yomouSpider.items import top2000spiderItem
class top2000Spider(scrapy.Spider):
    name = 'top2000'
    collection_name = 'top2000'
    allowed_domains = ['yomou.syosetu.com','mypage.syosetu.com','ncode.syosetu.com']
    start_urls = ['http://yomou.syosetu.com/search.php?&type=er&order_former=search&order=new&notnizi=1&min_globalpoint=6240&p=48']
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client=pymongo.MongoClient('127.0.0.1:27017')
        self.db=self.client['yomouSpider']
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url,callback=self.parse_searchpage)
        # yield scrapy.Request(url='https://ncode.syosetu.com/n8563fi/',callback=self.parse_bookpage,meta={'item':top2000spiderItem()})
        # yield scrapy.Request(url='https://ncode.syosetu.com/n7742fl/',callback=self.parse_bookpage,meta={'item':top2000spiderItem()})
    def parse_searchpage(self, response):
        # for block in response.css('.searchkekka_box'):
        for block in response.css('.searchkekka_box'):
            # self.logger.info(str(block))
            item=top2000spiderItem()
            item['title'] = block.css('.tl::text').get(default='')
            item['desp'] =block.css('.ex::text').get(default='')
            # item['genre']=block.re('ジャンル：[\s\S]*?<a[\s\S]*?>([\s\S]*?)<')
            # keywordsStr=block.re(' キーワード：[\s\S](.*?)<br')[0]
            item['keywords']=block.css('a::text').getall()[4:]

            item['readtime']=block.re('span[\s\S]*?>読了時間：(.*?)（')[0]

            # print(block.re(' 週別ユニークユーザ： (.*?)[人満]'))
            # 当人数小于100的时候会出现100未满字样，造成匹配不到出现index out of range错误，所以这里加上满字的匹配
            item['weeklyUniqueUser']=block.re(' 週別ユニークユーザ： (.*?)[人満]')[0]

            item['reviewcounts']=block.re('レビュー数： (.*?)件')[0]

            item['commentUserCounts']=block.re('評価人数：  (.*?)  人 ')[0].replace(',','')

            item['evaluationponit']=block.re('評価人数：  (.*?)  人 ')[0].replace(',','')

            item['completeStatus']='完結済'

            item['ncode']=block.css('.tl::attr(href)').get().split('/')[-2]
            # 继续爬取信息页的信息
            # self.logger.info('info_page_len:'+str(len(info_page)))
            info_page = r'https://ncode.syosetu.com/novelview/infotop/ncode/{ncode}/'.format(ncode=item['ncode'])
            # self.logger.info('request info page')


            if not self.has_ncode(item['ncode']):
                yield scrapy.Request(url=info_page, callback=self.parse_infopage, meta={"item":item})
                # 回调函数传参，需要把meta属性赋值

            next_page=response.css('.nextlink::attr(href)').get()
            if next_page is not None:
                # self.logger.debug('get url')
                next_url=r'http://yomou.syosetu.com/search.php'+next_page
                yield scrapy.Request(url=next_url, callback=self.parse_searchpage)
            # ncode = block.re('／Nコード：(.*?)<table')
            # content = scrapy.Field()
            # self.logger.info(item)
    def has_ncode(self,ncode):
        count=self.db[self.collection_name].find({'ncode':ncode}).count()
        if count==0:
            return False
        return True
    def parse_infopage(self, response):
        # self.logger.info('info page')
        item=response.meta['item']
        content=response.css('#contents_main')
        # self.logger.info(str(response))
        item['author']=content.re('作者名</th>[\s\S]*?<a[\s\S]*?>([\s\S]*?)<')[0]
        item['genre']=content.re('ジャンル[\s\S]*?<td>([\s\S]*?)<')
        item['startTime']=content.re('掲載日[\s\S]*?<td>([\s\S]*?)<')[0]
        item['lastmodified']=content.re('掲載日[\s\S]*?<td>([\s\S]*?)<')[1]

        wordCountsStr=content.re('文字数[\s\S]*?<td>([\s\S]*?)<')[0][:-2]
        item['wordCounts']=wordCountsStr.replace(',','')

        item['overallpoint'] = content.re('総合評価[\s\S]*?<td>(.*?)pt')[0]
        item['bookmarkcounts']=content.re('ブックマーク登録[\s\S]*?<td>(.*?)件<')

        # self.logger.info('parse_infopage'+str(item))

        # 进入文章页爬取，因为下载功能现在需要cookie登录，为了避免封号，还是直接爬取网页稳妥一些
        bookUrl='https://ncode.syosetu.com/{ncode}/'.format(ncode=item['ncode'])
        yield scrapy.Request(url=bookUrl, callback=self.parse_bookpage, meta={"item":item})
        # self.logger.info("infopage item" + str(item))
        # downloadNcode=content.re('この小説のトラックバックURL[\s\S]*?<input[\s\S]*?value="(.*?)"')[0]
        # downloadPage=r'https://ncode.syosetu.com/txtdownload/top/ncode/{downloadNcode}/'.format(downloadNcode=downloadNcode)
        # request = scrapy.Request(url=downloadPage, callback=self.downloadpage_parse)
        # # 回调函数传参，需要把meta属性赋值
        # request.meta['item'] = item
        # yield request

    #     这里犯了一个挺大的错误，在scrap框架里面是异步的，所以这里在目录页提取连接，最后还要排序，倒不如直接进入书籍第一页，然后翻页就可以少写很多代码，也减少了无用的判断
    #     不过下载顺序的问题似乎依然要排序
    def parse_bookpage(self, response):
        item=response.meta['item']
        pageList=response.css('dl a')

        # tmpDict=[]
        # item['content']=tmpDict
        # item['contentDict'] = {}
        item['contentList'] = []
        totalCount=len(pageList)
        for index,page in enumerate(pageList):
            # self.logger.debug('index:{index},pageListLen:{pagaListLen}'.format(index=index, pagaListLen=len(pageList)))
            # if len(pageList)==index+1:
            #     isCompleted=True
            pageUrl='https://ncode.syosetu.com'+page.css('a::attr(href)').get()
            pageTitle=page.css('a::text').get()
            pageNum=index+1
            tmpDict={}
            tmpDict['pageTitle']=pageTitle
            tmpDict['pageNum']=pageNum
            # print('item',id(item),'contentList',id(item['contentList']))
            yield scrapy.Request(url=pageUrl,callback=self.parse_downloadpage,meta={'item':item,'tmpDict':tmpDict,'totalCount':totalCount})
            # 判断列表是否爬取完成，爬取完成时才可以提取item
            # self.logger.debug('index:{index},pageListLen:{pagaListLen}'.format(index=index,pagaListLen=len(pageList)))
            # if index==len(pageList)-1:
            #     yield item
        # self.logger.info("bookpage item"+str(item))

    def parse_downloadpage(self,response):
        item=response.meta['item']
        tmpDict=response.meta['tmpDict']
        totalCount=response.meta['totalCount']
        tmpDict['chapter_title']=response.css('.chapter_title::text').get()
        if tmpDict['chapter_title'] is None:
            tmpDict['chapter_title']=''
        # 请求获得的文章内容是一个列表，用join拼接成字符串
        # tmpDict['content']='\n'.join(response.css('.novel_view').xpath('./*/text()').getall())

        # br会被忽视掉，所以手动替换成换行
        tmpDict['content'] = ''
        for p in  response.css('.novel_view p'):
            text=p.css('p::text').get()
            # print('text:',text,text is None)
            if text is None:
                tmpDict['content']+='\n'+'\n'
            else:
                tmpDict['content']+='\n'+text
        # self.logger.debug('content:'+str(tmpDict['content']))
        # self.logger.debug('page {pageNum} download succeed: {conetnt}'.format(pageNum=tmpDict['pageNum'],conetnt=tmpDict['content']))
        item['contentList'].append(tmpDict)
        # item['contentDict'][tmpDict['pageNum']]=tmpDict
        # self.logger.debug('isCompleted:'+str(isCompleted))

        if len(item['contentList'])==totalCount:
            item['contentList']=sorted(item['contentList'],key=lambda l:l['pageNum'],reverse=False)
            # self.logger.debug('completed '*20)
            # self.logger.info('completed '*20)
            yield item
    # https://ncode.syosetu.com/txtdownload/dlstart/ncode/770330/?no=1&hankaku=0&code=utf-8&kaigyo=crlf
    # def getFormatedContent(self,plist,):















