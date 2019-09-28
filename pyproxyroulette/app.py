from .core import ProxyRouletteCore
from .exceptions import MaxRetriesExceeded
import requests as requests_original


class ProxyRoulette(object):
    def __init__(self, debug_mode=False, max_retries=2,max_timeout=15):
        self.proxy_core = ProxyRouletteCore(debug_mode=debug_mode)
        self.max_retries = max_retries
        self.max_timeout = max_timeout
        self.debug_mode = debug_mode

    def get(self, url, **kwargs):
        return self._wrapper_kernel(requests_original.get, "GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._wrapper_kernel(requests_original.post, "POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self._wrapper_kernel(requests_original.put, "PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._wrapper_kernel(requests_original.delete, "DELETE", url, **kwargs)

    def head(self, url, **kwargs):
        return self._wrapper_kernel(requests_original.head, "HEAD", url, **kwargs)

    def options(self, url, **kwargs):
        return self._wrapper_kernel(requests_original.options, "OPTIONS", url, **kwargs)

    def _wrapper_kernel(self, method, req_type, url, **kwargs):
        current_retry = 1

        while current_retry <= self.max_retries or self.max_retries == 0:
            request_args = {
                'proxies': self.proxy_core.current_proxy,
                'timeout': self.max_timeout
            }
            request_args.update(kwargs)

            try:
                if self.debug_mode:
                    print("{}: {} with arguments: {}".format(req_type, url, request_args))
                return method(url, **request_args)
            except requests_original.exceptions.Timeout:
                self.proxy_core.proxy_feedback(request_failure=True)
                self.proxy_core.force_update()
                if self.debug_mode:
                    print("{}: Timeout: get request failed".format(req_type))
            except requests_original.exceptions.ProxyError:
                self.proxy_core.proxy_feedback(request_fatal=True)
                self.proxy_core.force_update()
                if self.debug_mode:
                    print("{}: ProxyError: get request failed".format(req_type))
            except Exception as err:
                if not err.args:
                    err.args = ('',)
                raise
            current_retry += 1
        raise MaxRetriesExceeded('The maximum number of {} retries per request has been exceeded'.format(self.max_retries))

    def proxify(self):
        def wrapper_decorator(func):
            def func_wrapper(*args, **kwargs):
                g = func.__globals__
                sentinel = object()

                old_value = g.get('requests', sentinel)
                g['requests'] = self

                if self.debug_mode:
                    print("Proxify decorator called by {}".format(func))
                try:
                    res = func(*args, **kwargs)
                finally:
                    if old_value is sentinel:
                        del g['requests']
                    else:
                        g['requests'] = old_value
                return res
            return func_wrapper
        return wrapper_decorator
