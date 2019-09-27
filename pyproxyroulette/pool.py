from .defaults import defaults
from .proxy import ProxyObject
import queue
import random
import time
import threading
import requests


class ProxyPool:
    def __init__(self,
                 prepare_getproxy=True,
                 prepare_queue_length=5,
                 proxy_is_working=defaults.proxy_is_working,
                 proxy_timeout=8):
        self.pool = []
        self.pool_blacklist = []
        self.prepare_getproxy = prepare_getproxy
        self.proxy_get_queue = queue.Queue(prepare_queue_length)
        self.proxy_is_working = proxy_is_working
        self.proxy_timeout = proxy_timeout
        self.instance = None
        if self.prepare_getproxy:
            self.instance = threading.Thread(target=self._worker)
            self.instance.setDaemon(True)
            self.instance.start()

    def add(self, ip, port):
        inst = ProxyObject(ip, port)
        if inst in self.pool_blacklist:
            return
        if inst not in self.pool:
            self.pool.append(inst)

    def remove(self, ip, port):
        raise NotImplementedError

    def get(self):
        if not self.prepare_getproxy:
            ret_proxy = self._get_new_proxy()
        else:
            ret_proxy = self.proxy_get_queue.get(False)
        return ret_proxy

    def has_usable_proxy(self):
        for p in self.pool:
            if p.is_usable():
                return True
        return False

    def proxy_liveliness_check(self, proxy):
        try:
            return self.proxy_is_working(proxy, self.proxy_timeout)
        except requests.exceptions.ConnectTimeout:
            return False
        except requests.exceptions.ProxyError:
            return False

    def _get_new_proxy(self):
        if not self.has_usable_proxy():
            # Raise exception as no usable proxy is in the system
            return None
        scanned_indices = []
        while True:
            # Generate new random index
            rand_index = random.randint(0, len(self.pool))
            if rand_index in scanned_indices:
                continue

            # Check if there are working proxies left in the pool
            if len(scanned_indices) >= len(self.pool):
                return None
            scanned_indices.append(rand_index)

            # When the Proxy is usable then check if it is working
            if self.pool[rand_index].is_usable():
                if self.proxy_liveliness_check(self.pool[rand_index]):
                    return self.pool[rand_index]
                else:
                    self.pool[rand_index].counter_fails += 1
                    continue

            # If the proxy is unusable. It is moved to the blacklist
            elif self.pool[rand_index].should_be_blacklisted():
                self.pool_blacklist.append(self.pool[rand_index])
                del self.pool[rand_index]
                scanned_indices = [] # Reset, as all indices are invalid now

    def _worker(self):
        while True:
            if not self.proxy_get_queue.full():
                proxy_obj = self._get_new_proxy()
                self.proxy_get_queue.put(proxy_obj)
            else:
                time.sleep(1)