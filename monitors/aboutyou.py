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

software_names = [SoftwareName.CHROME.value]
hardware_type = [HardwareType.MOBILE__PHONE]
user_agent_rotator = UserAgent(software_names=software_names, hardware_type=hardware_type)

class aboutyou:
    def __init__(self,groups,delay=1,keywords=[],proxys=[],blacksku=[]):
        self.INSTOCK = []
        self.groups = groups
        self.delay = delay
        self.keywords = keywords
        self.proxys = proxys
        self.blacksku = blacksku

    def discord_webhook(self,group,sku,store,title, url, thumbnail,prize, sizes, stock):
            """
            Sends a Discord webhook notification to the specified webhook URL
            """
            if "aboutyou" not in group:
                return

            fields = []
            fields.append({"name": "[ PRIZE ]", "value": prize, "inline": True})
            fields.append({"name": "[ SKU ]", "value": sku, "inline": True})
            fields.append({"name": "[ REGION ]", "value": store, "inline": True})
            sizeField = {"name": "[ Sizes(stock) ]", "value": "", "inline": False}
            formater = 0
            for size in sizes:
                formatcharacter = "\t" if formater%2 == 0 else "\n"
                sizeField["value"]+=f"**{size}** ({stock[size]})"+formatcharacter
                formater+=1
            fields.append(sizeField)
            links = {"name": "[ Links ]", 
            "value": f"[CH](https://www.aboutyou.ch/p/nabil/nabil-{sku}) - [CZ](https://www.aboutyou.cz/p/nabil/nabil-{sku}) - [DE](https://www.aboutyou.de/p/nabil/nabil-{sku}) - [FR](https://www.aboutyou.fr/p/nabil/nabil-{sku}) - [IT](https://www.aboutyou.it/p/nabil/nabil-{sku}) - [PL](https://www.aboutyou.pl/p/nabil/nabil-{sku}) - [SK](https://www.aboutyou.sk/p/nabil/nabil-{sku}) - [ES](https://www.aboutyou.es/p/nabil/nabil-{sku}) - [NL](https://www.aboutyou.nl/p/nabil/nabil-{sku}) - [BE](https://www.aboutyou.nl/p/nabil/nabil-{sku})", "inline": False}
            fields.append(links)

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
                    "name": "About You"
                }
                }
                ]
            }
            
            
            result = rq.post(group["aboutyou"], data=json.dumps(data), headers={"Content-Type": "application/json"})
            
            try:
                result.raise_for_status()
            except rq.exceptions.HTTPError as err:
                logging.error(err)
            else:
                logging.info(msg=f'[ABOUT YOU] Successfully sent Discord notification to {group["aboutyou"]}')
                print(f'[ABOUT YOU] Successfully sent Discord notification to {group["aboutyou"]}')


    def scrape_site(self,url, headers, proxy):
        """
        Scrapes the specified Shopify site and adds items to array
        """
        items = []

        # Makes request to site
        s = rq.Session()
    
        html = s.get(url, headers=headers, proxies=proxy, verify=False, timeout=20)
        output = json.loads(html.text)['entities']
        
        # Stores particular details in array
        for product in output:
            #Format each Product
            product_item = {
                'title': product['attributes']['brand']['values']['label']+" "+product['attributes']['name']['values']['label'], 
                'image': "https://cdn.aboutstatic.com/file/"+product['images'][0]['hash'] if "images" in product['images'][0]['hash'] else "https://cdn.aboutstatic.com/file/images/"+product['images'][0]['hash'], 
                'id': product['id'],
                'variants': product['variants']}
            items.append(product_item)
        
        
        logging.info(msg='[ABOUT YOU] Successfully scraped site')
        s.close()
        return items

    def remove(self,id,store):
        """
        Remove all Products from INSTOCK with the same id and same Store
        """
        for elem in self.INSTOCK:
            if id == elem["Product"][2] and store == elem["Region"]:
                self.INSTOCK.remove(elem)

    def checkUpdated(self,product, store):
        """
        Check if the Variants got updated
        """
        for elem in self.INSTOCK:
            #Check if Product was not changed
            if product[2] == elem["Product"][2] and product[3] == elem["Product"][3]:
                return [False,False]
                
            #Dont ping if no new size was added
            if product[2] == elem["Product"][2] and len(product[3]) <= len(elem["Product"][3]):
                if all(size in elem["Product"][3] for size in product[3]) and store == elem["Region"]:
                    return [False,True]

        return[True,True]


    def comparitor(self,product, start, groups, store):
        product_item = [product['title'], product['image'], product['id']]

        # Collect all available sizes
        available_sizes = []
        # Stock of every Size
        stocks = {}
        for size in product['variants']:
            if size['stock']['quantity'] > 0 or size['stock']['isSellableWithoutStock']: # Check if size is instock
                available_sizes.append(size['attributes']['vendorSize']['values']['label'])
                stocks[size['attributes']['vendorSize']['values']['label']] = size['stock']['quantity']
        
        product_item.append(available_sizes) # Appends in field
        
        if available_sizes:
            ping, updated = self.checkUpdated(product_item, store)
            if updated or start == 1:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2],store)
                
                self.INSTOCK.append({"Region":store,"Product":product_item})
                if start == 0:
                    print(f"[ABOUT YOU] {product_item}")
                    logging.info(msg=f"[ABOUT YOU] {product_item}")
                if start == 0 and ping:
                    for group in groups:
                        #Send Ping to each Group
                        '''discord_webhook(
                            group=group,
                            title=product['title'],
                            sku=product['id'],
                            store=store,
                            url=f"https://www.aboutyou.{store}/p/nabil/nabil-{product['id']}",
                            thumbnail=product['image'],
                            sizes=available_sizes,
                            stock=stocks,
                            prize=str(product['variants'][0]['price']['withTax']/100)
                        )'''
                        Thread(target=self.discord_webhook,args=(
                            group,
                            product['id'],
                            store,
                            product['title'],
                            f"https://www.aboutyou.{store}/p/nabil/nabil-{product['id']}",
                            product['image'],
                            str(product['variants'][0]['price']['withTax']/100),
                            available_sizes,
                            stocks,
                            )).start()
        else:
            # Remove old version of the product
            self.remove(product_item[2],store)

    def update(self,groups,settings):
        """
        Update groups and settings
        """
        self.groups = groups
        self.delay = settings["aboutyou"]["delay"]
        self.keywords = settings["aboutyou"]["keywords"]
        self.blacksku = settings["aboutyou"]["blacksku"]
        self.proxys = settings["proxys"]

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """
        print(f'STARTING ABOUT YOU MONITOR')
        logging.info(msg='[ABOUT YOU] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        
        STORES = [["DE",139],["CH",431],["FR",658],["ES",670],["IT",671],["PL",550],["CZ",554],["SK",586],["NL",545],["BE",558]]

        # Initialising proxy and headers
        proxy_no = 0
        proxy = {} if len(self.proxys) == 0 else {"http": f"http://{self.proxys[proxy_no]}"}
        headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}

    
        while True:
            try:
                for store in STORES:
                    # Makes request to site and stores products 
                    items = self.scrape_site(f"https://api-cloud.aboutyou.de/v1/products?with=attributes:key(brand|name),variants,variants.attributes:key(vendorSize)&filters[category]=20207,20215&filters[brand]=53709,61263&filters[excludedFromBrandPage]=false&sortDir=desc&sortScore=brand_scores&sortChannel=web_default&page=1&perPage=2000&forceNonLegacySuffix=true&shopId={store[1]}", proxy, headers)
                    for product in items:
                        if int(product['id']) not in self.blacksku:
                            if len(self.keywords) == 0:
                                # If no keywords set, checks whether item status has changed
                                self.comparitor(product, start, self.groups, store[0])

                            else:
                                # For each keyword, checks whether particular item status has changed
                                for key in self.keywords:
                                    if key.lower() in product['title'].lower():
                                        self.comparitor(product, start, self.groups, store[0])

                # Allows changes to be notified
                start = 0

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[ABOUT YOU] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(60)

                # Rotates headers
                headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
                
                if len(self.proxys) != 0:
                    # If optional proxy set, rotates if there are multiple proxies
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {"http": f"http://{self.proxys[proxy_no]}"}


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "aboutyou":"https://discord.com/api/webhooks/954776382603419738/Myj91IW77mVYxCVuR0UBXygDW49CvPJeNej3FHuWl1fKI_VZ4m_ZzrrJyaNGtPKVL5ti"
    }
    aboutyou(groups=[devgroup],proxys=["padifozj-rotate:36cjopf6jt4p@154.13.90.91:80"],keywords=["dunk","jordan 1"],delay=0.1).monitor()
