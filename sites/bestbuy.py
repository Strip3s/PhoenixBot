from sites.selenium_base import *


class BestBuy(SeleniumBaseClass):

    def site_init(self) -> None:
        self.atc_button_path = '//div[@class="fulfillment-add-to-cart-button"]/div/div/button | //div[@class="fulfillment-combo-add-to-cart-button"]/div/div/button'
        self.selector_sequence = [
            {'type': 'method', 'path': self.atc_button_path, 'method': self.find_and_click_atc, 'message': 'Adding to cart', 'message_type': 'normal'}
        #     , {'type': 'button', 'path': '//button[@data-test="espModalContent-declineCoverageButton"]', 'message': 'Declining Coverage', 'message_type': 'normal'}
        #     , {'type': 'button', 'path': '//button[@data-test="addToCartModalViewCartCheckout"]', 'message': 'Viewing Cart before Checkout', 'message_type': 'normal'}
        #     , {'type': 'button', 'path': '//button[@data-test="checkout-button"]', 'message': 'Checking out', 'message_type': 'normal'}
        #     , {'type': 'method', 'path': '//button[@data-test="placeOrderButton"]', 'method': self.submit_order, 'message': 'Submitting order', 'message_type': 'normal'}
        ]
        self.possible_interruptions = [
            {'type': 'method', 'path': '//input[@id="fld-p1"]', 'method': self.fill_and_authenticate, 'message': 'Authenticating', 'message_type': 'normal'}
        #     , {'type': 'input', 'path': '//input[@id="creditCardInput-cardNumber"]', 'args': {'value': self.profile['card_number'], 'confirm_button': '//button[@data-test="verify-card-button"]'}, 'message': 'Entering CC #', 'message_type': 'normal'}
        #     , {'type': 'input', 'path': '//input[@id="creditCardInput-cvv"]', 'args': {'value': self.profile['card_cvv']}, 'message': 'Entering CC #', 'message_type': 'normal'}
        ]
        self.site_label = 'BestBuy'

    def login(self):
        self.browser.get("https://www.bestbuy.com/identity/global/signin")
        wait(self.browser, self.TIMEOUT_LONG).until(EC.presence_of_element_located((By.ID, 'fld-e')))
        self.fill_and_authenticate()
        wait(self.browser, 120).until(
            lambda x: "Official Online Store" in self.browser.title
        )

    def fill_and_authenticate(self) -> None:
        if self.browser.find_elements_by_id('fld-e'):
            self.fill_field_and_proceed('//input[@id="fld-e"]', {'value': settings.bestbuy_user})
        self.fill_field_and_proceed('//input[@id="fld-p1"]', {'value': settings.bestbuy_pass, 'confirm_button': '//button[@class="btn btn-secondary btn-lg btn-block btn-leading-ficon c-button-icon c-button-icon-leading cia-form__controls__submit "]'})

    def populate_image(self) -> None:
        if self.browser.find_elements_by_xpath('//img[@class="primary-image"] | //div[@class="primary-image-grid"]/div/div/img'):
            product_img = self.browser.find_element_by_xpath('//img[@class="primary-image"] | //div[@class="primary-image-grid"]/div/div/img')
        self.image_signal.emit(product_img.get_attribute('src'))
        self.product_image = product_img.get_attribute('src')

    def check_stock(self, new_tab: bool=False):
        stock = False
        if new_tab:
            self.open_new_tab(self.product)
        if self.browser.find_elements_by_xpath(self.atc_button_path):
            if self.browser.find_element_by_xpath(self.atc_button_path).is_enabled():
                stock = True
        if new_tab:
            self.close_tab()
        return stock

    def find_and_click_atc(self) -> None:
        while self.browser.current_url == self.product:
            try:
                button = wait(self.browser, 5).until(EC.presence_of_element_located((By.XPATH, self.atc_button_path)))
                if button.is_enabled():
                    button.click()
                    time.sleep(5)
                    button = wait(self.browser, 1800).until(EC.presence_of_element_located((By.XPATH, self.atc_button_path)))
                    button.click()
            except:
                self.browser.refresh()
