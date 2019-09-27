import requests
from .core import ProxyRouletteCore


class ProxyRoulette(object):
    def __init__(self):
        self.proxy_core = ProxyRouletteCore()
        self.max_retries = 2

    def get(self, url, **kwargs):
        current_retry = 1

        while current_retry <= self.max_retries:
            request_args = {
                'proxies': self.proxy_core.get_proxy()
            }
            request_args.update(kwargs)
            try:
                return requests.get(url, **request_args)
            except requests.exceptions.Timeout:
                self.proxy_core.proxy_feedback(request_failure=True)
                self.proxy_core.force_update()
            except Exception as err:
                if not err.args:
                    err.args = ('',)
                raise
            current_retry += 1

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass

    def head(self):
        pass

    def options(self):
        pass
