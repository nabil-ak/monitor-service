from multiprocessing import Process
from proxymanager import ProxyManager
import requests as rq
import time
import loggerfactory
import traceback
import urllib3
import webhook
import threadrunner

SITE = __name__.split(".")[1]

class demandware_wishlist_morelist(Process):
    def __init__(self, groups, settings):
        Process.__init__(self)
        self.groups = groups
        self.site = settings["name"]
        self.domain = settings["domain"]
        self.url = settings["url"]
        self.proxys = ProxyManager(settings["proxys"])
        self.delay = settings["delay"]
        self.imageproxy = settings["imageproxy"]
        self.firstScrape = True
        self.logger = loggerfactory.create(self.site)

        self.INSTOCK = []
        
    def discord_webhook(self, group, title, pid, url, thumbnail, price, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """

        fields = []
        fields.append({"name": "Price", "value": f"{price}", "inline": True})
        fields.append({"name": "Pid", "value": f"{pid}", "inline": True})
        fields.append({"name": "Stock", "value": f"{str(len(sizes))}+", "inline": True})

        i = 0
        for _ in range((len(sizes)//7)+(1 if len(sizes)%7 != 0 else 0)):
            sizesString = ""
            for size in sizes[:i+7]:
                sizesString+=f"{size}\n"
                i+=1
            fields.append({"name": f"Size", "value": sizesString, "inline": True})
            sizes = sizes[i:]

        webhook.send(group=group, webhook=group[self.site], site=f"{self.site}", title=title, url=url, thumbnail=thumbnail, fields=fields, logger=self.logger)


    def scrape_site(self):
        """
        Scrapes the specified Shopify site and adds items to array
        """
        items = []
        page = 1

        headers = {
            'authority': f'www.{self.domain}',
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

        while True:
            #Fetch the Site
            html = rq.get(self.url + f'&pageNumber={page}', headers=headers, proxies=self.proxys.next())
            html.raise_for_status()
            output = html.json()
            
            # Stores particular details in array
            for product in output["wishlist"]["items"]:
                product_item = {
                    'title': product['name'], 
                    'image': product['imageObj']['wishlistSecondImage'][0]['url'], 
                    'pid': product['pid'],
                    'variants': product['variationAttributes'][1]["values"],
                    "price":product["price"]["sales"]["formatted"],
                    "url":f"https://{self.domain}{product['productUrl']}"
                    }
                items.append(product_item)
            if not output["wishlist"]["showMore"]:
                break
            page+=1
        
        self.logger.info(msg=f'[{self.site}] Successfully scraped Page {page}')
        return items

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
            if size['selectable'] and size['fitFinderSelectable'] and size['graySoldOutSizes']:
                available_sizes.append(size['title'])

        
        product_item.append(available_sizes)
        
        if available_sizes:
            ping, updated = self.updated(product_item)
            if updated or self.firstScrape:
                # If product is available but not stored or product is stored but available sizes are changed - sends notification and stores

                # Remove old version of the product
                self.remove(product_item[2])
                
                self.INSTOCK.append(product_item)
                if ping and not self.firstScrape:
                    print(f"[{self.site}] {product_item[0]} got restocked")
                    self.logger.info(msg=f"[{self.site}] {product_item[0]} got restocked")
                    for group in self.groups:
                        #Send Ping to each Group
                        threadrunner.run(
                            self.discord_webhook,
                            group=group,
                            title=product["title"],
                            pid=product['pid'],
                            url=product['url'],
                            thumbnail="https://imageresize.24i.com/?w=300&url="+product['image'] if self.imageproxy else product['image'],
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

        print(f'STARTING {self.site} MONITOR')
        
        while True:
            try:
                startTime = time.time()

                # Makes request to the wishlist and stores products 
                items = self.scrape_site()

                for product in items:
                    self.comparitor(product)                         

                self.logger.info(msg=f'[{self.site}] Checked in {time.time()-startTime} seconds')
                
                # User set delay
                time.sleep(float(self.delay))

            except Exception as e:
                print(f"[{self.site}] Exception found: {traceback.format_exc()}")
                self.logger.error(e)
                time.sleep(3)