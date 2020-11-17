import requests, string, random
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from webdriver_manager.chrome import ChromeDriverManager
from chromedriver_py import binary_path as driver_path
import re

DONT_BUY = True

class Target:
    def __init__(self, task_id, status_signal, image_signal, product, profile, proxy, monitor_delay, error_delay):
        self.status_signal, self.image_signal, self.product, self.profile, self.monitor_delay, self.error_delay = status_signal, image_signal, product, profile, float(
            monitor_delay), float(error_delay)

        self.session = requests.Session()
        #
        # if proxy != False:
        #     self.session.proxies.update(proxy)
        self.run()

        self.status_signal.emit(self.send_msg("Starting", "normal"))
        # self.product_image = self.monitor()
        # self.product_image, offer_id = self.monitor()

    def run(self):
        driver_manager = ChromeDriverManager()
        driver_manager.install()

        self.change_driver(driver_path)
        browser = webdriver.Chrome(driver_path)

        browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
             get: () => undefined
            })
          """
        })

        browser.get("https://www.target.com")

        browser.find_element_by_id("account").click()

        wait(browser, 3).until(EC.element_to_be_clickable((By.ID, "accountNav-signIn"))).click()

        my_username = "username"
        my_password = "password"

        wait(browser, 3).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(my_username)
        password = browser.find_element_by_id("password")
        password.send_keys(my_password)
        browser.find_element_by_id("login").click()

    # https://stackoverflow.com/questions/33225947/can-a-website-detect-when-you-are-using-selenium-with-chromedriver
    def change_driver(self, loc):
        print(loc)
        fin = open(loc, 'rb')
        data = fin.read()
        val = "$cdc_" + "".join(random.choices(string.ascii_letters + string.digits, k=22)) + "_"

        result = re.search(b"[$]cdc_[a-zA-Z0-9]{22}_", data)

        if result is not None:
            data = data.replace(result.group(0), val.encode())
            fin.close()
            fin = open(loc, 'wb')
            fin.truncate()
            fin.write(data)
            fin.close()
        else:
            fin.close()


    def send_msg(self, msg, status):
        return {"msg": msg, "status": status}

    #
    # def monitor(self):
    #     headers = {
    #         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #         "accept-encoding": "gzip, deflate, br",
    #         "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    #         "cache-control": "max-age=0",
    #         "upgrade-insecure-requests": "1",
    #         "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36"
    #     }
    #
    #     image_found = False
    #     product_image = ""
    #
    #     self.status_signal.emit(self.send_msg("Loading Product Page", "normal"))
    #
    #     try:
    #         r = self.session.get(self.product, headers=headers)
    #         print("Loaded Product Page w/ Status Code: ", r.status_code)
    #
    #         if r.status_code == 200:
    #             doc = lxml.html.fromstring(r.text)
    #
    #             if not image_found:
    #                 product_image = "https:" + doc.xpath('//meta[@property="og:image"]/@content')[0]
    #                 self.image_signal.emit(product_image)
    #                 image_found = True
    #
    #                 if "Ship It" in r.text:
    #                     return product_image
    #
    #
    #     except Exception as e:
    #         print("Fail..")
    #         print(e)
    #         return