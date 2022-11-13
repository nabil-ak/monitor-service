from threading import Thread
from datetime import datetime
from proxymanager import ProxyManager
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool 
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import os

class kickz:
    def __init__(self,groups,region,regionname,user_agent,proxymanager,delay=1,keywords=[],blacksku=[]):
        self.user_agent = user_agent
        self.region = region
        self.regionname = regionname
        self.groups = groups
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxymanager
        self.blacksku = blacksku

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, sku, url, thumbnail, prize, status, raffle_date):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "kickz" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})

        if status == "RESTOCK":
            fields.append({"name": "Status", "value": f"```🟢 INSTOCK```", "inline": True})
        else:
            fields.append({"name": "Status", "value": f"```🟡 RAFFLE```", "inline": True})
            fields.append({"name": "Ending", "value": f"```{raffle_date.replace('Release: ','')}```", "inline": True})

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
                "name": "kickz "+self.regionname
            }
            }]
        }
        result = rq.post(group["kickz"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[kickz-{self.region}] Exception found: {err}")
        else:
            logging.info(msg=f'[kickz] Successfully sent Discord notification to {group["kickz"]}')
            print(f'[kickz-{self.region}] Successfully sent Discord notification to {group["kickz"]}')


    def scrape_site(self,headers, category):
        """
        Scrapes the specified kickz query site and adds items to array
        """
        items = []

        # Makes request to site
        html = rq.get(f"https://www.kickz.com/on/demandware.store/{self.region}/en/Search-ShowAjax?cgid={category}&srule=new-arrivals&start=0&sz={random.randint(2000,100000)}&prefv1=Sneakers&prefn1=categoriesAssignment&prefv2=nike|jordan|new%20balance&prefn2=brand",  headers=headers, proxies=self.proxys.next(), timeout=10)
        html.raise_for_status()
        output = BeautifulSoup(html.text, "html.parser")
        
        products = output.find_all("section", {"class": "b-product_tile"})

        # Stores particular details in array
        for product in products:
            button = product.find("a", {"class": "b-product_tile-link"})
            raffle_date = ""

            if product.find("div", {"class": "b-product_tile-release"}):
                status = "RAFFLE"
                raffle_date = product.find("div", {"class": "b-product_tile-release"}).text
            elif product.find("div", {"class": "b-raffle-tile_attr"}):
                status = "RAFFLE_OVER"
            else:
                status = "RESTOCK"

            product_item = {
                    "name":button.text,
                    "sku":button["data-pid"],
                    "prize":product.find("span", {"class": "b-price-item"}).text,
                    "image": f"{os.environ['IMAGEPROXY']}{product.find('img')['src']}",
                    "url":"https://www.kickz.com"+button["href"],
                    "status": status,
                    "raffle_date":raffle_date
                    }
            items.append(product_item)

        
        logging.info(msg=f'[kickz-{self.region}] Successfully scraped category {category}')
        return items
        
    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/kickz-{self.region}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING kickz-{self.region} MONITOR')
        logging.info(msg=f'kickz-{self.region} Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising headers
        headers = {
                'user-agent': self.user_agent
        }

        #Initialise categorys and instock items for each category
        # new_M_shoes = New Men(https://www.kickz.com/de/l/neu/m%C3%A4nner/schuhe/)
        # new_F_shoes = New Women(https://www.kickz.com/de/l/neu/frauen/schuhe/)
        # new_U_shoes = New Unisex(https://www.kickz.com/de/l/neu/unisex/schuhe/)
        # 3_M_46 = Men(https://www.kickz.com/de/l/schuhe/m%C3%A4nner/sneaker/)
        # 3_F_46 = Women(https://www.kickz.com/de/l/schuhe/frauen/sneaker/)
        # 3_K_42 = Kids(https://www.kickz.com/de/l/schuhe/kinder/schuhe-grade-school/)
        # Air_Jordan_1 = Jordan1(https://www.kickz.com/de/l/jordan/retros/air-jordan-1-retro/)
        # Air_Jordan_3 = Jordan3(https://www.kickz.com/de/l/jordan/retros/air-jordan-3-retro/)
        categorys = ["new_M_shoes","new_F_shoes","new_U_shoes","3_M_46","3_F_46","3_K_42","Air_Jordan_1","Air_Jordan_3"]
        while True:
            try:
                startTime = time.time()

                # Makes request to each category and stores products 
                args = []
                for c in categorys:
                    args.append((headers, c))

                products = []

                with ThreadPool(len(categorys)) as threadpool:
                    items = sum(threadpool.starmap(self.scrape_site, args), [])

                    for product in items:
                        if product["sku"] not in self.blacksku:
                            #Check for Keywords
                            if self.keywords and not any(key.lower() in product["name"].lower() for key in self.keywords):
                                continue
                            
                            save = {
                                "sku":product["sku"],
                                "status":product["status"]
                            }

                            # Check if Product is INSTOCK
                            if save not in products:
                                if save not in self.INSTOCK and save["status"] != "RAFFLE_OVER" and start != 1:
                                            print(f"[kickz-{self.region}] {product}")
                                            logging.info(msg=f"[kickz-{self.region}] {product}")
                                            for group in self.groups:
                                                #Send Ping to each Group
                                                Thread(target=self.discord_webhook,args=(
                                                    group,
                                                    product['name'],
                                                    product['sku'],
                                                    product['url'],
                                                    product['image'],
                                                    product['prize'],
                                                    product['status'],
                                                    product['raffle_date']
                                                    )).start()
                                products.append(save)

                    self.INSTOCK = products

                    # Allows changes to be notified
                    start = 0

                    logging.info(msg=f'[kickz-{self.region}] Checked all querys in {time.time()-startTime} seconds')

                    time.sleep(self.delay)

            except Exception as e:
                print(f"[kickz-{self.region}] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(2)


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "kickz":"https://discord.com/api/webhooks/954818030834188368/v4kzvzQxIHl_Bm_F35E5wl4E6gF0ucM3rde4rQTOs9Ic__JjnIul-NxyUIPb1tUKmLtG"
    }
    s = kickz(groups=[devgroup],keywords=["pegasus"],delay=3,user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}])
    s.monitor()