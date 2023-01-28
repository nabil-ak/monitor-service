from multiprocessing import Process
from timeout import timeout
from proxymanager import ProxyManager
from user_agent import CHROME_USERAGENT
import threadrunner
import tls
import time
import logging
import traceback
import urllib3
import webhook

SITE = __name__.split(".")[1]

class wethenew(Process):
    def __init__(self,groups,endpoint,settings):
        Process.__init__(self)
        self.groups = groups
        self.endpoint = endpoint
        self.blacksku = settings["blacksku"]
        self.delay = settings["delay"]
        self.keywords= settings["keywords"]
        self.auth = settings["auth"]
        self.proxys = ProxyManager(settings["proxys"])
        self.INSTOCK = []
        self.timeout = timeout()
        self.authPointer = -1
        self.firstScrape = True

        self.sizesKey = {
            "products":"wantedSizes",
            "sell-nows":"sellNows",
            "consignment-slots":"sizes"
        }

    def getAuth(self):
        """
        Get a new Auth token
        """
        self.authPointer = 0 if self.authPointer == len(self.auth)-1 else self.authPointer+1 
        return self.auth[self.authPointer]
        
    def discord_webhook(self, group, pid, title, thumbnail, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        if self.endpoint == "sell-nows":
            s = ""
            prices = ""
            links = "\n"
            for size in sizes:
                s+=f"`{size['size']}`\n"
                prices+=f"`{size['price']}€`\n"
                links+=f"[Sell Now](https://sell.wethenew.com/instant-sales/{size['id']})\n"
            fields.append({"name": "Sizes", "value": s, "inline": True})
            fields.append({"name": "Prices", "value": prices, "inline": True})
            fields.append({"name": "Accept", "value": links, "inline": True})
        else:
            s = ""
            status = ""
            for size in sizes:
                s+=size+"\n"
                status+="🟡 WTB\n"
            fields.append({"name": "Pid", "value": f"{pid}", "inline": False})
            fields.append({"name": "Sizes", "value": f"{s}", "inline": True})
        
        webhook.send(group=group, webhook=group["wethenew-"+self.endpoint], site=f"{SITE}_{self.endpoint}", title=title, url=f"https://sell.wethenew.com/{'consignment' if self.endpoint == 'consignment-slots' else 'listing'}/product/"+pid, thumbnail=thumbnail, fields=fields)


    def scrape_site(self):
        """
        Scrapes Wethenew site and adds items to array
        """

        items = []
        output = []
        skip = 0


        #Get all Products from the Site
        while True:
            headers = {
                'authority': 'api-sell.wethenew.com',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                'authorization': f'Bearer {self.getAuth()}',
                'cache-control': 'no-cache',
                'feature-policy': "microphone 'none'; geolocation 'none'; camera 'none'; payment 'none'; battery 'none'; gyroscope 'none'; accelerometer 'none';",
                'origin': 'https://sell.wethenew.com',
                'pragma': 'no-cache',
                'referer': 'https://sell.wethenew.com/',
                'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': CHROME_USERAGENT,
                'x-xss-protection': '1;mode=block',
            }

            url = f"https://api-sell.wethenew.com/{self.endpoint}?skip={skip}&take=100&onlyWanted=true"
            logging.info(msg=f'[{SITE}_{self.endpoint}] Scrape {url}')
            response = tls.get(url, proxies=self.proxys.next(), headers=headers)
            response.raise_for_status()

            r = response.json()
            for product in r["results"]:
                output.append(product)
            if r["pagination"]["totalPages"] <= r["pagination"]["page"]:
                break
            skip+=100

        # Stores particular details in array
        for product in output:
            product_item = {
                'title': product['brand'] + " " + product['name'], 
                'image': product['image'], 
                'pid': str(product['id']),
                'variants': product[self.sizesKey[self.endpoint]]
            }
            items.append(product_item)
        
        logging.info(msg=f'[{SITE}_{self.endpoint}] Successfully scraped site')
        return items

    def remove(self, pid):
        """
        Remove all Products from INSTOCK with the same pid
        """
        for elem in self.INSTOCK:
            if pid == elem[2]:
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

    def removeduplicate(self,items):
        """
        Remove duplicates
        """
        newItems = []
        pids = []
        for item in items:
            if item["pid"] not in pids:
                newItems.append(item)
                pids.append(item["pid"])
        
        return newItems

    def comparitor(self, product):
        product_item = [product['title'], product['image'], product['pid'], product['variants']]
        
        if product['variants']:
            ping, updated = self.updated(product_item)
            if updated or self.firstScrape:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if ping and self.timeout.ping(product_item) and not self.firstScrape:
                    print(f"[{SITE}_{self.endpoint}] {product_item[0]} got restocked")
                    logging.info(msg=f"[{SITE}_{self.endpoint}] {product_item[0]} got restocked")
                    for group in self.groups:
                        #Send Ping to each Group
                        threadrunner.run(
                            self.discord_webhook,
                            group=group,
                            pid=product['pid'],
                            title=product['title'],
                            thumbnail=product['image'],
                            sizes=product['variants'],
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
        logging.basicConfig(filename=f'logs/{SITE}_{self.endpoint}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING {SITE}_{self.endpoint} MONITOR')
 
        while True:
            try:
                startTime = time.time()
                
                # Makes request to site and stores products 
                items = self.scrape_site()

                #Remove duplicates
                items = self.removeduplicate(items)

                for product in items:
                    if product["pid"] not in self.blacksku:
                        if len(self.keywords) == 0:
                            # If no keywords set, checks whether item status has changed
                            self.comparitor(product)

                        else:
                            # For each keyword, checks whether particular item status has changed
                            for key in self.keywords:
                                if key.lower() in product['title'].lower():
                                    self.comparitor(product)
                  
            
                # Allows changes to be notified
                self.firstScrape = False

                logging.info(msg=f'[{SITE}_{self.endpoint}] Checked in {time.time()-startTime} seconds')

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[{SITE}_{self.endpoint}] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(4)