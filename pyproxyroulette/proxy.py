import datetime


class ProxyObject:
    def __init__(self, _ip, _port):
        self.ip = _ip
        self.port = _port
        self.counter_requests = 0
        self.counter_fails = 0
        self._cooldown = None
        self.counter_fatal = 0
        self.last_checked = None

        # Criteria: usability config
        self.max_fatal_count = 1
        self.max_fail_count = 3

        self.__response_time_total = 0
        self.__response_counter = 0

    def is_in_cooldown(self):
        if self._cooldown is None:
            return False
        if self._cooldown >= datetime.datetime.now():
            return True
        self._cooldown = None
        return False

    @property
    def cooldown(self):
        if self._cooldown is not None:
            return self._cooldown
        return False

    @cooldown.setter
    def cooldown(self, _cooldown_timeperiod):
        assert(isinstance(_cooldown_timeperiod, datetime.timedelta) or _cooldown_timeperiod is None)
        if _cooldown_timeperiod is None:
            self._cooldown = None
            return
        self._cooldown = datetime.datetime.now() + _cooldown_timeperiod

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.ip == self.ip and other.port == self.port

    def __hash__(self):
        return hash(self.ip) ^ hash(self.port)

    def to_dict(self):
        return {"http": str(self.ip) + ":" + str(self.port),
                "https": str(self.ip) + ":" + str(self.port)}

    def is_usable(self):
        return self.counter_fails < self.max_fail_count and \
               not self.is_in_cooldown() and \
               self.counter_fatal < self.max_fatal_count

    def should_be_blacklisted(self):
        return self.counter_fails >= self.max_fail_count or \
               self.counter_fatal >= self.max_fatal_count

    @property
    def response_time(self):
        if self.__response_counter == 0:
            return 0
        return float(self.__response_time_total)/self.__response_counter

    @response_time.setter
    def response_time(self, value):
        self.last_checked = datetime.datetime.now()
        self.__response_time_total += value
        self.__response_counter += 1

    def reset_response_time(self):
        self.__response_counter = 0
        self.__response_time_total = 0