from multiprocessing import Process
from proxymanager import ProxyManager
from bs4 import BeautifulSoup
from multiprocessing.pool import ThreadPool 
from user_agent import CHROME_USERAGENT
import random
import requests as rq
import time
import webhook
import logging
import traceback
import urllib3
import os
import threadrunner

SITE = __name__.split(".")[1]

class kickz(Process):
    def __init__(self, groups, region, regionname, settings):
        Process.__init__(self)
        self.region = region
        self.regionname = regionname
        self.groups = groups
        self.delay = settings["delay"]
        self.keywords= settings["keywords"]
        self.proxys = ProxyManager(settings["proxys"])
        self.blacksku = settings["blacksku"]
        self.firstScrape = True

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, pid, url, thumbnail, price, status, raffle_date):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        fields.append({"name": "Price", "value": f"{price}", "inline": True})
        fields.append({"name": "Pid", "value": f"{pid}", "inline": True})

        if status == "RESTOCK":
            fields.append({"name": "Status", "value": f"**New Add**", "inline": True})
        else:
            fields.append({"name": "Status", "value": f"**Raffle**", "inline": True})
            fields.append({"name": "Ending", "value": f"{raffle_date.replace('Release: ','')}", "inline": True})
        
        webhook.send(group=group, webhook=group[SITE], site=f"{SITE}_{self.regionname}", title=title, url=url, thumbnail=thumbnail, fields=fields)


    def scrape_site(self, category):
        """
        Scrapes the specified kickz query site and adds items to array
        """
        items = []

        url = f"https://www.kickz.com/on/demandware.store/{self.region}/en/Search-ShowAjax?cgid={category}&srule=new-arrivals&start=0&sz={random.randint(2000,100000)}&prefv1=Sneakers&prefn1=categoriesAssignment&prefv2=nike|jordan|new%20balance&prefn2=brand"

        # Makes request to site
        html = rq.get(url, headers={
                'user-agent': CHROME_USERAGENT
        })
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
                    "name":button.text.replace("\n",""),
                    "pid":button["data-pid"],
                    "price":product.find("span", {"class": "b-price-item"}).text,
                    "image": f"{os.environ['IMAGEPROXY']}?url={product.find('img')['src']}&proxy={','.join(self.proxys.proxygroups)}",
                    "url":"https://www.kickz.com"+button["href"],
                    "status": status,
                    "raffle_date":raffle_date
                    }
            items.append(product_item)

        
        logging.info(msg=f'[{SITE}_{self.regionname}] Successfully scraped category {category}')
        return items
        
    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/{SITE}_{self.regionname}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING {SITE}_{self.regionname} MONITOR')

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
                args = [(c,) for c in categorys]

                products = []

                with ThreadPool(len(categorys)) as threadpool:
                    items = sum(threadpool.starmap(self.scrape_site, args), [])

                    for product in items:
                        if product["pid"] not in self.blacksku:
                            #Check for Keywords
                            if self.keywords and not any(key.lower() in product["name"].lower() for key in self.keywords):
                                continue
                            
                            save = {
                                "pid":product["pid"],
                                "status":product["status"]
                            }

                            # Check if Product is INSTOCK
                            if save not in products:
                                if save not in self.INSTOCK and save["status"] != "RAFFLE_OVER" and not self.firstScrape:
                                            print(f"[{SITE}_{self.regionname}] {product['name']} got restocked")
                                            logging.info(msg=f"[{SITE}_{self.regionname}] {product['name']} got restocked")
                                            for group in self.groups:
                                                #Send Ping to each Group
                                                threadrunner.run(
                                                    self.discord_webhook,
                                                    group=group,
                                                    title=product['name'],
                                                    pid=product['pid'],
                                                    url=product['url'],
                                                    thumbnail=product['image'],
                                                    price=product['price'],
                                                    status=product['status'],
                                                    raffle_date=product['raffle_date']
                                                )
                                products.append(save)

                    self.INSTOCK = products

                    # Allows changes to be notified
                    self.firstScrape = False

                    logging.info(msg=f'[{SITE}_{self.regionname}] Checked all querys in {time.time()-startTime} seconds')

                    time.sleep(self.delay)

            except Exception as e:
                print(f"[{SITE}_{self.regionname}] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(4)