import json
import urllib3
import requests as rq
import logging
import time
import random
import traceback
from datetime import datetime
from threading import Thread


class nbb:
    def __init__(self,groups,user_agents,delay=1,proxys=[]):
        self.user_agents = user_agents
        self.INSTOCK = []
        self.groups = groups
        self.delay = delay
        self.proxys = proxys
        self.proxytime = 0

    def discord_webhook(self,group,product):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "nbb" not in group:
                return
        fields = []
        fields.append({"name": "Prize", "value": product["price"]+"€", "inline": True})
        fields.append({"name": "SKU", "value": product["fe_sku"], "inline": True})

        if "rtx+3060+ti+founders" in product["product_url"]:
            title = "NVIDIA GEFORCE RTX 3060 Ti Founders Edition"
            thumbnail = "https://assets.nvidia.partners/images/png/nvidia-geforce-rtx-3060-ti.png"
        if "rtx+3070+founders" in product["product_url"]:
            title = "NVIDIA GEFORCE RTX 3070 Founders Edition"
            thumbnail = "https://assets.nvidia.partners/images/png/nvidia-geforce-rtx-3070.png"
        if "rtx+3070+ti+founders" in product["product_url"]:
            title = "NVIDIA GEFORCE RTX 3070 Ti Founders Edition"
            thumbnail = "https://assets.nvidia.partners/images/png/3070-ti-back-300x198.png"
        if "rtx+3080+founders" in product["product_url"]:
            title = "NVIDIA GEFORCE RTX 3080 Founders Edition"
            thumbnail = "https://i.imgur.com/wIbls7G.png"
        if "rtx+3080+ti+founders" in product["product_url"]:
            title = "NVIDIA GEFORCE RTX 3080 Ti Founders Edition"
            thumbnail = "https://assets.nvidia.partners/images/png/3080-ti-back-300x198.png"
        if "rtx+3090+founders" in product["product_url"]:
            title = "NVIDIA GEFORCE RTX 3090 Founders Edition"
            thumbnail = "https://assets.nvidia.partners/images/png/nvidia-geforce-rtx-3090.png"

        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": product["product_url"], 
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
                "author": {
                    "name": "notebookbilliger"
                }
            }]
        }
        result = rq.post(group["nbb"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[NBB] Exception found: {err}")
        else:
            logging.info(msg=f'[NBB] Successfully sent Discord notification to {group["nbb"]}')
            print(f'[NBB] Successfully sent Discord notification to {group["nbb"]}')

    def monitor(self):
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/nbb.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        urllib3.disable_warnings()

        print(f'STARTING NBB MONITOR')
        logging.info(msg='[NBB] Successfully started monitor')

        # Initialising proxy and headers
        proxy_no = 0
        headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}

        while True:
                try:
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                    startTime = time.time()

                    # Makes request to site and stores products 
                    response = rq.get("https://api.store.nvidia.com/partner/v1/feinventory?skus=DE~NVGFT070~NVGFT080~NVGFT090~NVLKR30S~NSHRMT01~NVGFT060T~187&locale=DE",headers=headers,proxies=proxy,timeout=10)
                    items = response.json()["listMap"]
                    logging.info(msg='[NBB] Successfully scraped site')
                    
                    for product in items:
                        if product["is_active"] == "true" and product["fe_sku"] not in self.INSTOCK and "geforce" in product["product_url"]:
                            for group in self.groups:
                                Thread(target=self.discord_webhook,args=(group,product,)).start()
                            self.INSTOCK.append(product["fe_sku"])
                            print(f"[NBB] {product}")
                        if product["is_active"] == "false" and product["fe_sku"] in self.INSTOCK:
                            self.INSTOCK.remove(product["fe_sku"])

                    logging.info(msg=f'[NBB] Checked in {time.time()-startTime} seconds')

                    # User set delay
                    time.sleep(float(self.delay))

                except Exception as e:
                    print(f"[NBB] Exception found: {traceback.format_exc()}")
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
        "nbb":"https://discord.com/api/webhooks/954709947751473202/rREovDHUt60B8ws8ov4dPj0ZP_k5Tf0t-gUnpcEIVQTrmVKzJ1v0alkG5VKoqeZIS85g"
    }
    nbb([devgroup]).monitor()