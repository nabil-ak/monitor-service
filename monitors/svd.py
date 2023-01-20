from multiprocessing import Process
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
from multiprocessing.pool import ThreadPool 
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import os
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class svd(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.delay = settings["delay"]
        self.keywords= settings["keywords"]
        self.proxys = ProxyManager(settings["proxys"])
        self.blacksku = settings["blacksku"]
        self.firstScrape = True

        self.INSTOCK = {}
        
    def discord_webhook(self, group, title, sku, url, thumbnail, price):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        fields.append({"name": "Price", "value": f"{price}", "inline": True})
        fields.append({"name": "Sku", "value": f"{sku}", "inline": True})
        fields.append({"name": "Status", "value": f"**New Add**", "inline": True})
        
        webhook.send(group=group, webhook=group[SITE], site=f"{SITE}", title=title, url=url, thumbnail=thumbnail, fields=fields)


    def scrape_site(self, category):
        """
        Scrapes the specified svd query site and adds items to array
        """
        items = []

        url = f"https://www.sivasdescalzo.com/graphql?query=query%20categoryV2(%24id%3A%20Int!%2C%20%24pageSize%3A%20Int!%2C%20%24currentPage%3A%20Int!%2C%20%24filters%3A%20ProductAttributeFilterInput!%2C%20%24sort%3A%20ProductAttributeSortInput)%20%7B%0A%20%20category(id%3A%20%24id)%20%7B%0A%20%20%20%20name%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20products(pageSize%3A%20%24pageSize%2C%20currentPage%3A%20%24currentPage%2C%20filter%3A%20%24filters%2C%20sort%3A%20%24sort)%20%7B%0A%20%20%20%20items%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20brand_name%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20sku%0A%20%20%20%20%20%20small_image%20%7B%0A%20%20%20%20%20%20%20%20url%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20url%0A%20%20%20%20%20%20original_price%0A%20%20%20%20%20%20final_price%0A%20%20%20%20%20%20percent_off%0A%20%20%20%20%20%20state%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20aggregations%20%7B%0A%20%20%20%20%20%20attribute_code%0A%20%20%20%20%20%20label%0A%20%20%20%20%20%20count%0A%20%20%20%20%20%20options%20%7B%0A%20%20%20%20%20%20%20%20label%0A%20%20%20%20%20%20%20%20value%0A%20%20%20%20%20%20%20%20count%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20page_info%20%7B%0A%20%20%20%20%20%20total_pages%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20total_count%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=categoryV2&variables=%7B%22currentPage%22%3A1%2C%22id%22%3A4089%2C%22filters%22%3A%7B%22brand%22%3A%7B%22in%22%3A%5B%22Jordan%22%2C%22Nike%22%2C%22New%20Balance%22%5D%7D%2C%22category_id%22%3A%7B%22eq%22%3A%22{category}%22%7D%7D%2C%22pageSize%22%3A1000%2C%22sort%22%3A%7B%22sorting_date%22%3A%22DESC%22%7D%7D"

        # Makes request to site
        html = rq.get(url, headers={
                'user-agent': CHROME_USERAGENT
        }, proxies=self.proxys.next())
        html.raise_for_status()
        products = json.loads(html.text)['data']['products']['items']

        # Stores particular details in array
        for product in products:
            product_item = {
                    "name":product["brand_name"]+" "+product["name"],
                    "sku":product["sku"],
                    "price":str(product["final_price"])+" €",
                    'image': f"{os.environ['IMAGEPROXY']}?url=https://media.sivasdescalzo.com/media/catalog/product/{product['small_image']['url']}?width=300&proxy={','.join(self.proxys.proxygroups)}",
                    "url":"https://www.sivasdescalzo.com"+product["url"] if "sivasdescalzo" not in product["url"] else product["url"],
                    "state":product["state"]
                    }
            items.append(product_item)

        
        logging.info(msg=f'[{SITE}] Successfully scraped category {category}')
        return [category,items]
        

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/{SITE}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING {SITE} MONITOR')
    
        #Initialise categorys and instock items for each category
        # 4089 = Sneakers (https://www.sivasdescalzo.com/en/footwear/sneakers)
        # 2900 = New Arrivals (https://www.sivasdescalzo.com/en/new-arrivals)
        # 2513(REMOVED) = Adidas Yeezy (https://www.sivasdescalzo.com/en/brands/adidas/yeezy)
        # 2479 = Adidas (https://www.sivasdescalzo.com/en/brands/adidas)
        # 3558 = Jordan Sneakers (https://www.sivasdescalzo.com/en/brands/jordan/sneakers)
        # 2552 = Jordan (https://www.sivasdescalzo.com/en/brands/jordan)
        # 3473 = Nike Sneakers(https://www.sivasdescalzo.com/en/brands/nike/sneakers)
        # 2572 = Nike (https://www.sivasdescalzo.com/en/brands/nike)
        # 33 = Footwear (https://www.sivasdescalzo.com/en/footwear)
        categorys = [4089,2900,2479,3558,2552,3473,2572,33]
        for c in categorys:
            self.INSTOCK[c] = []
        
        while True:
            try:
                startTime = time.time()

                # Makes request to each category
                with ThreadPool(len(categorys)) as threadpool:
                    args = [(c,) for c in categorys]
                    itemsSplited = threadpool.starmap(self.scrape_site, args)

                    for c, items in itemsSplited:
                        products = []

                        for product in items:
                            if product["sku"] not in self.blacksku and product["state"] not in ["Sold Out", "Raffle"] and len(product["sku"]) > 1:
                                #Check for Keywords
                                if self.keywords and not any(key.lower() in product["name"].lower() for key in self.keywords):
                                    continue

                                # Check if Product is INSTOCK
                                if not any([product["sku"] in cat for cat in self.INSTOCK.values()]) and not self.firstScrape:
                                        print(f"[{SITE}] {product['name']} got restocked")
                                        logging.info(msg=f"[{SITE}] {product['name']} got restocked")
                                        for group in self.groups:
                                            #Send Ping to each Group
                                            threadrunner.run(
                                                self.discord_webhook,
                                                group=group,
                                                title=product['name'],
                                                sku=product['sku'],
                                                url=product['url'],
                                                thumbnail=product['image'],
                                                price=product['price']
                                                )
                                products.append(product["sku"])

                        self.INSTOCK[c] = products

                # Allows changes to be notified
                self.firstScrape = False

                logging.info(msg=f'[{SITE}] Checked all querys in {time.time()-startTime} seconds')

                time.sleep(self.delay)

            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(3)