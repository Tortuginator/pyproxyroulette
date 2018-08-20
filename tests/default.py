from pyproxyroulette import ProxyRoulette

pr = ProxyRoulette()
req = pr.get("http://spiegel.de")
print(len(req.content))
req = pr.get("http://spiegel.de")
print(len(req.content))
req = pr.get("http://golem.de")
print(len(req.content))