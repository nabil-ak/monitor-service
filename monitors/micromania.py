from threading import Thread
from datetime import datetime
from bs4 import BeautifulSoup
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3

class micromania:
    def __init__(self,groups,user_agents,delay=2,querys=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.delay = delay
        self.querys= querys
        self.proxys = proxys
        self.proxytime = 0

        self.INSTOCK = []
        
    def discord_webhook(self,group,title,sku, url, thumbnail,prize):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "micromania" not in group:
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
                "name": "micromania"
            }
            }]
        }
        
        
        result = rq.post(group["micromania"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[micromania] Exception found: {err}")
        else:
            logging.info(msg=f'[micromania] Successfully sent Discord notification to {group["micromania"]}')
            print(f'[micromania] Successfully sent Discord notification to {group["micromania"]}')


    def scrape_site(self,query,headers, proxy):
        """
        Scrapes the specified micromania query site and adds items to array
        """
        items = []

        # Makes request to site
        html = rq.get(f"https://www.micromania.fr/on/demandware.store/Sites-Micromania-Site/default/Search-Show?q={query}&isApp=true",  headers=headers, proxies=proxy, verify=False, timeout=10)
        html.raise_for_status()
        output = BeautifulSoup(html.text, 'html.parser')
        products = output.find_all('div', {'class': 'product-column'})

        
        # Stores particular details in array
        for product in products:
            data = json.loads(product.find('div', {'class': 'product-tile'})["data-gtm"])["ecommerce"]["impressions"]
            product_item = {
                    "name":data["name"],
                    "sku":data["id"],
                    "prize":f"{data['price']} €",
                    "image":product.find('source')["data-srcset"],
                    "instock":True if product.find('div', {'class': 'back-in-stock-container'}) == None else False
                }
            items.append(product_item)
        
        logging.info(msg=f'[micromania] Successfully scraped Query {query}')
        return items

    def comparitor(self,product, start):

        #Ping when Product goes Instock
        if product["instock"] and product["sku"] not in self.INSTOCK: 
            self.INSTOCK.append(product["sku"])

            if start == 0:
                print(f"[micromania] {product}")
                logging.info(msg=f"[micromania] {product}")
                for group in self.groups:
                    #Send Ping to each Group
                    Thread(target=self.discord_webhook,args=(
                        group,
                        product["name"],
                        product['sku'],
                        f"https://www.micromania.fr/{product['sku']}.html?isApp=true",
                        product['image'],
                        product['prize'],
                        )).start()
        
        #Remove Product when it goes OOS
        if not product["instock"] and product["sku"] in self.INSTOCK:
            self.INSTOCK.remove(product["sku"])

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/micromania.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING micromania MONITOR')
        logging.info(msg=f'micromania Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = 0
        headers = {
                'user-agent': random.choice(self.user_agents)["user_agent"]
        }
        
        while True:
            try:
                proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                startTime = time.time()
                for query in self.querys:
                # Makes request to site and stores products 
                    items = self.scrape_site(query, headers, proxy)
                    for product in items:
                            # Check if Item Status has changed
                            self.comparitor(product, start)
                    time.sleep(self.delay)

                # Allows changes to be notified
                start = 0

                #Shuffle Query Order
                random.shuffle(self.querys)
                logging.info(msg=f'[micromania] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[micromania] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(60)
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
        "micromania":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    logging.basicConfig(filename=f'micromania.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    s = micromania(groups=[devgroup],user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=["xbox"])
    s.monitor()