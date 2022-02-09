from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait as wait
# from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from chromedriver_py import binary_path as driver_path
from selenium.webdriver.firefox.options import Options

from utils import random_delay, send_webhook, create_msg
from utils.selenium_utils import change_driver
import settings, time, random

# options = Options()

# ### Need to experiment with options below to optimize page load but not piss off target

# # options.page_load_strategy = "eager"
# # options.add_experimental_option("excludeSwitches", ["enable-automation"])
# # options.add_experimental_option("useAutomationExtension", False)
# options.add_argument('--disable-blink-features=AutomationControlled')

# # prefs = {
# #         "profile.managed_default_content_settings.images":1,
# #         "profile.default_content_setting_values.notifications":1,
# #         "profile.managed_default_content_settings.stylesheets":1,
# #         "profile.managed_default_content_settings.cookies":1,
# #         "profile.managed_default_content_settings.javascript":1,
# #         "profile.managed_default_content_settings.plugins":1,
# #         "profile.managed_default_content_settings.popups":1,
# #         "profile.managed_default_content_settings.geolocation":1,
# #         "profile.managed_default_content_settings.media_stream":1,
# # }

# # options.add_experimental_option("prefs", prefs)
# options.add_argument(f"user-data-dir={mypath}") 
# # options.add_argument("user-data-dir=C:\\Users\\larse\\AppData\\Local\\Google\\Chrome\\User Data\\") 
# options.add_argument(f"User-Agent={settings.userAgent}")

