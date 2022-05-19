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

class shopify:
    def __init__(self,groups,site,url,user_agents,delay=1,keywords=[],proxys=[]):
        self.user_agents = user_agents

        self.groups = groups
        self.site = site
        self.url = url
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxys
        self.proxytime = 0

        self.INSTOCK = []
        self.timeout = timeout()
        
    def discord_webhook(self,group,site,title,sku, url, thumbnail,prize, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if self.site not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        fields.append({"name": "Stock", "value": f"```{str(len(sizes))}+```", "inline": True})
        for size in sizes:
            fields.append({"name": size['title'], "value": size['url'], "inline": True})

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
                "name": site
            }
            }]
        }
        
        
        result = rq.post(group[self.site], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[{self.site}] Exception found: {err}")
        else:
            logging.info(msg=f'[{self.site}] Successfully sent Discord notification to {group[self.site]}')
            print(f'[{self.site}] Successfully sent Discord notification to {group[self.site]}')


    def scrape_site(self,url,page,headers, proxy):
        """
        Scrapes the specified Shopify site and adds items to array
        """
        items = []

        # Makes request to site
        s = rq.Session()
        
        html = s.get(url + f'?page={page}&limit=250', headers=headers, proxies=proxy, verify=False, timeout=10)
        output = json.loads(html.text)['products']
        
        # Stores particular details in array
        for product in output:
            #Just scrape Sneakers and Sandals when the site is Kith or Slamjam
            if self.site in ["kith","slamjam","asphaltgold"] and product["product_type"] not in ["Sneakers","Sandals","Footwear","Sandals and Slides"]:
                continue
            product_item = {
                'title': product['title'], 
                'image': product['images'][0]['src'] if product['images'] else "", 
                'handle': product['handle'],
                'variants': product['variants']}
            items.append(product_item)
        
        logging.info(msg=f'[{self.site}] Successfully scraped Page {page}')
        s.close()
        return items

    def remove(self,handle):
        """
        Remove all Products from INSTOCK with the same handle
        """
        for elem in self.INSTOCK:
            if handle == elem[2]:
                self.INSTOCK.remove(elem)

    def updated(self,product):
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


    def comparitor(self,product, start):
        product_item = [product['title'], product['image'], product['handle']]

        # Collect all available sizes
        available_sizes = []
        for size in product['variants']:
            if size['available']: # Makes an ATC link from the variant ID
                available_sizes.append({'title': size['title'], 'url': '[ATC](' + self.url[:self.url.find('/', 10)] + '/cart/' + str(size['id']) + ':1)'})

        
        product_item.append(available_sizes) # Appends in field
        
        if available_sizes:
            ping, updated = self.updated(product_item)
            if updated or start == 1:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if start == 0:
                    print(f"[{self.site}] {product_item}")
                    logging.info(msg=f"[{self.site}] {product_item}")

                    if ping and self.timeout.ping(product_item):
                        for group in self.groups:
                            #Send Ping to each Group
                            Thread(target=self.discord_webhook,args=(
                                group,
                                self.site,
                                product["title"],
                                product['handle'],
                                self.url.replace('.json', '/') + product['handle'],
                                product['image'],
                                product['variants'][0]['price']+" €",
                                available_sizes,
                                )).start()
        else:
            # Remove old version of the product
            self.remove(product_item[2])

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/{self.site}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING {self.site} MONITOR')
        logging.info(msg=f'[{self.site}] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = -1
        headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}

        
        while True:
            try:
                startTime = time.time()
                items = [1]
                page = 1
                while items:
                    #Rotate Proxys on each request
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}

                    # Makes request to site and stores products 
                    items = self.scrape_site(self.url,page, headers, proxy)
                    for product in items:

                        if len(self.keywords) == 0:
                            # If no keywords set, checks whether item status has changed
                            self.comparitor(product, start)

                        else:
                            # For each keyword, checks whether particular item status has changed
                            for key in self.keywords:
                                if key.lower() in product['title'].lower():
                                    self.comparitor(product, start)
                    page+=1

                # Allows changes to be notified
                start = 0

                logging.info(msg=f'[{self.site}] Checked in {time.time()-startTime} seconds')

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[{self.site}] Exception found: {traceback.format_exc()}")
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
        "kith":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    s = shopify(site="asphaltgold",groups=[devgroup],url="https://asphaltgold.com/products.json",user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}])
    s.monitor()