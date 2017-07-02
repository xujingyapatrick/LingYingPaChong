from linkedin import LinkedinSpider
spider=LinkedinSpider()
try:
	spider.findNewJobs()
finally:
    spider.sendmail()