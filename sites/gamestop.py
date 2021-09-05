from requests.sessions import default_headers
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from chromedriver_py import binary_path as driver_path
from utils import random_delay, send_webhook, create_msg
from utils.selenium_utils import change_driver
import settings, time

options = Options()
options.page_load_strategy = "eager"
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

### Need to optimize options below for pageload but not piss off gamestop

prefs = {
        "profile.managed_default_content_settings.images":2,
        # "profile.default_content_setting_values.notifications":2,
        # "profile.managed_default_content_settings.stylesheets":2,
        # "profile.managed_default_content_settings.cookies":1,
        # "profile.managed_default_content_settings.javascript":1,
        # "profile.managed_default_content_settings.plugins":1,
        # "profile.managed_default_content_settings.popups":2,
        # "profile.managed_default_content_settings.geolocation":1,
        # "profile.managed_default_content_settings.media_stream":2,
}

options.add_experimental_option("prefs", prefs)
options.add_argument(f"User-Agent={settings.userAgent}")

class GameStop:
    def __init__(self, task_id, status_signal, image_signal, product, profile, proxy, monitor_delay, error_delay, max_price):
        self.task_id, self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay, self.max_price = task_id, status_signal, image_signal, product, profile, float(
            monitor_delay), float(error_delay), max_price

        starting_msg = "Starting GameStop"
        self.browser = self.init_driver()
        self.product_image = None

        self.SHORT_TIMEOUT = 5
        self.LONG_TIMEOUT = 20

        if settings.dont_buy:
            starting_msg = "Starting GameStop in dev mode; will not actually checkout."

        self.status_signal.emit(create_msg(starting_msg, "normal"))
        self.login()
        self.monitor()
        self.add_to_cart()

        #### Need to setup captcha solvers to work the below, TODO Still needed??
        self.submit_billing()
        self.submit_order()

    def init_driver(self):
        if settings.run_headless:
            self.status_signal.emit(create_msg("Running headless","normal"))
            options.add_argument("--headless")

        ## Gamestop does not like it when we do not have a user-agent

        
        driver = webdriver.Chrome(ChromeDriverManager().install(),options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                  Object.defineProperty(navigator, 'webdriver', {
                   get: () => undefined
                  })
                """
        })
        driver.minimize_window()
        return driver

    def login(self):
        self.status_signal.emit(create_msg("Logging In..", "normal"))

        #load home page so we get the cookies and referrer crap
        self.browser.get('https://www.gamestop.com/')

        time.sleep(5)

        if not settings.run_headless:
            # self.browser.maximize_window()
            self.browser.get("https://www.gamestop.com/?openLoginModal=accountModal")

            time.sleep(5)
        
            self.browser.find_element_by_xpath('//a[@id="account-modal-link-nocache"]').click()
        else:
            self.browser.get("https://www.gamestop.com/login/")
        
        wait(self.browser, self.LONG_TIMEOUT).until(EC.element_to_be_clickable((By.ID, "login-form-email")))

        email = self.browser.find_element_by_id("login-form-email")
        email.send_keys(settings.gamestop_user)

        wait(self.browser, self.LONG_TIMEOUT).until(EC.element_to_be_clickable((By.ID, "login-form-password")))
        time.sleep(5)
        password = self.browser.find_element_by_id("login-form-password")
        password.send_keys(settings.gamestop_pass)

        time.sleep(2) # slight delay for in-between filling out login info and clicking Sign In

        sign_in_btn = wait(self.browser, self.LONG_TIMEOUT).until(
             EC.presence_of_element_located((By.XPATH, "//button[@class='btn btn-block mb-2 sign-in-submit']"))
        )
        sign_in_btn.click()
        time.sleep(10)

    def monitor(self):

        ## verify we have signed successfully else we should abort the task or attempt sign-in again
        # (TODO: add max attempts to sign-in before exiting task)
        if "user-message-initial" in self.browser.page_source:
            self.status_signal.emit(create_msg("Gamestop Successfully logged in...", "normal"))
        else:
            self.status_signal.emit(create_msg("Error logging in... please restart task","stopnow"))

        # TODO: Exit task if we are not signed in
        self.status_signal.emit(create_msg("Checking Stock..", "normal"))
        
        # self.browser.set_window_size(900, 900)

        self.browser.get(self.product)
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == self.product)

        in_stock = False

        while not in_stock:
            try: 
                wait(self.browser, random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop)).until(EC.element_to_be_clickable((By.XPATH, '//button[@data-buttontext="Add to Cart"]')))
                add_to_cart_btn = self.browser.find_element_by_xpath('//button[@data-buttontext="Add to Cart"]')
                add_to_cart_btn.click()
                time.sleep(1)
                if not add_to_cart_btn.is_enabled():
                    self.status_signal.emit(create_msg("Waiting For Restock", "normal"))
                    self.browser.refresh()
                    continue
                in_stock = True
                self.status_signal.emit(create_msg("Added to cart", "normal"))
                self.browser.maximize_window()
                # remove stop temporarily to see if gamestop captcha is an issue
                # self.status_signal.emit(create_msg("Added to cart, check for captcha","stopnow"))
                self.browser.get("https://www.gamestop.com/cart/")
            except:
                self.status_signal.emit(create_msg("Waiting For Restock", "normal"))
                self.browser.refresh()

    def add_to_cart(self):
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == "https://www.gamestop.com/cart/")

        ##### THERE IS NOW A CAPTCHA HERE (POPUP)
        
        self.status_signal.emit(create_msg("Checking Age Verification", "normal"))

        try:
            seventeen_or_older_btn = self.browser.find_element_by_xpath('//*[@id="age-gate-modal"]/div/div/div[2]/div/div[2]/button')
            seventeen_or_older_btn.click()
            time.sleep(2) # short delay for age verification modal to disappear
            self.browser.get("https://www.gamestop.com/checkout/?stage=payment#payment")
        except:
            self.browser.get("https://www.gamestop.com/checkout/?stage=payment#payment")

    def submit_billing(self):
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == "https://www.gamestop.com/checkout/?stage=payment#payment")

        self.status_signal.emit(create_msg("Entering CVV #", "normal"))

        wait(self.browser, self.LONG_TIMEOUT).until(EC.element_to_be_clickable((By.ID, "saved-payment-security-code")))
        cvv_input = self.browser.find_element_by_id("saved-payment-security-code")
        cvv_input.send_keys(self.profile["card_cvv"])
        order_review_btn = self.browser.find_element_by_class_name("btn.btn-primary.btn-block.submit-payment")
        order_review_btn.click()

    def submit_order(self):
        wait(self.browser, self.LONG_TIMEOUT).until(lambda _: self.browser.current_url == "https://www.gamestop.com/checkout/?stage=placeOrder#placeOrder")

        self.status_signal.emit(create_msg("Submitting Order..", "normal"))
        
        ##### THERE IS NOW A CAPTCHA HERE (POPULATED - NEED TO CLICK)

        wait(self.browser, self.LONG_TIMEOUT).until(EC.element_to_be_clickable((By.CLASS_NAME, 'btn.btn-primary.btn-block.place-order')))

        if not settings.dont_buy:
            order_review_btn = self.browser.find_element_by_class_name("btn.btn-primary.btn-block.place-order")
            order_review_btn.click()
            self.status_signal.emit(create_msg("Order Placed", "success"))
            send_webhook("OP", "GameStop", self.profile["profile_name"], self.task_id, self.product_image)
        else:
            self.status_signal.emit(create_msg("Mock Order Placed", "success"))
            send_webhook("OP", "GameStop", self.profile["profile_name"], self.task_id, self.product_image)

    # TODO: when running with headless == False it would be good to quit browsers when task is stopped (might be good to keep it open if it errors out however for diagnostics)
    # def stop(self):
    #     self.browser.quit()