from threading import Thread, Event
from timeout import timeout
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
import time
import loggerfactory
import traceback
import urllib3
import tls
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class eleventeamsports(Thread):
    def __init__(self, groups, settings):
        Thread.__init__(self)
        self.daemon = True   
        self.groups = groups
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.querys= settings["query"]
        self.blacksku = settings["blacksku"]
        self.proxytime = 0
        self.timeout = timeout(timeout=120, pingdelay=20)
        self.firstScrape = True
        self.stop = Event()
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
        Scrapes the specified eleventeamsports query site and adds items to array
        """
        items = []

        # Makes request to site
        html = tls.get(f"https://www.11teamsports.com/de-de/ds/?type=deep_search&q={query}&limit=10000&offset=0&sort=created+desc", headers={
                'user-agent': CHROME_USERAGENT
        }, proxies=self.proxys.next())
        html.raise_for_status()
        products = html.json()["hits"]["hit"]

        # Stores particular details in array
        for product in products:
            product = product["fields"]

            #Only Ping shoes
            if "Schuhe" in product["category"]:
                product_item = {
                        "name":product["title"],
                        "pid":product["sku"],
                        "price":str(product["price"])+" €",
                        "image":product["media_file"],
                        "url":product["deeplink"]
                        }
                items.append(product_item)

        
        self.logger.info(msg=f'[{SITE}] Successfully scraped query {query}')
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
                
                # Makes request to site and stores products 
                for query in self.querys:

                    items = self.scrape_site(query)

                    for product in items:
                        if product["pid"] not in self.blacksku:
                            # Check if Product is INSTOCK
                            if product["pid"] not in self.INSTOCK and not self.firstScrape and self.timeout.ping(product):
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

                self.firstScrape = False

                self.logger.info(msg=f'[{SITE}] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                self.stop.wait(4)