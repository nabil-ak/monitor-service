from multiprocessing import Process
from datetime import datetime
from timeout import timeout
from multiprocessing.pool import ThreadPool 
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
import quicktask as qt
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class shopify(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.site = settings["name"]
        self.url = settings["url"]
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["url"]
        self.keywords= settings["keywords"]
        self.negativkeywords = settings["negativkeywords"]
        self.tags = settings["tags"]
        self.blacksku = settings["blacksku"]
        self.firstScrape = True

        self.INSTOCK = []
        self.timeout = timeout()
        
    def discord_webhook(self, group, title, pid, url, thumbnail, price, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        
        if self.site in group:
            if len(group[self.site]) == 0:
                return
            webhookurl = group[self.site]
        elif "shopify" in group:
            webhookurl = group["shopify"]

        fields = []
        fields.append({"name": "Price", "value": f"{price}", "inline": True})
        fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
        fields.append({"name": "Stock", "value": f"{str(len(sizes))}+", "inline": True})

        i = 0
        for _ in range((len(sizes)//7)+(1 if len(sizes)%7 != 0 else 0)):
            sizesString = ""
            for size in sizes[:i+7]:
                sizesString+=f"{size['url']} | {size['title']}\n"
                i+=1
            fields.append({"name": f"ATC | Size", "value": sizesString, "inline": True})
            sizes = sizes[i:]

        fields.append({"name": "Quicktasks", "value": f"{qt.cybersole(link=url)} - {qt.adonis(site='shopify', link=url)} - {qt.thunder(site='shopify', link=url)} - {qt.panaio(site='Shopify', link=url)}", "inline": False})

        webhook.send(group=group, webhook=webhookurl, site=f"{self.site}", title=title, url=url, thumbnail=thumbnail, fields=fields)


    def scrape_site(self, page):
        """
        Scrapes the specified Shopify site and adds items to array
        """
        items = []

        #Fetch the Shopify-Page
        html = rq.get(self.url + f'?page={page}&limit={random.randint(251,1000000)}', headers={"user-agent":CHROME_USERAGENT}, proxies=self.proxys.next())
        html.raise_for_status()
        output = json.loads(html.text)['products']
        
        # Stores particular details in array
        for product in output:
            product_item = {
                'title': product['title'], 
                'image': product['images'][0]['src'] if product['images'] else "", 
                'handle': product['handle'],
                'variants': product['variants'],
                'tags':product['tags']
                }
            items.append(product_item)
        
        logging.info(msg=f'[{self.site}] Successfully scraped Page {page}')
        return items

    def remove(self, handle):
        """
        Remove all Products from INSTOCK with the same handle
        """
        for elem in self.INSTOCK:
            if handle == elem[2]:
                self.INSTOCK.remove(elem)

    def updated(self, product):
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


    def comparitor(self,product):
        product_item = [product['title'], product['image'], product['handle']]

        # Collect all available sizes
        available_sizes = []
        for size in product['variants']:
            if size['available']: # Makes an ATC link from the variant ID
                available_sizes.append({'title': size['title'], 'url': '[ATC](' + self.url[:self.url.find('/', 10)] + '/cart/' + str(size['id']) + ':1)'})

        
        product_item.append(available_sizes)
        
        if available_sizes:
            ping, updated = self.updated(product_item)
            if updated or self.firstScrape:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if not self.firstScrape:
                    print(f"[{self.site}] {product_item[0]} got restocked")
                    logging.info(msg=f"[{self.site}] {product_item[0]} got restocked")

                    if ping and self.timeout.ping(product_item):
                        for group in self.groups:
                            #Send Ping to each Group
                            threadrunner.run(
                                self.discord_webhook,
                                group=group,
                                title=product["title"],
                                pid=product['handle'],
                                url=self.url.replace('.json', '/') + product['handle'],
                                thumbnail=product['image'],
                                price=product['variants'][0]['price']+" €",
                                sizes=available_sizes,
                            )
        else:
            # Remove old version of the product
            self.remove(product_item[2])

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/{self.site}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING {self.site} MONITOR')

        maxpage = 20
        
        while True:
            try:
                startTime = time.time()

                args = []
                for page in range(1,maxpage):
                    args.append((page,))

                # Makes request to the pages and stores products 
                with ThreadPool(maxpage) as threadpool:
                    itemsSplited = threadpool.starmap(self.scrape_site, args)

                    items = sum(itemsSplited, [])

                    for product in items:
                            if product["handle"] not in self.blacksku and not any([key in product["handle"] for key in self.negativkeywords]):
                                if len(self.keywords) == 0 and len(self.tags) == 0:
                                    # If no keywords and tags set, checks whether item status has changed
                                    self.comparitor(product)

                                else:
                                    # For each keyword, checks whether particular item status has changed
                                    for key in self.keywords:
                                        if key.lower() in product['title'].lower():
                                            self.comparitor(product)

                                    # For each tag, checks whether particular item status has changed
                                    for tag in self.tags:
                                        if tag in product['tags']:
                                            self.comparitor(product)


                    logging.info(msg=f'[{self.site}] Checked in {time.time()-startTime} seconds')
                    

                    self.firstScrape = False

                    #Check if maxpage is reached otherwise increase by 5
                    try:
                        maxpage = itemsSplited.index([])+2
                    except:
                        maxpage+=5
                        start = 1

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[{self.site}] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(3)