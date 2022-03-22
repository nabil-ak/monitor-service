import logging
from datetime import datetime
import json
import requests as rq

def start_webhook(group,delay,website):
    """
    Send initial Message
    """
    data = {
        "username": group["Name"],
        "avatar_url": group["Avatar_Url"],
        "embeds": [{
            "title": "Start Monitor",
            "description": f"Start monitoring {website} with a delay of {delay} seconds. Thanks for using our monitors!",
            "color": int(group['Colour']),
            "footer": {
                "text": f"{group['Name']} | {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
                "icon_url": group["Avatar_Url"]
            },
            "author": {
                "name": website
            }
        }]
    }
    
    result = rq.post(group["Webhook"], data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except rq.exceptions.HTTPError as err:
        logging.error(err)

def discord_webhook(group,site,title, url, thumbnail,prize, sizes):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        fields = []
        fields.append({"name": "[ PRIZE ]", "value": prize, "inline": False})
        for size in sizes:
            fields.append({"name": size['title'], "value": size['url'], "inline": True})

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
            }
            ]
        }
        
        
        result = rq.post(group["Webhook"], data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        try:
            result.raise_for_status()
        except rq.exceptions.HTTPError as err:
            logging.error(err)
        else:
            logging.info(msg=f'Successfully sent Discord notification to {group["Webhook"]}')
            print(f'Successfully sent Discord notification to {group["Webhook"]}')
            