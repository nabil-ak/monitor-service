from threading import Thread
from datetime import datetime
from timeout import timeout
from multiprocessing.pool import ThreadPool 
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3
import cloudscraper

class magento:
    def __init__(self,groups,site,store_id,url,user_agent,delay=1,keywords=[],proxys=[],blacksku=[]):

        self.groups = groups
        self.site = site
        self.store_id = store_id
        self.url = url
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxys
        self.proxytime = 0
        self.blacksku = blacksku
        self.user_agent = user_agent

        self.INSTOCK = []
        self.timeout = timeout()
        
    def discord_webhook(self,group,site,title,sku, url, thumbnail,prize):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if self.site not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize} €```", "inline": True})
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


    def scrape_site(self,page, proxy):
        """
        Scrapes the specified magento site and adds items to array
        """
        items = []

        #Fetch the magento-Page
        scraper = cloudscraper.create_scraper(browser={'custom': self.user_agent})
        scraper.headers["Accept"] = "application/json"
        html = scraper.get(f'{self.url}/V1/products-render-info?searchCriteria[pageSize]=100&storeId={self.store_id}&currencyCode=EUR&searchCriteria[currentPage]={page}&searchCriteria[filter_groups][0][filters][0][field]=name&searchCriteria[filter_groups][0][filters][0][value]={random.randint(10000,999999)}&searchCriteria[filter_groups][0][filters][0][condition_type]=nin', proxies=proxy, timeout=10)
        html.raise_for_status()
        output = json.loads(html.text)['items']
        
        # Stores particular details in array
        for product in output:
            product_item = {
                'name': product['name'],
                'url': product['url'],  
                'image': product['images'][0]['url'] if product['images'] else "", 
                'sku': str(product['id']),
                'price': str(product['price_info']['final_price']),
                'is_salable': str(product['is_salable'])
                }
            items.append(product_item)
        scraper.close()
        logging.info(msg=f'[{self.site}] Successfully scraped Page {page}')
        return items

    def comparitor(self,product, start):
        """
            Check if the Product is instock
        """
        if product['is_salable'] == "1":
            if product['sku'] not in self.INSTOCK:
                    self.INSTOCK.append(product['sku'])
                    if start == 0:
                        print(f"[{self.site}] {product}")
                        logging.info(msg=f"[{self.site}] {product}")

                        if self.timeout.ping(product):
                            for group in self.groups:
                                #Send Ping to each Group
                                Thread(target=self.discord_webhook,args=(
                                    group,
                                    self.site,
                                    product["name"],
                                    product['sku'],
                                    product['url'],
                                    product['image'],
                                    product['price']
                                    )).start()
        else:
            try:
                self.INSTOCK.remove(product['sku'])
            except:
                pass

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
        proxy = {}
        

        maxpage = 10
        
        while True:
            try:
                startTime = time.time()

                args = []
                for page in range(1,maxpage):
                    #Rotate Proxys on each request
                    proxy_no = 0 if proxy_no == (len(self.proxys) - 1) else proxy_no + 1
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                    args.append(( page, proxy))

                # Makes request to the pages and stores products 
                threadpool = ThreadPool(maxpage)
                itemsSplited = threadpool.starmap(self.scrape_site, args)

                items = sum(itemsSplited, [])

                for product in items:
                        if product["sku"] not in self.blacksku:
                            if len(self.keywords) == 0:
                                # If no keywords and tags set, checks whether item status has changed
                                self.comparitor(product, start)

                            else:
                                # For each keyword, checks whether particular item status has changed
                                for key in self.keywords:
                                    if key.lower() in product['name'].lower():
                                        self.comparitor(product, start)


                logging.info(msg=f'[{self.site}] Checked in {time.time()-startTime} seconds')
                

                # Allows changes to be notified
                start = 0

                #Check if maxpage is reached otherwise increase by 5
                try:
                    maxpage = itemsSplited.index([])+2
                except:
                    maxpage+=5
                    start = 1

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[{self.site}] Exception found: {traceback.format_exc()}")
                logging.error(e)

                # Safe time to let the Monitor only use the Proxy for 5 min
                if proxy == {}:
                    self.proxytime = time.time()+300


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "kith":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    s = magento(site="asphaltgold",groups=[devgroup],url="https://asphaltgold.com/products.json",user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}])
    s.monitor()