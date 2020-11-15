import logging
import requests

from http_request_randomizer.requests.proxy.requestProxy import RequestProxy

logging.getLogger("http_request_randomizer").setLevel(logging.ERROR)

class RequestSessionProxyUtil():
    TEST_URL = 'https://ipinfo.io/json'

    def __init__(self, country='United States'):
        # The http_request_randomizer really likes to aggressively log.  
        # They set logger level to DEBUG explicitly in __init__ of RequestProxy (super annoying and hard to patch)
        req_proxy = RequestProxy()
        req_proxy.logger.setLevel(logging.ERROR)

        self.proxy_list = list((proxy for proxy in req_proxy.get_proxy_list() if proxy.country == country))
        print("Found {} potential proxies in the {}".format(len(self.proxy_list), country))
        self.curr_proxy_num = 0

    def get_request_session(self):
        valid_proxy = False
        while not valid_proxy:
            self.curr_proxy = self.proxy_list[self.curr_proxy_num]
            proxies = {
                "http": "http://{}".format(self.curr_proxy.get_address()),
                "https": "https://{}".format(self.curr_proxy.get_address())
            }
            session = requests.Session()
            session.proxies = proxies
            valid_proxy = self.is_curr_proxy_valid(session)
            self.curr_proxy_num += 1
        return session

    def get_request_sessions(self, num_sessions):
        sessions = []
        for _ in range(num_sessions):
            sessions.append(self.get_request_session())
        return sessions
    
    def is_curr_proxy_valid(self, session):
        try:
            response = session.get(self.TEST_URL, timeout=5)
            if response.status_code == 200:
                return True
        except Exception:
            pass
        return False
