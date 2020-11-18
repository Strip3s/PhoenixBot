from sites.walmart_encryption import walmart_encryption as w_e
from utils import send_webhook, random_delay
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from PyQt5 import QtCore
import urllib, requests, time, lxml.html, json, sys, settings

class Walmart:
    def __init__(self,task_id,status_signal,image_signal, wait_poll_signal, polling_wait_condition, product,profile,proxy,monitor_delay,error_delay,max_price):
        self.task_id,self.status_signal,self.image_signal,self.product,self.profile,self.monitor_delay,self.error_delay,self.max_price = task_id,status_signal,image_signal,product,profile,float(monitor_delay),float(error_delay),max_price
        
        ####### Browser/Captcha Polling Variables ######
        self.captcha_mutex = QtCore.QMutex()
        self.captcha_wait_condition = polling_wait_condition
        self.wait_poll_signal = wait_poll_signal
        #################################################

        
        self.session = requests.Session()
        if proxy != False:
            self.session.proxies.update(proxy)
        starting_msg = "Starting"
        if settings.dont_buy:
            starting_msg = "Starting in dev mode will not actually checkout (dont_buy = True)"
        self.status_signal.emit({"msg":starting_msg,"status":"normal"})
        self.product_image, offer_id = self.monitor()
        did_add = False
        while did_add is False:
            did_add = self.atc(offer_id)

        item_id, fulfillment_option, ship_method = self.check_cart_items()
        self.submit_shipping_method(item_id, fulfillment_option, ship_method)
        self.submit_shipping_address()
        card_data,PIE_key_id,PIE_phase = self.get_PIE()
        pi_hash = self.submit_payment(card_data,PIE_key_id,PIE_phase)
        self.submit_billing(pi_hash)
        self.submit_order()

    def monitor(self):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "cache-control": "max-age=0",
            "upgrade-insecure-requests": "1",
            "user-agent": settings.userAgent
        }
        image_found = False
        product_image = ""
        while True:
            self.status_signal.emit({"msg":"Loading Product Page","status":"normal"})
            try:
                r = self.session.get(self.product,headers=headers)
                if r.status_code == 200:
                    # check for captcha page
                    if self.is_captcha(r.text):
                        self.status_signal.emit({"msg":"CAPTCHA - Opening Product Page","status":"error"})
                        self.handle_captcha(self.product)
                        continue

                    doc = lxml.html.fromstring(r.text)
                    if not image_found:
                        product_image = doc.xpath('//meta[@property="og:image"]/@content')[0]
                        self.image_signal.emit(product_image)
                        image_found = True
                    price = float(doc.xpath('//span[@itemprop="price"]/@content')[0])
                    if "add to cart" in r.text.lower():
                        if self.max_price !="":
                            if float(self.max_price) < price:
                                self.status_signal.emit({"msg":"Waiting For Price Restock","status":"normal"})
                                self.session.cookies.clear()
                                time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                                continue
                        offer_id = json.loads(doc.xpath('//script[@id="item"]/text()')[0])["item"]["product"]["buyBox"]["products"][0]["offerId"]
                        return product_image, offer_id
                    self.status_signal.emit({"msg":"Waiting For Restock","status":"normal"})
                    self.session.cookies.clear()
                    time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                else:
                    self.status_signal.emit({"msg":"Product Not Found","status":"normal"})
                    time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
            except Exception as e:
                self.status_signal.emit({"msg":"Error Loading Product Page (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)
    
    def atc(self,offer_id):
        headers={
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.walmart.com",
            "referer": self.product,
            "user-agent": settings.userAgent,
            "wm_offer_id": offer_id
        }
        body = {"offerId":offer_id,"quantity":1, "location":{"postalCode":self.profile["shipping_zipcode"],"city":self.profile["shipping_city"],"state":self.profile["shipping_state"],"isZipLocated":True},"shipMethodDefaultRule":"SHIP_RULE_1"}


        while True:
            self.status_signal.emit({"msg":"Adding To Cart","status":"normal"})
            try:
                r = self.session.post("https://www.walmart.com/api/v3/cart/guest/:CID/items",json=body,headers=headers)

                # check for captcha page
                if self.is_captcha(r.text):
                    self.status_signal.emit({"msg":"Opening CAPTCHA","status":"error"})
                    self.handle_captcha(self.product)
                    return False

                if r.status_code == 201 or r.status_code == 200 and json.loads(r.text)["checkoutable"] == True:
                    self.status_signal.emit({"msg":"Added To Cart","status":"carted"})
                    return True
                else:
                    self.handle_captcha("https://www.walmart.com/cart")
                    self.status_signal.emit({"msg":"Error Adding To Cart","status":"error"})
                    time.sleep(self.error_delay) 
                    return False
            except Exception as e:
                self.status_signal.emit({"msg":"Error Adding To Cart (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)
                return False

    def check_cart_items(self):
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.walmart.com",
            "referer": "https://www.walmart.com/checkout/",
            "user-agent": settings.userAgent,
            "wm_vertical_id": "0",
            "wm_cvv_in_session": "true",
        }
            

        profile = self.profile
        body = {"postalCode":profile["shipping_zipcode"],"city":profile["shipping_city"],"state":profile["shipping_state"],"isZipLocated":True,"crt:CRT":"","customerId:CID":"","customerType:type":"","affiliateInfo:com.wm.reflector":"","storeList": []}
        
        while True:
            self.status_signal.emit({"msg":"Loading Cart Items","status":"normal"})
            try:
                r = self.session.post("https://www.walmart.com/api/checkout/v3/contract?page=CHECKOUT_VIEW",json=body,headers=headers)

                if r.status_code == 201 or r.status_code == 200:
                    r = json.loads(r.text)["items"][0]
                    item_id = r["id"]
                    fulfillment_option = r["fulfillmentSelection"]["fulfillmentOption"]
                    ship_method = r["fulfillmentSelection"]["shipMethod"]
                    self.status_signal.emit({"msg":"Loaded Cart Items","status":"normal"})
                    return item_id, fulfillment_option, ship_method
                else:
                    if json.loads(r.text)["message"] == "Item is no longer in stock.":
                        self.status_signal.emit({"msg":"Waiting For Restock","status":"normal"})
                        time.sleep(random_delay(self.monitor_delay, settings.random_delay_start, settings.random_delay_stop))
                    else:
                        if self.is_captcha(r.text):
                            self.handle_captcha("https://www.walmart.com/checkout")
                        self.status_signal.emit({"msg":"Error Loading Cart Items, Got Response: "+str(r.text),"status":"error"})
                        time.sleep(self.error_delay) 
            except Exception as e:
                self.status_signal.emit({"msg":"Error Loading Cart Items (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)

    def submit_shipping_method(self, item_id, fulfillment_option, ship_method):
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.walmart.com",
            "referer": "https://www.walmart.com/checkout/",
            "user-agent": settings.userAgent,
            "wm_vertical_id": "0"
        }
        body = {"groups":[{"fulfillmentOption":fulfillment_option,"itemIds":[item_id],"shipMethod":ship_method}]}
        while True:
            self.status_signal.emit({"msg":"Submitting Shipping Method","status":"normal"})
            try:
                r = self.session.post("https://www.walmart.com/api/checkout/v3/contract/:PCID/fulfillment",json=body,headers=headers)
                if r.status_code == 200:
                    try:
                        r = json.loads(r.text)
                        self.status_signal.emit({"msg":"Submitted Shipping Method","status":"normal"})
                        return
                    except:
                        pass
                self.status_signal.emit({"msg":"Error Submitting Shipping Method","status":"error"})
                time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg":"Error Submitting Shipping Method (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)
    
    def submit_shipping_address(self):
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "content-type": "application/json",
            "inkiru_precedence": "false",
            "origin": "https://www.walmart.com",
            "referer": "https://www.walmart.com/checkout/",
            "user-agent": settings.userAgent,
            "wm_vertical_id": "0"
        }
        profile = self.profile
        body = {
            "addressLineOne":profile["shipping_a1"],
            "city":profile["shipping_city"],
            "firstName":profile["shipping_fname"],
            "lastName":profile["shipping_lname"],
            "phone":profile["shipping_phone"],
            "email":profile["shipping_email"],
            "marketingEmailPref":False,
            "postalCode":profile["shipping_zipcode"],
            "state":profile["shipping_state"],
            "countryCode":"USA",
            "addressType":"RESIDENTIAL",
            "changedFields":[]
        }
        if profile["shipping_a2"] !="":
            body.update({"addressLineTwo":profile["shipping_a2"]})
        while True:
            self.status_signal.emit({"msg":"Submitting Shipping Address","status":"normal"})
            try:
                r = self.session.post("https://www.walmart.com/api/checkout/v3/contract/:PCID/shipping-address",json=body,headers=headers)
                if r.status_code == 200:
                    try:
                        r = json.loads(r.text)
                        self.status_signal.emit({"msg":"Submitted Shipping Address","status":"normal"})
                        return
                    except:
                        pass
                self.status_signal.emit({"msg":"Error Submitting Shipping Address","status":"error"})
                time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg":"Error Submitting Shipping Address (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)
    
    def get_PIE(self):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Connection": "keep-alive",
            "Host": "securedataweb.walmart.com",
            "Referer": "https://www.walmart.com/",
            "User-Agent": settings.userAgent
        }
        profile = self.profile
        while True:
            self.status_signal.emit({"msg":"Getting Checkout Data","status":"normal"})
            try:
                r = self.session.get("https://securedataweb.walmart.com/pie/v1/wmcom_us_vtg_pie/getkey.js?bust="+str(int(time.time())),headers=headers)
                if r.status_code == 200:
                    PIE_L = int(r.text.split("PIE.L = ")[1].split(";")[0])
                    PIE_E = int(r.text.split("PIE.E = ")[1].split(";")[0])
                    PIE_K = str(r.text.split('PIE.K = "')[1].split('";')[0])
                    PIE_key_id = str(r.text.split('PIE.key_id = "')[1].split('";')[0])
                    PIE_phase = int(r.text.split('PIE.phase = ')[1].split(';')[0])
                    card_data = w_e.encrypt(profile["card_number"],profile["card_cvv"],PIE_L,PIE_E,PIE_K,PIE_key_id,PIE_phase)
                    self.status_signal.emit({"msg":"Got Checkout Data","status":"normal"})
                    return card_data, PIE_key_id, PIE_phase
                self.status_signal.emit({"msg":"Error Getting Checkout Data","status":"error"})
                time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg":"Error Getting Checkout Data (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)
    
    def submit_payment(self,card_data,PIE_key_id,PIE_phase):
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.walmart.com",
            "referer": "https://www.walmart.com/checkout/",
            "user-agent": settings.userAgent
        }
            # "inkiru_precedence": "false",
        profile = self.profile
        body = {
            "encryptedPan": card_data[0],
            "encryptedCvv": card_data[1],
            "integrityCheck": card_data[2],
            "keyId": PIE_key_id,
            "phase": PIE_phase,
            "state": profile["billing_state"],
            "postalCode": profile["billing_zipcode"],
            "addressLineOne": profile["billing_a1"],
            "addressLineTwo": profile["billing_a2"],
            "city": profile["billing_city"],
            "firstName": profile["billing_fname"],
            "lastName": profile["billing_lname"],
            "expiryMonth": profile["card_month"],
            "expiryYear": profile["card_year"],
            "phone": profile["billing_phone"],
            "cardType": profile["card_type"].upper(),
            "isGuest":True
        }
        while True:
            self.status_signal.emit({"msg":"Submitting Payment","status":"normal"})
            try:
                r = self.session.post("https://www.walmart.com/api/checkout-customer/:CID/credit-card",json=body,headers=headers)

                if r.status_code == 200:
                    pi_hash = json.loads(r.text)["piHash"]
                    self.status_signal.emit({"msg":"Submitted Payment","status":"normal"})
                    return pi_hash
                self.status_signal.emit({"msg":"Error Submitting Payment","status":"error"})
                if self.check_browser():
                    return
                time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg":"Error Submitting Payment (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)

    def submit_billing(self,pi_hash):
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "content-type": "application/json",
            "origin": "https://www.walmart.com",
            "referer": "https://www.walmart.com/checkout/",
            "user-agent": settings.userAgent,
            "wm_vertical_id": "0"
        }

        profile = self.profile
        card_data,PIE_key_id,PIE_phase = self.get_PIE()
        body = {
            "payments":[{
                "paymentType":"CREDITCARD",
                "cardType": profile["card_type"].upper(),
                "firstName": profile["billing_fname"],
                "lastName": profile["billing_lname"],
                "addressLineOne": profile["billing_a1"],
                "addressLineTwo": profile["billing_a2"],
                "city": profile["billing_city"],
                "state": profile["billing_state"],
                "postalCode": profile["billing_zipcode"],
                "expiryMonth": profile["card_month"],
                "expiryYear": profile["card_year"],
                "email": profile["billing_email"],
                "phone": profile["billing_phone"],
                "encryptedPan": card_data[0],
                "encryptedCvv": card_data[1],
                "integrityCheck": card_data[2],
                "keyId": PIE_key_id,
                "phase": PIE_phase,
                "piHash": pi_hash
            }]
        }
        while True:
            self.status_signal.emit({"msg":"Submitting Billing","status":"normal"})
            try:
                r = self.session.post("https://www.walmart.com/api/checkout/v3/contract/:PCID/payment",json=body,headers=headers)
                if r.status_code == 200:
                    try:
                        r  = json.loads(r.text)
                        self.status_signal.emit({"msg":"Submitted Billing","status":"normal"})
                        return
                    except:
                        pass
                self.status_signal.emit({"msg":"Error Submitting Billing","status":"error"})
                if self.check_browser():
                    return
                time.sleep(self.error_delay)
            except Exception as e:
                self.status_signal.emit({"msg":"Error Submitting Billing (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)
    
    def submit_order(self):
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://www.walmart.com",
            "referer": "https://www.walmart.com/checkout/",
            "user-agent": settings.userAgent,
            "wm_vertical_id": "0"
        }
        
        if settings.dont_buy is True:
            # TODO: this used to open the page up with everything filled out but only works for some users
            self.status_signal.emit({"msg":"Opening Checkout Page","status":"alt"})
            self.handle_captcha("https://www.walmart.com/checkout/#/payment", close_window_after=False) # OPEN BROWSER TO SEE IF SHIT WORKED
            self.check_browser()  
            return              

        while True:
            self.status_signal.emit({"msg":"Submitting Order","status":"alt"})
            try:
                r = self.session.put("https://www.walmart.com/api/checkout/v3/contract/:PCID/order",json={},headers=headers)
                try:
                    json.loads(r.text)["order"]
                    self.status_signal.emit({"msg":"Order Placed","status":"success"})
                    send_webhook("OP","Walmart",self.profile["profile_name"],self.task_id,self.product_image)
                    return
                except:
                    self.status_signal.emit({"msg":"Payment Failed","status":"error"})
                    
                    # open the page for checkout if failed to auto submit
                    self.handle_captcha("https://www.walmart.com/checkout/#/payment")
                    if self.check_browser():
                        return

                    send_webhook("PF","Walmart",self.profile["profile_name"],self.task_id,self.product_image)
                    return
            except Exception as e:
                self.status_signal.emit({"msg":"Error Submitting Order (line {} {} {})".format(sys.exc_info()[-1].tb_lineno, type(e).__name__, e),"status":"error"})
                time.sleep(self.error_delay)
    
    def check_browser(self):
        if settings.browser_on_failed:
            self.status_signal.emit({"msg":"Browser Ready","status":"alt","url":"https://www.walmart.com/checkout/#/payment","cookies":[{"name":cookie.name,"value":cookie.value,"domain":cookie.domain} for cookie in self.session.cookies]})
            send_webhook("B","Walmart",self.profile["profile_name"],self.task_id,self.product_image)
            return True
        return False

    def handle_captcha(self, url_to_open, close_window_after=True):
        # this opens up chrome browser to get prompted with captcha
        browser = webdriver.Chrome(ChromeDriverManager().install()) # I used ChromeDriverManager to not worry about what chrome driver i had installed
        browser.get("https://www.walmart.com")

        # pass current session cookies to browser before loading url
        for c in self.session.cookies:
            browser.add_cookie({
                'name' : c.name,
                'value' : c.value,
                'domain': c.domain,
                'path': c.path
            })

        browser.get(url_to_open)

        # lock the mutex and let the thread handler know we are awaiting
        # a gui event
        self.captcha_mutex.lock()
        self.wait_poll_signal.emit()
        try:
            # wait for condition to be released 
            self.captcha_wait_condition.wait(self.captcha_mutex)
        finally:
            # unlock the thread
            self.captcha_mutex.unlock()

        for c in browser.get_cookies():
            if c['name'] not in [x.name for x in self.session.cookies]:
                self.session.cookies.set(c['name'], c['value'], path=c['path'], domain=c['domain'])

        if close_window_after:
            browser.quit()

    def is_captcha(self, text):
        return '<div class="re-captcha">' in text
