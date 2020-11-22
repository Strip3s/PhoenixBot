try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
except:
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Cipher import PKCS1_OAEP
from base64 import b64encode
from utils import send_webhook, random_delay
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
from urllib import parse
import requests, time, lxml.html, json, sys, settings, urllib3, threading, random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class BestBuy:

    def __init__(self, task_id, status_signal, image_signal, product, profile, proxy, monitor_delay, error_delay):
        self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay = status_signal, image_signal, product, profile, float(monitor_delay), float(error_delay)
        self.payment_id = None
        self.session = requests.Session()
        self.sku_id = parse.parse_qs(parse.urlparse(self.product).query)['skuId'][0]
        self.cookies_from_browser = self.get_cookies_using_browser
        self.kill_cookie_thread = False
        cookie_thread = threading.Thread(
            target=self.launch_cookie_thread,
            args=(),
        )
        cookie_thread.name = "cookieThread"
        cookie_thread.daemon = True
        cookie_thread.start()

        if proxy != False:
            self.session.proxies.update(proxy)
        starting_msg = "Starting"
        if settings.dont_buy:
            starting_msg = "Starting in dev mode - Phoenix Bot will not actually checkout (dont_buy = True)"
        self.status_signal.emit({"msg": starting_msg, "status": "normal"})

        while True:
            self.status_signal.emit({"msg": "Checking Stock", "status": "normal"})
            in_stock = self.check_stock()
            while in_stock is False:
                self.status_signal.emit({"msg": "Waiting For Restock", "status": "normal"})
                time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                in_stock = self.check_stock()
            tas_data = self.get_tas_data()
            # Get Cookies using the browser
            self.set_cookies_using_browser()
            product_image = self.setup_product_metadata()
            if not self.add_to_cart():
                continue
            self.start_checkout()
            self.submit_shipping()
            self.submit_payment(tas_data)
            self.refresh_payment()

            while True:
                success, jwt = self.submit_order()
                if not success and jwt is not None:
                    transaction_id = self.handle_3dsecure(jwt)
                    self.submit_card(transaction_id)
                else:
                    if success:
                        send_webhook("OP", "Bestbuy", self.profile["profile_name"],
                                     task_id, product_image)
                    else:
                        if settings.browser_on_failed:
                            self.status_signal.emit(
                                {"msg": "Browser Ready", "status": "alt",
                                 "url": "https://www.bestbuy.com/checkout/r/fulfillment",
                                 "cookies": [
                                     {"name": cookie.name, "value": cookie.value,
                                      "domain": cookie.domain} for cookie in
                                     self.session.cookies]})
                            send_webhook("B", "Bestbuy",
                                         self.profile["profile_name"], task_id,
                                         product_image)
                        else:
                            send_webhook("PF", "Bestbuy",
                                         self.profile["profile_name"], task_id,
                                         product_image)
                    break
            if success:
                break

            self.kill_cookie_thread = True
            cookie_thread.join()

    def launch_cookie_thread(self):
        while not self.kill_cookie_thread:
            self.status_signal.emit(
                {"msg": "Getting Cookies Using Browser", "status": "normal"})
            self.cookies_from_browser = self.get_cookies_using_browser
            self.status_signal.emit(
                {"msg": "Got Cookies Using Browser", "status": "normal"})
            time.sleep(600)

    def set_cookies_using_browser(self):
        self.status_signal.emit(
            {"msg": "Getting Cookies from Selenium", "status": "normal"})
        cookies = self.cookies_from_browser
        if cookies is not None:
            for cookie in cookies:
                self.session.cookies.set(name=cookie['name'],
                                         value=cookie['value'],
                                         domain=cookie['domain'])
            self.session.cookies.set(name='G_ENABLED_IDPS', value='google',
                                     domain='www.bestbuy.com')
            self.status_signal.emit(
                {"msg": "Got Cookies from Selenium", "status": "normal"})

    @property
    def get_cookies_using_browser(self):
        # setting options for headless, profile to
        # ignore certs, chrome driver & timeout
        options = Options()
        options.headless = True
        options.add_argument('ignore-certificate-errors')
        browser = None
        try:
            browser = webdriver.Chrome(
                ChromeDriverManager().install())
            browser.get(self.product)
            browser.get('https://www.bestbuy.com/cart')
            # Waiting a few seconds to for the JS to execute.
            time.sleep(5)
            return browser.get_cookies()
        except exceptions.TimeoutException:
            print(f"Timeout while connecting to {self.product}")
            return None
        except Exception as e:
            self.status_signal.emit({
                "msg": "Error Getting Cookies From Browser(line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e),
                "status": "error"})
            return None
        finally:
            if browser is not None:
                browser.quit()

    def get_tas_data(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-encoding": "gzip, deflate",
            "Accept-language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": settings.userAgent
        }
        while True:
            try:
                self.status_signal.emit({"msg": "Getting TAS Data", "status": "normal"})
                r = requests.get("https://www.bestbuy.com/api/csiservice/v2/key/tas", headers=headers)
                self.status_signal.emit({"msg": "Got TAS Data", "status": "normal"})
                return json.loads(r.text)
            except Exception as e:
                self.status_signal.emit({"msg": "Error Getting TAS Data(line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def setup_product_metadata(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
            "user-agent": settings.userAgent
        }
        image_found = False
        while True:
            self.status_signal.emit({"msg": "Loading Product Page For Metadata", "status": "normal"})
            try:
                r = self.session.get(self.product, headers=headers, verify=False)
                if r.status_code == 200:
                    doc = lxml.html.fromstring(r.text)
                    if not image_found:
                        self.status_signal.emit({"msg": "Checking For Product Image", "status": "normal"})
                        product_image = doc.xpath('//img[@class="primary-image"]/@src')[0]
                        self.image_signal.emit(product_image)
                        image_found = True
                        self.status_signal.emit({"msg": "Retrieved Product Image", "status": "normal"})
                        return product_image
                    self.status_signal.emit({"msg": "Unable To Retrieve Product Image", "status": "normal"}) # not really an error since we don't really care about the image
                    time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                else:
                    self.status_signal.emit({"msg": "Product Not Found", "status": "normal"})
                    time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
            except Exception as e:
                self.status_signal.emit({"msg": "Error Loading Product Page (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def check_stock(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "User-Agent": settings.userAgent
        }
        while True:
            try:
                #TODO: Refactor to utilize URL decoded versions across all sites during base class design shift
                url = "https://www.bestbuy.com/api/tcfb/model.json?paths=%5B%5B%22shop%22%2C%22scds%22%2C%22v2%22%2C%22page%22%2C%22tenants%22%2C%22bbypres%22%2C%22pages%22%2C%22globalnavigationv5sv%22%2C%22header%22%5D%2C%5B%22shop%22%2C%22buttonstate%22%2C%22v5%22%2C%22item%22%2C%22skus%22%2C{}%2C%22conditions%22%2C%22NONE%22%2C%22destinationZipCode%22%2C%22%2520%22%2C%22storeId%22%2C%22%2520%22%2C%22context%22%2C%22cyp%22%2C%22addAll%22%2C%22false%22%5D%5D&method=get".format(
                    self.sku_id)
                r = self.session.get(url, headers=headers, verify=False)
                return "ADD_TO_CART" in r.text
            except Exception as e:
                self.status_signal.emit({"msg": "Error Checking Stock (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def add_to_cart(self):
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Content-length": "31",
            "Content-Type": "application/json; charset=UTF-8",
            "Origin": "https://www.bestbuy.com",
            "Referer": self.product,
            "User-Agent": settings.userAgent
        }
        body = {
            "items":
                [{
                    "skuId": self.sku_id
                }]
        }
        tries = 0
        while True:
            self.status_signal.emit({"msg": "Adding To Cart", "status": "normal"})
            try:
                r = self.session.post("https://www.bestbuy.com/cart/api/v1/addToCart", json=body,
                                      headers=headers, verify=False)
                if r.status_code == 200 and json.loads(r.text)["cartCount"] >= 1:
                    self.status_signal.emit({"msg": "Added To Cart", "status": "carted"})
                    return True
                else:
                    self.status_signal.emit({"msg": "Error Adding To Cart", "status": "error"})
                    if tries == 3:
                        return False
                    tries += 1
                    time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg": "Error Adding To Cart (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def go_identity_url(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.bestbuy.com/cart",
            "User-Agent": settings.userAgent
        }
        try:
            r = self.session.get(self.identity_url, headers=headers, verify=False)
        except Exception as e:
            self.status_signal.emit({
                "msg": "Error Starting Cart Checkout (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e),
                "status": "error"})

    def cart_checkout(self):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Origin": "https://www.bestbuy.com",
            "X-ORDER-ID": self.order_id,
            "User-Agent": settings.userAgent
        }
        try:
            r = self.session.post(
                "https://www.bestbuy.com/cart/d/checkout",
                headers=headers, json=None, verify=False)
            if r.status_code == 200:
                r = json.loads(
                    r.text)
                self.identity_url = r['updateData']['redirectUrl']
                return
            self.status_signal.emit(
                {"msg": "Error Starting Cart Checkout", "status": "error"})
            time.sleep(self.error_delay)
        except Exception as e:
            self.status_signal.emit({
                "msg": "Error Starting Cart Checkout (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e),
                "status": "error"})

    def start_checkout(self):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": settings.userAgent,
        }
        while True:
            self.status_signal.emit({"msg": "Starting Checkout", "status": "normal"})
            try:
                r = self.session.get("https://www.bestbuy.com/checkout/r/fast-track", headers=headers, verify=False)
                if r.status_code == 200:
                    r = json.loads(r.text.split("var orderData = ")[1].split(";")[0])
                    self.order_id = r["id"]
                    self.items_id = r["items"][0]["id"]
                    self.customerOrderId = r['customerOrderId']
                    self.status_signal.emit({"msg": "Started Checkout", "status": "normal"})
                    self.cart_checkout()
                    self.go_identity_url()
                    return
                self.status_signal.emit({"msg": "Error Starting Checkout", "status": "error"})
                time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg": "Error Starting Checkout (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def submit_shipping(self):
        headers = {
            "Accept": "application/com.bestbuy.order+json",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://www.bestbuy.com",
            "Referer": "https://www.bestbuy.com/checkout/r/fulfillment",
            "User-Agent": settings.userAgent,
            "x-user-interface": "DotCom-Optimized"
        }
        profile = self.profile
        body = {"items": [{
            "id": self.items_id,
            "type": "DEFAULT",
            "selectedFulfillment": {
                "shipping": {
                    "address": {
                        "country": "US",
                        "saveToProfile": False,
                        "street2": profile["shipping_a2"],
                        "useAddressAsBilling": False,
                        "middleInitial": "",
                        "lastName": profile["shipping_lname"],
                        "street": profile["shipping_a1"],
                        "city": profile["shipping_city"],
                        "override": False,
                        "zipcode": profile["shipping_zipcode"],
                        "state": profile["shipping_state"],
                        "firstName": profile["shipping_fname"],
                        "isWishListAddress": False,
                        "dayPhoneNumber": profile["shipping_phone"],
                        "type": "RESIDENTIAL"
                    }
                }
            },
            "giftMessageSelected": False
        }],
            "phoneNumber": profile["shipping_phone"],
            "smsNotifyNumber": "",
            "smsOptIn": False,
            "emailAddress": profile["shipping_email"]}
        while True:
            self.status_signal.emit({"msg": "Submitting Shipping", "status": "normal"})
            try:
                if self.payment_id is None:
                    r = self.session.patch("https://www.bestbuy.com/checkout/orders/{}/".format(
                        self.order_id), json=body, headers=headers, verify=False)
                if json.loads(r.text)["id"] == self.order_id:
                    self.payment_id = json.loads(r.text)["payment"]['id']
                    r = self.session.post("https://www.bestbuy.com/checkout/orders/{}/validate".format(
                        self.order_id), headers=headers, verify=False)
                    if r.status_code is 200 or r.status_code is 201:
                        self.status_signal.emit({"msg": "Submitted Shipping", "status": "normal"})
                    else:
                        self.status_signal.emit({"msg": "Error Submitting Shipping - Received following status code: {}", "status": "error"}).format(
                            r.status_code
                        )
                        time.sleep(self.error_delay)
                    return
            except Exception as e:
                self.status_signal.emit({"msg": "Error Submitting Shipping (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def submit_payment(self, tas_data):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Origin": "https://www.bestbuy.com",
            "Referer": "https://www.bestbuy.com/checkout/r/payment",
            "User-Agent": settings.userAgent,
            "X-CLIENT": "CHECKOUT",
            "X-CONTEXT-ID": self.customerOrderId
        }
        profile = self.profile
        card_number = profile["card_number"]
        key = RSA.importKey(tas_data["publicKey"])
        cipher = PKCS1_OAEP.new(key)
        encrypted_card = b64encode(cipher.encrypt(("00926999" + card_number).encode("utf-8"))).decode("utf-8")
        zero_string = ""
        for i in range(len(card_number) - 10):
            zero_string += "0"
        self.bin_number = card_number[:6]
        encrypted_card += ":3:" + tas_data["keyId"] + ":" + self.bin_number + zero_string + card_number[-4:]
        body = {
            "billingAddress": {
                "country": "US",
                "useAddressAsBilling": True,
                "middleInitial": "",
                "lastName": profile["billing_lname"],
                "city": profile["billing_city"],
                "state": profile["billing_state"],
                "firstName": profile["billing_fname"],
                "isWishListAddress": False,
                "addressLine1": profile["billing_a1"],
                "addressLine2": profile["billing_a2"],
                "dayPhone": profile["billing_phone"],
                "postalCode": profile["billing_zipcode"],
                "userOverridden": False
            },
            "creditCard": {
                "hasCID": False,
                "invalidCard": False,
                "isCustomerCard": False,
                "isNewCard": True,
                "isVisaCheckout": False,
                "govPurchaseCard": False,
                "number": encrypted_card,
                "binNumber": self.bin_number,
                "isPWPRegistered": False,
                "expMonth": profile["card_month"],
                "expYear": profile["card_year"],
                "cvv": profile["card_cvv"],
                "orderId": self.customerOrderId,
                "saveToProfile": False,
                "type": profile["card_type"].upper(),
                "international": False,
                "virtualCard": False
            }
        }
        while True:
            self.status_signal.emit({"msg": "Submitting Payment", "status": "normal"})
            try:
                r = self.session.put("https://www.bestbuy.com/payment/api/v1/payment/{}/creditCard".format(
                    self.payment_id), data=json.dumps(body), headers=headers, verify=False)
                r = json.loads(r.text)
                if r["paymentId"] == self.payment_id:
                    self.status_signal.emit({"msg": "Submitted Payment", "status": "normal"})
                    return
                self.status_signal.emit({"msg": "Error Submitting Payment", "status": "error"})
                time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg": "Error Submitting Payment (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def refresh_payment(self):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Origin": "https://www.bestbuy.com",
            "Referer": "https://www.bestbuy.com/checkout/r/payment",
            "User-Agent": settings.userAgent,
            "X-Native-Checkout-Version": "__VERSION__",
            "X-User-Interface": "DotCom-Optimized"
        }
        while True:
            self.status_signal.emit(
                {"msg": "Refreshing Payment", "status": "normal"})
            try:
                r = self.session.post(
                    "https://www.bestbuy.com/checkout/orders/{}/paymentMethods/refreshPayment".format(
                        self.order_id), json={}, headers=headers,
                    verify=False)
                r = json.loads(r.text)
                if r['id'] == self.order_id:
                    self.status_signal.emit({"msg": "Payment Refreshed", "status": "normal"})
                    return
            except Exception as e:
                self.status_signal.emit({
                    "msg": "Error Submitting Order (line {} {} {})".format(
                        sys.exc_info()[-1].tb_lineno, type(e).__name__, e),
                    "status": "error"})
                time.sleep(self.error_delay)

    def submit_order(self):
        if settings.dont_buy is True:
            self.status_signal.emit({"msg": "DEV MODE ENABLED - Skipping Order Submission", "status": "normal"})
            return

        headers = {
            "Accept": "application/com.bestbuy.order+json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://www.bestbuy.com",
            "Referer": "https://www.bestbuy.com/checkout/r/payment",
            "User-Agent": settings.userAgent,
            "X-User-Interface": "DotCom-Optimized"
        }
        body = {
            "browserInfo": {
                "javaEnabled": False,
                "language": "en-US",
                "userAgent": settings.userAgent,
                "height": "{}".format(random.randint(1000, 1300)),
                "width": "{}".format(random.randint(1000, 1300)),
                "timeZone": "240",
                "colorDepth": "24"
            }
        }
        while True:
            self.status_signal.emit({"msg": "Submitting Order", "status": "alt"})
            try:
                r = self.session.post("https://www.bestbuy.com/checkout/orders/{}/".format(
                    self.order_id), json=body, headers=headers, verify=False)
                r = json.loads(r.text)
                if r["state"] == "SUBMITTED":
                    self.status_signal.emit({"msg": "Order Placed", "status": "success"})
                    return True, None
                else:
                    errors = r.get("errors")
                    if errors:
                        if errors[0].get("errorCode") == "PAY_SECURE_REDIRECT":
                            self.status_signal.emit({"msg": "3DSecure Found, Starting Auth Process", "status": "error"})
                            self.status_signal.emit({"msg": f"Payment error {errors[0]['errorCode']}", "status": "error"})
                            return False, r["paySecureResponse"]["stepUpJwt"]
                        else:
                            self.status_signal.emit({"msg": "Payment Failed", "status": "error"})
                            return False, None
            except Exception as e:
                self.status_signal.emit({"msg": "Error Submitting Order (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def handle_3dsecure(self, jwt):
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.bestbuy.com",
            "Referer": "https://www.bestbuy.com/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": settings.userAgent
        }
        body = {
            "JWT": jwt,
            "TermUrl": "/payment/r/threeDSecure/redirect",
            "MD": ""
        }
        while True:
            self.status_signal.emit({"msg": "Authorizing Card (1)", "status": "normal"})
            try:
                r = self.session.post("https://centinelapi.cardinalcommerce.com/V2/Cruise/StepUp",
                                      data=body, headers=headers, verify=False)
                doc = lxml.html.fromstring(r.text)
                pa_req = doc.xpath('//input[@id="payload"]/@value')[0]
                md = doc.xpath('//input[@id="mcsId"]/@value')[0]
                term_url = doc.xpath('//input[@id="termUrl"]/@value')[0]
                acs_url = doc.xpath('//input[@id="acsUrl"]/@value')[0]
                break
            except Exception as e:
                self.status_signal.emit({"msg": "Error Authorizing Card (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "1eaf.cardinalcommerce.com",
            "Origin": "https://centinelapi.cardinalcommerce.com",
            "Referer": "https://centinelapi.cardinalcommerce.com/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": settings.userAgent
        }
        body = {
            "PaReq": pa_req,
            "MD": md,
            "TermUrl": term_url
        }
        while True:
            self.status_signal.emit({"msg": "Authorizing Card (2)", "status": "normal"})
            try:
                r = self.session.post(acs_url, data=body, headers=headers, verify=False)
                doc = lxml.html.fromstring(r.text)
                pa_req = doc.xpath('//input[@name="PaReq"]/@value')[0]
                term_url = doc.xpath('//input[@name="TermUrl"]/@value')[0]
                md = doc.xpath('//input[@name="MD"]/@value')[0]
                url = doc.xpath("//form/@action")[0]
                break
            except Exception as e:
                self.status_signal.emit({"msg": "Error Authorizing Card (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "secure4.arcot.com",
            "Origin": "https://1eaf.cardinalcommerce.com",
            "Referer": "https://1eaf.cardinalcommerce.com/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": settings.userAgent
        }
        body = {
            "PaReq": pa_req,
            "TermUrl": term_url,
            "MD": md
        }
        while True:
            self.status_signal.emit({"msg": "Authorizing Card (3)", "status": "normal"})
            try:
                r = self.session.post(url, data=body, headers=headers, verify=False)
                doc = lxml.html.fromstring(r.text)
                pa_res = doc.xpath('//input[@name="PaRes"]/@value')[0]
                pa_req = doc.xpath('//input[@name="PaReq"]/@value')[0]
                md = doc.xpath('//input[@name="MD"]/@value')[0]
                device_id = doc.xpath('//input[@name="DeviceID"]/@value')[0]
                locale = doc.xpath('//input[@name="locale"]/@value')[0]
                ABSlog = doc.xpath('//input[@name="ABSlog"]/@value')[0]
                device_DNA = doc.xpath('//input[@name="deviceDNA"]/@value')[0]
                execution_time = \
                    doc.xpath('//input[@name="executionTime"]/@value')[0]
                dna_error = doc.xpath('//input[@name="dnaError"]/@value')[0]
                mesc = doc.xpath('//input[@name="mesc"]/@value')[0]
                mesc_iteration_count = \
                    doc.xpath('//input[@name="mescIterationCount"]/@value')[0]
                desc = doc.xpath('//input[@name="desc"]/@value')[0]
                is_DNA_done = doc.xpath('//input[@name="isDNADone"]/@value')[0]
                url = doc.xpath("//form/@action")[0]
                break
            except Exception as e:
                self.status_signal.emit({"msg": "Error Authorizing Card (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "1eaf.cardinalcommerce.com",
            "Origin": "https://secure4.arcot.com",
            "Referer": "https://secure4.arcot.com/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": settings.userAgent
        }
        body = {
            "PaRes": pa_res,
            "PaReq": pa_req,
            "MD": md,
            "DeviceID": device_id,
            "locale": locale,
            "ABSlog": ABSlog,
            "deviceDNA": device_DNA,
            "executionTime": execution_time,
            "dnaError": dna_error,
            "mesc": mesc,
            "mescIterationCount": mesc_iteration_count,
            "desc": desc,
            "isDNADone": is_DNA_done
        }
        while True:
            self.status_signal.emit({"msg": "Authorizing Card (4)", "status": "normal"})
            try:
                r = self.session.post(url, data=body, headers=headers, verify=False)
                doc = lxml.html.fromstring(r.text)
                pa_res = doc.xpath('//input[@name="PaRes"]/@value')[0]
                md = doc.xpath('//input[@name="MD"]/@value')[0]
                url = doc.xpath("//form/@action")[0]
                break
            except Exception as e:
                self.status_signal.emit({"msg": "Error Authorizing Card (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://1eaf.cardinalcommerce.com",
            "referer": "https://1eaf.cardinalcommerce.com/",
            "upgrade-insecure-requests": "1",
            "user-agent": settings.userAgent
        }
        body = {
            "PaRes": pa_res,
            "MD": md
        }
        while True:
            self.status_signal.emit({"msg": "Authorizing Card (5)", "status": "normal"})
            try:
                r = self.session.post(url, data=body, headers=headers, verify=False)
                jwt = r.text.split('parent.postMessage("')[1].split('"')[0]
                break
            except Exception as e:
                self.status_signal.emit({"msg": "Error Authorizing Card (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://centinelapi.cardinalcommerce.com",
            "referer": "https://centinelapi.cardinalcommerce.com/V2/Cruise/StepUp",
            "upgrade-insecure-requests": "1",
            "user-agent": settings.userAgent
        }
        body = {
            "McsId": md,
            "CardinalJWT": jwt,
            "Error": ""
        }
        while True:
            self.status_signal.emit({"msg": "Authorizing Card (6)", "status": "normal"})
            try:
                r = self.session.post("https://centinelapi.cardinalcommerce.com/V1/Cruise/TermRedirection",
                                      data=body, headers=headers, verify=False)
                doc = lxml.html.fromstring(r.text)
                transaction_id = doc.xpath('//input[@name="TransactionId"]/@value')[0]
                return transaction_id
            except Exception as e:
                self.status_signal.emit({"msg": "Error Authorizing Card (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)

    def submit_card(self, transaction_id):
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://www.bestbuy.com",
            "Referer": "https://www.bestbuy.com/checkout/r/payment",
            "User-Agent": settings.userAgent,
            "X-User-Interface": "DotCom-Optimized",
            "X-Native-Checkout-Version": "__VERSION__"
        }
        body = {"PaRes": "", "orderId": self.order_id, "TransactionId": transaction_id}
        while True:
            self.status_signal.emit({"msg": "Submitting Card", "status": "normal"})
            try:
                r = self.session.post("https://www.bestbuy.com/checkout/api/1.0/paysecure/submitCardAuthentication",
                                      json=body, headers=headers, verify=False)
                if r.status_code == 200:
                    self.status_signal.emit({"msg": "Submitted Card", "status": "normal"})
                    return
                else:
                    self.status_signal.emit({"msg": "Error Submitting Card", "status": "error"})
                    time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg": "Error Submitting Card (line {} {} {})".format(
                    sys.exc_info()[-1].tb_lineno, type(e).__name__, e), "status": "error"})
                time.sleep(self.error_delay)
