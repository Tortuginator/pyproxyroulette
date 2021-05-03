import datetime
from enum import Enum
from typing import Dict


class ProxyState(Enum):
    UNKNOWN = 0
    ACTIVE = 1
    COOLDOWN = 2
    DEAD = 3
    REMOVAL = 4


class ProxyObject:
    def __init__(self, _ip: str, _port: int, average_response_time: float = None, max_timeout: int = 8):
        self.ip: str = str(_ip).strip(" ")
        self.port: int = int(_port)
        self._max_timeout: int = max_timeout
        self.last_checked: datetime = None

        # Counter for statistics
        self.counter_consequtive_request_fails: int = 0  # Consequtive failures to respond to requests.

        # Cooldown variables
        self._cooldown: bool = None

        # Death Date
        self.death_date: datetime = None

        # Criteria: usability config
        self.max_c_request_fails: int = 2

        self.__response_time_total: int = 0
        self.__response_counter: int = 0

        self.to_be_removed: bool = False
        if average_response_time is not None:
            self.__response_counter: int = 1
            self.__response_time_total: float = float(average_response_time)

        # Checks
        assert (0 <= self.port <= 65535)
        # TODO: check if valid IP

    @property
    def state(self) -> ProxyState:
        if self.to_be_removed:
            return ProxyState.REMOVAL
        if self.max_c_request_fails <= self.counter_consequtive_request_fails:
            if self.death_date is None:
                self.death_date = datetime.datetime.now()
            return ProxyState.DEAD
        if self.is_in_cooldown():
            return ProxyState.COOLDOWN
        if self.__response_counter == 0:
            return ProxyState.UNKNOWN
        return ProxyState.ACTIVE

    def is_in_cooldown(self) -> bool:
        if self._cooldown is None:
            return False
        if self._cooldown >= datetime.datetime.now():
            return True
        self._cooldown = None
        return False

    @property
    def cooldown(self) -> bool:
        if self._cooldown is not None:
            return self._cooldown
        return False

    @cooldown.setter
    def cooldown(self, _cooldown_timeperiod: datetime.timedelta):
        assert (isinstance(_cooldown_timeperiod, datetime.timedelta) or _cooldown_timeperiod is None)
        if _cooldown_timeperiod is None:
            self._cooldown = None
            return
        self._cooldown = datetime.datetime.now() + _cooldown_timeperiod

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other.ip == self.ip and other.port == self.port

    def __hash__(self) -> int:
        return hash(self.ip) ^ hash(self.port)

    def __repr__(self) -> str:
        return f"Proxy[{self.ip}:{self.port}|{self.response_time}|{self.state}]"

    def to_dict(self) -> Dict:
        return {"http": f"{self.ip}:{self.port}",
                "https": f"{self.ip}:{self.port}"}

    def report_request_failed(self):
        self.response_time = self._max_timeout
        self.counter_consequtive_request_fails += 1
        self.cooldown = datetime.timedelta(hours=1)

    def report_success(self):
        self.counter_consequtive_request_fails = 0
        self.death_date = None

    def mark_for_removal(self):
        self.to_be_removed = True

    @property
    def response_time(self) -> float:
        if self.__response_counter == 0:
            return 0
        return float(self.__response_time_total) / self.__response_counter

    @response_time.setter
    def response_time(self, value: int):
        self.__response_time_total += value
        self.__response_counter += 1

    def reset_response_time(self):
        self.__response_counter = 0
        self.__response_time_total = 0
