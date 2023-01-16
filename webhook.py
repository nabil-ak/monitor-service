import logging
from datetime import datetime
import json
import requests as rq


def send(group,webhook,site,title,url,thumbnail,fields):
        """
        Sends a Discord webhook notification to the specified webhook URL
        """
        fields.append({
            "name": "Links", 
            "value": f"[StockX](https://stockx.com/search?s={title.replace(' ','+')}) | [GOAT](https://www.goat.com/search?query={title.replace(' ','+')}) | [Wethenew](https://wethenew.com/search?type=product&q={title.replace(' ','+')})", 
            "inline": False
        })

        data = {
            "username": group["Name"],
            "avatar_url": group["Avatar_Url"],
            "embeds": [{
            "title": title,
            "url": url, 
            "thumbnail": {"url": thumbnail},
            "fields": fields,
            "color": group['Colour'],
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
        
        result = rq.post(webhook, data=json.dumps(data), headers={"Content-Type": "application/json"})
        
        result.raise_for_status()
    
        logging.info(msg=f'[{site}] Successfully sent Discord notification to {group["Name"]} with product {title}')
        print(f'[{site}] Successfully sent Discord notification to {group["Name"]} with product {title}')
            