# PyProxyRoulette
The pyproxyroulette library provides a wrapper for python [Requests](http://docs.python-requests.org/en/master/). It takes care of randomly selecting proxys and swapping them out to when needed. Additionally it ensures, that the proxy is working corrctly.

### Example Usage
```python
from pyproxyroulette import ProxyRoulette
pr = ProxyRoulette()
pr.get("http://github.com")
```
### Initialisation parameters
```python
pr = Proxyroulette(myIP = None,
                   securitylevel = 3,
                   maxRetries = 5,
                   maxReqestsThreshold = 100,
                   requireSSL = False,
                   requireGoogleCompatibility = False):
```
| Parameter | Description |
| --------- | ----------- |
| myIP | ProxyRoulette needs to know your real IP to compare against to ensure your real ip is hidden. This ip is usually determined automatically, but you can provide one as well |
| securityLevel | between 1 and 3, 3 beeing the best. |
| maxRetries | When a request failes, the number of retries to be done, before returning None |
| maxRequestsThreshold | number of requests to be send on the same proxy, before switching to another proxy |
| requireSSL | only use proxys which support SSL |
| requireGoogleCompability | only use proxys which are not blocked or detected by google |

## Disclaimer
THIS SOFTWARE IS PROVIDED ''AS IS'' AND ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTOR(S) BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
