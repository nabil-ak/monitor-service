from threading import Thread
from datetime import datetime
from timeout import timeout
from proxymanager import ProxyManager
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import os



class asos:
    def __init__(self,groups,region,currency,user_agents,skus,proxymanager,delay=1):
        self.INSTOCK = []
        self.groups = groups
        self.region = region
        self.currency = currency
        self.user_agents = user_agents
        self.skus = skus
        self.proxys = proxymanager
        self.delay = delay
        self.proxytime = 0
        self.timeout = timeout()

    def discord_webhook(self,group,sku,store,title, url, thumbnail,prize, sizes):
            """
            Sends a Discord webhook notification to the specified webhook URL
            """
            if "asos" not in group:
                return

            fields = []
            fields.append({"name": "Prize", "value": f"```{prize}```", "inline": True})
            fields.append({"name": "Base SKU", "value": f"```{sku}```", "inline": True})
            fields.append({"name": "Region", "value": f"```{store}```", "inline": True})

            variantsSTR = "\n"
            statusSTR = ""
            for size in sizes:
                variantsSTR+=str(size['id'])+"\n"
                statusSTR+=f"{'🟢 HIGH' if not size['isLowInStock'] else '🟡 LOW'}\n"
            fields.append({"name": "Variants", "value": f"```{variantsSTR}```", "inline": True})
            fields.append({"name": "Status", "value": f"```{statusSTR}```", "inline": True})

            links = {"name": "Links", 
            "value": f"[NL](https://www.asos.com/nl/nabil/prd/{sku}) - [DE](https://www.asos.com/de/nabil/prd/{sku}) - [FR](https://www.asos.com/fr/nabil/prd/{sku}) - [IT](https://www.asos.it/p/nabil/nabil-{sku}) - [GB](https://www.asos.com/gb/nabil/prd/{sku}) - [ES](https://www.asos.com/es/nabil/prd/{sku}) - [PT](https://www.asos.com/pt/nabil/prd/{sku})", "inline": False}
            fields.append(links)

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
                    "name": "Asos"
                }
                }
                ]
            }
            
            
            result = rq.post(group["asos"], data=json.dumps(data), headers={"Content-Type": "application/json"})
            
            try:
                result.raise_for_status()
            except rq.exceptions.HTTPError as err:
                logging.error(err)
                print(f"[Asos {self.region}] Exception found: {err}")
            else:
                logging.info(msg=f'[Asos {self.region}] Successfully sent Discord notification to {group["asos"]}')
                print(f'[Asos {self.region}] Successfully sent Discord notification to {group["asos"]}')

    def getTitle(self, sku):
        """
        Get the title of a product that belongs to a specific sku
        """
        for product in self.skus:
            if sku == product["sku"]:
                return product["title"]

    def scrape_site(self,url,headers):
        """
        Scrapes the specified Asos site and adds items to array
        """
        items = []
    
        html = rq.get(url, proxies=self.proxys.next(), headers=headers, timeout=10)
        products = html.json()
        
        # Stores particular details in array
        for product in products:
            #Format each Product
            product_item = {
                'title': self.getTitle(str(product['productId'])), 
                'image': f"{os.environ['IMAGEPROXY']}/https://images.asos-media.com/products/nabil/{product['productId']}-2", 
                'id': str(product['productId']),
                'variants': product['variants']}
            items.append(product_item)
        
        
        logging.info(msg=f'[Asos {self.region}] Successfully scraped site')
        return items

    def remove(self,id):
        """
        Remove all Products from INSTOCK with the same id
        """
        for elem in self.INSTOCK:
            if id == elem[2]:
                self.INSTOCK.remove(elem)

    def checkUpdated(self,product):
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
        product_item = [product['title'], product['image'], product['id']]

        # Collect all available sizes
        available_sizes = []

        for size in product['variants']:
            if size['isInStock']: # Check if size is instock
                available_sizes.append(size)
        
        product_item.append(available_sizes) # Appends in field
        
        if available_sizes:
            ping, updated = self.checkUpdated(product_item)
            if updated or start == 1:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if start == 0:
                    print(f"[Asos {self.region}] {product_item[:-1]}")
                    logging.info(msg=f"[Asos {self.region}] {product_item}")

                    if ping and self.timeout.ping(product_item):
                        for group in self.groups:
                            #Send Ping to each Group
                            Thread(target=self.discord_webhook,args=(
                                group,
                                product['id'],
                                self.region,
                                product['title'],
                                f"https://www.asos.com/{self.region}/nabil/prd/{product['id']}",
                                product['image'],
                                str(product['variants'][0]['price']['current']['text']),
                                available_sizes
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
        logging.basicConfig(filename=f'logs/asos-{self.region}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)


        print(f'STARTING Asos {self.region} MONITOR')
        logging.info(msg=f'[Asos {self.region}] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}
    
        while True:
            try:
                startTime = time.time()
                url = f"https://www.asos.com/api/product/catalogue/v3/stockprice?productIds={(''.join([sku['sku']+',' for sku in self.skus]))[:-1]}&store={self.region}&currency={self.currency}&keyStoreDataversion=dup0qtf-35&cache={random.randint(10000,999999999)}"
    

                # Makes request to site and stores products 
                items = self.scrape_site(url, headers)
                for product in items:
                    self.comparitor(product, start)

                # Allows changes to be notified
                start = 0
                
                logging.info(msg=f'[Asos {self.region}] Checked in {time.time()-startTime} seconds')

                # User set delay
                time.sleep(float(self.delay))


            except Exception as e:
                print(f"[Asos {self.region}] Exception found: {traceback.format_exc()}")
                logging.error(e)

                #Rotate user_agent
                headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "asos":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    STORES = [["DE",139],["CH",431],["FR",658],["ES",670],["IT",671],["PL",550],["CZ",554],["SK",586],["NL",545],["BE",558]]
    logging.basicConfig(filename=f'asos.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    for store in STORES:
        a = asos(groups=[devgroup],keywords=[],delay=0.1,store=store[0],storeid=store[1],
        user_agent=[{"user_agent":""}])
        Thread(target=a.monitor).start()
