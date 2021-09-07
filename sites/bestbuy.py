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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException

from utils.json_utils import find_values
from utils.selenium_utils import enable_headless # not sure this actually works since we call options() below
from utils import create_msg, log_webpage

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

prefs = {
        "profile.managed_default_content_settings.images":2,
        "profile.default_content_setting_values.notifications":2,
        "profile.managed_default_content_settings.stylesheets":2,
        "profile.managed_default_content_settings.cookies":1,
        "profile.managed_default_content_settings.javascript":1,
        "profile.managed_default_content_settings.plugins":1,
        "profile.managed_default_content_settings.popups":2,
        "profile.managed_default_content_settings.geolocation":1,
        "profile.managed_default_content_settings.media_stream":2,
}
options.add_experimental_option("prefs", prefs)
options.add_argument("user-data-dir=.profile-bb")
# print(options.to_capabilities(),flush=True)

def driver_click(driver, find_type, selector):
    """Driver Wait and Click Settings."""
    while True:
        if find_type == 'css':
            try:
                driver.find_element_by_css_selector(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)
        elif find_type == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)
        elif find_type == 'xpath':
            try:
                driver.find_element_by_xpath(f"//*[@class='{selector}']").click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)

class BestBuy:

    def __init__(self, status_signal, image_signal, product, profile, proxy, monitor_delay, error_delay):
        self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay = status_signal, image_signal, product, profile, float(monitor_delay), float(error_delay)
        self.sku_id = parse.parse_qs(parse.urlparse(self.product).query)['skuId'][0]
        self.session = requests.Session()
        # TODO: Refactor Bird Bot Auto Checkout Functionality.
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
        # self.status_signal.emit(create_msg("Loading headless driver.", "normal"))


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

        chrome_options = Options()
        if settings.run_headless:
            self.status_signal.emit(create_msg("Running headless","normal"))
            chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"User-Agent={settings.userAgent}")

        driver = webdriver.Chrome(ChromeDriverManager().install(),options=chrome_options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                  Object.defineProperty(navigator, 'webdriver', {
                   get: () => undefined
                  })
                """
        })

        return driver

    def login(self):
        try:
            self.status_signal.emit(create_msg("Logging in...", "normal"))
            self.browser.get("https://www.bestbuy.com/identity/global/signin")

            time.sleep(5)
            # set remember me to true, probably don't need this TBH
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "ca-remember-me"))
            ).click()
            
            # Fill email field
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "fld-e"))
            ).send_keys(settings.bestbuy_user)
            
            # Fill password field
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "fld-p1"))
            ).send_keys(settings.bestbuy_pass)
            
            time.sleep(2)
            signInButton = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH,"//button[contains(@class,'cia-form__controls__submit')]"))
            )
            signInButton.click()
                    
            WebDriverWait(self.browser, 10).until(
                lambda x: "Official Online Store" in self.browser.title or "Sign In - Add Recovery Phone" in self.browser.title
            )

            if "Sign In - Add Recovery Phone" in self.browser.title:
                self.status_signal.emit(create_msg("Sign In - Add Recovery phone page hit, probably can ignore...","normal"))
                # skipBtn = WebDriverWait(self.browser, 10).until(
                #     EC.presence_of_element_located((By.XPATH,"//button[@text()='Skip for now']"))
                # )
                # skipBtn.click()
                self.browser.get("https://www.bestbuy.com")
        except Exception as e:
            self.status_signal.emit(create_msg("Bestbuy login error, see console for details","error"))
            print(f"Dumped webpage to file: {log_webpage('errors','bby_login',self.browser.page_source)}")

        if not settings.run_headless:
            try:
                closeModal = WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@class='c-close-icon c-modal-close-icon']"))
                )
                if closeModal:
                    closeModal.click()
                    self.status_signal.emit(create_msg("Closing annoying modal", "normal"))
            except Exception as e:
                pass
        
    def verify_signed_in(self):
        signedIn = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[@class='plButton-label v-ellipsis']"))
        )
        if signedIn:
            return True
        else:
            return False


    def check_stock(self):
        if self.verify_signed_in():
            self.status_signal.emit(create_msg("Bestbuy successfully logged in.","normal"))
        time.sleep(2)
        # verify we are on the product page here and prep to add to cart
        self.browser.get(self.product)

        # this queries the bestbuy api for stock
        while not self.in_stock():
            sleep(5)
        self.status_signal.emit(create_msg(f"Item {self.sku_id} is in stock!", "normal"))
        # TODO: Refactor Bird Bot Auto Checkout Functionality.
        self.browser.refresh()
        self.status_signal.emit(create_msg(f"SKU: {self.sku_id} in stock: {BEST_BUY_CART_URL.format(sku=self.sku_id)}", "normal"))
        self.add_to_cart()
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


    def add_to_cart(self, retry=False):
        self.status_signal.emit(create_msg("Opening Cart", "normal"))
        # webbrowser.open_new(BEST_BUY_CART_URL.format(sku=self.sku_id))
        
        if retry:
            self.browser.get(self.product)

        atcBtn = WebDriverWait(self.browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".add-to-cart-button"))
        )
        if atcBtn:
            atcBtn.click()
            self.status_signal.emit(create_msg("Add to cart button is live!", "normal"))

            # Queue system logic - courtesy RTX-3070-BEST-BUY-BOT
            WebDriverWait(self.browser, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,".add-to-cart-button"))
            )

            driver_click(self.browser, 'css', '.add-to-cart-button')

            self.status_signal.emit(create_msg("In Queue, refreshing page until our turn", "normal"))
            # send text message here
            time.sleep(5)
            self.browser.refresh()

            while True:
                try:
                    add_to_cart = self.browser.find_element_by_css_selector(".add-to-cart-button")
                    please_wait_enabled = add_to_cart.get_attribute('aria-describedby')

                    if please_wait_enabled:
                        print("Please wait enabled",flush=True)
                        self.browser.refresh()
                        time.sleep(15)
                    else:  # When Add to Cart appears. This will click button.
                        WebDriverWait(self.browser, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".add-to-cart-button"))
                        )
                        time.sleep(2)
                        driver_click(self.browser, 'css', '.add-to-cart-button')
                        time.sleep(2)
                        break
                except(NoSuchElementException, TimeoutException) as error:
                    print(f'Queue System Refresh Error: ${error}',flush=True)
            
            self.browser.get('https://www.bestbuy.com/cart')

            try:
                WebDriverWait(self.browser, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary']"))
                )
                time.sleep(1)
                driver_click(self.browser, 'xpath', 'btn btn-lg btn-block btn-primary')
                self.status_signal.emit(create_msg("Product still in cart", "normal"))
                self.start_checkout()
            except (NoSuchElementException, TimeoutException):
                self.status_signal.emit(create_msg("Item is not in cart anymore, Retrying...","normal"))
                time.sleep(3)
                self.add_to_cart(True)
        
    def start_checkout(self):

        self.status_signal.emit(create_msg("Attempting Checkout", "normal"))

        if "Returning Customer" in self.browser.page_source:
             # Fill password field
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.ID, "fld-p1"))
            ).send_keys(settings.bestbuy_pass)
            
            time.sleep(2)
            signInButton = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH,"//button[contains(@class,'cia-form__controls__submit')]"))
            )
            signInButton.click()


        #### keep this for now, not sure if we still need it
        # # click shipping option if available, currently sets it to ISPU (in store pick up)
        # try:

        #     self.status_signal.emit(create_msg("Selecting Shipping Checkout", "normal"))
        #     WebDriverWait(self.browser, 5).until(
        #         EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary button__fast-track']"))
        #     )
        #     time.sleep(2)
        #     shipping_class = self.browser.find_element_by_xpath("//*[@class='ispu-card__switch']")
        #     shipping_class.click()
        # except (NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as error:
        #     print(f'shipping error: {error}',flush=True)


        try:
            self.status_signal.emit(create_msg("Trying CVV Number.","normal"))
            security_code = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.ID, "credit-card-cvv"))
            )
            # time.sleep(1)
            # security_code = self.browser.find_element_by_id("cvv")
            time.sleep(1)
            security_code.send_keys(self.profile['card_cvv'])
        except (NoSuchElementException, TimeoutException):
            pass

        self.did_submit = False
        while not self.did_submit:
            try:
                WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary button__fast-track']"))
                )
                # comment the one down below. vv
                if not settings.dont_buy:
                    driver_click(self.browser, 'xpath', 'btn btn-lg btn-block btn-primary button__fast-track')
                
                if 'https://www.bestbuy.com/checkout/r/thank-you' in self.browser.current_url or settings.dont_buy:
                    if settings.dont_buy:
                        self.status_signal.emit(create_msg("Mock Order Placed", "success"))
                        self.did_submit = True
                    else:
                        self.status_signal.emit(create_msg("Order Placed", "success"))
                        self.did_submit = True
            except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
                print("Could Not Complete Checkout.",flush=True)
                pass
            except:
                self.status_signal.emit(create_msg('Retrying submit order until success', 'normal'))