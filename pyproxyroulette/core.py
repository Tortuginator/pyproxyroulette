import datetime
import time
import threading
from .pool import ProxyPool
from .defaults import defaults


class ProxyRouletteCore:
    def __init__(self, proxy_pool_update_fnc=defaults.get_proxies_from_web):
        self.proxy_pool = ProxyPool()
        self.current_proxy = None
        self.proxy_pool_update_fnc = proxy_pool_update_fnc
        self.update_interval = datetime.timedelta(minutes=20)
        self.update_instance = threading.Thread(target=self._proxy_pool_update_thread)
        self.update_instance.setDaemon(True)
        self.update_instance.start()

    def get_proxy(self):
        if self.current_proxy is not None and self.current_proxy.is_usable():
            return self.current_proxy.to_dict()
        else:
            self.current_proxy.cooldown = datetime.timedelta(hours=1)
            self.current_proxy = self.proxy_pool.get()
            return self.get_proxy()

    def force_update(self):
        self.current_proxy = self.proxy_pool.get()
        return self.current_proxy

    def proxy_feedback(self, request_success=False, request_failure=False):
        if request_success and not request_failure:
            self.current_proxy.counter_requests += 1
        elif request_failure and not request_success:
            self.current_proxy.counter_fails += 1

    def _proxy_pool_update_thread(self):
        while True:
            proxy_list = self.proxy_pool_update_fnc()
            for p in proxy_list:
                self.add_proxy(p[0], p[1])
            time.sleep(self.update_interval.total_seconds())

    def add_proxy(self, ip, port):
        self.proxy_pool.add(ip, port)

