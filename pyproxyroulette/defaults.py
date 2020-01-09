import requests as requests_original


class defaults:
    @staticmethod
    def proxy_is_working(proxy, timeout=5):
        try:
            res = requests_original.get("http://icanhazip.com/", proxies=proxy.to_dict(), timeout=timeout)
            proxy.response_time = res.elapsed.total_seconds()
        except requests_original.exceptions.ConnectTimeout:
            proxy.response_time = timeout
            return False
        except requests_original.exceptions.ProxyError:
            proxy.response_time = timeout
            return False
        return True

    @staticmethod
    def get_proxies_from_web():
        """
        Downloads a list containing proxy ip's and their ports with the security details
        Returns a list of proxyies matching the security requirements
        """
        proxy_list = requests_original.get("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt")
        proxy_processed = []
        for i in str(proxy_list.content).split("\\n")[10:-2]:
            i_uri, i_port = i.split(" ")[0].split(":")
            proxy_processed.append((i_uri, i_port, 0))
        return proxy_processed

    @staticmethod
    def proxy_response_validator(response):
        return True

    @staticmethod
    def is_anonymous_proxy(proxy, timeout=5):
        # WARNING - this is a external proxy leak service
        try:
            res = requests_original.get("http://proxydb.net/anon", proxies=proxy.to_dict(), timeout=timeout)
        except Exception:
            return False
        if "text-danger" in str(res.content):
            return False
        else:
            return True
