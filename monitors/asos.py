from timeout import timeout
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
from threading import Thread, Event
from multiprocessing import Process
import random
import requests as rq
import quicktask as qt
import time
import loggerfactory
import traceback
import urllib3
import os
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class asos(Process):
    def __init__(self, groups, settings, region, currency):
        Thread.__init__(self)
        self.daemon = True
        self.INSTOCK = []
        self.groups = groups
        self.region = region
        self.currency = currency
        self.pids = settings["skus"]
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.timeout = timeout()
        self.firstScrape = True
        self.stop = Event()
        self.logger = loggerfactory.create(f"{SITE}_{self.region}")

    def discord_webhook(self, group, pid, region, title, url, thumbnail, price, sizes):
            """
            Sends a Discord webhook notification to the specified webhook URL
            """

            if f"{SITE}_{self.region}" in group:
                webhookurl = group[f"{SITE}_{self.region}"]
            elif "asos" in group:
                webhookurl = group["asos"]

            fields = []
            fields.append({"name": "Price", "value": f"{price}", "inline": True})
            fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
            fields.append({"name": "Region", "value": f"{region}", "inline": True})

            variantsSTR = "\n"
            statusSTR = ""
            for size in sizes:
                variantsSTR+=str(size['id'])+"\n"
                statusSTR+=f"{'**HIGH**' if not size['isLowInStock'] else 'LOW'}\n"
            fields.append({"name": "Variants", "value": f"{variantsSTR}", "inline": True})
            fields.append({"name": "Status", "value": f"{statusSTR}", "inline": True})

            fields.append({"name": "Links", 
            "value": f"[NL](https://www.asos.com/nl/nabil/prd/{pid}) - [DE](https://www.asos.com/de/nabil/prd/{pid}) "+
            f"- [FR](https://www.asos.com/fr/nabil/prd/{pid}) - [IT](https://www.asos.it/p/nabil/nabil-{pid}) - [GB](https://www.asos.com/gb/nabil/prd/{pid}) "+
            f"- [ES](https://www.asos.com/es/nabil/prd/{pid}) - [PT](https://www.asos.com/pt/nabil/prd/{pid})", "inline": False})

            fields.append({"name": "Quicktasks", "value": f"{qt.adonis(site='asos', link=pid)} - {qt.koi(site='ASOS', link=pid)} - {qt.storm(site='asos', link=pid)} - {qt.panaio(site='Asos', link=pid)} - {qt.thunder(site='Asos', link=pid)}", "inline": True})

            webhook.send(group=group, webhook=webhookurl, site=f"{SITE}_{self.region}", title=title, url=url, thumbnail=thumbnail, fields=fields, logger=self.logger)
            

    def getTitle(self, pid):
        """
        Get the title of a product that belongs to a specific pid
        """
        for product in self.pids:
            if pid == product["sku"]:
                return product["title"]

    def scrape_site(self, url):
        """
        Scrapes the specified Asos site and adds items to array
        """
        items = []
    
        html = rq.get(url, proxies=self.proxys.next(), headers={"user-agent":CHROME_USERAGENT})
        products = html.json()
        
        for product in products:
            product_item = {
                'title': self.getTitle(str(product['productId'])), 
                'image': f"{os.environ['IMAGEPROXY']}?url=https://images.asos-media.com/products/nabil/{product['productId']}-2&proxy={','.join(self.proxys.proxygroups)}", 
                'id': str(product['productId']),
                'variants': product['variants']}
            items.append(product_item)
        
        self.logger.info(msg=f'[{SITE}_{self.region}] Successfully scraped all pids')
        return items

    def remove(self, id):
        """
        Remove all Products from INSTOCK with the same id
        """
        for elem in self.INSTOCK:
            if id == elem[2]:
                self.INSTOCK.remove(elem)

    def checkUpdated(self, product):
        """
        Check if the Variants got updated
        """
        for elem in self.INSTOCK:
            #Check if Product was not changed
            if product[2] == elem[2] and product[3] == elem[3]:
                return [False,False]
                
            #Dont ping if no new size was added
            if product[2] == elem[2] and len(product[3]) <= len(elem[3]):
                if all(size in elem[3] for size in product[3]):
                    return [False,True]

        return[True,True]


    def comparitor(self, product):
        product_item = [product['title'], product['image'], product['id']]

        # Collect all available sizes
        available_sizes = []

        for size in product['variants']:
            if size['isInStock']: # Check if size is instock
                available_sizes.append(size)
        
        product_item.append(available_sizes) # Appends in field
        
        if available_sizes:
            ping, updated = self.checkUpdated(product_item)
            if updated or self.firstScrape:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if ping and self.timeout.ping(product_item) and not self.firstScrape:
                    print(f"[{SITE}_{self.region}] {product_item[0]} got restocked")
                    self.logger.info(msg=f"[{SITE}_{self.region}] {product_item[0]} got restocked")
                    for group in self.groups:
                        #Send Ping to each Group
                        threadrunner.run(
                            self.discord_webhook,
                            group=group,
                            pid=product['id'],
                            region=self.region,
                            title=product['title'],
                            url=f"https://www.asos.com/{self.region}/nabil/prd/{product['id']}",
                            thumbnail=product['image'],
                            price=str(product['variants'][0]['price']['current']['text']),
                            sizes=available_sizes
                        )
        else:
            # Remove old version of the product
            self.remove(product_item[2])

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {SITE}_{self.region} MONITOR')


        while not self.stop.is_set():
            try:
                startTime = time.time()
                url = f"https://www.asos.com/api/product/catalogue/v3/stockprice?productIds={(''.join([pid['sku']+',' for pid in self.pids]))[:-1]}&store={self.region}&currency={self.currency}&keyStoreDataversion=dup0qtf-35&cache={random.randint(10000,999999999)}"
    

                # Makes request to site and stores products 
                items = self.scrape_site(url)
                for product in items:
                    self.comparitor(product)

                # Allows changes to be notified
                self.firstScrape = False
                
                self.logger.info(msg=f'[{SITE}_{self.region}] Checked in {time.time()-startTime} seconds')

                # User set delay
                self.stop.wait(float(self.delay))


            except Exception as e:
                print(f"[{SITE}_{self.region}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                self.stop.wait(3)