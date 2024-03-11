# Monitor-Service

A monitor service that was monitoring over 100 pages for exclusive items, using keywords or products ids.
It helped members of cookgroups to make multiple thousand euros in profit from these exclusive restocks of sneakers, collectibles
and other profitable items.

## Supported Sites

- aboutyou
- asos
- bsn
- courir
- demandware
- eleventeamsports
- kickz
- newbalance
- nittygrittystore
- pid_bruteforcer
- prodirectsoccer_release
- prodirectsoccer
- salomen
- shopify_priceerror
- shopify
- svd
- wethenew
- zuslassungsstelle
- many more....

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the requirement frameworks.

```bash
pip install -r requirements.txt
```
## Settings
- Set the ```db``` connection string to your **MongoDB** database,
```env
db = mongodb+srv://......
```
## Usage
Create three collections in the **MongoDB** database ```groups```, ```proxys```:
1. ```groups``` - all the cook groups with their custom settings and webhook url for each site
2. ```proxys``` - proxy groups that can be used for specific sites to bypass their IP restrictions
3. ```settings``` - all global settings like the keywords that are monitored, the pids, which site, the delay

Many sites are protected by a bot protecion that has to be bypassed.
- You can use a ```tls proxy``` that will imitate tls headers of a real browser to bypass cloudflare for example
- Many ```proxys``` to not get rate limited by the sites and also map specific proxysgroups to sites when they ban a subnet
- A ```image proxy``` to bypass the IP restriction of the CDN of the sites, when they ban discords IP

## Docker
1. Create a Docker image
```
docker build -t monitor-service .
```

2. Run it
```
docker run -d --name monitor-service --env-file .env monitor-service
```

You can also use ```docker compose``` to spin up multiple containers of the microservices you need.

## Example
<img src="https://i.imgur.com/D3RSTpf.png" alt="icon" width="512" hight="512"/>


## License
[MIT](https://choosealicense.com/licenses/mit/)