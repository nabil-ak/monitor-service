import json
import urllib3
import requests as rq
import logging
import time
import traceback
from datetime import datetime
from threading import Thread
from random_user_agent.params import SoftwareName, HardwareType
from random_user_agent.user_agent import UserAgent


software_names = [SoftwareName.CHROME.value]
hardware_type = [HardwareType.MOBILE__PHONE]
user_agent_rotator = UserAgent(software_names=software_names, hardware_type=hardware_type)

INSTOCK = []

def discord_webhook(group,product):
    """
    Sends a Discord webhook notification to the specified webhook URL
    """
    if group["nbb"] == "":
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
    else:
        logging.info(msg=f'[NBB] Successfully sent Discord notification to {group["nbb"]}')
        print(f'[NBB] Successfully sent Discord notification to {group["nbb"]}')

def monitor(groups,delay=1,proxys=[]):
    urllib3.disable_warnings()
    """
    Initiates the monitor
    """
    print(f'STARTING NBB MONITOR')
    logging.info(msg='[NBB] Successfully started monitor')

    # Initialising proxy and headers
    proxy_no = 0
    proxy_list = proxys
    proxy = {} if len(proxys) == 0 else {"http": f"http://{proxy_list[proxy_no]}"}
    headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}

    while True:
            try:
                # Makes request to site and stores products 
                response = rq.get("https://api.store.nvidia.com/partner/v1/feinventory?skus=DE~NVGFT070~NVGFT080~NVGFT090~NVLKR30S~NSHRMT01~NVGFT060T~187&locale=DE",headers=headers,proxies=proxy,timeout=20)
                items = response.json()["listMap"]
                logging.info(msg='[NBB] Successfully scraped site')
                
                for product in items:
                    if product["is_active"] == "true" and product["fe_sku"] not in INSTOCK and "geforce" in product["product_url"]:
                        for group in groups:
                            Thread(target=discord_webhook,args=(group,product,)).start()
                        INSTOCK.append(product["fe_sku"])
                        print(f"[NBB] {product}")
                    if product["is_active"] == "false" and product["fe_sku"] in INSTOCK:
                        INSTOCK.remove(product["fe_sku"])

                # User set delay
                time.sleep(float(delay))

            except Exception as e:
                print(f"[NBB] Exception found: {traceback.format_exc()}")
                logging.error(e)

                # Rotates headers
                headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
                
                if len(proxys) != 0:
                    # If optional proxy set, rotates if there are multiple proxies
                    proxy_no = 0 if proxy_no == (len(proxy_list) - 1) else proxy_no + 1
                    proxy = {"http": f"http://{proxy_list[proxy_no]}"}



if __name__ == '__main__':
    devgroup = {
        "Name":"Nabil DEV",
        "Avatar_Url":"https://i.imgur.com/H7rGtJ1.png",
        "Colour":1382451,
        "nbb":"https://discord.com/api/webhooks/953640704209485854/qBo9_7bjQNRgfdnsH6PInagJzwuc_EkXAfIKmY7r5jNU234vaI87COUyWlnLyB2W4fur"
    }
    monitor([devgroup])