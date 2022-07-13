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

class eleventeamsports:
    def __init__(self,groups,user_agents,delay=2,querys=[],blacksku=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.delay = delay
        self.querys= querys
        self.proxys = proxys
        self.blacksku = blacksku
        self.proxytime = 0
        self.timeout = timeout(timeout=120, pingdelay=20)

        self.INSTOCK = []
        
    def discord_webhook(self,group,title,sku, url, thumbnail,prize):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "eleventeamsports" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        fields.append({"name": "Status", "value": f"```🟢 INSTOCK```", "inline": True})


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
                "name": "eleventeamsports"
            }
            }]
        }
        
        
        result = rq.post(group["eleventeamsports"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[eleventeamsports] Exception found: {err}")
        else:
            logging.info(msg=f'[eleventeamsports] Successfully sent Discord notification to {group["eleventeamsports"]}')
            print(f'[eleventeamsports] Successfully sent Discord notification to {group["eleventeamsports"]}')


    def scrape_site(self,headers, proxy, query):
        """
        Scrapes the specified eleventeamsports query site and adds items to array
        """
        items = []

        # Makes request to site
        html = rq.get(f"https://www.11teamsports.com/de-de/ds/?type=deep_search&q={query}&limit=10000&offset=0&sort=sold_count+desc",  headers=headers, proxies=proxy, verify=False, timeout=10)
        html.raise_for_status()
        products = html.json()["hits"]["hit"]

        # Stores particular details in array
        for product in products:
            product = product["fields"]

            #Only Ping shoes
            if "Schuhe" in product["category"]:
                product_item = {
                        "name":product["title"],
                        "sku":product["sku"],
                        "prize":str(product["price"])+" €",
                        "image":product["media_file"],
                        "url":product["deeplink"]
                        }
                items.append(product_item)

        
        logging.info(msg=f'[eleventeamsports] Successfully scraped site')
        return items
        

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/eleventeamsports.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING eleventeamsports MONITOR')
        logging.info(msg=f'eleventeamsports Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = -1
        headers = {
                'user-agent': random.choice(self.user_agents)["user_agent"]
        }
        
        while True:
            try:
                startTime = time.time()
                
                products = []
                
                # Makes request to site and stores products 
                for query in self.querys:
                    #Rotate Proxys on each request
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}

                    items=self.scrape_site(headers, proxy, query)

                    for product in items:
                        if product["sku"] not in self.blacksku:
                            # Check if Product is INSTOCK
                            if product["sku"] not in self.INSTOCK and start != 1 and self.timeout.ping(product):
                                    print(f"[eleventeamsports] {product}")
                                    logging.info(msg=f"[eleventeamsports] {product}")
                                    for group in self.groups:
                                        #Send Ping to each Group
                                        Thread(target=self.discord_webhook,args=(
                                            group,
                                            product['name'],
                                            product['sku'],
                                            product['url'],
                                            product['image'],
                                            product['prize']
                                            )).start()
                            products.append(product["sku"])

                    time.sleep(self.delay/len(self.querys))

                self.INSTOCK = products

                # Allows changes to be notified
                start = 0

                logging.info(msg=f'[eleventeamsports] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[eleventeamsports] Exception found: {traceback.format_exc()}")
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
        "eleventeamsports":"https://discord.com/api/webhooks/954818030834188368/v4kzvzQxIHl_Bm_F35E5wl4E6gF0ucM3rde4rQTOs9Ic__JjnIul-NxyUIPb1tUKmLtG"
    }
    s = eleventeamsports(groups=[devgroup],querys=["nike"],delay=3,user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}])
    s.monitor()