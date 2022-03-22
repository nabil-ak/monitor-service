from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent
from threading import Thread
from datetime import datetime

import requests as rq

import time

import json
import logging
import traceback
import urllib3

class shopify:
    def __init__(self,groups,site,url,delay=1,keywords=[],proxys=[]):
        software_names = [SoftwareName.CHROME.value]
        hardware_type = [HardwareType.MOBILE__PHONE]
        self.user_agent_rotator = UserAgent(software_names=software_names, hardware_type=hardware_type)

        self.groups = groups
        self.site = site
        self.url = url
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxys

        self.INSTOCK = []
        
    def discord_webhook(self,group,site,title, url, thumbnail,prize, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if group[self.site] == "":
            return

        fields = []
        fields.append({"name": "[ PRIZE ]", "value": prize, "inline": True})
        fields.append({"name": "[ STOCK ]", "value": str(len(sizes))+"+", "inline": False})
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
        else:
            logging.info(msg=f'[{self.site}] Successfully sent Discord notification to {group[self.site]}')
            print(f'[{self.site}] Successfully sent Discord notification to {group[self.site]}')


    def scrape_site(self,url, headers, proxy):
        """
        Scrapes the specified Shopify site and adds items to array
        """
        items = []

        # Makes request to site
        s = rq.Session()
        page = 1
        while True:
            html = s.get(url + f'?page={page}&limit=250', headers=headers, proxies=proxy, verify=False, timeout=20)
            output = json.loads(html.text)['products']
            if output == []:
                break
            else:
                # Stores particular details in array
                for product in output:
                    #Just scrape Sneakers
                    if product["product_type"] == "Sneakers":
                        product_item = {
                            'title': product['title'], 
                            'image': product['images'][0]['src'], 
                            'handle': product['handle'],
                            'variants': product['variants']}
                        items.append(product_item)
                page += 1
        
        logging.info(msg=f'[{self.site}] Successfully scraped site')
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
                if start == 0 and ping:
                    for group in self.groups:
                        #Send Ping to each Group
                        '''self.discord_webhook(
                            group=group,
                            title=product['title'],
                            site=self.site,
                            url=self.url.replace('.json', '/') + product['handle'],
                            thumbnail=product['image'],
                            sizes=available_sizes,
                            prize=product['variants'][0]['price']+" €"
                        )'''
                        Thread(target=self.discord_webhook,args=(
                            group,
                            self.site,
                            product["title"],
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
        print(f'STARTING {self.site} MONITOR')
        logging.info(msg=f'[{self.site}] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = 0
        proxy = {} if len(self.proxys) == 0 else {"http": f"http://{self.proxys[proxy_no]}"}
        headers = {'User-Agent': self.user_agent_rotator.get_random_user_agent()}

        
        while True:
            try:
                # Makes request to site and stores products 
                items = self.scrape_site(self.url, proxy, headers)
                for product in items:

                    if len(self.keywords) == 0:
                        # If no keywords set, checks whether item status has changed
                        self.comparitor(product, start)

                    else:
                        # For each keyword, checks whether particular item status has changed
                        for key in self.keywords:
                            if key.lower() in product['title'].lower():
                                self.comparitor(product, start)

                # Allows changes to be notified
                start = 0

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[{self.site}] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(90)

                # Rotates headers
                headers = {'User-Agent': self.user_agent_rotator.get_random_user_agent()}
                
                if len(self.proxys) != 0:
                    # If optional proxy set, rotates if there are multiple proxies
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {"http": f"http://{self.proxys[proxy_no]}"}


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "kith":"https://discord.com/api/webhooks/953049618848051230/tMu7dKb8cNHEGHsAeBQo8gWmibLYdAm2MaSzUw8hEZV5KhaFCr6LmDg_EkwebqG6xdy1"
    }
    logging.basicConfig(filename=f'kith.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    s = shopify(site="kith",groups=[devgroup],url="https://eu.kith.com/products.json",proxys=["padifozj-rotate:36cjopf6jt4p@154.13.90.91:80"])
    s.monitor()