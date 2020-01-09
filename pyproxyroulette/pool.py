from .defaults import defaults
from .proxy import ProxyObject, ProxyState
import time
import threading
import requests
import datetime
import random


class ProxyPool:
    def __init__(self,
                 func_proxy_validator=defaults.proxy_is_working,
                 max_timeout=8,
                 debug_mode=False):
        self.pool = []
        self.pool_dead = []
        self.proxy_is_valid = func_proxy_validator
        self._max_timeout = max_timeout
        self.instances = []
        self.debug_mode = debug_mode
        self.worker_instances = 2
        self.keyboard_interrupt = False
        self.anonymity_check = True
        # Period to keep dead proxies in dead list
        self.death_keep_period = datetime.timedelta(days=1)

        # Start Proxy getter instance
        self.start()

    def start(self):
        for i in range(self.worker_instances):
            if i < len(self.instances) and not self.instances[i].isAlive():
                self.instances[i] = (threading.Thread(target=self._worker))
                self.instances[i].setDaemon(True)
                self.instances[i].start()
            elif i >= len(self.instances):
                self.instances.append(threading.Thread(target=self._worker))
                self.instances[i].setDaemon(True)
                self.instances[i].start()

    def stop(self):
        self.keyboard_interrupt = True
        print("[PPR] Termination signal set")
        for i in self.instances:
            i.join()

    def add(self, ip, port, init_responsetime=0):
        inst = ProxyObject(ip, port, max_timeout=self._max_timeout)
        if init_responsetime != 0:
            inst.response_time = float(init_responsetime)
        if inst in self.pool_dead:
            return
        if inst not in self.pool:
            self.pool.append(inst)

    def remove(self, ip, port):
        raise NotImplementedError

    def get_best_proxy(self):
        if not all([i.isAlive() for i in self.instances]) and len(self.instances) >= self.worker_instances:
            self.start()

        active_proxies = [p for p in self.pool if p.state == ProxyState.ACTIVE or p.state == ProxyState.UNKNOWN]

        while len(active_proxies) == 0:
            if self.debug_mode:
                print("[PPR] Currently no Usable proxy to get in the system. Waiting")
            time.sleep(2)
            active_proxies = [p for p in self.pool if p.state == ProxyState.ACTIVE or p.state == ProxyState.UNKNOWN]

        # Obtain a proxy ranking
        ranked_proxies = sorted(active_proxies, key=lambda i: i.response_time)

        ret_proxy = ranked_proxies[0]
        if ret_proxy is None:
            raise Exception("[PPR] Returned 'best proxy' is None")
        return ret_proxy

    def has_usable_proxy(self):
        for p in self.pool:
            if p.state == ProxyState.ACTIVE:
                return True
        return False

    def proxy_liveliness_check(self, proxy):
        try:
            proxy.last_checked = datetime.datetime.now()
            check_result = self.proxy_is_valid(proxy, self._max_timeout)
            if check_result:
                if self.anonymity_check:
                    if defaults.is_anonymous_proxy(proxy, self._max_timeout):
                        proxy.report_success()
                    else:
                        if self.debug_mode:
                            print("[PPR] Leaking/Unresponsive proxy {} detected. Removing proxy.".format(proxy))
                        proxy.set_as_dead()
                else:
                    proxy.report_success()
            else:
                proxy.report_check_failed()
            return check_result
        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ProxyError,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ConnectionError,
                requests.exceptions.TooManyRedirects):
            proxy.report_check_failed()
            return False
        except Exception as e:
            print("[WARNING] an error occured while lifeliness check.")
            print("[WARNING] {}".format(str(e)))
            return False

    def state(self):
        unchecked_proxies = []
        active_proxies = []
        cooldown_proxies = []
        for p in self.pool:
            state = p.state
            if state == ProxyState.UNKNOWN:
                unchecked_proxies.append(p)
            elif state == ProxyState.ACTIVE:
                active_proxies.append(p)
            elif state == ProxyState.COOLDOWN:
                cooldown_proxies.append(p)
        print("[PPR] Total: " + str(len(self.pool)+len(self.pool_dead)) + " | " + "Dead: " + str(len(self.pool_dead)) + " | " + "Active: " + str(len(active_proxies)) + " | " + "Cooldown: " + str(len(cooldown_proxies)) + " | " + "Unknown: " + str(len(unchecked_proxies)))

    def _worker(self):
        last_round = datetime.datetime.now() - datetime.timedelta(minutes=1)
        while True and not self.keyboard_interrupt:
            while last_round + datetime.timedelta(minutes=1) > datetime.datetime.now():
                time.sleep(5)
            last_round = datetime.datetime.now()
            if self.debug_mode:
                self.state()

            # Zero, check for blacklisted proxies
            for b in [p for p in self.pool if p.state == ProxyState.DEAD]:
                self.pool.remove(b)
                self.pool_dead.append(b)
                if self.debug_mode:
                    print("[PPR] Proxy classified as Dead {b}".format(b=b))

            # Remove proxies which are longer dead than the death period
            i = 0
            while i < len(self.pool_dead):
                if self.pool_dead[i].death_date is None:
                    self.pool_dead[i].death_date = datetime.datetime.now()

                if self.pool_dead[i].death_date + self.death_keep_period < datetime.datetime.now():
                    if self.debug_mode:
                        print("[PPR] deleted {}".format(self.pool_dead[i]))
                    del self.pool_dead[i]
                else:
                    i += 1

            # First, check if any proxies have never been checked
            unchecked_proxies = [p for p in self.pool if p.state == ProxyState.UNKNOWN]

            if len(unchecked_proxies) != 0:
                # If proxy does not work according to validator
                chosen_proxy = random.choice(unchecked_proxies)
                check_result = self.proxy_liveliness_check(chosen_proxy)
                if self.debug_mode and not check_result:
                    print("[PPR] Proxy not working {chosen_proxy}".format(**locals()))
                continue

            # Second, see if any proxies have not been checked for a long time
            delta_threshold = datetime.datetime.now() - datetime.timedelta(hours=5)
            unchecked_proxies = [p for p in self.pool if p.last_checked is None]
            recheck_proxies = [p for p in self.pool if p.last_checked is not None and p.last_checked < delta_threshold]

            if len(unchecked_proxies) > 0:
                unchecked_proxies = random.shuffle(unchecked_proxies,random.random)
            else:
                time.sleep(3)

            # check in batches
            if unchecked_proxies is not None:
                for p in unchecked_proxies[:4]:
                     self.proxy_liveliness_check(p)

            if len(recheck_proxies) != 0:
                self.proxy_liveliness_check(recheck_proxies[0])


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
