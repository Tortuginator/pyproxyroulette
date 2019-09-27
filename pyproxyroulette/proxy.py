import datetime


class ProxyObject:
    def __init__(self, _ip, _port):
        self.ip = _ip
        self.port = _port
        self.counter_requests = 0
        self.counter_fails = 0
        self.cooldown = None

    def is_in_cooldown(self):
        if self.cooldown >= datetime.datetime.now():
            return True
        self.cooldown = None
        return False

    @property
    def cooldown(self):
        if self.cooldown is not None:
            return self.cooldown
        return False

    @cooldown.setter
    def cooldown(self, _cooldown_timeperiod):
        assert(isinstance(_cooldown_timeperiod, datetime.timedelta))
        self.cooldown = datetime.datetime.now() + _cooldown_timeperiod

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.ip == self.ip and other.port == self.port

    def __hash__(self):
        return hash(self.ip) ^ hash(self.port)

    def to_dict(self):
        return {"http": str(self.ip) + ":" + str(self.port),
                "https": str(self.ip) + ":" + str(self.port)}

    def is_usable(self):
        return self.counter_fails < 3 and not self.is_in_cooldown()

    def should_be_blacklisted(self):
        return self.counter_fails >= 3