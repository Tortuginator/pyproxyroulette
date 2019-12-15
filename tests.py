from pyproxyroulette import ProxyRoulette, defaults, exceptions
import requests
import threading


@ProxyRoulette.proxy_pool_updater
def cool_proxy_updater():
    return defaults.get_proxies_from_web()


print("Initializing PyProxyRoulette")
pr = ProxyRoulette(debug_mode=True, max_retries=0)

print("Loading Spiegel.de")
req = pr.get("http://spiegel.de")
print("Spiegel.de Content Length:{}".format(len(req.content)))


def foo_bar():
    req = requests.get("http://welt.de")
    print(len(req.content))


# Test Decorator
@pr.proxify()
def foo_bar_deco():
    req = requests.get("http://welt.de")
    print(len(req.content))


# test with and without decorator
foo_bar()

# Test with decorator
foo_bar_deco()

# Prepare decorator exception test
t1 = threading.Thread(target=foo_bar_deco)

# Test Exception
try:
    t1.start()
except exceptions.DecoratorNotApplicable:
    pr.acknowledge_decorator_restrictions = True

# Now test without the restrictions
# This will fail if the exception is not caught
t1 = threading.Thread(target=foo_bar_deco)
t1.start()
t1.join()

