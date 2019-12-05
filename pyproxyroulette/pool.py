from .defaults import defaults
from .proxy import ProxyObject
import queue
import random
import time
import threading
import requests
import datetime


class ProxyPool:
    def __init__(self,
                 func_proxy_validator=defaults.proxy_is_working,
                 max_timeout=8,
                 debug_mode=False):
        self.pool = []
        self.pool_blacklist = []
        self.proxy_is_valid = func_proxy_validator
        self._max_timeout = max_timeout
        self.instance = None
        self.debug_mode = debug_mode

        # Start Proxy getter instance
        self.start()

    def start(self):
        self.instance = threading.Thread(target=self._worker)
        self.instance.setDaemon(True)
        self.instance.start()

    def add(self, ip, port, init_responsetime=0):
        inst = ProxyObject(ip, port)
        if init_responsetime != 0:
            inst.response_time = int(init_responsetime)
        if inst in self.pool_blacklist:
            return
        if inst not in self.pool:
            self.pool.append(inst)

    def remove(self, ip, port):
        raise NotImplementedError

    def get(self):
        if self.instance is None:
            raise Exception("The thread to obtain proxies was not started. It can be started using .start()")

        while True:
            usable_proxies = [p for p in self.pool if p.is_usable()]
            if len(usable_proxies) == 0:
                if self.debug_mode:
                    print("[PPR] Currently no Usable proxy to get in the system. Waiting")
                    time.sleep(1)
            else:
                break
        # Obtain a proxy ranking
        ranked_proxies = sorted(usable_proxies, key=lambda i: i.response_time)
        # Try to ingore the response_time == 0 entries if possible
        usability_threshold = 0
        for i in range(0, len(ranked_proxies)):
            if ranked_proxies[i].response_time == 0:
                usability_threshold = i
        if len(ranked_proxies) > usability_threshold + 1:
            usability_threshold = usability_threshold + 1

        ret_proxy = ranked_proxies[usability_threshold]
        if ret_proxy is None:
            raise Exception("[PPR] Returned proxy is None")
        return ret_proxy

    def has_usable_proxy(self):
        for p in self.pool:
            if p.is_usable():
                return True
        return False

    def proxy_liveliness_check(self, proxy):
        try:
            return self.proxy_is_valid(proxy, self._max_timeout)
        except requests.exceptions.ConnectTimeout:
            proxy.response_time = self._max_timeout
            return False
        except requests.exceptions.ProxyError:
            proxy.response_time = self._max_timeout
            return False
        except requests.exceptions.ReadTimeout:
            proxy.response_time = self._max_timeout
            return False
        except requests.exceptions.ChunkedEncodingError:
            proxy.response_time = self._max_timeout
            return False
        except requests.exceptions.ConnectionError:
            proxy.response_time = self._max_timeout
            return False
        except requests.exceptions.TooManyRedirects:
            proxy.response_time = self._max_timeout
            return False
        except Exception as e:
            print("[WARNING] an error occured while lifeliness check.")
            print("[WARNING] {}".format(str(e)))
            return False

    def _worker(self):
        while True:
            # Zero, check for blacklisted proxies
            for b in [p for p in self.pool if p.should_be_blacklisted()]:
                self.pool.remove(b)
                self.pool_blacklist.append(b)
                if self.debug_mode:
                    print("[PPR] Blacklisted {}".format(b))

            # First, check if any proxies have never been checked
            unused_proxies = [p for p in self.pool if p.response_time == 0]
            usable_proxies = [p for p in self.pool if p.is_usable()]
            if self.debug_mode:
                print("[PPR] Pool size: {}| Blacklist size: {}|"
                      " Usable size: {}| Unusable size: {}".format(len(self.pool),
                                                                   len(self.pool_blacklist),
                                                                   len(usable_proxies),
                                                                   len(unused_proxies)))

            if len(unused_proxies) != 0:
                # If proxy does not work according to validator
                if not self.proxy_liveliness_check(unused_proxies[0]):
                    assert(unused_proxies[0].response_time != 0)
                    unused_proxies[0].counter_fails += 1
                    if self.debug_mode:
                        print("[PPR] Checked proxy not working {}".format(unused_proxies[0]))
                continue

            # Second, see if any proxies have not been checked for a long time
            delta_threshold = datetime.datetime.now() - datetime.timedelta(hours=5)
            unchecked_proxies = [p for p in self.pool if p.last_checked is None or p.last_checked < delta_threshold]

            if len(unchecked_proxies) != 0:
                if not self.proxy_liveliness_check(unchecked_proxies[0]):
                    assert (unchecked_proxies[0].response_time != 0)
                    unchecked_proxies[0].counter_fails += 1
                continue
            # Third, check blacklisted proxies
            # TODO

            # Sleep when nothing is to do
            time.sleep(3)

    @property
    def function_proxy_validator(self):
        return self.proxy_is_valid

    @function_proxy_validator.setter
    def function_proxy_validator(self, value):
        self.proxy_is_valid = value

    @property
    def max_timeout(self):
        return self._max_timeout

    @max_timeout.setter
    def max_timeout(self, value):
        self._max_timeout = value
