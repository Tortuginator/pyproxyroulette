import requests, warnings, re 

class ProxyRoulette(object):
    ValidIpAddressRegex = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
    def __init__(
                self,
                myIP = None,
                securitylevel = 3,
                maxRetries = 5,
                maxReqestsThreshold = 100,
                ):


        self.setDefaults()
        if not 0 <= int(securitylevel) <= 3:
            self.securitylevel = 3
            warnings.warn("invalid security level. securitylevel set to 3")
        else:
            self.securitylevel = int(securitylevel)

        if myIP == None:
            self.originalIP = getIP()
        else:
            if re.match(ValidIpAddressRegex, str(myIP)):
                self.originalIP = myIP
            else:
                pass
                #TODO:raise value error

        self.proxies = self.getProxyList()
        #Init some variables
        #The request counter gets incremented for reach request made through a proxy. Then it hits the maxRequests Threshold a new proxy is selected
        self.requestCounter = 0
        self.requestRetries = 0

    def setDefaults(self):
        """Sets all default values"""

        #securitylevel describes the security of the proxy connection. 1 beeing the weakest and 3 the strongest.
        #level 0: No protection at all
        #level 1: Uses proxy, but header contains your IP
        #level 2: Proxy tells server, that is is a proxied connection, but the IP in the header is not yours
        #level 3 (Elite): Proxy does not tell the server, that it is a proxy 
        #BE AWARE: increasing the security level will decrease the number of proxies available

        self.securityLevel = 3

        #force only SSL proxy usage
        self.requireSSL = False

        #force only to use proxies, which are not blocked by google
        self.reqireGoogleCompatibility = False

        #sets the validity checking method this can be customized
        self.responseValidity = self.isValidResponse

        #sets the verification method to determine if we really are bedind a proxy
        self.proxyVerificator = self.reviewProxy

        #Maximal number of retries with different proxies for a single url before raising a not reachable error
        self.maxRetries = 5

        #timeout for the ip request
        self.proxyVerificatorTimeout = (10,10)

        #use length bound th check if the proxy did not include additonal html code in the reponse when verificating the ip
        self.proxylengthVerification = True

        #init the proxylist
        self.proxies = []

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

    def getIP(self,proxy = ""):
        """calls icanhazip.com to retrieve the ip. This request can be both proxied & unprovied"""
        ip_request = requests.get("http://icanhazip.com/",proxies = proxy,timeout = self.proxyVerificatorTimeout)
        ip_candidates = re.findall(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", str(ip_request.content))
        if len(ip_candidate) == 1:
            if self.proxylengthVerification:
                if len(ip_request.content) < 100:
                    return ip_candidates[0]
                return None
            else:
                return ip_candidates[0]
        else:
            return None

    def getProxy(self):
        """Returns a valid proxy as a string. This method calls the proxychanging method to check if it has to be changed"""
        pass

    def selectNewProxy(self):
        self.requestCounter = 0

    def isValidResponse(self,request):
        """Decides whereas the request returned a valid response"""
        if request.status_code == 407:
            self.selectNewProxy()
            return False
        if request.status_code == 502:
            return False
        return True

    def isValidProxy(self,proxy):
        """calls a webpage which returns the IP-address of the requestee. In the best case, this is the ip of the proxy"""
        ip = self.getIP(proxy = proxy)
        if ip != self.originalIP:
            return True
        return False

    def request(self, uri, method='GET', **kwargs):
        request_args = {
            'uri': uri,
            'method': method
        }
        self.requestCounter +=1
        request_args.update(kwargs)
        try:
            response = requests.request(**request_args)
        except requests.exceptions.Timeout as e:
            #TODO:proper handling
            raise e
        if self.responseValidity(self,response):
            rr = response
        else:
            if self.maxRetries <= self.requestRetries:
                self.maxRetries +=1
                rr = self.request(**request_args)
            else:
                self.requestRetries = 0
                rr = None
                #raise serious error

        if self.requestCounter >= self.maxReqestsThreshold:
            self.selectNewProxy()
        return rr