from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from webdriver_manager.chrome import ChromeDriverManager
from chromedriver_py import binary_path as driver_path
from utils import random_delay, send_webhook, change_driver, create_msg
import settings, time


class Target:
    def __init__(
        self,
        task_id,
        status_signal,
        image_signal,
        product,
        profile,
        proxy,
        monitor_delay,
        error_delay,
    ):
        (
            self.task_id,
            self.status_signal,
            self.image_signal,
            self.product,
            self.profile,
            self.monitor_delay,
            self.error_delay,
        ) = (
            task_id,
            status_signal,
            image_signal,
            product,
            profile,
            float(monitor_delay),
            float(error_delay),
        )

        starting_msg = "Starting Target"
        self.browser = self.init_driver()
        self.product_image = None

        if settings.dont_buy:
            starting_msg = "Starting Target in dev mode; will not actually checkout"

        self.status_signal.emit(create_msg(starting_msg, "normal"))
        self.status_signal.emit(create_msg("Logging In..", "normal"))
        self.login()
        self.monitor()
        self.atc()
        self.checkout()
        self.submit_billing()

        if not settings.dont_buy:
            self.submit_order()
        else:
            self.status_signal.emit(create_msg("Mock Order Placed", "success"))
            send_webhook(
                "OP",
                "Target",
                self.profile["profile_name"],
                self.task_id,
                self.product_image,
            )

    def init_driver(self):
        driver_manager = ChromeDriverManager()
        driver_manager.install()
        change_driver(self.status_signal, driver_path)
        var = driver_path
        browser = webdriver.Chrome(driver_path)

        browser.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                  Object.defineProperty(navigator, 'webdriver', {
                   get: () => undefined
                  })
                """
            },
        )

        return browser

    def login(self):
        self.browser.get("https://www.target.com")
        self.browser.find_element_by_id("account").click()
        wait(self.browser, 3).until(
            EC.element_to_be_clickable((By.ID, "accountNav-signIn"))
        ).click()
        wait(self.browser, 3).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(settings.target_user)
        password = self.browser.find_element_by_id("password")
        password.send_keys(settings.target_pass)
        self.browser.find_element_by_id("login").click()

        # Gives it time for the login to complete
        time.sleep(
            random_delay(
                self.monitor_delay,
                settings.random_delay_start,
                settings.random_delay_stop,
            )
        )

    def monitor(self):
        img_found = False
        in_stock = False

        self.browser.get(self.product)

        while not in_stock:
            try:
                if not img_found:
                    product_img = self.browser.find_elements_by_class_name(
                        "slideDeckPicture"
                    )[0].find_element_by_tag_name("img")
                    self.image_signal.emit(product_img.get_attribute("src"))
                    self.product_image = product_img.get_attribute("src")
                    img_found = True
            except Exception as e:
                continue

            try:
                ship_btn = self.browser.find_element_by_xpath(
                    '//button[@data-test= "shipItButton"]'
                )
                self.browser.execute_script(
                    "return arguments[0].scrollIntoView(true);", ship_btn
                )
                ship_btn.click()
                in_stock = True
                self.status_signal.emit(create_msg("Added to cart", "normal"))
            except Exception as e:
                self.status_signal.emit(create_msg("Waiting on Restock", "normal"))
                time.sleep(
                    random_delay(
                        self.monitor_delay,
                        settings.random_delay_start,
                        settings.random_delay_stop,
                    )
                )
                self.browser.refresh()

    def atc(self):
        declined_ins = False
        at_checkout = False

        self.status_signal.emit(create_msg("Declining Insurance", "normal"))

        while not declined_ins:
            try:
                decline_ins_btn = self.browser.find_element_by_xpath(
                    '//button[@data-test= "espModalContent-declineCoverageButton"]'
                )
                decline_ins_btn.click()
                declined_ins = True
            except:
                continue

        self.status_signal.emit(create_msg("Viewing Cart before Checkout", "normal"))

        while not at_checkout:
            try:
                checkout_btn = self.browser.find_element_by_xpath(
                    '//button[@data-test= "addToCartModalViewCartCheckout"]'
                )
                checkout_btn.click()
                at_checkout = True
            except:
                continue

    def checkout(self):
        did_checkout = False
        self.status_signal.emit(create_msg("Checking out", "normal"))

        while not did_checkout:
            try:
                self.browser.find_element_by_xpath(
                    '//button[@data-test= "checkout-button"]'
                ).click()
                did_checkout = True
                time.sleep(
                    random_delay(
                        self.monitor_delay,
                        settings.random_delay_start,
                        settings.random_delay_stop,
                    )
                )
            except:
                continue

    def submit_billing(self):
        added_cc = False
        added_cvv = False

        self.status_signal.emit(create_msg("Entering CC #", "normal"))

        while not added_cc:
            try:
                cc_input = self.browser.find_element_by_id("creditCardInput-cardNumber")
                cc_input.send_keys(self.profile["card_number"])
                self.browser.find_element_by_xpath(
                    '//button[@data-test= "verify-card-button"]'
                ).click()
                added_cc = True
            except:
                self.status_signal.emit(
                    create_msg("CC Verification not needed", "normal")
                )
                return

        while not added_cvv:
            try:
                cvv_input = self.browser.find_element_by_xpath(
                    "input[@data-test= 'credit-card-cvv-input']"
                )
                self.status_signal.emit(create_msg("Entering CC Last 3", "normal"))

                cvv_input.send_keys(self.profile["card-cvv"])
                self.browser.find_element_by_xpath(
                    '//button[@data-test= "save-and-continue-button"]'
                ).click()
                added_cvv = True
            except:
                self.status_signal.emit(create_msg("No need to enter last 3", "normal"))
                break

    def submit_order(self):
        did_submit = False

        self.status_signal.emit(create_msg("Submitting Order", "normal"))
        while not did_submit:
            try:
                self.browser.find_element_by_xpath(
                    '//button[@data-test= "placeOrderButton"]'
                ).click()
                self.status_signal.emit(create_msg("Order Placed", "success"))
                send_webhook(
                    "OP",
                    "Target",
                    self.profile["profile_name"],
                    self.task_id,
                    self.product_image,
                )
                did_submit = True
            except:
                continue
