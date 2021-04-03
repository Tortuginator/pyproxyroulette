from pyproxyroulette import ProxyRoulette, defaults, exceptions
import requests
import threading


@ProxyRoulette.proxy_pool_updater
def cool_proxy_updater():
    return defaults.get_proxies_from_web()


print("Initializing PyProxyRoulette")
pr = ProxyRoulette(max_retries=0)

print("Loading Spiegel.de")
req = pr.get("http://spiegel.de")
print("Spiegel.de Content Length:{}".format(len(req.content)))
print(pr.status())