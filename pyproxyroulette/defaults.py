import datetime, requests


class defaults:
    @staticmethod
    def proxy_is_working(proxy, timeout=5):
        try:
            requests.get("http://icanhazip.com/", proxies=proxy.to_dict(), timeout=timeout)
        except requests.exceptions.ConnectTimeout:
            return False
        except requests.exceptions.ProxyError:
            return False
        return True

    @staticmethod
    def get_proxies_from_web():
        """
        Downloads a list containing proxy ip's and their ports with the security details
        Returns a list of proxyies matching the security requirements
        """
        proxy_list = requests.get("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt")
        proxy_processed = []
        for i in str(proxy_list.content).split("\\n")[3:-2]:
            i_uri, i_port = i.split(" ")[0].split(":")
            proxy_processed.append((i_uri, i_port))
        return proxy_processed
