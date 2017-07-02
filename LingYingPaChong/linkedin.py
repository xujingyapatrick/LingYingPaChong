from scrapy.selector import Selector
from bs4 import BeautifulSoup
import re
import pymongo
from pymongo import MongoClient
import io
from selenium import webdriver
import time, random
from selenium.webdriver.support.ui import Select
from dbhelper import DBhelper
import datetime
from selenium.common.exceptions import NoSuchElementException
import mailsender



class LinkedinSpider(object):
    name = "linkedin"
    dbhelper=DBhelper()
    start_urls=["https://www.linkedin.com"]
        
    def waitForLoading(self):
        time.sleep(5+random.randint(2,9))
        return
    def findNewJobs(self):
        # your chrome driver location like :'/home/patrick/Documents/referral/chromedriver'
        driver = webdriver.Chrome('your chrome driver location')
        driver.set_window_size(1000, 1000)
        driver.get(self.start_urls[0])
        self.waitForLoading()
        driver.find_element_by_name(u"session_key").clear()
        # ####your linkedin user name: u"example@gmail.com"
        driver.find_element_by_name(u"session_key").send_keys(u"")
        driver.find_element_by_name(u"session_password").clear()
        # ####your linkedin user name: u"abcabcabc"
        driver.find_element_by_name(u"session_password").send_keys(u"")
        driver.find_element_by_css_selector("input#login-submit.login.submit-button").click()
        self.waitForLoading()

        #go to search and set software, entry level, computer... i.e. set up search and search
        driver.find_element_by_class_name(u"nav-search-button").click()
        self.waitForLoading()
        
        lilist = driver.find_elements_by_class_name(u"sub-nav-item")
        lilist[2].find_element_by_tag_name("button").click()
        self.waitForLoading()
        
        inputDivs=driver.find_elements_by_class_name("type-ahead-input")
        inputDivs[0].find_element_by_tag_name("input").clear()
        inputDivs[0].find_element_by_tag_name("input").send_keys("new grad software")
        driver.find_element_by_css_selector("button.submit-button.button-primary-large").click()
        self.waitForLoading()
        select=Select(driver.find_element_by_id("sort-dropdown-select"))
        select.select_by_visible_text("Post date")
        self.waitForLoading()

        crawled_count=0
        page_count=0
        while crawled_count<5 and page_count<100:
            page_count=page_count+1
            body=driver.find_element_by_tag_name("body")
            # print(body.size)
            height=body.size['height']/20
            for h in range(1,height):
                script="window.scrollTo(0, "+str(h*20)+");"
                driver.execute_script(script)
                time.sleep(0.08)
            source=driver.page_source.encode('utf8')
            crawled_count=self.extract_items_scrapy(source)
            next=driver.find_element_by_css_selector("button.next").click()
            self.waitForLoading()
        driver.close()


    # get new jobs and send email
    def sendmail(self):
        today , old = self.dbhelper.getLatestItems()
        mailsender.send(today = today, old = old)
        return


    def extract_items_scrapy(self,source):
        crawled_count=0
        selector=Selector(text=source, type="html")
        db=self.dbhelper.client.linkedin
        # filename="page.html"
        # with open(filename,'wb') as f:
        #     f.write(source)
        ul=selector.xpath('//*[@id="careers"]/div[2]/div/section/div/div[2]/ul')
        alist=ul.xpath("./div/a")
        print("len(alist)="+str(len(alist)))
        
        for a in alist:
            url=a.xpath("./@href").extract()
            url=url[0].encode('utf8')
            url=self.start_urls[0]+url[:(url.find('/',14))]
            companie=a.css("h4.job-card__company-name::text").extract()
            title=a.css("span.truncate-multiline--last-line-wrapper").xpath("./span/text()").extract()
            title=companie[0]+": "+title[0]
            hashCode=hash(title + url)
            date=str(datetime.date.today())
            item={}
            item['title']=title
            item['_id'] = hashCode
            item['date'] = date
            item['url']=url
            # print("Job title:"+item['title']+"  Link:"+item['url'])
            if self.exists(item,db.repo):
                crawled_count=crawled_count+1
            print("Job title:"+item['title']+"  Link:"+item['url'])
            self.dbhelper.insert_one(item)
        return crawled_count

    def exists(self,item,collection):
        return collection.find_one({'_id' : item['_id']}) != None


