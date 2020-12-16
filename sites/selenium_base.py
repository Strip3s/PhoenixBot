from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from webdriver_manager.chrome import ChromeDriverManager
from chromedriver_py import binary_path as driver_path
from utils import random_delay, send_webhook, create_msg
from utils.selenium_utils import change_driver
from PyQt5.QtCore import pyqtBoundSignal
import settings, time


class SeleniumBaseClass:
    def __init__(self, task_id: str, status_signal: pyqtBoundSignal, image_signal: pyqtBoundSignal, product: str, profile: dict, proxy: bool, monitor_delay: str, error_delay: str) -> None:
        self.task_id, self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay = task_id, status_signal, image_signal, product, profile, float(
            monitor_delay), float(error_delay)
        self.selector_sequence = list()
        self.possible_interruptions = list()
        self.site_label = ''
        self.product_image = None
        self.TIMEOUT_SHORT = 5
        self.TIMEOUT_LONG = 20
        self.did_submit = False
        self.failed = False
        self.retry_attempts = 10
        self.site_init()
        self.browser = self.init_driver()
        starting_msg = f'Starting {self.site_label}'
        if settings.dont_buy:
            starting_msg = f'Starting {self.site_label} in dev mode; will not actually checkout'
        self.status_signal.emit(create_msg(starting_msg, 'normal'))
        self.status_signal.emit(create_msg('Logging In..', 'normal'))
        self.login()
        self.product_loop()
        send_webhook('OP', self.site_label, self.profile['profile_name'], self.task_id, self.product_image)

    def site_init(self) -> None:
        pass

    def init_driver(self) -> None:
        driver_manager = ChromeDriverManager()
        driver_manager.install()
        change_driver(self.status_signal, driver_path)
        var = driver_path
        browser = webdriver.Chrome(driver_path)

        browser.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                  Object.defineProperty(navigator, 'webdriver', {
                   get: () => undefined
                  })
                '''
        })

        return browser

    def login(self) -> None:
        pass

    def product_loop(self) -> None:
        while not self.did_submit and not self.failed:
            self.monitor()
            self.atc_and_checkout()

    def open_new_tab(self, url: str) -> None:
        windows_before = self.browser.window_handles
        self.browser.execute_script(f'window.open("{url}")')
        wait(self.browser, 10).until(EC.number_of_windows_to_be(2))
        new_window = [x for x in self.browser.window_handles if x not in windows_before][0]
        self.browser.switch_to_window(new_window)

    def close_tab(self) -> None:
        self.browser.close()
        wait(self.browser, 10).until(EC.number_of_windows_to_be(1))
        old_window = self.browser.window_handles[0]
        self.browser.switch_to_window(old_window)

    def check_stock(self, new_tab: bool=False) -> bool:
        pass

    def populate_image(self) -> None:
        pass

    def monitor(self) -> None:
        self.in_stock = False
        self.browser.get(self.product)
        wait(self.browser, self.TIMEOUT_LONG).until(lambda _: self.browser.current_url == self.product)
        while not self.product_image:
            try:
                self.populate_image()
            except:
                continue

        while not self.in_stock:
            try:
                self.in_stock = self.check_stock()
                if self.in_stock:
                    continue
                else:
                    self.status_signal.emit(create_msg('Waiting on Restock', 'normal'))
                    time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                    self.browser.refresh()
            except:
                self.browser.refresh()
                continue

    def atc_and_checkout(self) -> None:
        while not self.did_submit:
            for selector_step in self.selector_sequence:
                for attempt in range(self.retry_attempts + 1):
                    try:
                        wait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, selector_step['path'])))
                        self.process_step(selector_step)
                        break
                    except:
                        if selector_step['optional']:
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

    def find_and_click(self, xpath: str) -> None:
        self.browser.find_element_by_xpath(xpath).click()
            
    def fill_field_and_proceed(self, xpath: str, args: dict) -> None:
        input_field = self.browser.find_element_by_xpath(xpath)
        if len(input_field.get_attribute('value')) == 0:
            input_field.send_keys(args['value'])
        if 'confirm_button' in args:
            if self.browser.find_elements_by_xpath(args['confirm_button']):
                self.find_and_click(args['confirm_button'])

    def process_step(self, selector_step: dict, wait_after: bool=False, silent: bool=False) -> None:
        if self.browser.find_elements_by_xpath(selector_step['path']):
            if not silent:
                self.status_signal.emit(create_msg(selector_step['message'], selector_step['message_type']))
            if selector_step['type'] == 'button':
                self.find_and_click(selector_step['path'])
            elif selector_step['type'] == 'method':
                selector_step['method']()
            elif selector_step['type'] == 'input':
                self.fill_field_and_proceed(selector_step['path'], selector_step['args'])
            if wait_after:
                time.sleep(self.TIMEOUT_SHORT)
        
    def process_interruptions(self, attempt: int=0, silent: bool=False) -> None:
        if not silent:
            self.status_signal.emit(create_msg(f'Interrupted, attempting to resolve ({attempt+1}/{self.retry_attempts})', 'error'))
        for selector_step in self.selector_sequence:
            if selector_step['optional']:
                self.process_step(selector_step, wait_after=True, silent=True)
        for selector_step in self.possible_interruptions:
            self.process_step(selector_step, wait_after=True, silent=True)
