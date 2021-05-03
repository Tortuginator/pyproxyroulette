from .defaults import defaults
from .proxy import ProxyObject, ProxyState
import concurrent.futures
import time
import threading
import requests
import datetime
import random
import logging
import queue
from typing import Callable, List

logger = logging.getLogger(__name__)
mutex = threading.Lock()


class ProxyPool:
    def __init__(self,
                 func_proxy_validator: Callable = defaults.proxy_is_working,
                 max_timeout: int = 8):
        self.pool_active: List[ProxyObject] = []
        self.pool_inactive: List[ProxyObject] = []
        self.proxy_is_valid: Callable = func_proxy_validator
        self._max_timeout: int = max_timeout

        self.cleaning_instance = None
        self.checking_instance = None
        self.keyboard_interrupt: bool = False
        self.anonymity_check: bool = True

        # Period to keep dead proxies in dead list
        self.death_keep_period: datetime = datetime.timedelta(hours=12)

        # Start Proxy getter instance
        self.start()

    def start(self):
        if self.cleaning_instance is None or not self.cleaning_instance.is_alive():
            self.cleaning_instance = threading.Thread(target=self._cleaning_worker)
            self.cleaning_instance.setDaemon(True)
            self.cleaning_instance.start()

        if self.checking_instance is None or not self.checking_instance.is_alive():
            self.checking_instance = threading.Thread(target=self._checking_worker)
            self.checking_instance.setDaemon(True)
            self.checking_instance.start()

    def stop(self):
        self.keyboard_interrupt = True
        logger.warning("Termination signal set")
        for i in [self.cleaning_instance, self.checking_instance]:
            i.join()

    def add(self, ip: str, port: int, init_responsetime: int = 0):
        inst = ProxyObject(ip, port, max_timeout=self._max_timeout)
        if init_responsetime != 0:
            inst.response_time = float(init_responsetime)
        if inst not in self.pool_active and inst not in self.pool_inactive:
            self.pool_inactive.append(inst)

    def _active_proxies(self) -> List[ProxyObject]:
        return [p for p in self.pool_active if p.state == ProxyState.ACTIVE]

    def get_best_proxy(self) -> ProxyObject:
        self.start()
        self.pool_active.sort(key=lambda i: i.response_time)
        while not self.has_active_proxy:
            logger.debug("Currently no Usable proxy to get in the system. Waiting")
            time.sleep(2)
        mutex.acquire()
        try:
            active_proxies = self._active_proxies()
        finally:
            mutex.release()
        return active_proxies[0]

    @property
    def has_active_proxy(self) -> bool:
        for p in self.pool_active:
            if p.state == ProxyState.ACTIVE:
                return True
        return False

    def proxy_liveliness_check(self, proxy: ProxyObject) -> bool:
        try:
            proxy.last_checked = datetime.datetime.now()
            check_result = self.proxy_is_valid(proxy, self._max_timeout)
            if check_result:
                if self.anonymity_check:
                    if defaults.is_anonymous_proxy(proxy, self._max_timeout):
                        proxy.report_success()
                    else:
                        logger.debug(f"Leaking proxy {proxy} detected. Removing proxy.")
                        proxy.mark_for_removal()
                else:
                    proxy.report_success()
            else:
                proxy.report_request_failed()
            return check_result

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ProxyError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                ConnectionResetError,
                requests.exceptions.TooManyRedirects):
            proxy.report_request_failed()
            return False

        except Exception as e:
            logger.error(f"An unexpected error occured while lifeliness check. {e}")
            proxy.report_request_failed()
            return False

    def state(self):
        unchecked_proxies = 0
        dead_proxies = 0
        cooldown_proxies = 0
        for p in self.pool_inactive:
            if p.state == ProxyState.UNKNOWN:
                unchecked_proxies += 1
            elif p.state == ProxyState.COOLDOWN:
                cooldown_proxies += 1
            elif p.state == ProxyState.DEAD:
                dead_proxies += 1
        return f"Total: {len(self.pool_active) + len(self.pool_inactive)} | " + \
               f"Active: {len(self.pool_active)} | " + \
               f"Dead: {dead_proxies} | " + \
               f"Cooldown: {cooldown_proxies} | " + \
               f"Unknown: {unchecked_proxies}"

    def _cleaning_worker(self):
        last_round = datetime.datetime.now() - datetime.timedelta(minutes=1)
        while True and not self.keyboard_interrupt:
            while last_round + datetime.timedelta(minutes=1) > datetime.datetime.now():
                time.sleep(5)
                if self.keyboard_interrupt:
                    exit(0)

            # Do some garbage collection
            mutex.acquire()
            try:
                last_round = datetime.datetime.now()

                # Clean Active proxies pool of dead or otherwise deactivated proxies
                for p in [b for b in self.pool_active if b.state is not ProxyState.ACTIVE]:
                    self.pool_active.remove(p)
                    self.pool_inactive.append(p)
                    logger.debug(f"moved proxy {p} to inactive pool")

                # Delete all proxies which are dead longer than the death_keep_period
                for p in [x for x in self.pool_inactive if (x.death_date is not None and
                                                            x.death_date + self.death_keep_period < datetime.datetime.now())
                                                           or x.state == ProxyState.REMOVAL]:
                    self.pool_inactive.remove(p)
                    logger.debug(f"deleted proxy {p}")
            finally:
                mutex.release()

    def _checking_worker(self):
        while True and not self.keyboard_interrupt:
            check_at_once = 30
            mutex.acquire()
            try:
                unchecked_proxies = self.pool_inactive[:check_at_once]
                self.pool_inactive = self.pool_inactive[check_at_once:]
            finally:
                mutex.release()
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                instances = {executor.submit(self.proxy_liveliness_check, p): p for p in unchecked_proxies}
                for future in concurrent.futures.as_completed(instances):
                    future.result()
            mutex.acquire()
            try:
                for p in unchecked_proxies:
                    if p.state == ProxyState.ACTIVE:
                        self.pool_active.append(p)
                    else:
                        self.pool_inactive.append(p)
            finally:
                mutex.release()
            # TODO: maybe check proxies again after some period in the active pool
            if len(self.pool_active) > 100 or len(self.pool_inactive) == 0:
                time.sleep(5)

    @property
    def function_proxy_validator(self) -> Callable:
        return self.proxy_is_valid

    @function_proxy_validator.setter
    def function_proxy_validator(self, value: int):
        self.proxy_is_valid = value

    @property
    def max_timeout(self) -> int:
        return self._max_timeout

    @max_timeout.setter
    def max_timeout(self, value: int):
        self._max_timeout = value
