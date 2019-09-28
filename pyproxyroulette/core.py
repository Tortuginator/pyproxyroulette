import datetime
import time
import threading
from .pool import ProxyPool
from .defaults import defaults


class ProxyRouletteCore:
    def __init__(self, proxy_pool_update_fnc=defaults.get_proxies_from_web, debug_mode=False):
        self.proxy_pool = ProxyPool(debug_mode=debug_mode)
        self._current_proxy = None
        self.proxy_pool_update_fnc = proxy_pool_update_fnc
        self.update_interval = datetime.timedelta(minutes=20)
        self.update_instance = threading.Thread(target=self._proxy_pool_update_thread)
        self.update_instance.setDaemon(True)
        self.update_instance.start()
        self.debug_mode = debug_mode

    @property
    def current_proxy(self):
        if self._current_proxy is not None and self._current_proxy.is_usable():
            if self.debug_mode:
                print("Proxy requested, decided: not changeing proxy")
            return self._current_proxy.to_dict()
        elif self._current_proxy is not None:
            if self.debug_mode:
                print("Proxy not usable. Updating current_proxy now")
            self._current_proxy.cooldown = datetime.timedelta(hours=1)
            self._current_proxy = self.proxy_pool.get()
            return self._current_proxy.to_dict()
        else:
            if self.debug_mode:
                print("No proxy set. Updating current_proxy now")
            self._current_proxy = self.proxy_pool.get()
            return self._current_proxy.to_dict()

    def force_update(self):
        self._current_proxy = self.proxy_pool.get()
        return self._current_proxy

    def proxy_feedback(self, request_success=False, request_failure=False, request_fatal=False):
        if request_success and not request_failure and not request_fatal:
            self._current_proxy.counter_requests += 1
        elif request_failure and not request_success and not request_fatal:
            self._current_proxy.counter_fails += 1
        elif request_fatal and not request_success and not request_failure:
            self._current_proxy.counter_fatal += 1

    def _proxy_pool_update_thread(self):
        while True:
            proxy_list = self.proxy_pool_update_fnc()
            for p in proxy_list:
                self.add_proxy(p[0], p[1])
            self.proxy_pool.flag_proxies_loaded = True
            time.sleep(self.update_interval.total_seconds())

    def add_proxy(self, ip, port):
        self.proxy_pool.add(ip, port)

