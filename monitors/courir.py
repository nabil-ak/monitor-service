from threading import Thread, Event
from multiprocessing import Process
from bs4 import BeautifulSoup
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
import tls
import time
import os
import loggerfactory
import traceback
import urllib3
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class courir(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]  
        self.pids = settings["pids"]
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


    def scrape_site(self):
        """
        Scrapes the courir pids
        """
        items = []

        headers = {
            'accept': '*/*',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.courir.com',
            'pragma': 'no-cache',
            'referer': 'https://www.courir.com/fr/c/accessoires/casquette-bob/',
            'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }

        data = {
            'scid': '663359b5e78b3462df55ef4a79',
        }

        for x in range(len(self.pids)):
            data[f"pid{x}"]=self.pids[x]

        # Makes request to site
        html = tls.post(
            'https://www.courir.com/on/demandware.store/Sites-Courir-FR-Site/fr_FR/CQRecomm-Start',
            headers=headers,
            data=data,
        )
        html.raise_for_status()

        output = BeautifulSoup(html.text, 'html.parser')
        html.close()
        products = output.find_all('div', {'class': 'product-recommendations__item js--product-recommendations__item js-product-tile'})

        # Stores particular details in array
        for product in products:
            link = product.find('a')
            product_item = {
                    "name":link["title"],
                    "pid":product["data-itemid"],
                    "price":product.find('meta', {'itemprop': 'price'})["content"]+"€",
                    "image":product.find('img')["src"],
                    "image":f"https://imageresize.24i.com/?w=300&url={product.find('img')['src']}",
                    "url":link["href"]
                    }
            items.append(product_item)

        self.logger.info(msg=f'[{SITE}] Successfully scraped {len(self.pids)} pids')
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

                # Makes request to query-site and stores products 
                items = self.scrape_site()
                for product in items:
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

                self.logger.info(msg=f'[{SITE}] Checked all pids in {time.time()-startTime} seconds')

                time.sleep(self.delay)

            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                time.sleep(5)