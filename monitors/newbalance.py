from multiprocessing import Process
from proxymanager import ProxyManager
from concurrent.futures import ThreadPoolExecutor
import requests as rq
import time
import loggerfactory
import traceback
import urllib3
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class newbalance(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.pids = settings["pids"]
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.firstScrape = True
        self.logger = loggerfactory.create(SITE)

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, pid, url, thumbnail, price, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        fields.append({"name": "Price", "value": f"{price}", "inline": True})
        fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
        fields.append({"name": "Stock", "value": f"{str(len(sizes))}+", "inline": True})

        for _ in range((len(sizes)//7)+(1 if len(sizes)%7 != 0 else 0)):
            sizesString = ""
            for size in sizes[:7]:
                sizesString+=f"{size}\n"
            fields.append({"name": f"Size", "value": sizesString, "inline": True})
            sizes = sizes[7:]

        webhook.send(group=group, webhook=group[SITE], site=f"{SITE}", title=title, url=url, thumbnail=thumbnail, fields=fields, logger=self.logger)


    def scrape_site(self, pid):
        """
        Scrape the specific new balance product
        """

        headers = {
            'authority': 'www.newbalance.de',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
        }

        
        #Fetch the Site
        html = rq.get(f"https://www.newbalance.de/on/demandware.store/Sites-BANG-Site/fr_FR/Product-Variation?pid={pid}", headers=headers, proxies=self.proxys.next())
        html.raise_for_status()
        output = html.json()["product"]
        
        product = {
            'title': output['brand']+" "+output['id'].split("-")[0], 
            'image': output['images']['productDetail'][0]['url'], 
            'pid': output['id'],
            'variants': output['variationAttributes'][1]["values"],
            "price":output["price"]["sales"]["formatted"],
            "url":f"https://www.newbalance.fr/{output['id']}.html"
        } if output["online"] else {
            'title': output['brand']+" "+output['id'].split("-")[0], 
            'image': None, 
            'pid': output['id'],
            'variants': [],
            "price":None,
            "url":f"https://www.newbalance.fr/{output['id']}.html"
        }
        
        self.logger.info(msg=f'[{SITE}] Successfully scraped {pid}')
        return product

    def remove(self, pid):
        """
        Remove all Products from INSTOCK with the same pid
        """
        for elem in self.INSTOCK:
            if pid == elem[2]:
                self.INSTOCK.remove(elem)

    def updated(self, product):
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


    def comparitor(self,product):
        product_item = [product['title'], product['image'], product['pid']]

        # Collect all available sizes
        available_sizes = []
        for size in product['variants']:
            if size['selectable']:
                available_sizes.append(size['displayValue'])

        
        product_item.append(available_sizes)
        
        if available_sizes:
            ping, updated = self.updated(product_item)
            if updated or self.firstScrape:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if ping and not self.firstScrape:
                    print(f"[{SITE}] {product_item[0]} got restocked")
                    self.logger.info(msg=f"[{SITE}] {product_item[0]} got restocked")
                    for group in self.groups:
                        #Send Ping to each Group
                        threadrunner.run(
                            self.discord_webhook,
                            group=group,
                            title=product["title"],
                            pid=product['pid'],
                            url=product['url'],
                            thumbnail=product['image'],
                            price=product['price'],
                            sizes=available_sizes,
                        )
        else:
            # Remove old version of the product
            self.remove(product_item[2])

    def run(self):
        urllib3.disable_warnings()
        """
        Initiates the monitor
        """

        print(f'STARTING {SITE} MONITOR')
        
        while True:
            try:
                startTime = time.time()
                with ThreadPoolExecutor(len(self.pids)) as executor:
                    items = [item for item in executor.map(self.scrape_site, self.pids)]
                    # Makes request to the wishlist and stores products 

                    for product in items:
                        self.comparitor(product)                         

                    self.logger.info(msg=f'[{SITE}] Checked in {time.time()-startTime} seconds')

                    self.firstScrape = False
                    
                # User set delay
                time.sleep(float(self.delay))
            except Exception as e:
                print(f"[{SITE}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                time.sleep(3)