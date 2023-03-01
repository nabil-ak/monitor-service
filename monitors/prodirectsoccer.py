from threading import Thread, Event
from bs4 import BeautifulSoup
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
import time
import json
import loggerfactory
import traceback
import urllib3
import webhook
import tls
import threadrunner

SITE = __name__.split(".")[1]

class prodirectsoccer(Thread):
    def __init__(self, groups, settings):
        Thread.__init__(self)
        self.daemon = True
        self.groups = groups
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.querys= settings["query"]
        self.blacksku = settings["blacksku"]
        self.firstScrape = True
        self.stop = Event()
        self.logger = loggerfactory.create(SITE)

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, pid, url, thumbnail, price):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        fields.append({"name": "Price", "value": f"{price}£", "inline": True})
        fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
        fields.append({"name": "Status", "value": f"**New Add**", "inline": True})
        
        webhook.send(group=group, webhook=group[SITE], site=f"{SITE}", title=title, url=url, thumbnail=thumbnail, fields=fields, logger=self.logger)


    def scrape_site(self, query):
        """
        Scrapes the specified prodirectsoccer query site and adds items to array
        """
        items = []

        #Page Counter
        page = 1

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': CHROME_USERAGENT,
        }

        #Scrape all available Pages
        while True:
            # Makes request to site
            html = tls.get(f"https://www.prodirectsoccer.com/search/?qq={query}&pg={page}",  headers=headers, proxies=self.proxys.next())
            html.raise_for_status()

            output = BeautifulSoup(html.text, 'html.parser')
            products = output.find_all('a', {'class': 'product-thumb__link'})
            if not products:
                break

            # Stores particular details in array
            for product in products:
                info = json.loads(product["data-gtmi"])
                product_item = {
                        "name":info["name"],
                        "pid":info["id"],
                        "price":info["price"],
                        "image":product.find('img')["data-src"],
                        "url":product["href"]
                        }
                items.append(product_item)

            page+=1
        
        self.logger.info(msg=f'[{SITE}] Successfully scraped Query {query}')
        return items
        

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {SITE} MONITOR')
        
        while not self.stop.is_set():
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
                            self.stop.wait(self.delay/len(self.querys))
                    
                self.INSTOCK = products


                # Allows changes to be notified
                self.firstScrape = False

                self.logger.info(msg=f'[{SITE}] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                self.stop.wait(5)