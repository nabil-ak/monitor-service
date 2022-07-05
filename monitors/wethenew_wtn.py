from user_agent import getcurrentChromeUseragent
import cloudscraper
from threading import Thread
from datetime import datetime
from timeout import timeout
import requests as rq
import time
import json
import logging
import traceback
import random
import urllib3

class wethenew_wtn:
    def __init__(self,groups,user_agent,blacksku=[],delay=1,keywords=[],proxys=[]):

        self.groups = groups
        self.blacksku = blacksku
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxys
        self.proxytime = 0
        self.scraper = cloudscraper.create_scraper(browser={'custom': user_agent})
        self.INSTOCK = []
        self.timeout = timeout()
        
    def discord_webhook(self,group,title, thumbnail, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "wethenew_wtn" not in group:
            return

        fields = []
        fields.append({"name": "Status", "value": f"```🟢 SELL NOW```", "inline": False})
        s = ""
        prices = ""
        links = "\n"
        for size in sizes:
            s+=size["size"]+"\n"
            prices+=str(size["price"])+"€\n"
            links+=f"[ATC](https://sell.wethenew.com/sell-now/{size['id']})\n"
        fields.append({"name": "Sizes", "value": s, "inline": True})
        fields.append({"name": "Prices", "value": prices, "inline": True})
        fields.append({"name": "Links", "value": links, "inline": True})
        
        
        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": "https://sell.wethenew.com/sell-now", 
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
            "author": {
                "name": "wethenew"
            }
            }]
        }
        
        
        result = rq.post(group["wethenew_wtn"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[wethenew_wtn] Exception found: {err}")
        else:
            logging.info(msg=f'[wethenew_wtn] Successfully sent Discord notification to {group["wethenew_wtn"]}')
            print(f'[wethenew_wtn] Successfully sent Discord notification to {group["wethenew_wtn"]}')


    def scrape_site(self, proxy):
        """
        Scrapes Wethenew site and adds items to array
        """

        items = []
        output = []
        skip = 0


        #Get all Products from the Site
        while True:
            response = self.scraper.get(f'https://sell.wethenew.com/api/sell-nows?skip={skip}&take=100', proxies=proxy)
            response.raise_for_status()
            r = response.json()
            for product in r["results"]:
                output.append(product)
            if r["pagination"]["totalPages"] <= r["pagination"]["page"]:
                break
            skip+=100

            #Rotate proxy and delete Cookies after each request
            p = "" if len(self.proxys) == 0 else random.choice(self.proxys)
            proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{p}", "https": f"http://{p}"}
            self.scraper.cookies.clear()
            time.sleep(1)


        # Stores particular details in array
        for product in output:
            product_item = {
                'title': product['brand'] + " " + product['name'], 
                'image': product['image'], 
                'sku': str(product['id']),
                'variants': product['sellNows']
            }
            items.append(product_item)
        
        logging.info(msg=f'[wethenew_wtn] Successfully scraped site')
        return items

    def remove(self,sku):
        """
        Remove all Products from INSTOCK with the same sku
        """
        for elem in self.INSTOCK:
            if sku == elem[2]:
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

    def removeduplicate(self,items):
        """
        Remove duplicates
        """
        newItems = []
        skus = []
        for item in items:
            if item["sku"] not in skus:
                newItems.append(item)
                skus.append(item["sku"])
        
        return newItems

    def comparitor(self,product, start):
        product_item = [product['title'], product['image'], product['sku']]

        product_item.append(product['variants']) # Appends in field
        
        if product['variants']:
            ping, updated = self.updated(product_item)
            if updated or start == 1:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if start == 0:
                    print(f"[wethenew_wtn] {product_item}")
                    logging.info(msg=f"[wethenew_wtn] {product_item}")
                    
                    if ping and self.timeout.ping(product_item):
                        for group in self.groups:
                            #Send Ping to each Group
                            Thread(target=self.discord_webhook,args=(
                                group,
                                product['title'],
                                product['image'],
                                product['variants'],
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
        logging.basicConfig(filename=f'logs/wethenew_wtn.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING wethenew_wtn MONITOR')
        logging.info(msg=f'[wethenew_wtn] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        # Initialising proxy and headers
        proxy_no = 0

        
        while True:
            try:
                proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                startTime = time.time()
                
                
                # Makes request to site and stores products 
                items = self.scrape_site(proxy)

                #Remove duplicates
                items = self.removeduplicate(items)

                for product in items:
                    if product["sku"] not in self.blacksku:
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

                logging.info(msg=f'[wethenew_wtn] Checked in {time.time()-startTime} seconds')

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[wethenew_wtn] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(10)


                #Just update the User_Agent when the Proxy is set
                if proxy != {}:
                    try:
                        # Update User_Agent
                        self.scraper.close()
                        self.scraper = cloudscraper.create_scraper(browser={'custom': getcurrentChromeUseragent()})
                    except Exception as ex:
                        print(f"[wethenew_wtn] Exception found: {traceback.format_exc()}")
                        logging.error(ex)

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
        "wethenew_wtn":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    s = wethenew_wtn(groups=[devgroup],blacksku=[])
    s.monitor()