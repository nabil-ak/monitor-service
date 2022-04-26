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

class popito:
    def __init__(self,groups,user_agents,delay=1,querys=[],blacksku=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.delay = delay
        self.querys= querys
        self.proxys = proxys
        self.blacksku = blacksku
        self.proxytime = 0

        self.INSTOCK = []
        
    def discord_webhook(self,group,title,sku, url, atc, thumbnail,prize,status):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "popito" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        fields.append({"name": "Status", "value": f"```{'🟢 INSTOCK' if status == 'INSTOCK' else '🟡 RESERVATION'}```", "inline": True})
        fields.append({"name": "🛒", "value": f"[ATC]({atc})", "inline": True})


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
                "name": "popito"
            }
            }]
        }
        
        
        result = rq.post(group["popito"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[popito] Exception found: {err}")
        else:
            logging.info(msg=f'[popito] Successfully sent Discord notification to {group["popito"]}')
            print(f'[popito] Successfully sent Discord notification to {group["popito"]}')


    def scrape_site(self,query,headers, proxy):
        """
        Scrapes the specified popito query site and adds items to array
        """
        items = []

        #Page Counter
        page = 1

        #Scrape all available Pages
        while True:
            # Makes request to site
            html = rq.get(f"https://popito.fr/page/{page}/?s={query}&post_type=product&product_cat=0",  headers=headers, proxies=proxy, verify=False, timeout=10)
            if html.status_code == 404:
                    break
            html.raise_for_status()

            output = BeautifulSoup(html.text, 'html.parser')
            products = output.find_all('div', {'class': 'content-product'})

            # Stores particular details in array
            for product in products:
                title = product.find('p', {'class': 'product-title'}).find('a')
                prize = product.find_all('span', {'class': 'woocommerce-Price-amount amount'})[-1].find('bdi').text
                sku = product.find('footer', {'class': 'footer-product'}).find('a')["data-product_id"]
                product_item = {
                        "name":title.text,
                        "sku":sku,
                        "prize":prize,
                        "image":product.find('a', {'class': 'product-content-image'}).find('img')["src"],
                        "url":title["href"],
                        "ATC":"https://popito.fr/panier/?add-to-cart="+sku,
                        "status":"RESERVATION" if product.find('div', {'class': 'pre_order_loop'}) != None else "INSTOCK",
                        }
                items.append(product_item)

            page+=1
        
        logging.info(msg=f'[popito] Successfully scraped Query {query}')
        return items
        

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/popito.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING popito MONITOR')
        logging.info(msg=f'popito Successfully started monitor')

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

                for query in self.querys:
                    #Rotate Proxys on each request
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}

                    # Makes request to site and stores products 
                    items = self.scrape_site(query, headers, proxy)
                    for product in items:
                        if product["sku"] not in self.blacksku:
                            # Check if Product is INSTOCK
                            if product["sku"] not in self.INSTOCK and start != 1:
                                print(f"[popito] {product}")
                                logging.info(msg=f"[popito] {product}")
                                for group in self.groups:
                                    #Send Ping to each Group
                                    Thread(target=self.discord_webhook,args=(
                                        group,
                                        product['name'],
                                        product['sku'],
                                        product['url'],
                                        product['ATC'],
                                        product['image'],
                                        product['prize'],
                                        product['status']
                                        )).start()

                            products.append(product["sku"])
                    time.sleep(self.delay)

                self.INSTOCK = products

                # Allows changes to be notified
                start = 0

                #Shuffle Query Order
                random.shuffle(self.querys)
                logging.info(msg=f'[popito] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[popito] Exception found: {traceback.format_exc()}")
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
        "popito":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    logging.basicConfig(filename=f'popito.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    s = popito(groups=[devgroup],user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=["xbox"])
    s.monitor()