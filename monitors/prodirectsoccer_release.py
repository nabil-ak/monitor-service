from threading import Thread
from datetime import datetime, timedelta
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import os

class prodirectsoccer_release:
    def __init__(self,groups,user_agents,proxymanager,delay=2,querys=[],blacksku=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.proxys = proxymanager
        self.delay = delay
        self.querys= querys
        self.blacksku = blacksku

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, sku, url, thumbnail, prize, launchdate):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "prodirectsoccer_release" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}£```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        fields.append({"name": "Status", "value": f"```🟡 RELEASE```", "inline": True})
        fields.append({"name": "Launchdate", "value": f"```{launchdate[-2:]}/{launchdate[4:6]}/{launchdate[:4]}```", "inline": True})
        

        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": url, 
            "thumbnail": {"url": f"{os.environ['IMAGEPROXY']}/"+thumbnail.replace(" ","")},
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
        print(data)
        
        
        result = rq.post(group["prodirectsoccer_release"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[prodirectsoccer_release] Exception found: {err}")
        else:
            logging.info(msg=f'[prodirectsoccer_release] Successfully sent Discord notification to {group["prodirectsoccer_release"]}')
            print(f'[prodirectsoccer_release] Successfully sent Discord notification to {group["prodirectsoccer_release"]}')



    def scrape_release_site(self,query,headers):
        """
        Scrapes the specified prodirectsoccer release query site and adds items to array
        """
        items = []

        # Makes request to site
        html = rq.get(f"https://query.published.live1.suggest.eu1.fredhopperservices.com/pro_direct/json?scope=//catalog01/en_GB/categories%3E%7Bsoccerengb%7D&search={query}&callback=jsonpResponse",  headers=headers, proxies=self.proxys.next(), verify=False, timeout=10)
        html.raise_for_status()

        products = json.loads(html.text[14:-1])["suggestionGroups"][1]["suggestions"]
       

        # Stores particular details in array
        for product in products:
            product_item = {
                    "name":product["name"],
                    "sku":product["quickref"],
                    "prize":product["currentprice"].replace("000",""),
                    "image":product["_thumburl"],
                    "url":product["producturl"],
                    "launchdate":product["launchdate"]
                    }
            items.append(product_item)

         
        
        logging.info(msg=f'[prodirectsoccer_release] Successfully scraped releases for query {query}')
        return items
        

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/prodirectsoccer_release.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING prodirectsoccer_release MONITOR')
        logging.info(msg=f'prodirectsoccer_release Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising headers
        headers = {
                'user-agent': random.choice(self.user_agents)["user_agent"]
        }
        
        while True:
            try:
                startTime = time.time()

                products = []

                for query in self.querys:
        
                    # Make request to release-site and stores products
                    items = self.scrape_release_site(query, headers)
                    for product in items:
                        date = datetime.strptime(f"{product['launchdate'][-2:]}/{product['launchdate'][4:6]}/{product['launchdate'][:4]}","%d/%m/%Y")
                        if product["sku"] not in self.blacksku and date>(datetime.now()-timedelta(days=1)):
                            # Check if Product is INSTOCK
                            if product not in self.INSTOCK and start != 1:
                                print(f"[prodirectsoccer_release] {product}")
                                logging.info(msg=f"[prodirectsoccer_release] {product}")
                                for group in self.groups:
                                    #Send Ping to each Group
                                    Thread(target=self.discord_webhook,args=(
                                        group,
                                        product['name'],
                                        product['sku'],
                                        product['url'],
                                        product['image'],
                                        product['prize'],
                                        product['launchdate']
                                        )).start()

                            products.append(product)

                self.INSTOCK = products

                # Allows changes to be notified
                start = 0

                #Shuffle Query Order
                random.shuffle(self.querys)
                logging.info(msg=f'[prodirectsoccer_release] Checked all querys in {time.time()-startTime} seconds')
                time.sleep(self.delay)

            except Exception as e:
                print(f"[prodirectsoccer_release] Exception found: {traceback.format_exc()}")
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
    logging.basicConfig(filename=f'logs/prodirectsoccer_release.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    s = prodirectsoccer_release(groups=[devgroup],delay=5,user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=["dunk"], proxymanager=ProxyManager)
    s.monitor()