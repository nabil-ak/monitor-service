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

class popinabox:
    def __init__(self,groups,user_agents,delay=1,querys=[],blacksku=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.delay = delay
        self.querys= querys
        self.proxys = proxys
        self.blacksku = blacksku
        self.proxytime = 0

        self.INSTOCK = []
        
    def discord_webhook(self,group,title,sku, url, thumbnail,prize,status):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "popinabox" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        fields.append({"name": "Status", "value": f"```{'🟢 INSTOCK' if status == 'INSTOCK' else '🟡 RESERVATION'}```", "inline": True})


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
                "name": "popinabox"
            }
            }]
        }
        
        
        result = rq.post(group["popinabox"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[popinabox] Exception found: {err}")
        else:
            logging.info(msg=f'[popinabox] Successfully sent Discord notification to {group["popinabox"]}')
            print(f'[popinabox] Successfully sent Discord notification to {group["popinabox"]}')


    def scrape_site(self,query,headers, proxy):
        """
        Scrapes the specified popinabox query site and adds items to array
        """
        items = []

        #Page Counter
        page = 1
        pages = 2

        #Scrape all available Pages
        while page != pages:
            # Makes request to site
            html = rq.get(f"{query}&pageNumber={page}",  headers=headers, proxies=proxy, verify=False, timeout=10)
            html.raise_for_status()
            output = BeautifulSoup(html.text, 'html.parser')
            products = output.find_all('li', {'class': 'productListProducts_product'})
            maxpage = output.find('nav', {'class': 'responsivePaginationPages'})

            pages = 2 if maxpage == None else int(maxpage["data-total-pages"])+1

            # Stores particular details in array
            for product in products:
                    info = product.find('span', {'class': 'js-enhanced-ecommerce-data hidden'})
                    statusBlock = product.find('div', {'class': 'productBlock_actions'})
                    status = ""
                    if statusBlock.find('a') != None:
                            status = "RESERVATION"
                    elif statusBlock.find('button', {'class': 'productQuickbuySimple js-e2e-add-basket'}) != None:
                            status = "INSTOCK"
                    else:
                            status = "OUTOFSTOCK"
                    product_item = {
                            "name":info["data-product-title"],
                            "sku":info["data-product-id"],
                            "prize":info["data-product-price"],
                            "image":product.find('img')["src"],
                            "url":"https://www.popinabox.fr"+product.find('a', {'class': 'productBlock_link'})["href"],
                            "status":status,
                            }
                    items.append(product_item)
            page+=1
        
        logging.info(msg=f'[popinabox] Successfully scraped Query {query}')
        return items

    def remove(self,sku):
        """
        Remove all Products from INSTOCK with the same sku
        """
        for p in self.INSTOCK:
            if p["sku"] == sku:
                self.INSTOCK.remove(p)

    def updated(self,product): 
        """
        Check if Product-Status has changed
        """
        for elem in self.INSTOCK:
            if product["sku"] == elem["sku"] and product["status"] == elem["status"]:
                    return False
        return True

    def comparitor(self,product, start):
        if product["status"] != "OUTOFSTOCK":
            updated = self.updated(product)
            if updated or start == 1:

                # Remove old version of the product
                self.remove(product["sku"])
                self.INSTOCK.append({"sku":product["sku"], "status":product["status"]})

                if start == 0:
                    print(f"[popinabox] {product}")
                    logging.info(msg=f"[popinabox] {product}")
                    for group in self.groups:
                        #Send Ping to each Group
                        Thread(target=self.discord_webhook,args=(
                            group,
                            product['name'],
                            product['sku'],
                            product['url'],
                            product['image'],
                            product['prize'],
                            product['status']
                            )).start()
        else:
            self.remove(product["sku"])

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/popinabox.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING popinabox MONITOR')
        logging.info(msg=f'popinabox Successfully started monitor')

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
                for query in self.querys:
                    #Rotate Proxys on each request
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                    
                    # Makes request to site and stores products 
                    items = self.scrape_site(query, headers, proxy)
                    for product in items:
                        if product["sku"] not in self.blacksku:
                            # Check if Item Status has changed
                            self.comparitor(product, start)
                    time.sleep(self.delay)

                # Allows changes to be notified
                start = 0

                #Shuffle Query Order
                random.shuffle(self.querys)
                logging.info(msg=f'[popinabox] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[popinabox] Exception found: {traceback.format_exc()}")
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
        "popinabox":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    logging.basicConfig(filename=f'popinabox.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    s = popinabox(groups=[devgroup],user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=["xbox"])
    s.monitor()