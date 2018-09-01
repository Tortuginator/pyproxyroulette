# PyProxyRoulette
The pyproxyroulette library provides a wrapper for python [Requests](http://docs.python-requests.org/en/master/). It takes care of randomly selecting proxys and swapping them out when needed. Additionally it ensures, that the proxy is working corrctly.

### Example Usage
```python
from pyproxyroulette import ProxyRoulette
pr = ProxyRoulette()
pr.get("http://github.com")
```
### Initialisation parameters
```python
pr = ProxyRoulette(myIP = None,
                   securitylevel = 3,
                   maxRetries = 5,
                   maxReqestsThreshold = 100,
                   requireSSL = False,
                   requireGoogleCompatibility = False)
```
| Parameter | Description |
| --------- | ----------- |
| myIP | ProxyRoulette needs to know your real IP to compare against the proxys IP to ensure your real ip is hidden. It is usually determined automatically, but you can provide it well |
| securityLevel | between 1 and 3, 3 beeing the best. level 1 uses a proxy, but sends your real ip in the header. Level 2 sends a random IP in the header and level 3 does not disclose that the request came from a proxy |
| maxRetries | When a request fails, the number of retries to be done, before returning None |
| maxRequestsThreshold | number of requests to be send on the same proxy, before switching to another proxy |
| requireSSL | only use proxys which support SSL |
| requireGoogleCompability | only use proxys which are not blocked or detected by google |

## Disclaimer
THIS SOFTWARE IS PROVIDED ''AS IS'' AND ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTOR(S) BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
