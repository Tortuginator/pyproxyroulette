# PyProxyRoulette
The pyproxyroulette library is a wrapper for the [Requests](http://docs.python-requests.org/en/master/) library. The wrapper applies a random proxy to each request and ensures that the proxy is working and swaps it out when needed. Additionally, the wrapper tries to detect if a request has been blocked by the requested web-host. Blocked requests are repeated with different proxy servers. The wrapper can be used in multi-threaded applications like crawlers or scrapers. 

## Installation
This library is available on pypi. Hence it can be installed as follows:
```bash
pip install pyproxyroulette
```
## Example Wrapper Usage
```python
from pyproxyroulette import ProxyRoulette
pr = ProxyRoulette()
pr.get("http://github.com")
```
The functions `get`, `post`, `option`, `put`, `delete` and `head` form the requests library are wrapped and callable through the wrapper.
It is generally **only recommended to call and use idempotent methods** as requests which timeout can be registered by the server, despite not beeing registerd in time at the client. Hence it is only recommended to use the `GET` method in production environments.

### Initialisation parameters
```python
pr = ProxyRoulette(debug_mode=False, 
                   max_retries=5,
                   max_timeout=15,
                   func_proxy_validator=defaults.proxy_is_working,
                   func_proxy_response_validator=defaults.proxy_response_validator)
```
| Parameter | Default | Description |
| --------- | ----------- | ----------- |
| debug_mode | False | When activated, it prints additional internal information used for debugging |
| max_retries | 5 | Number of retries with different proxies when a request fails. Set to 0 for unlimited retries. |
| max_timeout | 15 | Timeout until a request is assumed to have failed |
| func_proxy_validator |defaults.proxy_is_working() | Function, that can check if a specific (ip,port) combination is valid and working |
| func_proxy_response_validator | defaults.proxy_response_validator() | Function, which checks if a request has been blocked by inspecting the response. A blocked request will lead to repetition of the request using a different proxy |

## Extend the Plol of Proxies
It is possible to add functions to the system, which are called on a regular basis and return pairs of IP,PORT to be used in the proxy roulette.
A proxy pool update function has to return a list of IP,PORT tuples. A default function is used to populate the proxy pool if no
explicit function is defined. Multiple functions can be added using the following decorator:
```python
from pyproxyroulette import ProxyRoulette

@ProxyRoulette.proxy_pool_updater
def my_cool_proxy_obtaining_function():
    return [("172.0.0.1",80),...]

pr = ProxyRoulette()

pr.get("http://some.url")
```

## Example Decorator Usage
**WARNING: USE THE DECORATOR ONLY FOR SINGLE-THREADED APPLICATIONS**
```python
import requests
from pyproxyroulette import ProxyRoulette
pr = ProxyRoulette()

@pr.proxify()
def foo_bar():
    requests.get("http://github.com")
```

Using the `@pr.proxify()` decorator above the declaration of a function, will apply pyproxyroulette to all requests made by the requests library in that specific function. Instead of the decorator the usual function `pr.get(...)` is also applicable.

When the decorator detects beeing used in multiple threads, it will raise an exception, as that behaviour is dangerous. The exception can be completely disabled by setting `pr.acknowledge_decorator_restrictions = True`. By default the value is set to False.

**WARNING: Use the decorator ONLY when your application uses the requests library in only ONE thread and when the the requests library is referred to as `requests` in the function. Using a different name for the library than 'requests' will prevent the wrapper from applying the proxy to the requests.**
## Disclaimer
THIS SOFTWARE IS PROVIDED ''AS IS'' AND ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTOR(S) BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
