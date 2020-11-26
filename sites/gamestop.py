from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from webdriver_manager.chrome import ChromeDriverManager
from chromedriver_py import binary_path as driver_path
from utils import random_delay, send_webhook
import string, random, settings, time, re

class GameStop:
    def __init__(self, task_id, status_signal, image_signal, product, profile, proxy, monitor_delay, error_delay, max_price):
        self.task_id, self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay, self.max_price = task_id, status_signal, image_signal, product, profile, float(
            monitor_delay), float(error_delay), max_price

        starting_msg = "Starting GameStop"
        self.browser = self.init_driver()
        self.product_image = None

        self.SHORT_TIMEOUT = 5
        self.LONG_TIMEOUT = 15

        if settings.dont_buy:
            starting_msg = "Starting GameStop in dev mode; will not actually checkout."

        self.status_signal.emit(self.create_msg(starting_msg, "normal"))
        self.login()
        self.monitor()
        self.add_to_cart()
        self.submit_billing()
        self.submit_order()



    def create_msg(self, msg, status):
        return {"msg": msg, "status": status}


    # https://stackoverflow.com/questions/33225947/can-a-website-detect-when-you-are-using-selenium-with-chromedriver
    def change_driver(self, loc):
        print(loc)
        fin = open(loc, 'rb')
        data = fin.read()
        val = "$cdc_" + "".join(random.choices(string.ascii_letters + string.digits, k=22)) + "_"

        result = re.search(b"[$]cdc_[a-zA-Z0-9]{22}_", data)

        if result is not None:
            self.status_signal.emit(self.create_msg("Changing value in Chromedriver", "normal"))
            data = data.replace(result.group(0), val.encode())
            fin.close()
            fin = open(loc, 'wb')
            fin.truncate()
            fin.write(data)
            fin.close()
        else:
            fin.close()


    def init_driver(self):
        driver_manager = ChromeDriverManager()
        driver_manager.install()
        # self.change_driver(driver_path)
        browser = webdriver.Chrome(driver_path)

        browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                  Object.defineProperty(navigator, 'webdriver', {
                   get: () => undefined
                  })
                """
        })

        return browser


    def login(self):
        my_username = "username"
        my_password = "password"

        self.status_signal.emit(self.create_msg("Logging In..", "normal"))

        self.browser.get("https://www.gamestop.com")

        wait(self.browser, self.SHORT_TIMEOUT).until(EC.element_to_be_clickable((By.LINK_TEXT, "MY ACCOUNT")))
        self.browser.find_element_by_link_text('MY ACCOUNT').click()

        wait(self.browser, self.SHORT_TIMEOUT).until(EC.element_to_be_clickable((By.ID, "signIn"))).click()

        wait(self.browser, self.SHORT_TIMEOUT).until(EC.presence_of_element_located((By.ID, "login-form-email"))).send_keys(my_username)

        password = self.browser.find_element_by_id("login-form-password")
        password.send_keys(my_password)

        time.sleep(1) # slight delay for in-between filling out login info and clicking Sign In

        self.browser.find_element_by_xpath('//*[@id="signinCheck"]/button').click()

        # Gives it time for the login to complete
        time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))


    def monitor(self):
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == "https://www.gamestop.com/account/")

        self.status_signal.emit(self.create_msg("Checking Stock..", "normal"))

        in_stock = False

        self.browser.get(self.product)
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == self.product)

        while not in_stock:
            try: 
                wait(self.browser, self.LONG_TIMEOUT).until(EC.visibility_of_element_located((By.XPATH, '//button[@data-buttontext="Add to Cart"]')))
                wait(self.browser, random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop)).until(EC.element_to_be_clickable((By.XPATH, '//button[@data-buttontext="Add to Cart"]')))
                add_to_cart_btn = self.browser.find_element_by_xpath('//button[@data-buttontext="Add to Cart"]')
                add_to_cart_btn.click()
                in_stock = True
                self.status_signal.emit(self.create_msg("Added to cart", "normal"))
                time.sleep(3)
                self.browser.get("https://www.gamestop.com/cart/")
            except:
                self.status_signal.emit(self.create_msg("Waiting For Restock", "normal"))
                time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                self.browser.refresh()


    def add_to_cart(self):
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == "https://www.gamestop.com/cart/")
        
        self.status_signal.emit(self.create_msg("Checking Age Verification", "normal"))

        try:
            seventeen_or_older_btn = self.browser.find_element_by_xpath('//*[@id="age-gate-modal"]/div/div/div[2]/div/div[2]/button')
            seventeen_or_older_btn.click()
            time.sleep(2) # short delay for age verification modal to disappear
            self.browser.get("https://www.gamestop.com/checkout/?stage=payment#payment")
        except:
            self.browser.get("https://www.gamestop.com/checkout/?stage=payment#payment")
        

    def submit_billing(self):
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == "https://www.gamestop.com/checkout/?stage=payment#payment")

        self.status_signal.emit(self.create_msg("Entering CVV #", "normal"))

        wait(self.browser, self.SHORT_TIMEOUT).until(EC.element_to_be_clickable((By.ID, "saved-payment-security-code")))
        cvv_input = self.browser.find_element_by_id("saved-payment-security-code")
        cvv_input.send_keys(self.profile["card_cvv"])
        order_review_btn = self.browser.find_element_by_xpath('//*[@id="checkout-main"]/div[1]/div[1]/div[7]/div/div/div/div[11]/button[2]')
        order_review_btn.click()


    def submit_order(self):
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == "https://www.gamestop.com/checkout/?stage=placeOrder#placeOrder")

        self.status_signal.emit(self.create_msg("Submitting Order..", "normal"))

        wait(self.browser, self.SHORT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="checkout-main"]/div[1]/div[2]/div[1]/div[2]/div[11]/button')))

        if not settings.dont_buy:
            order_review_btn = self.browser.find_element_by_xpath('//*[@id="checkout-main"]/div[1]/div[1]/div[7]/div/div/div/div[11]/button[2]')
            order_review_btn.click()
            self.status_signal.emit(self.create_msg("Order Placed", "success"))
            send_webhook("OP", "GameStop", self.profile["profile_name"], self.task_id, self.product_image)
        else:
            self.status_signal.emit(self.create_msg("Mock Order Placed", "success"))
            send_webhook("OP", "GameStop", self.profile["profile_name"], self.task_id, self.product_image)
