from threading import Thread
from datetime import datetime
from timeout import timeout 
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import numpy

class zalando:
    def __init__(self,groups,user_agents,blacksku=[],delay=1,keywords=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.blacksku = blacksku
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxys
        self.proxytime = 0
        self.INSTOCK = []
        self.timeout = timeout()
        
    def discord_webhook(self,group,sku,title, url, thumbnail, prize, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "zalando" not in group:
            return

        fields = []
        fields.append({"name": "[ PRIZE ]", "value": prize, "inline": True})
        fields.append({"name": "[ SKU ]", "value": sku, "inline": True})
        fields.append({"name": "[ STOCK ]", "value": str(len(sizes))+"+", "inline": True})
        fields.append({"name": "[ SIZES ]", "value": "⠀", "inline": False})
        for size in sizes:
            fields.append({"name": size['size'], "value": f"`{size['sku']}`", "inline": True})
        fields.append({"name": "[ Links ]", 
            "value": f"[CH](https://zalando.ch/home/?q={sku}) - [CZ](https://zalando.cz/home/?q={sku}) - [DE](https://zalando.de/home/?q={sku}) - [FR](https://zalando.fr/home/?q={sku}) - [IT](https://zalando.it/home/?q={sku}) - [PL](https://zalando.pl/home/?q={sku}) - [SK](https://zalando.sk/home/?q={sku}) - [ES](https://zalando.es/home/?q={sku}) - [NL](https://zalando.nl/home/?q={sku}) - [BE](https://zalando.be/home/?q={sku}) - [UK](https://zalando.uk/home/?q={sku})", "inline": False})
        
        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": url, 
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
            "author": {
                "name": "Zalando"
            }
            }]
        }
        
        
        result = rq.post(group["zalando"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[Zalando] Exception found: {err}")
        else:
            logging.info(msg=f'[Zalando] Successfully sent Discord notification to {group["zalando"]}')
            print(f'[Zalando] Successfully sent Discord notification to {group["zalando"]}')


    def scrape_site(self, headers, proxy, women = False):
        """
        Scrapes the specified Shopify site and adds items to array
        """

        # Makes request to site
        s = rq.Session()

        #Body of request
        data = [
            {
                "id": "e368030e65564d6a0b7329ac40b16870dddca3b404c3c86ee29b34c465cd2e04",
                "variables": {
                    "id": "ern:collection:cat:categ:herrenschuhe-sneaker",
                    "orderBy": "POPULARITY",
                    "filters": {
                        "discreteFilters": [
                            {
                                "key": "brands",
                                "options": ["ADID", "JOC", "NE2", "NI1"]
                            }
                        ],
                        "rangeFilters": [],
                        "toggleFilters": []
                    },
                    "after": "WzEsNTM5MzY1MjcxXQ==",
                    "first": 1000,
                    "uri": "/herrenschuhe-sneaker/adidas.jordan.nike-sportswear/",
                    "isPaginationRequest": True,
                    "isFDBEDisabled": True,
                    "width": 2079,
                    "height": 1000,
                    "notLoggedIn": True,
                    "disableTopTeasers": False,
                    "disableInCatalogTeasers": False
                }
            }
        ]

        #Check if the Women Page is needed
        if women:
            data[0]["variables"]["id"] = "ern:collection:cat:categ:damenschuhe-sneaker"
            data[0]["variables"]["after"] = "WzEsODk3MDMyOTQ3XQ=="
            data[0]["variables"]["uri"] = "/damenschuhe-sneaker/adidas.jordan.nike-sportswear/"

        #SKUs for size request
        skus = []

        #Url
        URL = "https://www.zalando.de/api/graphql/"

        
        currentpage = 1
        lastpage = 2
        a = time.time()
        while currentpage != lastpage:
            r = s.post(URL, headers=headers, json=data, proxies=proxy, verify=False, timeout=15)
            ent = r.json()[0]["data"]["collection"]["entities"]
            for edge in ent["edges"]:
                skus.append({"id":"42065a950350321d294bf6f0d60a2267042fe634956f00ef63a0a43c0db7dc38","variables":{"id":edge["node"]["id"],"skipHoverData":False}})
            data[0]["variables"]["after"] = ent["pageInfo"]["endCursor"]
            currentpage = ent["pageInfo"]["currentPage"]
            lastpage = ent["pageInfo"]["numberOfPages"]
        logging.info(msg=f"first api {time.time()-a}")
        #Split SKUS because second API Call only accepts 110 Skus at once
        skus = numpy.array_split(skus,(len(skus)//100)+1)

        output = []
        b = time.time()
        for skupart in skus:
            r = s.post(URL, headers=headers, json=skupart.tolist(), proxies=proxy, verify=False, timeout=15)
            for elem in r.json():
                output.append(elem['data']['product'])
        logging.info(msg=f"second api {time.time()-b}")
        items = []
        # Stores particular details in array
        for product in output:
            if product == None:
                continue
            product_item = {
                'title': product['brand']['name'] + " " + product['name'], 
                'image': product['smallDefaultMedia']['uri'], 
                'sku': product['sku'],
                'variants': product['simples'],
                'url':product['uri'],
                'prize':product['displayPrice']['original']['formatted']
            }
            items.append(product_item)
        
        logging.info(msg=f'[Zalando] Successfully scraped site')
        s.close()
        return items

    def remove(self,handle):
        """
        Remove all Products from INSTOCK with the same handle
        """
        for elem in self.INSTOCK:
            if handle == elem[2]:
                self.INSTOCK.remove(elem)

    def updated(self,product):
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


    def comparitor(self,product, start):
        product_item = [product['title'], product['image'], product['sku']]

        product_item.append(product['variants']) # Appends in field
        
        if product['variants']:
            ping, updated = self.updated(product_item)
            if updated or start == 1:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if start == 0:
                    print(f"[Zalando] {product_item}")
                    logging.info(msg=f"[Zalando] {product_item}")
                    
                    if ping and self.timeout.ping(product_item):
                        for group in self.groups:
                            #Send Ping to each Group
                            print("send webhook")
                            Thread(target=self.discord_webhook,args=(
                                group,
                                product['sku'],
                                product['title'],
                                product['url'],
                                product['image'],
                                product['prize'],
                                product['variants'],
                                )).start()
        else:
            # Remove old version of the product
            self.remove(product_item[2])

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/zalando.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING ZALANDO MONITOR')
        logging.info(msg=f'[Zalando] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = 0
        headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}

        
        while True:
            try:
                proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                startTime = time.time()
                
                women = False
                for _ in range(2):
                    # Makes request to site and stores products 
                    items = self.scrape_site(headers, proxy, women)
                    for product in items:
                        if product["sku"] not in self.blacksku:
                            if len(self.keywords) == 0:
                                # If no keywords set, checks whether item status has changed
                                self.comparitor(product, start)

                            else:
                                # For each keyword, checks whether particular item status has changed
                                for key in self.keywords:
                                    if key.lower() in product['title'].lower():
                                        self.comparitor(product, start)
                    women = True
            

                # Allows changes to be notified
                start = 0

                logging.info(msg=f'[Zalando] Checked in {time.time()-startTime} seconds')

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[Zalando] Exception found: {traceback.format_exc()}")
                logging.error(e)

                # Rotates headers
                headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}

                # Safe time to let the Monitor only use the Proxy for 5 min
                if proxy == {}:
                    self.proxytime = time.time()+300
                
                if len(self.proxys) != 0:
                    # If optional proxy set, rotates if there are multiple proxies
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "zalando":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    s = zalando(groups=[devgroup],user_agents=[{"user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36"}],blacksku=["test"])
    s.monitor()