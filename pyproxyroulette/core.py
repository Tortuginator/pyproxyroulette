import datetime
import time
import threading
from .pool import ProxyPool
from .defaults import defaults


class ProxyRouletteCore:
    def __init__(self,
                 func_proxy_pool_updater=defaults.get_proxies_from_web,
                 func_proxy_validator=defaults.proxy_is_working,
                 debug_mode=False,
                 max_timeout=15):
        self.proxy_pool = ProxyPool(debug_mode=debug_mode,
                                    func_proxy_validator=func_proxy_validator,
                                    max_timeout=max_timeout)
        self._current_proxy = None
        self.proxy_pool_update_fnc = func_proxy_pool_updater
        self.update_interval = datetime.timedelta(minutes=20)
        self.update_instance = threading.Thread(target=self._proxy_pool_update_thread)
        self.update_instance.setDaemon(True)
        self.update_instance.start()
        self.debug_mode = debug_mode
        self.proxy_current_thlock = threading.Lock()

    def current_proxy(self, return_obj=False):
        self.proxy_current_thlock.acquire()

        if self._current_proxy is not None and self._current_proxy.is_usable():
            if self.debug_mode:
                print("Proxy requested, decided: not changeing proxy")
        elif self._current_proxy is not None:
            if self.debug_mode:
                print("Proxy not usable. Updating current_proxy now")
            self._current_proxy.cooldown = datetime.timedelta(hours=1)
            self._current_proxy = self.proxy_pool.get()
        else:
            if self.debug_mode:
                print("No proxy set. Updating current_proxy now")
            self._current_proxy = self.proxy_pool.get()

        if return_obj:
            result = self._current_proxy
        else:
            result = self._current_proxy.to_dict()

        self.proxy_current_thlock.release()
        return result

    def force_update(self, last_proxy_obj=None):
        if last_proxy_obj is not None:
            if last_proxy_obj != self._current_proxy:
                if self.debug_mode:
                    print("Force update not executed, as current proxy has already been changed")
                return self._current_proxy
        self._current_proxy = self.proxy_pool.get()
        return self._current_proxy

    def proxy_feedback(self, request_success=False, request_failure=False, request_fatal=False, proxy_obj=None):
        if proxy_obj is None:
            proxy_obj = self._current_proxy
        if request_success and not request_failure and not request_fatal:
            proxy_obj.counter_requests += 1
        elif request_failure and not request_success and not request_fatal:
            proxy_obj.counter_fails += 1
        elif request_fatal and not request_success and not request_failure:
            proxy_obj.counter_fatal += 1

    def _proxy_pool_update_thread(self):
        while True:
            proxy_list = self.proxy_pool_update_fnc()
            for p in proxy_list:
                self.add_proxy(p[0], p[1])
            self.proxy_pool.flag_proxies_loaded = True
            time.sleep(self.update_interval.total_seconds())

    def add_proxy(self, ip, port):
        self.proxy_pool.add(ip, port)

    @property
    def function_proxy_validator(self):
        return self.proxy_pool.function_proxy_validator

    @function_proxy_validator.setter
    def function_proxy_validator(self, value):
        self.proxy_pool.function_proxy_validator = value

    @property
    def function_proxy_pool_updater(self):
        return self.proxy_pool_update_fnc

    @function_proxy_pool_updater.setter
    def function_proxy_pool_updater(self, value):
        self.proxy_pool_update_fnc = value

    @property
    def max_timeout(self):
        return self.proxy_pool.max_timeout

    @max_timeout.setter
    def max_timeout(self, value):
        self.proxy_pool.max_timeout = value
