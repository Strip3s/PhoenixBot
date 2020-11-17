import argparse
import logging
import json
import random
import requests

from http_request_randomizer.requests.proxy.requestProxy import RequestProxy

logging.getLogger("http_request_randomizer").setLevel(logging.ERROR)

class RequestSessionProxyUtil():
    DEFAULT_DATA_FILE_PATH = "./data/requests_session_proxies.json"
    TEST_URL = 'https://ipinfo.io/json'

    def __init__(self, country='United States'):
        # The http_request_randomizer really likes to aggressively log.  
        # They set logger level to DEBUG explicitly in __init__ of RequestProxy (super annoying and hard to patch)
        req_proxy = RequestProxy(log_level=logging.ERROR)
        req_proxy.logger.setLevel(logging.ERROR)

        self.proxy_list = list((proxy for proxy in req_proxy.get_proxy_list() if proxy.country == country))
        # Shuffle it so not everyone is using the same order of proxies in the list
        random.shuffle(self.proxy_list)
        print("Found {} potential proxies in the {}".format(len(self.proxy_list), country))

    def get_request_session(self):
        valid_proxy = False
        while not valid_proxy:
            if len(self.proxy_list) == 0:
                raise OutOfProxiesError("Ran out of potential proxy candidates")
            self.curr_proxy = self.proxy_list[0]
            proxies = {
                "http": "http://{}".format(self.curr_proxy.get_address()),
                "https": "https://{}".format(self.curr_proxy.get_address())
            }
            session = requests.Session()
            session.proxies = proxies
            valid_proxy = self.is_curr_proxy_valid(session)
            self.proxy_list.pop(0)
        return session

    def get_request_sessions(self, num_sessions):
        sessions = []
        for _ in range(num_sessions):
            sessions.append(self.get_request_session())
        return sessions
    
    def is_curr_proxy_valid(self, session):
        try:
            response = session.get(self.TEST_URL, timeout=10)
            if response.status_code == 200:
                return True
        except Exception:
            logging.warning("Proxy with IP {} failed. Trying another".format(self.curr_proxy.get_address()))
        return False

    def generate_working_proxy_list_file(self, num_proxies, filepath=None):
        if filepath is None:
            filepath = RequestSessionProxyUtil.DEFAULT_DATA_FILE_PATH
        proxies = []
        try:
            for i in range(num_proxies):
                self.get_request_session()
                print("Found {}/{} working proxies".format(str(i+1), num_proxies))
                proxies.append({
                    "http": "http://{}".format(self.curr_proxy.get_address()),
                    "https": "https://{}".format(self.curr_proxy.get_address())
                })
        except OutOfProxiesError:
            print("Ran out of valid proxies that match the criteria. Dumping current set of {} proxies to data file".format(len(proxies)))
        with open(filepath, 'w') as outfile:
            json.dump(proxies, outfile)

    @classmethod
    def get_proxy_list_from_file(filepath=None):
        if filepath is None:
            filepath = RequestSessionProxyUtil.DEFAULT_DATA_FILE_PATH
        try:
            with open(filepath, 'r') as infile:
                return json.load(infile)
        except FileNotFoundError:
            print("File {} not found, you need to first generate this file via RequestSessionProxyUtil().generate_working_proxy_list_file(<num_proxies>)")


class OutOfProxiesError(RuntimeError):
    def __init__(self, message):
        super()

if __name__ == '__main__':
    supported_actions = ['--generate_proxy_list']
    parser = argparse.ArgumentParser(description='Script version used for generating proxy list.')
    parser.add_argument('--generate_proxy_list',
                        action='store_true',
                        default=False,
                        help='Specifies that we want to generate a proxy list')
    parser.add_argument('--num_proxies',
                        type=int,
                        default=5,
                        help='The number of proxies to generate. (default: 5)')
    parser.add_argument('--file_path',
                        default=RequestSessionProxyUtil.DEFAULT_DATA_FILE_PATH,
                        help='The path to the JSON data output file we want to write to proxy info to. Defaults to: {}'.format(RequestSessionProxyUtil.DEFAULT_DATA_FILE_PATH))
    parser.add_argument('--country',
                        default='United States',
                        help='The country location of the proxies you would like to build a list of')
    args = parser.parse_args()

    if not args.generate_proxy_list:
        print("Must specify supported action that you want, current supported actions: {}".format(supported_actions))
        exit(1)
    proxy_util = RequestSessionProxyUtil(country=args.country)
    proxy_util.generate_working_proxy_list_file(args.num_proxies, filepath=args.file_path)