class Target:
    def __init__(self, task_id, status_signal, image_signal, product, profile, proxy, monitor_delay, error_delay):
        self.task_id, self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay = task_id, status_signal, image_signal, product, profile, float(
            monitor_delay), float(error_delay)
        self.xpath_sequence = [
            {'type': 'method', 'path': '//button[@data-test="orderPickupButton"] | //button[@data-test="shipItButton"]', 'method': self.find_and_click_atc, 'message': 'Added to cart', 'message_type': 'normal', 'optional': False}
            , {'type': 'button', 'path': '//button[@data-test="espModalContent-declineCoverageButton"]', 'message': 'Declining Coverage', 'message_type': 'normal', 'optional': True}
            , {'type': 'button', 'path': '//button[@data-test="addToCartModalViewCartCheckout"]', 'message': 'Viewing Cart before Checkout', 'message_type': 'normal', 'optional': False}
            , {'type': 'button', 'path': '//button[@data-test="checkout-button"]', 'message': 'Checking out', 'message_type': 'normal', 'optional': False}
            , {'type': 'method', 'path': '//button[@data-test="placeOrderButton"]', 'method': self.submit_order, 'message': 'Submitting order', 'message_type': 'normal', 'optional': False}
        ]
        self.possible_interruptions = [
            {'type': 'method', 'path': '//input[@id="password"]', 'method': self.quick_fill_for_checkout, 'message': 'Authenticating', 'message_type': 'normal'},
            {'type': 'input', 'path': '//input[@id="creditCardInput-cardNumber"]', 'args': {'value': self.profile['card_number'], 'confirm_button': '//button[@data-test="verify-card-button"]'}, 'message': 'Entering CC #', 'message_type': 'normal'},
            {'type': 'input', 'path': '//input[@id="creditCardInput-cvv"]', 'args': {'value': self.profile['card_cvv']}, 'message': 'Entering CC #', 'message_type': 'normal'}
        ]
        starting_msg = "Starting Target"
        self.browser = self.init_driver()
        if self.browser:
            self.product_image = None
            self.TIMEOUT_SHORT = 5
            self.TIMEOUT_LONG = 20
            self.did_submit = False
            self.failed = False
            self.retry_attempts = 10
            if settings.dont_buy:
                starting_msg = "Starting Target in dev mode; will not actually checkout"
            self.status_signal.emit(create_msg(starting_msg, "normal"))
            self.status_signal.emit(create_msg("Logging In..", "normal"))
            self.login()
            self.img_found = False
            self.product_loop()
            send_webhook("OP", "Target", self.profile["profile_name"], self.task_id, self.product_image)

    def init_driver(self):
        options = Options()
        if settings.run_headless:
            self.status_signal.emit(create_msg("Running headless","normal"))
            options.headless = True            
        
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", settings.userAgent)
        if settings.geckodriver_path == "":
            self.status_signal.emit(create_msg("Install geckodriver & set folder location","stopnow"))

            return False
        else:
            driver = webdriver.Firefox(firefox_profile=profile, firefox_options=options, executable_path='geckodriver')

            return driver

    def login(self):
        self.browser.get("https://www.target.com")
        accountBtn = wait(self.browser, self.TIMEOUT_LONG).until(
            EC.presence_of_element_located((By.ID, "account"))
        )
        accountBtn.click()

        test = wait(self.browser, 5).until(
            EC.presence_of_element_located((By.XPATH,"//li[@id='accountNav-signIn']/a"))
        )
        test.click()
        time.sleep(10)
        self.fill_and_authenticate()

        test = self.browser.find_element_by_xpath('//span[@data-test="accountUserName"]')
        time.sleep(1)
        if "sign in" in test.text.lower():
            if settings.run_headless:
                self.status_signal.emit(create_msg("Did not detect username on target page. Got \"{}\"".format(test.text),"stopnow"))
            else:
                self.status_signal.emit(create_msg("Did not detect username on target page. Got \"{}\"".format(test.text),"normal"))
        else:
            self.status_signal.emit(create_msg("Succesfully signed in as {}".format(test.text),"normal"))
        # # Gives it time for the login to complete
        time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))

        #TODO verify we logged in here

    def fill_and_authenticate(self):

        # slowly enters username and password with random waits between each character

        if self.browser.find_elements_by_id('username'):
            for key in settings.target_user:
                self.browser.find_element_by_xpath('//input[@id="username"]').send_keys(key)
                time.sleep(random.uniform(0.5, 1.5))
        
            for key in settings.target_pass:
                self.browser.find_element_by_xpath('//input[@id="password"]').send_keys(key)
                time.sleep(random.uniform(0.5, 1.5))
                
            loginBtn = wait(self.browser, self.TIMEOUT_LONG).until(
                EC.presence_of_element_located((By.XPATH,'//button[@id="login"]'))
            )
            loginBtn.click()

            time.sleep(2)
        else:
            self.browser.find_element_by_xpath('//input[@id="password"]').send_keys(settings.target_pass)

            loginBtn = wait(self.browser, self.TIMEOUT_LONG).until(
                EC.presence_of_element_located((By.XPATH,'//button[@id="login"]'))
            )
            loginBtn.click()

    def quick_fill_for_checkout(self):
        self.browser.find_element_by_xpath('//input[@id="password"]').send_keys(settings.target_pass)
        time.sleep(random.uniform(0.5,2.5))

        time.sleep(2)
        # self.browser.find_element_by_xpath('//button[@id="login"]').click()
        loginBtn = wait(self.browser, 5).until(
            EC.presence_of_element_located((By.XPATH,'//button[@id="login"]'))
        )
        loginBtn.click()
        time.sleep(2)

    def product_loop(self):
        while not self.did_submit and not self.failed:
            self.monitor()
            self.atc_and_checkout()

    def check_stock(self, new_tab=False):
        stock = False
        if new_tab:
            windows_before = self.browser.window_handles
            self.browser.execute_script(f'window.open("{self.product}")')
            wait(self.browser, 10).until(EC.number_of_windows_to_be(2))
            new_window = [x for x in self.browser.window_handles if x not in windows_before][0]
            self.browser.switch_to_window(new_window)
        if len(self.browser.find_elements_by_xpath('//button[@data-test="orderPickupButton"]')) > 0 or len(self.browser.find_elements_by_xpath('//button[@data-test="shipItButton"]')) > 0:
            stock = True
        if new_tab:
            self.browser.close()
            wait(self.browser, 10).until(EC.number_of_windows_to_be(1))
            old_window = self.browser.window_handles[0]
            self.browser.switch_to_window(old_window)
            return False
        return stock

    def monitor(self):
        self.in_stock = False
        self.browser.get(self.product)
        wait(self.browser, self.TIMEOUT_LONG).until(lambda _: self.browser.current_url == self.product)

        if "product not available" in self.browser.page_source:
            # self.browser.quit()
            self.status_signal.emit(create_msg("Invalid URL","stopnow"))
        else:
            while not self.img_found:
                try:
                    if not self.img_found:
                        product_img = self.browser.find_elements_by_class_name('slideDeckPicture')[0].find_element_by_tag_name(
                            "img")
                        self.image_signal.emit(product_img.get_attribute("src"))
                        self.product_image = product_img.get_attribute("src")
                        self.img_found = True
                except Exception as e:
                    continue

            while not self.in_stock:
                self.in_stock = self.check_stock()
                if self.in_stock:
                    continue
                else:
                    self.status_signal.emit(create_msg("Waiting on Restock", "normal"))
                    time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                    self.browser.refresh()

    def atc_and_checkout(self):
        while not self.did_submit:
            for xpath_step in self.xpath_sequence:
                for attempt in range(self.retry_attempts + 1):
                    try:
                        wait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, xpath_step['path'])))
                        self.process_step(xpath_step)
                        break
                    except:
                        if xpath_step['optional']:
                            break
                        elif attempt == self.retry_attempts:
                            if not self.check_stock(new_tab=True):
                                self.status_signal.emit(create_msg('Product is out of stock. Resuming monitoring.', 'error'))
                                return
                            else:
                                self.status_signal.emit(create_msg('Encountered unknown page while product in stock. Quitting.', 'error'))
                                self.failed = True
                                return
                        self.process_interruptions(attempt=attempt)

    def submit_order(self):
        self.did_submit = False
        url = self.browser.current_url
        while not self.did_submit:
            try:
                self.process_interruptions(silent=True)
                if not settings.dont_buy:
                    self.browser.find_element_by_xpath('//button[@data-test="placeOrderButton"]').click()
                    time.sleep(5)
                if 'https://www.target.com/co-thankyou' in self.browser.current_url or settings.dont_buy:
                    if settings.dont_buy:
                        self.status_signal.emit(create_msg("Mock Order Placed", "success"))
                    else:
                        self.status_signal.emit(create_msg("Order Placed", "success"))
                    send_webhook("OP", "Target", self.profile["profile_name"], self.task_id, self.product_image)
                    self.did_submit = True
            except:
                self.status_signal.emit(create_msg('Retrying submit order until success', 'normal'))

    def find_and_click(self, xpath):
        self.browser.find_element_by_xpath(xpath).click()
        
    def find_and_click_atc(self):
        if self.browser.current_url == self.product and self.check_stock():
            if self.browser.find_elements_by_xpath('//button[@data-test="orderPickupButton"]'):
                button = self.browser.find_element_by_xpath('//button[@data-test="orderPickupButton"]')
            elif self.browser.find_elements_by_xpath('//button[@data-test="shipItButton"]'):
                button = self.browser.find_element_by_xpath('//button[@data-test="shipItButton"]')
            else:
                button = None
        if button:
            self.browser.execute_script("return arguments[0].scrollIntoView(true);", button)
            self.atc_clicked = True
            button.click()
    
    def fill_field_and_proceed(self, xpath, args):
        input_field = self.browser.find_element_by_xpath(xpath)
        if len(input_field.get_attribute('value')) == 0:
            input_field.send_keys(args['value'])
        if 'confirm_button' in args:
            if self.browser.find_elements_by_xpath(args['confirm_button']):
                self.find_and_click(args['confirm_button'])

    def process_step(self, xpath_step, wait_after=False, silent=False):
        if self.browser.find_elements_by_xpath(xpath_step['path']):
            if not silent:
                self.status_signal.emit(create_msg(xpath_step['message'], xpath_step['message_type']))
            if xpath_step['type'] == 'button':
                self.find_and_click(xpath_step['path'])
            elif xpath_step['type'] == 'method':
                xpath_step['method']()
            elif xpath_step['type'] == 'input':
                self.fill_field_and_proceed(xpath_step['path'], xpath_step['args'])
            if wait_after:
                time.sleep(self.TIMEOUT_SHORT)
        
    def process_interruptions(self, attempt=0, silent=False):
        if not silent:
            self.status_signal.emit(create_msg(f'Interrupted, attempting to resolve ({attempt+1}/{self.retry_attempts})', 'error'))
        for xpath_step in self.xpath_sequence:
            if xpath_step['optional']:
                self.process_step(xpath_step, wait_after=True, silent=True)
        for xpath_step in self.possible_interruptions:
            self.process_step(xpath_step, wait_after=True, silent=True)
        
    
    # TODO: when running with headless == False it would be good to quit browsers when task is stopped (might be good to keep it open if it errors out however for diagnostics)
    # def stop(self):
    #     self.browser.quit()
