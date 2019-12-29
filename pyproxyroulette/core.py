import datetime
import time
import threading
from .pool import ProxyPool, ProxyState
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
        self._current_proxy = {}
        self.proxy_pool_update_fnc = func_proxy_pool_updater
        self.update_interval = datetime.timedelta(minutes=20)
        self.update_instance = threading.Thread(target=self._proxy_pool_update_thread)
        self.update_instance.setDaemon(True)
        self.update_instance.start()
        self.debug_mode = debug_mode
        self.cooldown = datetime.timedelta(hours=1, minutes=5)

    def current_proxy(self, return_obj=False):
        current_thread = threading.currentThread().ident
        if current_thread not in self._current_proxy.keys():
            self._current_proxy[current_thread] = None

        if self._current_proxy[current_thread] is not None and \
                self._current_proxy[current_thread].state == ProxyState.ACTIVE:
            if self.debug_mode:
                print("[PPR] Proxy requested but it will not be changed")
        elif self._current_proxy[current_thread] is not None:
            if self.debug_mode:
                print("[PPR] Current proxy not in state ACTIVE. Updating current_proxy for {current_thread} now".format(**locals()))
            self._current_proxy[current_thread].cooldown = self.cooldown
            self._current_proxy[current_thread] = self.proxy_pool.get_best_proxy()
        else:
            if self.debug_mode:
                print("[PPR] No current proxy found. Setting current_proxy for {current_thread} now".format(**locals()))
            self._current_proxy[current_thread] = self.proxy_pool.get_best_proxy()

        if return_obj:
            result = self._current_proxy[current_thread]
        else:
            result = self._current_proxy[current_thread].to_dict()
        return result

    def force_update(self, apply_cooldown=False):
        current_thread = threading.currentThread().ident
        if apply_cooldown:
            if self._current_proxy[current_thread] is not None:
                self._current_proxy[current_thread].cooldown = self.cooldown

        self._current_proxy[current_thread] = self.proxy_pool.get_best_proxy()
        return self._current_proxy

    def proxy_feedback(self, request_success=False, request_failure=False):
        current_thread = threading.currentThread().ident
        if self._current_proxy[current_thread] is not None:
            proxy_obj = self._current_proxy[current_thread]
        else:
            return None

        if request_success and not request_failure:
            proxy_obj.report_success()
        elif request_failure and not request_success:
            proxy_obj.cooldown = datetime.timedelta(minutes=30)
            proxy_obj.report_request_failed()

    def _proxy_pool_update_thread(self):
        while True:
            proxy_list = self.proxy_pool_update_fnc()
            for p in proxy_list:
                self.add_proxy(p[0], p[1], init_responsetime=p[2])
            time.sleep(self.update_interval.total_seconds())

    def add_proxy(self, ip, port, init_responsetime=0):
        self.proxy_pool.add(ip, port, init_responsetime=init_responsetime)

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
