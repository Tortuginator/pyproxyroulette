import requests, warnings, re, random

class ProxyRoulette(object):
    ValidIpAddressRegex = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
    def __init__(self,myIP = None,securitylevel = 3,maxRetries = 5,maxReqestsThreshold = 100):

        self.setDefaults()
        if not 0 <= int(securitylevel) <= 3:
            self.securitylevel = 3
            warnings.warn("invalid security level. securitylevel set to 3")
        else:
            self.securitylevel = int(securitylevel)

        if myIP == None:
            self.originalIP = self.getIP()
        else:
            if re.match(ValidIpAddressRegex, str(myIP)):
                self.originalIP = myIP
            else:
                pass
                #TODO:raise value error

        self.proxy = self.proxyGatherer()
        self.currentProxy = None
        #Init some variables
        #The request counter gets incremented for reach request made through a proxy. Then it hits the maxRequests Threshold a new proxy is selected
        self.requestCounter = maxReqestsThreshold + 1
        self.requestRetries = 0
        self.maxReqestsThreshold = maxReqestsThreshold

    def setDefaults(self): 
        """Sets all default values"""

        #securitylevel describes the security of the proxy connection. 1 beeing the weakest and 3 the strongest.
        #level 0: No protection at all
        #level 1: Uses proxy, but header contains your IP
        #level 2: Proxy tells server, that is is a proxied connection, but the IP in the header is not yours
        #level 3 (Elite): Proxy does not tell the server, that it is a proxy 
        #BE AWARE: increasing the security level will decrease the number of proxy available
        self.securityLevel = 3

        #force only SSL proxy usage
        self.requireSSL = False

        #force only to use proxy, which are not blocked by google
        self.requireGoogleCompatibility = False

        #sets the validity checking method this can be customized
        self.responseValidity = self.isValidResponse

        #sets the verification method to determine if we really are bedind a proxy
        self.proxyVerificator = self.isValidProxy

        #method downloading the proxy list
        self.proxyGatherer = self.getProxyList

        #method to test the proxy
        self.proxyTest = self.testProxy

        #Maximal number of retries with different proxy for a single url before raising a not reachable error
        self.maxRetries = 5

        #timeout for the ip request
        self.proxyVerificatorTimeout = (10,10)

        #use length bound th check if the proxy did not include additonal html code in the reponse when verificating the ip
        self.proxylengthVerification = True

        #init the proxylist
        self.proxy = []

    def getProxyList(self):
        proxylist = requests.get("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt")
        proxyProcessed = []
        for i in str(proxylist.content).split("\\n")[3:-2]:
            i_secLevel = 0
            if "-N" in i:
                i_secLevel = 1
            elif "-A" in i:
                i_secLevel = 2
            elif "-H" in i:
                i_secLevel = 3

            i_uri = i.split(" ")[0]
            i_ssl = True if "-S" in i else False
            i_google = True if "+" in i else False

            proxyProcessed.append((i_uri,i_secLevel,i_ssl,i_google))
        return proxyProcessed

    def getIP(self,proxy = {}):
        """calls icanhazip.com to retrieve the ip. This request can be both proxied & unprovied"""
        ip_request = requests.get("http://icanhazip.com/",proxies = proxy,timeout = self.proxyVerificatorTimeout)
        ip_candidates = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", str(ip_request.content))
        if len(ip_candidates) == 1:
            if self.proxylengthVerification:
                if len(ip_request.content) < 100:
                    return ip_candidates[0]
                return None
            else:
                return ip_candidates[0]
        else:
            return None

    def dictFromProxy(self):
        if self.requireSSL:
            return {"https":self.currentProxy,"http":self.currentProxy}
        else:
            return {"http":self.currentProxy}

    def getProxy(self):
        """Returns a valid proxy as a string. This method calls the proxychanging method to check if it has to be changed"""
        self.requestCounter +=1
        if self.requestCounter >= self.maxReqestsThreshold:
            self.selectNewProxy()
        return self.dictFromProxy()

    def selectNewProxy(self):
        self.requestCounter = 0
        possibleProxy = []
        #Structure: proxy - seclvl - ssl - google
        for i in self.proxy:
            if self.requireGoogleCompatibility:
                if not i[3]:continue;
            if self.securitylevel < i[1]:
                continue
            if self.requireSSL:
                if not i[2]:continue;
            possibleProxy.append(i)

        if len(possibleProxy) == 0:
            pass
            #raise serious error

        #random.randint is not secure. But in this case this is not reqired!
        selected = random.randint(0,len(possibleProxy)-1)
        self.currentProxy = possibleProxy[selected][0]
        try:
            if not self.proxyVerificator(self.dictFromProxy()) or not self.proxyTest(self.dictFromProxy()):
                self.selectNewProxy()
        except requests.exceptions.ConnectTimeout:
            self.selectNewProxy()
        except requests.exceptions.ProxyError:
            self.selectNewProxy()
        return self.currentProxy

    def isValidResponse(self,request):
        """Decides whereas the request returned a valid response"""
        if request.status_code == 407:
            self.selectNewProxy()
            return False
        if request.status_code == 502:
            return False
        return True

    def testProxy(self,proxy):
        try:
            requests.get("http://news.ycombinator.com/",proxies = proxy,timeout = self.proxyVerificatorTimeout)
            return True
        except Exception as e:
            raise e
            return False

    def isValidProxy(self,proxy):
        """calls a webpage which returns the IP-address of the requestee. In the best case, this is the ip of the proxy"""
        ip = self.getIP(proxy = proxy)
        print(ip,self.originalIP)
        if ip != self.originalIP:
            return True
        return False

    def get(self, uri, **kwargs):
        request_args = {
            'proxies':self.dictFromProxy()
        }
        request_args.update(kwargs)
        self.requestCounter +=1
        try:
            response = requests.get(uri,**request_args)
        except requests.exceptions.Timeout as e:
            #TODO:proper handling
            raise e
        if self.responseValidity(response):
            rr = response
        else:
            if self.maxRetries <= self.requestRetries:
                self.maxRetries +=1
                rr = self.get(url,**request_args)
            else:
                self.requestRetries = 0
                rr = None
                #raise serious error

        if self.requestCounter >= self.maxReqestsThreshold:
            self.selectNewProxy()
        return rr