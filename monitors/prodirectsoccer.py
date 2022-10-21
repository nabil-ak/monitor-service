from threading import Thread
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import os
import tls

class prodirectsoccer:
    def __init__(self,groups,user_agent,proxymanager,delay=2,querys=[],blacksku=[]):
        self.user_agent = user_agent

        self.groups = groups
        self.proxys = proxymanager
        self.delay = delay
        self.querys= querys
        self.blacksku = blacksku

        self.INSTOCK = []
        
    def discord_webhook(self,group,title,sku, url, thumbnail,prize,launchdate=None):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "prodirectsoccer" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}£```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        if not launchdate:
            fields.append({"name": "Status", "value": f"```🟢 INSTOCK```", "inline": True})
        else:
            fields.append({"name": "Status", "value": f"```🟡 RELEASE```", "inline": True})
            fields.append({"name": "Launchdate", "value": f"```{launchdate[-2:]}/{launchdate[4:6]}/{launchdate[:4]}```", "inline": True})
        

        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": url, 
            "thumbnail": {"url": f"{os.environ['IMAGEPROXY']}"+thumbnail},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
            "author": {
                "name": "prodirectsoccer"
            }
            }]
        }
        
        
        result = rq.post(group["prodirectsoccer"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[prodirectsoccer] Exception found: {err}")
        else:
            logging.info(msg=f'[prodirectsoccer] Successfully sent Discord notification to {group["prodirectsoccer"]}')
            print(f'[prodirectsoccer] Successfully sent Discord notification to {group["prodirectsoccer"]}')


    def scrape_site(self,query,headers):
        """
        Scrapes the specified prodirectsoccer query site and adds items to array
        """
        items = []

        #Page Counter
        page = 1

        #Scrape all available Pages
        while True:
            # Makes request to site
            html = tls.get(f"https://www.prodirectsoccer.com/search/?qq={query}&pg={page}",  headers=headers, proxies=self.proxys.next())
            html.raise_for_status()

            output = BeautifulSoup(html.text, 'html.parser')
            products = output.find_all('a', {'class': 'product-thumb__link'})
            if not products:
                break

            # Stores particular details in array
            for product in products:
                info = json.loads(product["data-gtmi"])
                product_item = {
                        "name":info["name"],
                        "sku":info["id"],
                        "prize":info["price"],
                        "image":product.find('img')["data-src"],
                        "url":product["href"]
                        }
                items.append(product_item)

            page+=1
        
        logging.info(msg=f'[prodirectsoccer] Successfully scraped Query {query}')
        return items
        

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/prodirectsoccer.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING prodirectsoccer MONITOR')
        logging.info(msg=f'prodirectsoccer Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising headers
        headers = {
                'user-agent': self.user_agent
        }
        
        while True:
            try:
                startTime = time.time()

                products = []

                for query in self.querys:
                    # Makes request to query-site and stores products 
                    items = self.scrape_site(query, headers)
                    for product in items:
                        if product["sku"] not in self.blacksku:
                            # Check if Product is INSTOCK
                            if product["sku"] not in self.INSTOCK and start != 1:
                                print(f"[prodirectsoccer] {product}")
                                logging.info(msg=f"[prodirectsoccer] {product}")
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
                    
                self.INSTOCK = products


                # Allows changes to be notified
                start = 0

                #Shuffle Query Order
                random.shuffle(self.querys)
                logging.info(msg=f'[prodirectsoccer] Checked all querys in {time.time()-startTime} seconds')
                time.sleep(self.delay)

            except Exception as e:
                print(f"[prodirectsoccer] Exception found: {traceback.format_exc()}")
                logging.error(e)
                # Rotates headers
                headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "prodirectsoccer":"https://discord.com/api/webhooks/954818030834188368/v4kzvzQxIHl_Bm_F35E5wl4E6gF0ucM3rde4rQTOs9Ic__JjnIul-NxyUIPb1tUKmLtG"
    }
    logging.basicConfig(filename=f'logs/prodirectsoccer.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    s = prodirectsoccer(groups=[devgroup],delay=5,user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=["jordan retro"])
    s.monitor()