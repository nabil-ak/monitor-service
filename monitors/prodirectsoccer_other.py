from threading import Thread
from datetime import datetime,timedelta
from bs4 import BeautifulSoup
import random
import requests as rq
import time
import json
import logging
import traceback
import urllib3

class prodirectsoccer_other:
    def __init__(self,name,releasecategory,groups,user_agents,delay=2,querys=[],blacksku=[],proxys=[]):
        self.user_agents = user_agents
        self.name = name
        self.releasecategory = releasecategory
        self.groups = groups
        self.delay = delay
        self.querys= querys
        self.proxys = proxys
        self.blacksku = blacksku
        self.proxytime = 0

        self.INSTOCK = []
        self.RELEASEINSTOCK = []
        
    def discord_webhook(self,group,title,sku, url, thumbnail,prize,launchdate=None):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "prodirectsoccer" not in group:
            return

        fields = []
        fields.append({"name": "Prize", "value": f"```{prize}```", "inline": True})
        fields.append({"name": "SKU", "value": f"```{sku}```", "inline": True})
        if not launchdate:
            fields.append({"name": "Status", "value": f"```🟢 INSTOCK```", "inline": True})
        else:
            fields.append({"name": "Status", "value": f"```🟡 RELEASE```", "inline": True})
            fields.append({"name": "Launchdate", "value": f"```{launchdate[-2:]}/{launchdate[4:6]}/{launchdate[:4]}```", "inline": True})
        

        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": url, 
            "thumbnail": {"url": "https://image-proxy.nabil-ak.repl.co/"+thumbnail},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
            "author": {
                "name": self.name
            }
            }]
        }
        
        
        result = rq.post(group["prodirectsoccer"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[{self.name}] Exception found: {err}")
        else:
            logging.info(msg=f'[{self.name}] Successfully sent Discord notification to {group[self.name]}')
            print(f'[{self.name}] Successfully sent Discord notification to {group[self.name]}')


    def scrape_site(self,query,headers, proxy):
        """
        Scrapes the specified prodirectsoccer query site and adds items to array
        """
        items = []

        #Page Counter
        page = 1

        #Last Url
        lasturl = ""

        #Scrape all available Pages
        while True:
            url = f"https://www.{self.name}.com/search.aspx?q={query}&pp=96&p={page}"

            #Set right referer
            headers["referer"] = url

            # Makes request to site
            html = rq.get(url,  headers=headers, proxies=proxy, verify=False, timeout=10)
            html.raise_for_status()

            output = BeautifulSoup(html.text, 'html.parser')
            products = output.find_all('div', {'class': 'item'})
            if html.url == lasturl:
                break
            
            lasturl = html.url

            # Stores particular details in array
            for product in products:
                nameandurl = product.find_all('a')[1]
                product_item = {
                        "name":nameandurl.text,
                        "sku":nameandurl["href"].split('-')[-1].replace(".aspx",""),
                        "prize":product.find("p", {'class': 'price'}).text.strip(),
                        "image":"https://"+product.find('img')["src"].replace("//",""),
                        "url":nameandurl["href"]
                        }
                items.append(product_item)

            page+=1
        
        logging.info(msg=f'[{self.name}] Successfully scraped Query {query}')
        return items

    def scrape_release_site(self,query,headers, proxy):
        """
        Scrapes the specified prodirectsoccer release query site and adds items to array
        """
        items = []

        # Makes request to site
        html = rq.get(f"https://query.published.live1.suggest.eu1.fredhopperservices.com/pro_direct/json?scope=//catalog01/en_GB/categories%3E%7B{self.releasecategory}%7D&search={query}&callback=jsonpResponse",  headers=headers, proxies=proxy, verify=False, timeout=10)
        html.raise_for_status()

        products = json.loads(html.text[14:-1])["suggestionGroups"][1]["suggestions"]
       

        # Stores particular details in array
        for product in products:
            product_item = {
                    "name":product["name"],
                    "sku":product["quickref"],
                    "prize":product["currentprice"].replace("000",""),
                    "image":product["_thumburl"],
                    "url":product["producturl"],
                    "launchdate":product["launchdate"]
                    }
            items.append(product_item)

         
        
        logging.info(msg=f'[{self.name}] Successfully scraped releases for query {query}')
        return items
        

    def monitor(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/{self.name}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING {self.name} MONITOR')
        logging.info(msg=f'{self.name} Successfully started monitor')

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

                    # Makes request to query-site and stores products 
                    items = self.scrape_site(query, headers, proxy)
                    for product in items:
                        if product["sku"] not in self.blacksku:
                            # Check if Product is INSTOCK
                            if product["sku"] not in self.INSTOCK and start != 1:
                                print(f"[{self.name}] {product}")
                                logging.info(msg=f"[{self.name}] {product}")
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
                    
                    self.INSTOCK = products.copy()
                    products.clear()
                    
                    # Make request to release-site and stores products
                    items = self.scrape_release_site(query, headers, proxy)
                    for product in items:
                        date = datetime.strptime(f"{product['launchdate'][-2:]}/{product['launchdate'][4:6]}/{product['launchdate'][:4]}","%d/%m/%Y")
                        if product["sku"] not in self.blacksku and date>(datetime.now()-timedelta(days=1)):
                            # Check if Product is INSTOCK
                            if product not in self.RELEASEINSTOCK and start != 1:
                                print(f"[{self.name}] {product}")
                                logging.info(msg=f"[{self.name}] {product}")
                                for group in self.groups:
                                    #Send Ping to each Group
                                    Thread(target=self.discord_webhook,args=(
                                        group,
                                        product['name'],
                                        product['sku'],
                                        product['url'],
                                        product['image'],
                                        product['prize'],
                                        product['launchdate']
                                        )).start()

                            products.append(product)

                    self.RELEASEINSTOCK = products

                    time.sleep(self.delay)

                

                # Allows changes to be notified
                start = 0

                #Shuffle Query Order
                random.shuffle(self.querys)
                logging.info(msg=f'[{self.name}] Checked all querys in {time.time()-startTime} seconds')

            except Exception as e:
                print(f"[{self.name}] Exception found: {traceback.format_exc()}")
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
        "prodirectsoccer":"https://discord.com/api/webhooks/954818030834188368/v4kzvzQxIHl_Bm_F35E5wl4E6gF0ucM3rde4rQTOs9Ic__JjnIul-NxyUIPb1tUKmLtG"
    }
    s = prodirectsoccer_other(name="prodirectselect",releasecategory="basketballengb",groups=[devgroup],user_agents=[{"user_agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/604.18 FABUILD-IOS/6.0.1 FABUILD-IOS-iOS/6.0.1 APP/6.0.1"}],querys=["jordan"])
    s.monitor()