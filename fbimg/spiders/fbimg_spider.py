import scrapy
import logging
import codecs

from scrapy.http import FormRequest
from scrapy.loader import ItemLoader
from fbimg.items import FbimgItem

class FbImgSpider(scrapy.Spider):
    name = "facebook_images"
    start_urls = ['https://mbasic.facebook.com']    

    def __init__(self, *args, **kwargs):
        #turn off annoying logging, set LOG_LEVEL=DEBUG in settings.py to see more logs
        logger = logging.getLogger('scrapy.middleware')
        logger.setLevel(logging.WARNING)
        
        super().__init__(*args,**kwargs)

        #email & pass need to be passed as attributes!
        if 'email' not in kwargs or 'password' not in kwargs:
            raise AttributeError('You need to provide valid email and password:\n'
                                 'scrapy fb -a email="EMAIL" -a password="PASSWORD"')
        else:
            self.logger.info('Email and password provided, will be used to log in')

        if 'uids' in kwargs:
            uids = codecs.open(self.uids, "r").readlines()
            uids = [l.strip() for l in uids][91:1000]
            self.albums = [("https://mbasic.facebook.com/{0}/photoset/pb.{0}/?owner_id={0}".format(uid.strip()), uid) for uid in uids] + \
                [("https://mbasic.facebook.com/{0}/photoset/t.{0}/?owner_id={0}".format(uid.strip()), uid) for uid in uids]
        else: 
            uids = [100000328344670]     

        self.max_images_per_uid = 200              
    
    def parse(self, response):
        '''
        Handle login with provided credentials
        '''
        return FormRequest.from_response(
                response,
                formxpath='//form[contains(@action, "login")]',
                formdata={'email': self.email,'pass': self.password},
                callback=self.parse_home
                )
  
    def parse_home(self, response):
        '''
        This method has multiple purposes:
        1) Handle failed logins due to facebook 'save-device' redirection
        2) Set language interface, if not already provided
        3) Navigate to given page 
        '''
        #handle 'save-device' redirection
        if response.xpath("//div/a[contains(@href,'save-device')]"):
            self.logger.info('Going through the "save-device" checkpoint')
            yield FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home
                )
            
        for href, uid in self.albums:
            self.logger.info('Scraping facebook page {}'.format(href))
            yield scrapy.Request(url=href, callback=self.parse_album, meta={"uid": uid})

    def parse_album(self, response):
        img_links = response.css("a::attr(href)")
        # print("{} links found!".format(len(img_links)))
        next_page = None
        offset = 0
        for link in img_links.getall():  
            if "photo.php" in link:          
                yield scrapy.Request(response.urljoin(link), callback=self.parse_photo, meta=response.meta)
            elif "photoset" in link:
                splits = link.split("&")
                for s in splits:
                    if "offset" in s:
                        try:
                            offset = int(s.split("=")[1])
                        except ValueError:
                            pass

                next_page = link

        if next_page is not None and offset <= self.max_images_per_uid:
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parse_album, meta=response.meta)

    def parse_photo(self, response):
        
        img_src = response.xpath('//img[contains(@src, "scontent")]')
        # print("{} photos found!".format(len(img_src)))
        for e in img_src:
            # print(e)
            yield FbimgItem(url=e.attrib.get("src", None), 
                            width=e.attrib.get("width", None), 
                            height=e.attrib.get("height", None),
                            alt=e.attrib.get('alt', None),
                            uid=response.meta["uid"])        
        

