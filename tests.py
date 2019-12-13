from pyproxyroulette import ProxyRoulette, defaults
import requests


@ProxyRoulette.proxy_pool_updater
def cool_proxy_updater():
    return defaults.get_proxies_from_web()


print("Initializing PyProxyRoulette")
pr = ProxyRoulette(debug_mode=True, max_retries=0)

print("Loading Spiegel.de")
req = pr.get("http://spiegel.de")
print("Spiegel.de Content Length:{}".format(len(req.content)))


# Test Decorator
def foo_bar():
    req = requests.get("http://welt.de")
    print(len(req.content))


@pr.proxify()
def foo_bar_deco():
    req = requests.get("http://welt.de")
    print(len(req.content))


# test with and without decorator
foo_bar()
foo_bar_deco()
