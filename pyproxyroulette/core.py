import datetime
import time
import threading
from .pool import ProxyPool, ProxyState, ProxyObject
from .defaults import defaults
import logging
from typing import List, Union, Dict, Callable

logger = logging.getLogger(__name__)


class ProxyRouletteCore:
    def __init__(self,
                 func_proxy_pool_updater: Callable = defaults.get_proxies_from_web,
                 func_proxy_validator: Callable = defaults.proxy_is_working,
                 max_timeout: int = 15):
        self.proxy_pool: ProxyPool = ProxyPool(func_proxy_validator=func_proxy_validator,
                                               max_timeout=max_timeout)
        self._current_proxy: Dict = {}
        self.proxy_pool_update_fnc = func_proxy_pool_updater
        self.update_interval: datetime.timedelta = datetime.timedelta(minutes=20)
        self.update_instance = threading.Thread(target=self._proxy_pool_update_thread)
        self.update_instance.setDaemon(True)
        self.update_instance.start()
        self.cooldown: datetime = datetime.timedelta(hours=1, minutes=5)

    def current_proxy(self, return_obj: bool = False) -> Union[Dict, ProxyObject]:
        """
        Returns the proxy of the current thread. THe proxy is changed if the proxy state changes
        The proxy state may change if feedback from this or another thread is submitted which changes the state.
        :param return_obj: bool if the returned proxy is already a dict or a proxy object
        :return:  proxy object or proxy dict
        """
        current_thread = threading.currentThread().ident
        if current_thread not in self._current_proxy.keys():
            self._current_proxy[current_thread] = None

        if self._current_proxy[current_thread] is not None and \
                self._current_proxy[current_thread].state == ProxyState.ACTIVE:
            logger.debug(f"Unchanged proxy returned for thread {current_thread}")
        elif self._current_proxy[current_thread] is not None:
            logger.debug(f"Assigned proxy of thread {current_thread} not in state ACTIVE. Assigning new proxy")
            self._current_proxy[current_thread].cooldown = self.cooldown
            self._current_proxy[current_thread] = self.proxy_pool.get_best_proxy()
        else:
            logging.error(f"No proxy set for thread {current_thread}. Assigning new proxy")
            self._current_proxy[current_thread] = self.proxy_pool.get_best_proxy()

        if return_obj:
            result = self._current_proxy[current_thread]
        else:
            result = self._current_proxy[current_thread].to_dict()
        return result

    def force_update(self, apply_cooldown: bool = False) -> Union[Dict, ProxyObject]:
        """
        Force the system to assign a new proxy to the thread. The old proxy may get a cooldown
        :param apply_cooldown: Apply a cooldown the the old proxy which prevents it from beeing used for the set cooldown period
        :return: the new proxy object
        """
        current_thread = threading.currentThread().ident
        if apply_cooldown:
            if self._current_proxy[current_thread] is not None:
                self._current_proxy[current_thread].cooldown = self.cooldown

        self._current_proxy[current_thread] = self.proxy_pool.get_best_proxy()
        return self._current_proxy

    def proxy_feedback(self, request_success: bool = False, request_failure: bool = False):
        """
        Provide feedback on the proxies performance after a request
        :param request_success: request using the proxy was successfull
        :param request_failure: request using the proxy failed
        :return:
        """
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

    def add_proxy(self, ip: str, port: int, init_responsetime: int = 0):
        self.proxy_pool.add(ip, port, init_responsetime=init_responsetime)

    @property
    def function_proxy_validator(self) -> Callable:
        return self.proxy_pool.function_proxy_validator

    @function_proxy_validator.setter
    def function_proxy_validator(self, value: Callable):
        self.proxy_pool.function_proxy_validator = value

    @property
    def function_proxy_pool_updater(self) -> Callable:
        return self.proxy_pool_update_fnc

    @function_proxy_pool_updater.setter
    def function_proxy_pool_updater(self, value: Callable):
        self.proxy_pool_update_fnc = value

    @property
    def max_timeout(self) -> int:
        return self.proxy_pool.max_timeout

    @max_timeout.setter
    def max_timeout(self, value: int):
        self.proxy_pool.max_timeout = value

    def state(self) -> ProxyState:
        return self.proxy_pool.state()
