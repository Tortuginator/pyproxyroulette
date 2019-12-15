from .core import ProxyRouletteCore
from .exceptions import MaxRetriesExceeded,DecoratorNotApplicable
import requests as requests_original
from .defaults import defaults


PROXY_POOL_UPDATERS = dict()


class ProxyRoulette(object):
    def __init__(self,
                 debug_mode=False,
                 max_retries=5,
                 max_timeout=15,
                 func_proxy_validator=defaults.proxy_is_working,
                 func_proxy_response_validator=defaults.proxy_response_validator):

        if len(PROXY_POOL_UPDATERS) == 0:
            print("[PPR] Using internal default as pool updater")
            func_proxy_pool_update = defaults.get_proxies_from_web
        else:
            if debug_mode:
                print("[PPR] Using decorator as pool updater origin")

            def local_updater():
                proxies = []
                for fname, f in PROXY_POOL_UPDATERS.items():
                    if debug_mode:
                        print(f"[PPR] calling pool updater: {fname}")
                    proxies += f()
                return proxies
            func_proxy_pool_update = local_updater
        self.proxy_core = ProxyRouletteCore(debug_mode=debug_mode,
                                            max_timeout=max_timeout,
                                            func_proxy_validator=func_proxy_validator,
                                            func_proxy_pool_updater=func_proxy_pool_update)
        self._max_retries = max_retries
        self.debug_mode = debug_mode
        self.acknowledge_decorator_restrictions = False

        # Functions
        self.__default_proxy_response_validator = func_proxy_response_validator

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

        while current_retry <= self.max_retries+1 or self.max_retries == 0:
            temp_proxy_obj = self.proxy_core.current_proxy(return_obj=True)
            request_args = {
                'proxies': temp_proxy_obj.to_dict(),
                'timeout': self.max_timeout
            }
            request_args.update(kwargs)

            try:
                if self.debug_mode:
                    print("[PPR] {}: {} with arguments: {}".format(req_type, url, request_args))
                res = method(url, **request_args)
                temp_proxy_obj.response_time = res.elapsed.total_seconds()

                if not self.__default_proxy_response_validator(res): #If not valid response:
                    if self.debug_mode:
                        print("[PPR] Validator noticed a invalid response")
                    self.proxy_core.force_update(apply_cooldown=True)
                else:
                    return res
            except (requests_original.exceptions.Timeout,
                    requests_original.exceptions.ProxyError,
                    requests_original.exceptions.ConnectionError,
                    requests_original.exceptions.ChunkedEncodingError):
                self.proxy_core.proxy_feedback(request_failure=True)
                self.proxy_core.force_update()
                if self.debug_mode:
                    print("[PPR] {}: Timeout: {} request failed".format(req_type, req_type))

            except Exception as err:
                if not err.args:
                    err.args = ('',)
                raise
            current_retry += 1
        raise MaxRetriesExceeded('The maximum number of {}'
                                 ' retries per request has been exceeded'.format(self.max_retries))

    def proxify(self):
        def wrapper_decorator(func):
            def func_wrapper(*args, **kwargs):
                if "requests" not in func.__globals__.keys():
                    raise DecoratorNotApplicable("'Requests' not imported or not imported as 'requests'")
                if "threading" in func.__globals__.keys() and not self.acknowledge_decorator_restrictions:
                    raise DecoratorNotApplicable("The decorator can not be used in a non-single-threaded environment. "
                                                 "This exception can be disabled by setting ProxyRoulette.acknowledge_"
                                                 "decorator_restrictions = True")
                g = func.__globals__
                sentinel = object()

                old_value = g.get('requests', sentinel)
                g['requests'] = self

                if self.debug_mode:
                    print("[PPR] Proxify decorator called by {}".format(func))
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

    @staticmethod
    def proxy_pool_updater(func):
        PROXY_POOL_UPDATERS[func.__name__] = func
        return func

    @property
    def function_proxy_validator(self):
        return self.proxy_core.function_proxy_validator

    @function_proxy_validator.setter
    def function_proxy_validator(self, value):
        self.proxy_core.function_proxy_validator = value

    @property
    def function_proxy_response_validator(self):
        return self.__default_proxy_response_validator

    @function_proxy_response_validator.setter
    def function_proxy_response_validator(self, value):
        self.__default_proxy_response_validator = value

    @property
    def function_proxy_pool_updater(self):
        return self.proxy_core.function_proxy_pool_updater

    @function_proxy_pool_updater.setter
    def function_proxy_pool_updater(self, value):
        self.proxy_core.function_proxy_pool_updater = value

    @property
    def max_timeout(self):
        return self.proxy_core.max_timeout

    @max_timeout.setter
    def max_timeout(self, value):
        self.proxy_core.max_timeout = value

    @property
    def max_retries(self):
        return self._max_retries

    @max_retries.setter
    def max_retries(self, value):
        self._max_retries = value
