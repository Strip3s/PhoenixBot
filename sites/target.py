from sites.selenium_base import *


class Target(SeleniumBaseClass):

    def site_init(self) -> None:
        self.selector_sequence = [
            {'type': 'method', 'path': '//button[@data-test="orderPickupButton"] | //button[@data-test="shipItButton"]', 'method': self.find_and_click_atc, 'message': 'Added to cart', 'message_type': 'normal', 'optional': False}
            , {'type': 'button', 'path': '//button[@data-test="espModaalContent-declineCoverageButton"]', 'message': 'Declining Coverage', 'message_type': 'normal', 'optional': True}
            , {'type': 'button', 'path': '//button[@data-test="addToCartModalViewCartCheckout"]', 'message': 'Viewing Cart before Checkout', 'message_type': 'normal', 'optional': False}
            , {'type': 'button', 'path': '//button[@data-test="checkout-button"]', 'message': 'Checking out', 'message_type': 'normal', 'optional': False}
            , {'type': 'method', 'path': '//button[@data-test="placeOrderButton"]', 'method': self.submit_order, 'message': 'Submitting order', 'message_type': 'normal', 'optional': False}
        ]
        self.possible_interruptions = [
            {'type': 'method', 'path': '//input[@id="password"]', 'method': self.fill_and_authenticate, 'message': 'Authenticating', 'message_type': 'normal'}
            , {'type': 'input', 'path': '//input[@id="creditCardInput-cardNumber"]', 'args': {'value': self.profile['card_number'], 'confirm_button': '//button[@data-test="verify-card-button"]'}, 'message': 'Entering CC #', 'message_type': 'normal'}
            , {'type': 'input', 'path': '//input[@id="creditCardInput-cvv"]', 'args': {'value': self.profile['card_cvv']}, 'message': 'Entering CC #', 'message_type': 'normal'}
        ]
        self.site_label = 'Target'

    def login(self) -> None:
        self.browser.get('https://www.target.com')
        self.browser.find_element_by_id('account').click()
        wait(self.browser, self.TIMEOUT_LONG).until(EC.element_to_be_clickable((By.ID, 'accountNav-signIn'))).click()
        wait(self.browser, self.TIMEOUT_LONG).until(EC.presence_of_element_located((By.ID, 'username')))
        self.fill_and_authenticate()

        # Gives it time for the login to complete
        time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))

    def fill_and_authenticate(self) -> None:
        if self.browser.find_elements_by_id('username'):
            self.fill_field_and_proceed('//input[@id="username"]', {'value': settings.target_user})
        self.fill_field_and_proceed('//input[@id="password"]', {'value': settings.target_pass, 'confirm_button': '//button[@id="login"]'})

    def check_stock(self, new_tab: bool=False):
        stock = False
        if new_tab:
            self.open_new_tab(self.product)
        if len(self.browser.find_elements_by_xpath('//button[@data-test="orderPickupButton"]')) > 0 or len(self.browser.find_elements_by_xpath('//button[@data-test="shipItButton"]')) > 0:
            stock = True
        if new_tab:
            self.close_tab()
        return stock

    def populate_image(self) -> None:
        product_img = self.browser.find_elements_by_class_name('slideDeckPicture')[0].find_element_by_tag_name(
            'img')
        self.image_signal.emit(product_img.get_attribute('src'))
        self.product_image = product_img.get_attribute('src')

    def submit_order(self) -> None:
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
                        self.status_signal.emit(create_msg('Mock Order Placed', 'success'))
                    else:
                        self.status_signal.emit(create_msg('Order Placed', 'success'))
                    send_webhook('OP', self.site_label, self.profile['profile_name'], self.task_id, self.product_image)
                    self.did_submit = True
            except:
                self.status_signal.emit(create_msg('Retrying submit order until success', 'normal'))

    def find_and_click_atc(self) -> None:
        if self.browser.current_url == self.product and self.check_stock():
            if self.browser.find_elements_by_xpath('//button[@data-test="orderPickupButton"]'):
                button = self.browser.find_element_by_xpath('//button[@data-test="orderPickupButton"]')
            elif self.browser.find_elements_by_xpath('//button[@data-test="shipItButton"]'):
                button = self.browser.find_element_by_xpath('//button[@data-test="shipItButton"]')
        if button:
            self.browser.execute_script('return arguments[0].scrollIntoView(true);', button)
            self.atc_clicked = True
            button.click()
