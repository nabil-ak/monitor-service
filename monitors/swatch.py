import json
import urllib3
import requests as rq
import logging
import time
import random
import traceback
from datetime import datetime
from threading import Thread


class swatch:
    def __init__(self,groups,user_agents,delay=1,proxys=[]):
        self.user_agents = user_agents
        self.INSTOCK = []
        self.groups = groups
        self.delay = delay
        self.proxys = proxys
        self.proxytime = 0

    def discord_webhook(self,group,watch):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        if "swatch" not in group:
                return
        fields = []
        fields.append({"name": "SKU", "value": watch["sku"], "inline": True})

        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": watch['name'],
            "url": f"https://www.swatch.com/de-de/{watch['sku']}.html", 
            "thumbnail": {"url": watch['image']},
            "fields": fields,
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
                },
                "author": {
                    "name": "Swatch"
                }
            }]
        }
        result = rq.post(group["swatch"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
            print(f"[swatch] Exception found: {err}")
        else:
            logging.info(msg=f'[swatch] Successfully sent Discord notification to {group["swatch"]}')
            print(f'[swatch] Successfully sent Discord notification to {group["swatch"]}')

    def monitor(self):
        """
        Initiates the monitor
        """

        #Initiate the Logger
        logging.basicConfig(filename=f'logs/swatch.log', filemode='w', format='%(asctime)s - %(name)s - %(message)s',
            level=logging.DEBUG)

        urllib3.disable_warnings()

        print(f'STARTING swatch MONITOR')
        logging.info(msg='[swatch] Successfully started monitor')

        # Initialising proxy and headers
        proxy_no = 0
        headers = {'User-Agent': random.choice(self.user_agents)["user_agent"]}

        while True:
                try:
                    proxy = {} if len(self.proxys) == 0 or self.proxytime <= time.time() else {"http": f"http://{self.proxys[proxy_no]}", "https": f"http://{self.proxys[proxy_no]}"}
                    startTime = time.time()

                    watches = [{"name":"Mission to the Sun","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw39e32ab0/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Sun_670x670.jpg","sku":"SO33J100"},{"name":"Mission to Mercury","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw6454db48/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Mercury_670x670.jpg","sku":"SO33A100"},
                    {"name":"Mission to Venus","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw88d1779b/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Venus_670x670.jpg","sku":"SO33P100"},{"name":"Mission on Earth","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dwbc19e5ac/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Earth_670x670.jpg","sku":"SO33G100"},
                    {"name":"Mission to the Moon","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw7f5be8ef/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Moon_670x670.jpg","sku":"SO33M100"},{"name":"Mission to Mars","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw805f9d9c/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Mars_670x670.jpg","sku":"SO33R100"},
                    {"name":"Mission to Jupiter","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw4be986fc/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Jupiter_670x670.jpg","sku":"SO33C100"},{"name":"Mission to Saturn","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw89700700/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Saturne_670x670.jpg","sku":"SO33T100"},
                    {"name":"Mission to Uranus","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dwb86e0273/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Uranus_670x670.jpg","sku":"SO33L100"},{"name":"Mission to Neptune","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw268ab8f1/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Neptune_670x670.jpg","sku":"SO33N100"},
                    {"name":"Mission to Pluto","image":"https://www.swatch.com/dw/image/v2/BDNV_PRD/on/demandware.static/-/Library-Sites-swarp-global/default/dw52419f75/images/Swatch/collections/2022/moonswatch/single-card/single_card_variation_2_Pluto_670x670.jpg","sku":"SO33M101"}]
                    # Makes request to site and stores products 
                    for watch in watches:
                        params = {
                            'pid': watch["sku"],
                            'pname': 'BLITE',
                            'qty': '1',
                            'readytoorder': 'true',
                            'brand': 'swatch',
                            'hasvariations': 'false',
                        }
                        response = rq.get("https://www.swatch.com/on/demandware.store/Sites-swarp-EU-Site/de_DE/Cart-AddToCartTileBtn",headers=headers,proxies=proxy,params=params,timeout=10)
                        response.raise_for_status()


                        if "button" not in response.text:
                            if watch["sku"] not in self.INSTOCK:
                                for group in self.groups:
                                    Thread(target=self.discord_webhook,args=(group,watch,)).start()
                                logging.info(msg=f'[swatch] {watch["name"]} is available')
                                print(f'[swatch] {watch["name"]} is available')
                                self.INSTOCK.append(watch["sku"])
                                time.sleep(float(self.delay))
                                continue
                        if watch["sku"] in self.INSTOCK:
                            self.INSTOCK.remove(watch["sku"])
                        time.sleep(float(self.delay))

                    logging.info(msg=f'[swatch] Checked in {time.time()-startTime} seconds')

                except Exception as e:
                    print(f"[swatch] Exception found: {traceback.format_exc()}")
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
        "swatch":"https://discord.com/api/webhooks/959045183448698930/k_pKi0GaBkaey0ABSqMsYWPPSZ8op-0hUao8Uk_g0tSlYtM4ju7END05H7W5z2mAR7nD"
    }
    swatch(delay=2,groups=[devgroup],user_agents=[{"user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0"}],proxys=["zlinqims-rotate:nibyi3ldiniu@p.webshare.io:80"]).monitor()