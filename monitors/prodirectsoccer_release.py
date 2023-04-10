from threading import Thread, Event
from multiprocessing import Process
from user_agent import CHROME_USERAGENT
from datetime import datetime, timedelta
from proxymanager import ProxyManager
import requests as rq
import time
import json
import loggerfactory
import traceback
import urllib3
import webhook
import threadrunner

SITE = __name__.split(".")[1]

LAUNCHTIMEDELTA = 946684800 #01.01.2000 00.00H

class prodirectsoccer_release(Process):
    def __init__(self, groups, site, releasecategory, settings):
        Process.__init__(self)
        self.site = site
        self.releasecategory = releasecategory
        self.groups = groups
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.querys= settings["query"]
        self.blacksku = settings["blacksku"]
        self.firstScrape = True
        self.logger = loggerfactory.create(f"{self.site}_release")

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, pid, url, thumbnail, price, launch):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        fields = []
        fields.append({"name": "Price", "value": f"{price}£", "inline": True})
        fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
        fields.append({"name": "Status", "value": f"**Release**", "inline": True})
        fields.append({"name": "Launch-Time", "value": f"<t:{launch}>", "inline": True})

        webhook.send(group=group, webhook=group[SITE], site=f"{self.site}_release", title=title, url=url, thumbnail=thumbnail, fields=fields, logger=self.logger)


    def scrape_release_site(self,query):
        """
        Scrapes the specified prodirectsoccer release query site and adds items to array
        """
        items = []

        url = f"https://query.published.live1.suggest.eu1.fredhopperservices.com/pro_direct/json?scope=//catalog01/en_GB/categories%3E%7B{self.releasecategory}%7D&search={query}&callback=jsonpResponse"

        # Makes request to site
        html = rq.get(url,  headers={
                'user-agent': CHROME_USERAGENT
        }, proxies=self.proxys.next())
        html.raise_for_status()

        products = json.loads(html.text[14:-1])["suggestionGroups"][1]["suggestions"]
        html.close()

        # Stores particular details in array
        for product in products:
            product_item = {
                    "name":product["name"],
                    "pid":product["quickref"],
                    "price":product["currentprice"].replace("000",""),
                    "image":product["_thumburl"],
                    "url":product["producturl"],
                    "launch":LAUNCHTIMEDELTA+(int(product["launchtimedelta"])*60)
                    }
            items.append(product_item)

         
        self.logger.info(msg=f'[{self.site}_release] Successfully scraped releases for query {query}')
        return items
        

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {self.site}_release MONITOR')

        while True:
            try:
                startTime = time.time()

                products = []

                for query in self.querys:
        
                    # Make request to release-site and stores products
                    items = self.scrape_release_site(query)
                    for product in items:
                        if product["pid"] not in self.blacksku and datetime.fromtimestamp(product['launch'])>(datetime.now()-timedelta(days=1)):
                            # Check if Product is INSTOCK
                            if product not in self.INSTOCK and not self.firstScrape:
                                print(f"[{self.site}_release] {product['name']} got restocked")
                                self.logger.info(msg=f"[{self.site}_release] {product['name']} got restocked")
                                for group in self.groups:
                                    #Send Ping to each Group
                                    threadrunner.run(
                                        self.discord_webhook,
                                        group=group,
                                        title=product['name'],
                                        pid=product['pid'],
                                        url=product['url'],
                                        thumbnail=product['image'],
                                        price=product['price'],
                                        launch=product['launch']
                                    )

                            products.append(product)

                self.INSTOCK = products

                self.firstScrape = False

                self.logger.info(msg=f'[{self.site}_release] Checked all querys in {time.time()-startTime} seconds')
                time.sleep(self.delay)

            except Exception as e:
                print(f"[{self.site}_release] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                time.sleep(5)