from threading import Thread
from datetime import datetime
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3

class svd:
    def __init__(self,groups,user_agents,delay=1,keywords=[],blacksku=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxys
        self.blacksku = blacksku
        self.proxytime = 0

        self.INSTOCK = {}
        
    def discord_webhook(self,group,title,sku, url, thumbnail,prize):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "svd" not in group:
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
                "name": "svd"
            }
            }]
        }
        
        
        result = rq.post(group["svd"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[svd] Exception found: {err}")
        else:
            logging.info(msg=f'[svd] Successfully sent Discord notification to {group["svd"]}')
            print(f'[svd] Successfully sent Discord notification to {group["svd"]}')


    def scrape_site(self,headers, proxy, category):
        """
        Scrapes the specified svd query site and adds items to array
        """
        items = []

        # Makes request to site
        html = rq.get(f"https://www.sivasdescalzo.com/graphql?query=query%20categoryV2(%24id%3A%20Int!%2C%20%24pageSize%3A%20Int!%2C%20%24currentPage%3A%20Int!%2C%20%24filters%3A%20ProductAttributeFilterInput!%2C%20%24sort%3A%20ProductAttributeSortInput)%20%7B%0A%20%20category(id%3A%20%24id)%20%7B%0A%20%20%20%20name%0A%20%20%20%20__typename%0A%20%20%7D%0A%20%20products(pageSize%3A%20%24pageSize%2C%20currentPage%3A%20%24currentPage%2C%20filter%3A%20%24filters%2C%20sort%3A%20%24sort)%20%7B%0A%20%20%20%20items%20%7B%0A%20%20%20%20%20%20id%0A%20%20%20%20%20%20brand_name%0A%20%20%20%20%20%20name%0A%20%20%20%20%20%20sku%0A%20%20%20%20%20%20small_image%20%7B%0A%20%20%20%20%20%20%20%20url%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20url%0A%20%20%20%20%20%20original_price%0A%20%20%20%20%20%20final_price%0A%20%20%20%20%20%20percent_off%0A%20%20%20%20%20%20state%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20aggregations%20%7B%0A%20%20%20%20%20%20attribute_code%0A%20%20%20%20%20%20label%0A%20%20%20%20%20%20count%0A%20%20%20%20%20%20options%20%7B%0A%20%20%20%20%20%20%20%20label%0A%20%20%20%20%20%20%20%20value%0A%20%20%20%20%20%20%20%20count%0A%20%20%20%20%20%20%20%20__typename%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20page_info%20%7B%0A%20%20%20%20%20%20total_pages%0A%20%20%20%20%20%20__typename%0A%20%20%20%20%7D%0A%20%20%20%20total_count%0A%20%20%20%20__typename%0A%20%20%7D%0A%7D%0A&operationName=categoryV2&variables=%7B%22currentPage%22%3A1%2C%22id%22%3A4089%2C%22filters%22%3A%7B%22brand%22%3A%7B%22in%22%3A%5B%22adidas%20YEEZY%22%2C%22Jordan%22%2C%22Nike%22%2C%22New%20Balance%22%5D%7D%2C%22category_id%22%3A%7B%22eq%22%3A%22{category}%22%7D%7D%2C%22pageSize%22%3A1000%2C%22sort%22%3A%7B%22sorting_date%22%3A%22DESC%22%7D%7D",  headers=headers, proxies=proxy, verify=False, timeout=10)
        html.raise_for_status()
        products = json.loads(html.text)['data']['products']['items']

        # Stores particular details in array
        for product in products:
            product_item = {
                    "name":product["brand_name"]+" "+product["name"],
                    "sku":product["sku"],
                    "prize":str(product["final_price"])+" €",
                    "image":"https://image-proxy.nabil-ak.repl.co/https://media.sivasdescalzo.com/media/catalog/product/"+product["small_image"]["url"]+"?width=300",
                    "url":product["url"],
                    "state":product["state"]
                    }
            items.append(product_item)

        
        logging.info(msg=f'[svd] Successfully scraped site')
        return items
        

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/svd.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING svd MONITOR')
        logging.info(msg=f'svd Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = -1
        headers = {
                'user-agent': random.choice(self.user_agents)["user_agent"]
        }

        #Initialise categorys and instock items for each category
        # 4089 = Sneakers (https://www.sivasdescalzo.com/en/footwear/sneakers)
        # 2900 = New Arrivals (https://www.sivasdescalzo.com/en/new-arrivals)
        # 2513 = Adidas Yeezy (https://www.sivasdescalzo.com/en/brands/adidas/yeezy)
        # 2479 = Adidas (https://www.sivasdescalzo.com/en/brands/adidas)
        # 3558 = Jordan Sneakers (https://www.sivasdescalzo.com/en/brands/jordan/sneakers)
        # 3473 = Nike Sneakers(https://www.sivasdescalzo.com/en/brands/nike/sneakers)
        categorys = [4089,2900,2513,2479,3558,3473]
        for c in categorys:
            self.INSTOCK[c] = []
        
        while True:
            try:
                startTime = time.time()

                # Makes request to site and stores products 

                for c in categorys:
                    #Rotate Proxys on each request
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}

                    items=self.scrape_site(headers, proxy, c)

                    products = []

                    for product in items:
                        if product["sku"] not in self.blacksku and product["state"] not in ["Sold Out", "Raffle"] and len(product["sku"]) > 1:
                            #Check for Keywords
                            if self.keywords and not any(key.lower() in product["name"].lower() for key in self.keywords):
                                continue

                            # Check if Product is INSTOCK
                            if not any([product["sku"] in cat for cat in self.INSTOCK.values()]) and start != 1:
                                    print(f"[svd] {product}")
                                    logging.info(msg=f"[svd] {product}")
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

                    self.INSTOCK[c] = products

                    time.sleep(self.delay/len(categorys))


                # Allows changes to be notified
                start = 0

                logging.info(msg=f'[svd] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[svd] Exception found: {traceback.format_exc()}")
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
        "svd":"https://discord.com/api/webhooks/954818030834188368/v4kzvzQxIHl_Bm_F35E5wl4E6gF0ucM3rde4rQTOs9Ic__JjnIul-NxyUIPb1tUKmLtG"
    }
    s = svd(groups=[devgroup],keywords=["pegasus"],delay=3,user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}])
    s.monitor()