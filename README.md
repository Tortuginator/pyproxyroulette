# PyProxyRoulette
The pyproxyroulette library is a wrapper for the [Requests](http://docs.python-requests.org/en/master/) library. The wrapper adds a random proxy to each request and ensures that the proxy is working and swaps it out when needed. Additionally, the wrapper tries to detect if a request has been blocked by the requested web-host. Blocked requests are repeated with different proxy servers.

## Example Wrapper Usage
```python
from pyproxyroulette import ProxyRoulette
pr = ProxyRoulette()
pr.get("http://github.com")
```
The functions `get`, `post`,`option`,`put`,`delete` and `head` form the requests library are wrapped and callable through the wrapper.
It is generally **only recommended to call and use idempotent methods** as requests which timeout can be registered by the server, despite not returning in time. Hence it is only recommended to use the `GET` method.
### Initialisation parameters
```python
pr = ProxyRoulette(debug_mode=False, 
                   max_retries=2,
                   max_timeout=15,
                   func_proxy_validator=defaults.proxy_is_working,
                   func_proxy_pool_update=defaults.get_proxies_from_web,
                   func_proxy_response_validator=defaults.proxy_response_validator)
```
| Parameter | Description |
| --------- | ----------- |
| debug_mode | activated, it prints additional internal information. Used for debugging |
| max_retries | Number of retries whith different proxies when a request fails.|
| max_timeout | Timeout until a request is assumed to have failed |
| func_proxy_validator | Function, that can check if a specific (ip,port) combination is valid and working |
| func_proxy_pool_update |  Function which returns a list of ip, port pairs. Gets called in intervalls |  
| func_proxy_response_validator | Function which checks if a request has been blocked by analyzig the response content. A blocked request will lead to a resending of the request using a different proxy |

## Example Decorator Usage
**WARNING: USE THE DECORATOR ONLY FOR SINGLE-THREADED APPLICATIONS**
```python
import requests
from pyproxyroulette import ProxyRoulette
pr = ProxyRoulette()

@pr.proxify()
def foo_bar():
    requests.get("http://github.com")
    requests.post("http://github.com/login",data = {"username":"foo","password":"bar"})
```

Using the `@pr.proxify()` decorator above the declaration of a funtion, will apply pyproxyroulette to all requests made by the requests library in that specific function. 

**WARNING: Use the decorator ONLY when your application uses the requests library in only ONE thread and when the the requests library is referred to as `requests` in the function. Using a different name for the library than 'requests' will prevent the wrapper from applying the proxy to the requests.**
## Disclaimer
THIS SOFTWARE IS PROVIDED ''AS IS'' AND ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTOR(S) BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
