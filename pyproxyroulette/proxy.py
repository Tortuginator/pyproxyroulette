import datetime
from enum import Enum


class ProxyState(Enum):
    UNKNOWN = 0
    ACTIVE = 1
    COOLDOWN = 2
    DEAD = 3


class ProxyObject:
    def __init__(self, _ip, _port, average_response_time=None, max_timeout=8):
        self.ip = str(_ip).strip(" ")
        self.port = int(_port)
        self._max_timeout = max_timeout
        self.last_checked = None

        # Counter for statistics
        self.counter_consequtive_check_fails = 0  # Consequtive failures to respond to proxy checks.
        self.counter_consequtive_request_fails = 0  # Consequtive failures to respond to requests.

        # Cooldown variables
        self._cooldown = None

        # Death Date
        self.death_date = None

        # Criteria: usability config
        self.max_c_check_fails = 2
        self.max_c_request_fails = 3

        self.__response_time_total = 0
        self.__response_counter = 0

        if average_response_time is not None:
            self.__response_counter = 1
            self.__response_time_total = float(average_response_time)

        # Checks
        assert (0 <= self.port <= 65535)
        # TODO: check if valid IP

    @property
    def state(self):
        if self.max_c_request_fails <= self.counter_consequtive_request_fails:
            return ProxyState.DEAD
        if self.max_c_check_fails <= self.counter_consequtive_check_fails:
            if self.death_date is None:
                self.death_date = datetime.datetime.now()
            return ProxyState.DEAD
        if self.is_in_cooldown():
            return ProxyState.COOLDOWN
        if self.__response_counter == 0:
            return ProxyState.UNKNOWN
        return ProxyState.ACTIVE

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

    def __repr__(self):
        return "Proxy[{ip}:{port}|{response_time}|{state}]".format(ip=self.ip,port=self.port,response_time=self.response_time,state=self.state)

    def to_dict(self):
        return {"http": str(self.ip) + ":" + str(self.port),
                "https": str(self.ip) + ":" + str(self.port)}

    def report_request_failed(self):
        self.response_time = self._max_timeout
        self.counter_consequtive_request_fails +=1

    def report_check_failed(self):
        self.response_time = self._max_timeout
        self.counter_consequtive_check_fails +=1
        self.cooldown = datetime.timedelta(hours=1)

    def report_success(self):
        self.counter_consequtive_request_fails = 0
        self.counter_consequtive_check_fails = 0

    def set_as_dead(self):
        self.counter_consequtive_request_fails = self.max_c_request_fails
        self.counter_consequtive_check_fails = self.max_c_check_fails
        if self.death_date is None:
            self.death_date = datetime.datetime.now()

    @property
    def response_time(self):
        if self.__response_counter == 0:
            return 0
        return float(self.__response_time_total)/self.__response_counter

    @response_time.setter
    def response_time(self, value):
        self.__response_time_total += value
        self.__response_counter += 1

    def reset_response_time(self):
        self.__response_counter = 0
        self.__response_time_total = 0
