from threading import Thread, Event
from multiprocessing import Process
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
from concurrent.futures import ThreadPoolExecutor
import tls
import time
import loggerfactory
import traceback
import urllib3
import os
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class bstn(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.delay = settings["delay"]
        self.querys = settings["querys"]
        self.proxys = ProxyManager(settings["proxys"])
        self.blacksku = settings["blacksku"]
        self.firstScrape = True
        self.logger = loggerfactory.create(SITE)

        self.INSTOCK = {}
        
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
        Scrapes the specified bstn query site and adds items to array
        """
        items = []

        url = f"https://www.bstn.com/eu_de/rest/eu_de/V1/products-render-info?searchCriteria[pageSize]=10000&storeId=2&currencyCode=EUR&searchCriteria[currentPage]=1&searchCriteria[filter_groups][0][filters][0][field]=name&searchCriteria[filter_groups][0][filters][0][value]=%25{query}%25&searchCriteria[filter_groups][0][filters][0][condition_type]=like"

        headers = {
            'authority': 'www.bstn.com',
            'accept': 'application/json',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        }

        # Makes request to site
        html = tls.get(url, headers=headers, proxies=self.proxys.next())
        html.raise_for_status()
        products = html.json()["items"]
        html.close()
        # Stores particular details in array
        for product in products:
            product_item = {
                    "name":product["name"],
                    "pid":product["id"],
                    "price":str(product["price_info"]["final_price"])+" €",
                    'image': product["images"][0]["url"],
                    "url":product["url"]
                    }
            items.append(product_item)

        
        self.logger.info(msg=f'[{SITE}] Successfully scraped query {query}')
        return [query,items]
        

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {SITE} MONITOR')
    
        for query in self.querys:
            self.INSTOCK[query] = []
        
        while True:
            try:
                startTime = time.time()

                # Makes request to each category
                with ThreadPoolExecutor(len(query)) as executor:
                    itemsSplited = [item for item in executor.map(self.scrape_site, self.querys)]

                    for query, items in itemsSplited:
                        products = []

                        for product in items:
                            if product["pid"] not in self.blacksku and any(query.lower() in product["name"].lower() for query in self.querys):

                                # Check if Product is INSTOCK
                                if not any([product["pid"] in query for query in self.INSTOCK.values()]) and not self.firstScrape:
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

                        self.INSTOCK[query] = products

                # Allows changes to be notified
                self.firstScrape = False

                self.logger.info(msg=f'[{SITE}] Checked all querys in {time.time()-startTime} seconds')
                time.sleep(self.delay)

            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                time.sleep(3)