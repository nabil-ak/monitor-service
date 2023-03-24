from threading import Thread, Event
from multiprocessing import Process
from timeout import timeout
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
import quicktask as qt
import random
import time
import json
import loggerfactory
import traceback
import urllib3
import tls
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class aboutyou(Process):
    def __init__(self, groups, settings, store, storeid):
        Process.__init__(self)
        self.INSTOCK = []
        self.groups = groups
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.keywords = settings["keywords"]
        self.blacksku = settings["blacksku"]
        self.whitesku = settings["whitesku"]
        self.store = store
        self.storeid = storeid
        self.timeout = timeout()
        self.firstScrape = True
        self.stop = Event()
        self.logger = loggerfactory.create(f"{SITE}_{self.store}")

    def discord_webhook(self, group, pid, title, url, thumbnail, price, sizes, stock):
            """
            Sends a Discord webhook notification to the specified webhook URL
            """

            fields = []
            fields.append({"name": "Price", "value": f"{price} €", "inline": True})
            fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
            fields.append({"name": "Region", "value": f"{self.store}", "inline": True})

            sizesSTR = "\n"
            stockSTR = ""
            for size in sizes:
                sizesSTR+=f"{size}\n"
                stockSTR+=f"{stock[size]}\n"
            fields.append({"name": "Sizes", "value": f"{sizesSTR}", "inline": True})
            fields.append({"name": "Stock", "value": f"{stockSTR}", "inline": True})


            fields.append({
                "name": "Links", 
                "value": f"[CH](https://www.aboutyou.ch/p/nabil/nabil-{pid}) - [CZ](https://www.aboutyou.cz/p/nabil/nabil-{pid}) - [DE](https://www.aboutyou.de/p/nabil/nabil-{pid}) - [FR](https://www.aboutyou.fr/p/nabil/nabil-{pid}) - [IT](https://www.aboutyou.it/p/nabil/nabil-{pid}) - [PL](https://www.aboutyou.pl/p/nabil/nabil-{pid}) - [SK](https://www.aboutyou.sk/p/nabil/nabil-{pid}) - [ES](https://www.aboutyou.es/p/nabil/nabil-{pid}) - [NL](https://www.aboutyou.nl/p/nabil/nabil-{pid}) - [BE](https://www.aboutyou.nl/p/nabil/nabil-{pid})", 
                "inline": False})

            fields.append({"name": "Quicktasks", "value": f"{qt.adonis(site='AboutYou', link=pid)} - {qt.koi(site='AboutYou', link=pid)} - {qt.loscobot(site='AboutYou', link=pid)} - {qt.panaio(site='AboutYou', link=pid)}", "inline": True})

            webhook.send(group=group, webhook=group[SITE], site=f"{SITE}_{self.store}", title=title, url=url, thumbnail=thumbnail, fields=fields, logger=self.logger)


    def scrape_site(self):
        """
        Scrapes the specified About You site and adds items to array
        """

        """
        Brands:
        53709 = Nike Sportwear
        61263 = Jordan

        Categorys:
        20727 = Women Sneakers
        21014 = Men Sneakers
        20207,20215 = Men and Women Shoes
        190025 = Boys GS
        189974 = Boys PS
        189879 = Girls GS
        189823 = Girls PS
        """
        url = f"https://api-cloud.aboutyou.de/v1/products?with=attributes:key(brand|name),variants,variants.attributes:key(vendorSize)&filters[category]=20727,21014,20207,20215,190025,189974,189879,189823&filters[brand]=61263,53709&filters[excludedFromBrandPage]=false&sortDir=desc&sortScore=brand_scores&sortChannel=web_default&page=1&perPage={random.randint(2000, 50000)}&forceNonLegacySuffix=true&shopId={self.storeid}"

        items = []
    
        html = tls.get(url, proxies=self.proxys.next(), headers={"user-agent":CHROME_USERAGENT})
        output = json.loads(html.text)['entities']
        
    
        for product in output:
            product_item = {
                'title': product['attributes']['brand']['values']['label']+" "+product['attributes']['name']['values']['label'], 
                'image': "https://cdn.aboutstatic.com/file/"+product['images'][0]['hash'] if "images" in product['images'][0]['hash'] else "https://cdn.aboutstatic.com/file/images/"+product['images'][0]['hash'], 
                'id': product['id'],
                'variants': product['variants']}
            items.append(product_item)
        
        
        self.logger.info(msg=f'[{SITE}_{self.store}] Successfully scraped all categorys')
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
            #Check if product is not changed
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
        # Stock of every Size
        stocks = {}
        for size in product['variants']:
            if size['stock']['quantity'] > 0 or size['stock']['isSellableWithoutStock']: # Check if size is instock
                available_sizes.append(size['attributes']['vendorSize']['values']['label'])
                stocks[size['attributes']['vendorSize']['values']['label']] = size['stock']['quantity']
        
        product_item.append(available_sizes)
        
        if available_sizes:
            ping, updated = self.checkUpdated(product_item)
            if updated or self.firstScrape:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if ping and self.timeout.ping(product_item) and not self.firstScrape:
                    print(f"[{SITE}_{self.store}] {product_item[0]} got restocked")
                    self.logger.info(msg=f"[{SITE}_{self.store}] {product_item[0]} got restocked")
                    for group in self.groups:
                        #Send Ping to each Group
                        threadrunner.run(
                            self.discord_webhook,
                            group=group,
                            pid=product['id'],
                            title=product['title'],
                            url=f"https://www.aboutyou.{self.store}/p/nabil/nabil-{product['id']}",
                            thumbnail=product['image'],
                            price=str(product['variants'][0]['price']['withTax']/100),
                            sizes=available_sizes,
                            stock=stocks,
                        )
        else:
            # Remove old version of the product
            self.remove(product_item[2])

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {SITE} {self.store} MONITOR')

        while not self.stop.is_set():
            try:
                startTime = time.time()

                # Makes request to site and stores products 
                items = self.scrape_site()
                for product in items:
                    if int(product['id']) not in self.blacksku:
                        if len(self.keywords) == 0 or int(product['id']) in self.whitesku:
                            # If no keywords set or sku is whitelisted, checks whether item status has changed
                            self.comparitor(product)

                        else:
                            # For each keyword, checks whether particular item status has changed
                            for key in self.keywords:
                                if key.lower() in product['title'].lower():
                                    self.comparitor(product)

                # Allows changes to be notified
                self.firstScrape = False
                
                self.logger.info(msg=f'[{SITE}_{self.store}] Checked in {time.time()-startTime} seconds')

                # User set delay
                self.stop.wait(float(self.delay))


            except Exception as e:
                print(f"[{SITE}_{self.store}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                self.stop.wait(3)