from multiprocessing import Process
from proxymanager import ProxyManager
import time
import loggerfactory
import traceback
import urllib3
import webhook
import requests as rq
import threadrunner

SITE = __name__.split(".")[1]

class salomen(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.querys= settings["query"]
        self.blacksku = settings["blacksku"]
        self.firstScrape = True
        self.logger = loggerfactory.create(SITE)

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, pid, url, thumbnail, price):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        fields.append({"name": "Price", "value": f"{price}", "inline": True})
        fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
        fields.append({"name": "Status", "value": f"**New Add**", "inline": True})
        
        webhook.send(group=group, webhook=group[SITE], site=f"{SITE}", title=title, url=url, thumbnail=thumbnail, fields=fields, logger=self.logger)


    def scrape_site(self, query):
        """
        Scrapes the specified salomen query site and adds items to array
        """
        items = []


        headers = {
            'Accept': '*/*',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://www.salomon.com',
            'Pragma': 'no-cache',
            'Referer': 'https://www.salomon.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded',
            'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        data = '{"requests":[{"indexName":"prod_salomon_magento2_sln_fr_fr_products","params":"clickAnalytics=true&filters=NOT pcm_not_visible_by_reason_code: D2C&highlightPostTag=__/ais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=50&maxValuesPerFacet=20&page=0&query='+query+'&tagFilters="}]}'

        html = rq.post(
            'https://kq2xe2uch0-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.17.0)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.55.0)%3B%20JS%20Helper%20(3.13.0)&x-algolia-api-key=MWYxMWY1N2RkM2NlM2ZhZjA1MjkzYTdiMDA4Nzc0MDczMTg0ZGM2NzdjYjU2YTYxN2IyNWEwNGE5OTZhYWJmOHRhZ0ZpbHRlcnM9&x-algolia-application-id=KQ2XE2UCH0',
            headers=headers,
            data=data,
        )
        html.raise_for_status()

        products = html.json()["results"][0]["hits"]

        # Stores particular details in array
        for product in products:
            product_item = {
                    "name":product["name"],
                    "pid":product["sku"][0],
                    "price":product["price"]["EUR"]["default_formated"],
                    "image":product["image_url"],
                    "url":product["url"]
                    }
            items.append(product_item)
        
        self.logger.info(msg=f'[{SITE}] Successfully scraped Query {query}')
        return items
        

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {SITE} MONITOR')
        
        while True:
            try:
                startTime = time.time()

                products = []

                for query in self.querys:
                    # Makes request to query-site and stores products 
                    items = self.scrape_site(query)
                    for product in items:
                        if product["pid"] not in self.blacksku:
                            # Check if Product is INSTOCK
                            if product["pid"] not in self.INSTOCK and not self.firstScrape:
                                print(f"[{SITE}] {product['name']} got restocked")
                                self.logger.info(msg=f"[{SITE}] {product['name']} got restocked")
                                for group in self.groups:
                                    #Send Ping to each Group
                                    threadrunner.run(
                                        self.discord_webhook,
                                        group=group,
                                        title=product['name'],
                                        pid=product['pid'],
                                        url=product['url'],
                                        thumbnail=product['image'],
                                        price=product['price']
                                    )

                            products.append(product["pid"])
                    
                self.INSTOCK = products

                # Allows changes to be notified
                self.firstScrape = False

                self.logger.info(msg=f'[{SITE}] Checked all querys in {time.time()-startTime} seconds')

                time.sleep(self.delay)

            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                time.sleep(5)