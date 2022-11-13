from threading import Thread
from datetime import datetime
from timeout import timeout
import requests as rq
import tls
import time
import json
import logging
import traceback
import urllib3

class wethenew:
    def __init__(self,groups,endpoint,user_agent,proxymanager,blacksku=[],delay=1,keywords=[]):

        self.groups = groups
        self.endpoint = endpoint
        self.blacksku = blacksku
        self.delay = delay
        self.keywords= keywords
        self.proxys = proxymanager
        self.user_agent = user_agent
        self.INSTOCK = []
        self.timeout = timeout()

        self.sizesKey = {
            "products":"wantedSizes",
            "sell-nows":"sellNows",
            "consignment-slots":"sizes"
        }

        
    def discord_webhook(self,group,sku,title, thumbnail, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if not any(["wethenew" not in g for g in group]):
            return

        fields = []
        if self.endpoint == "sell-nows":
            s = ""
            prices = ""
            links = "\n"
            for size in sizes:
                s+=f"`{size['size']}`\n"
                prices+=f"`{size['price']}€`\n"
                links+=f"[ATC](https://sell.wethenew.com/instant-sales/{size['id']})\n"
            fields.append({"name": "Sizes", "value": s, "inline": True})
            fields.append({"name": "Prices", "value": prices, "inline": True})
            fields.append({"name": "Accept", "value": links, "inline": True})
        else:
            s = ""
            status = ""
            for size in sizes:
                s+=size+"\n"
                status+="🟡 WTB\n"
            fields.append({"name": "SKU", "value": f"```{sku}```", "inline": False})
            fields.append({"name": "Sizes", "value": f"```{s}```", "inline": True})
            fields.append({"name": "Status", "value": f"```{status}```", "inline": True})
        
        fields.append({"name": "Links", "value": f"[STOCKX](https://stockx.com/search?s={title.replace(' ', '+')}) | [WETHENEW](https://wethenew.com/search?type=product&q={title.replace(' ', '+')})", "inline": False})
        
        
        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": f"https://sell.wethenew.com/{'consignment' if self.endpoint == 'consignment-slots' else 'listing'}/product/"+sku, 
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
            "author": {
                "name": f"wethenew-{self.endpoint}"
            }
            }]
        }
        
        
        result = rq.post(group[f"wethenew-{self.endpoint}"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[wethenew-{self.endpoint}] Exception found: {err}")
        else:
            logging.info(msg=f'[wethenew-{self.endpoint}] Successfully sent Discord notification to {group["wethenew-{self.endpoint}"]}')
            print(f'[wethenew-{self.endpoint}] Successfully sent Discord notification to {group["wethenew-{self.endpoint}"]}')


    def scrape_site(self):
        """
        Scrapes Wethenew site and adds items to array
        """

        items = []
        output = []
        skip = 0


        #Get all Products from the Site
        while True:
            url = f"https://api-sell.wethenew.com/{self.endpoint}?skip={skip}&take=100&onlyWanted=true"
            logging.info(msg=f'[wethenew] Scrape {url}')
            response = tls.get(url, proxies=self.proxys.next(), headers={
                'user-agent': self.user_agent
            })
            response.raise_for_status()
            r = response.json()
            for product in r["results"]:
                output.append(product)
            if r["pagination"]["totalPages"] <= r["pagination"]["page"]:
                break
            skip+=100


        # Stores particular details in array
        for product in output:
            product_item = {
                'title': product['brand'] + " " + product['name'], 
                'image': product['image'], 
                'sku': str(product['id']),
                'variants': product[self.sizesKey[self.endpoint]]
            }
            items.append(product_item)
        
        logging.info(msg=f'[wethenew-{self.endpoint}] Successfully scraped site')
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
                    print(f"[wethenew-{self.endpoint}] {product_item}")
                    logging.info(msg=f"[wethenew-{self.endpoint}] {product_item}")
                    
                    if ping and self.timeout.ping(product_item):
                        for group in self.groups:
                            #Send Ping to each Group
                            Thread(target=self.discord_webhook,args=(
                                group,
                                product['sku'],
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
        logging.basicConfig(filename=f'logs/wethenew-{self.endpoint}.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        print(f'STARTING wethenew-{self.endpoint} MONITOR')
        logging.info(msg=f'[wethenew-{self.endpoint}] Successfully started monitor')

        # Ensures that first scrape does not notify all products
        start = 1

        
        while True:
            try:
                startTime = time.time()
                
                # Makes request to site and stores products 
                items = self.scrape_site()

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

                logging.info(msg=f'[wethenew-{self.endpoint}] Checked in {time.time()-startTime} seconds')

                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[wethenew-{self.endpoint}] Exception found: {traceback.format_exc()}")
                logging.error(e)
                time.sleep(10)


if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "wethenew":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    s = wethenew(groups=[devgroup],blacksku=[])
    s.monitor()