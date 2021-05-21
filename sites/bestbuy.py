import json, settings, webbrowser, urllib3, requests, time
from time import sleep
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib import parse
from chromedriver_py import binary_path  # this will get you the path variable
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from webdriver_manager.chrome import ChromeDriverManager

from utils.json_utils import find_values
from utils.selenium_utils import enable_headless
from utils import create_msg

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
except:
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Cipher import PKCS1_OAEP

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# https://github.com/Hari-Nagarajan/nvidia-bot/blob/master/stores/bestbuy.py

BEST_BUY_PDP_URL = "https://api.bestbuy.com/click/5592e2b895800000/{sku}/pdp"
BEST_BUY_CART_URL = "https://api.bestbuy.com/click/5592e2b895800000/{sku}/cart"

BEST_BUY_ADD_TO_CART_API_URL = "https://www.bestbuy.com/cart/api/v1/addToCart"
BEST_BUY_CHECKOUT_URL = "https://www.bestbuy.com/checkout/c/orders/{order_id}/"

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "user-agent": settings.userAgent,
    "origin": "https://www.bestbuy.com",
}

options = Options()
options.page_load_strategy = "eager"
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)
options.add_argument("user-data-dir=.profile-bb")


class BestBuy:

    def __init__(self, status_signal, image_signal, product, profile, proxy, monitor_delay, error_delay):
        self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay = status_signal, image_signal, product, profile, float(monitor_delay), float(error_delay)
        self.sku_id = parse.parse_qs(parse.urlparse(self.product).query)['skuId'][0]
        self.session = requests.Session()
        # TODO: Refactor Bird Bot Auto Checkout Functionality. For now, it will just open the cart link.
        if settings.bb_ac_beta:
            self.auto_buy = True
        else:
            self.auto_buy = False
        self.browser = self.init_driver()
        starting_msg = "Starting Best Buy Task"
        if settings.dont_buy:
            starting_msg = "Starting Best Buy Task in dev mode - Phoenix Bot will not actually checkout. Check Settings page to disable Dev Mode"
        self.status_signal.emit(create_msg(starting_msg, "normal"))

        # TODO: Add Product Image To UI

        if proxy:
            self.session.proxies.update(proxy)

        adapter = HTTPAdapter(
            max_retries=Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            )
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        response = self.session.get(
            BEST_BUY_PDP_URL.format(sku=self.sku_id), headers=DEFAULT_HEADERS
        )
        self.status_signal.emit(create_msg(f"PDP Request: {response.status_code}", "normal"))
        self.product = response.url
        self.status_signal.emit(create_msg(f"Product URL: {self.product}", "normal"))
        self.session.get(self.product)
        self.status_signal.emit(create_msg(f"Product URL Request: {response.status_code}", "normal"))
        self.status_signal.emit(create_msg("Loading headless driver.", "normal"))

        # TODO - check if this still messes up the cookies for headless
        headless = True
        if headless:
            enable_headless()
        options.add_argument(f"User-Agent={settings.userAgent}")

        self.status_signal.emit(create_msg("Loading https://www.bestbuy.com/", "normal"))
        self.login()

        self.browser.get(self.product)
        cookies = self.browser.get_cookies()

        [
            self.session.cookies.set_cookie(
                requests.cookies.create_cookie(
                    domain=cookie["domain"],
                    name=cookie["name"],
                    value=cookie["value"]
                )
            )
            for cookie in cookies
        ]

        self.status_signal.emit(create_msg("Calling location/v1/US/approximate", "normal"))
        status_code = self.session.get(
            "https://www.bestbuy.com/location/v1/US/approximate",
            headers=DEFAULT_HEADERS
        ).status_code
        self.status_signal.emit(create_msg(f"{status_code}", "normal")
                                )
        self.status_signal.emit(create_msg("Calling basket/v1/basketCount", "normal"))
        status_code = self.session.get(
            "https://www.bestbuy.com/basket/v1/basketCount",
            headers=DEFAULT_HEADERS
        ).status_code
        self.status_signal.emit(create_msg(f"{status_code}", "normal"))
        self.check_stock()

    def init_driver(self):
        driver_manager = ChromeDriverManager()
        driver_manager.install()
        browser = webdriver.Chrome(binary_path)

        browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                  Object.defineProperty(navigator, 'webdriver', {
                   get: () => undefined
                  })
                """
        })

        return browser

    def login(self):
        self.status_signal.emit(create_msg("Logging in...", "normal"))
        self.browser.get("https://www.bestbuy.com/identity/global/signin")
        self.browser.find_element_by_xpath('//*[@id="fld-e"]').send_keys(settings.bestbuy_user)
        self.browser.find_element_by_xpath('//*[@id="fld-p1"]').send_keys(settings.bestbuy_pass)
        self.browser.find_element_by_xpath(
            "//button[contains(@class,'cia-form__controls__submit')]"
        ).click()
        WebDriverWait(self.browser, 10).until(
            lambda x: "Official Online Store" in self.browser.title
        )

    def check_stock(self):
        while not self.in_stock():
            sleep(5)
        self.status_signal.emit(create_msg(f"Item {self.sku_id} is in stock!", "normal"))
        # TODO: Refactor Bird Bot Auto Checkout Functionality. For now, it will just open the cart link when in stock.
        if self.auto_buy:
            self.auto_checkout()
        else:
            cart_url = self.add_to_cart()
            self.status_signal.emit(create_msg(f"SKU: {self.sku_id} in stock: {cart_url}", "normal"))
            sleep(5)

    def in_stock(self):
        self.status_signal.emit(create_msg("Checking stock", "normal"))
        url = "https://www.bestbuy.com/api/tcfb/model.json?paths=%5B%5B%22shop%22%2C%22scds%22%2C%22v2%22%2C%22page%22%2C%22tenants%22%2C%22bbypres%22%2C%22pages%22%2C%22globalnavigationv5sv%22%2C%22header%22%5D%2C%5B%22shop%22%2C%22buttonstate%22%2C%22v5%22%2C%22item%22%2C%22skus%22%2C{}%2C%22conditions%22%2C%22NONE%22%2C%22destinationZipCode%22%2C%22%2520%22%2C%22storeId%22%2C%22%2520%22%2C%22context%22%2C%22cyp%22%2C%22addAll%22%2C%22false%22%5D%5D&method=get".format(
            self.sku_id
        )
        # TODO: Add random delay configuration
        response = self.session.get(url, headers=DEFAULT_HEADERS)
        self.status_signal.emit(create_msg(f"Stock check response code: {response.status_code}", "normal"))
        try:
            response_json = response.json()
            item_json = find_values(
                json.dumps(response_json), "buttonStateResponseInfos"
            )
            item_state = item_json[0][0]["buttonState"]
            self.status_signal.emit(create_msg(f"Item state is: {item_state}", "normal"))
            if item_json[0][0]["skuId"] == self.sku_id and item_state in [
                "ADD_TO_CART",
                "PRE_ORDER"
            ]:
                return True
            else:
                return False
        except Exception as e:
            self.status_signal.emit(create_msg("Error parsing json. Using string search to determine state.", "error"))
            self.status_signal.emit(create_msg(f"{response_json}", "normal"))
            self.status_signal.emit(create_msg(f"{e}", "error"))
            if "ADD_TO_CART" in response.text: #TODO: Make this case insensitive
                self.status_signal.emit(create_msg("Item is in stock!", "normal"))
                return True
            else:
                self.status_signal.emit(create_msg("Item is out of stock", "normal"))
                webdriver.refresh()
                return False

    def add_to_cart(self):
        self.status_signal.emit(create_msg("Opening Cart", "normal"))
        webbrowser.open_new(BEST_BUY_CART_URL.format(sku=self.sku_id))
        return BEST_BUY_CART_URL.format(sku=self.sku_id)

    def auto_checkout(self):
        self.auto_add_to_cart()
        time.sleep(1)
        self.browser.get("https://www.bestbuy.com/checkout/r/fast-track")
        self.start_checkout()

    def auto_add_to_cart(self):
        self.status_signal.emit(create_msg("Attempting to auto add to cart...", "normal"))
        self.browser.refresh()
        time.sleep(2)
        if self.browser.find_elements_by_xpath("//button[@class='btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button'][1]"):
                button = self.browser.find_element_by_xpath("//button[@class='btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button'][1]")
        else:
                button = None
        if button:
            self.browser.execute_script("return arguments[0].scrollIntoView(true);", button)
            button.click()
        
    def start_checkout(self):
        self.status_signal.emit(create_msg("Attempting Checkout", "normal"))
        self.did_submit = False
        time.sleep(2)
        self.browser.find_element_by_xpath('//input[@id="credit-card-cvv"]').send_keys(self.profile['card_cvv'])
        while not self.did_submit:
            try:
                if not settings.dont_buy:
                    self.browser.find_element_by_xpath('//button[@class="btn btn-lg btn-block btn-primary button__fast-track"]').click()
                    time.sleep(5)
                if 'https://www.bestbuy.com/checkout/r/thank-you' in self.browser.current_url or settings.dont_buy:
                    if settings.dont_buy:
                        self.status_signal.emit(create_msg("Mock Order Placed", "success"))
                        self.did_submit = True
                    else:
                        self.status_signal.emit(create_msg("Order Placed", "success"))
                        self.did_submit = True
            except:
                self.status_signal.emit(create_msg('Retrying submit order until success', 'normal'))
