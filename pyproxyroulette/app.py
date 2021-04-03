from .core import ProxyRouletteCore
from .exceptions import MaxRetriesExceeded
import requests as requests_original
from .defaults import defaults
import threading
import logging

PROXY_POOL_UPDATERS = dict()
logger = logging.getLogger(__name__)


class ProxyRoulette(object):
    def __init__(self,
                 max_retries=5,
                 max_timeout=15,
                 func_proxy_validator=defaults.proxy_is_working,
                 func_proxy_response_validator=defaults.proxy_response_validator):

        if len(PROXY_POOL_UPDATERS) == 0:
            logger.info("Using internal default as pool updater")
            func_proxy_pool_update = defaults.get_proxies_from_web

        else:
            logger.debug("Using decorator as pool updater origin")

            def local_updater():
                proxies = []
                for fname, f in PROXY_POOL_UPDATERS.items():
                    logger.debug("calling pool updater: {fname}".format(**locals()))
                    proxies += f()
                return proxies
            func_proxy_pool_update = local_updater
        self.proxy_core = ProxyRouletteCore(max_timeout=max_timeout,
                                            func_proxy_validator=func_proxy_validator,
                                            func_proxy_pool_updater=func_proxy_pool_update)
        self._max_retries = max_retries

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
        try:
            while current_retry <= self.max_retries+1 or self.max_retries == 0:
                temp_proxy_obj = self.proxy_core.current_proxy(return_obj=True)
                request_args = {
                    'proxies': temp_proxy_obj.to_dict(),
                    'timeout': self.max_timeout
                }
                request_args.update(kwargs)

                try:
                    logger.debug("{} {} with arguments: {}".format(req_type, url, request_args))
                    res = method(url, **request_args)
                    temp_proxy_obj.response_time = res.elapsed.total_seconds()

                    if not self.__default_proxy_response_validator(res): #If not valid response:
                        logger.debug("Validator noticed a invalid response")
                        self.proxy_core.force_update(apply_cooldown=True)
                    else:
                        return res

                except (requests_original.exceptions.Timeout,
                        requests_original.exceptions.ProxyError,
                        requests_original.exceptions.ConnectionError,
                        ConnectionResetError,
                        requests_original.exceptions.ChunkedEncodingError) as e:
                    if type(e).__name__ == "ProxyError":
                        temp_proxy_obj.report_request_failed()
                    self.proxy_core.proxy_feedback(request_failure=True)
                    self.proxy_core.force_update()
                    logger.warning("{req_type} request failed with reason: {t}".format(req_type=req_type,
                                                                                       t=type(e).__name__))

                except Exception as err:
                    if not err.args:
                        err.args = ('',)
                    raise
                current_retry += 1
            raise MaxRetriesExceeded('The maximum number of {}'
                                     ' retries per request has been exceeded'.format(self.max_retries))
        except KeyboardInterrupt:
            logger.error("Registered Keyboard Interrupt. Terminating all threads")
            self.proxy_core.proxy_pool.stop()

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

    def status(self):
        return self.proxy_core.state()
