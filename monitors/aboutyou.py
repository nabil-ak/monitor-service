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



class aboutyou:
    def __init__(self,groups,store,storeid,user_agents,delay=1,keywords=[],proxys=[],blacksku=[],whitesku=[]):
        self.user_agents = user_agents
        self.INSTOCK = []
        self.groups = groups
        self.delay = delay
        self.keywords = keywords
        self.proxys = proxys
        self.proxytime = 0
        self.blacksku = blacksku
        self.whitesku = whitesku
        self.store = store
        self.storeid = storeid
        self.timeout = timeout()

    def discord_webhook(self,group,sku,store,title, url, thumbnail,prize, sizes, stock):
            """
            Sends a Discord webhook notification to the specified webhook URL
            """
            if "aboutyou" not in group:
                return

            fields = []
            fields.append({"name": "Prize", "value": f"```{prize} €```", "inline": True})
            fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
            fields.append({"name": "Region", "value": f"```{store}```", "inline": True})

            sizesSTR = "\n"
            stockSTR = ""
            for size in sizes:
                sizesSTR+=size+"\n"
                stockSTR+=f"{'🟢' if stock[size] >2 else '🟡'} {stock[size]}\n"
            fields.append({"name": "Sizes", "value": f"```{sizesSTR}```", "inline": True})
            fields.append({"name": "Stock", "value": f"```{stockSTR}```", "inline": True})

            links = {"name": "Links", 
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
                print(f"[ABOUT YOU {self.store}] Exception found: {err}")
            else:
                logging.info(msg=f'[ABOUT YOU {self.store}] Successfully sent Discord notification to {group["aboutyou"]}')
                print(f'[ABOUT YOU {self.store}] Successfully sent Discord notification to {group["aboutyou"]}')


    def scrape_site(self,url, headers, proxy):
        """
        Scrapes the specified About You site and adds items to array
        """
        items = []

        # Makes request to site
        s = rq.Session()
    
        html = s.get(url, headers=headers, proxies=proxy, verify=False, timeout=10)
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
        
        
        logging.info(msg=f'[ABOUT YOU {self.store}] Successfully scraped site')
        s.close()
        return items

    def remove(self,id):
        """
        Remove all Products from INSTOCK with the same id
        """
        for elem in self.INSTOCK:
            if id == elem[2]:
                self.INSTOCK.remove(elem)

    def checkUpdated(self,product):
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
            ping, updated = self.checkUpdated(product_item)
            if updated or start == 1:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if start == 0:
                    print(f"[ABOUT YOU {self.store}] {product_item}")
                    logging.info(msg=f"[ABOUT YOU {self.store}] {product_item}")

                    if ping and self.timeout.ping(product_item):
                        for group in self.groups:
                            #Send Ping to each Group
                            Thread(target=self.discord_webhook,args=(
                                group,
                                product['id'],
                                self.store,
                                product['title'],
                                f"https://www.aboutyou.{self.store}/p/nabil/nabil-{product['id']}",
                                product['image'],
                                str(product['variants'][0]['price']['withTax']/100),
                                available_sizes,
                                stocks,
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
        logging.basicConfig(filename=f'logs/aboutyou-{self.store}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)


        print(f'STARTING ABOUT YOU {self.store} MONITOR')
        logging.info(msg=f'[ABOUT YOU {self.store}] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = -1
        headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}

    
        while True:
            try:
                startTime = time.time()
                urls = [
                    f"https://api-cloud.aboutyou.de/v1/products?with=attributes:key(brand|name),variants,variants.attributes:key(vendorSize)&filters[category]=20207&filters[brand]=53709&filters[excludedFromBrandPage]=false&sortDir=desc&sortScore=brand_scores&sortChannel=web_default&page=1&perPage=2000&forceNonLegacySuffix=true&shopId={self.storeid}",
                    f"https://api-cloud.aboutyou.de/v1/products?with=attributes:key(brand|name),variants,variants.attributes:key(vendorSize)&filters[category]=20215&filters[brand]=53709&filters[excludedFromBrandPage]=false&sortDir=desc&sortScore=brand_scores&sortChannel=web_default&page=1&perPage=2000&forceNonLegacySuffix=true&shopId={self.storeid}",
                    f"https://api-cloud.aboutyou.de/v1/products?with=attributes:key(brand|name),variants,variants.attributes:key(vendorSize)&filters[category]=20207&filters[brand]=61263&filters[excludedFromBrandPage]=false&sortDir=desc&sortScore=brand_scores&sortChannel=web_default&page=1&perPage=2000&forceNonLegacySuffix=true&shopId={self.storeid}",
                    f"https://api-cloud.aboutyou.de/v1/products?with=attributes:key(brand|name),variants,variants.attributes:key(vendorSize)&filters[category]=20215&filters[brand]=61263&filters[excludedFromBrandPage]=false&sortDir=desc&sortScore=brand_scores&sortChannel=web_default&page=1&perPage=2000&forceNonLegacySuffix=true&shopId={self.storeid}"
                ]
            
                #Fetch Nike Women, Nike Men, Jordan Women and Jordan Men from About-You
                for url in urls:
                    #Rotate Proxys on each request
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}

                    # Makes request to site and stores products 
                    items = self.scrape_site(url, proxy, headers)
                    for product in items:
                        if int(product['id']) not in self.blacksku:
                            if len(self.keywords) == 0 or int(product['id']) in self.whitesku:
                                # If no keywords set or sku is whitelisted, checks whether item status has changed
                                self.comparitor(product, start)

                            else:
                                # For each keyword, checks whether particular item status has changed
                                for key in self.keywords:
                                    if key.lower() in product['title'].lower():
                                        self.comparitor(product, start)

                # Allows changes to be notified
                start = 0
                
                logging.info(msg=f'[ABOUT YOU {self.store}] Checked in {time.time()-startTime} seconds')

                # User set delay
                time.sleep(float(self.delay))


            except Exception as e:
                print(f"[ABOUT YOU {self.store}] Exception found: {traceback.format_exc()}")
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
        "aboutyou":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    STORES = [["DE",139],["CH",431],["FR",658],["ES",670],["IT",671],["PL",550],["CZ",554],["SK",586],["NL",545],["BE",558]]
    logging.basicConfig(filename=f'aboutyou.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)
    for store in STORES:
        a = aboutyou(groups=[devgroup],proxys=["padifozj-rotate:36cjopf6jt4p@154.13.90.91:80"],keywords=[],delay=0.1,store=store[0],storeid=store[1])
        Thread(target=a.monitor).start()
