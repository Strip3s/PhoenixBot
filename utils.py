try:
    from Crypto import Random
    from Crypto.Cipher import AES
except:
    from Cryptodome import Random
    from Cryptodome.Cipher import AES
from colorama import init, Fore, Back, Style
from datetime import datetime
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webhook import DiscordWebhook, DiscordEmbed
from chromedriver_py import binary_path as driver_path
import json, platform, darkdetect, random, settings, threading, hashlib, base64, string, re
normal_color = Fore.CYAN

def write_data(path,data):
    with open(path, "w") as file:
        json.dump(data, file)

#TODO: Enable this as an app setting for user to choose their own optional key & regenerate key on the fly button
try:
  with open("./data/vault.json","r") as file:
      keys = json.load(file)
except FileNotFoundError:
  generateKeySecret = "".join(random.choices(string.ascii_letters + string.digits, k=16))
  write_data("./data/vault.json",[{ "generated_key_secret": generateKeySecret }])
  with open("./data/vault.json","r") as file:
      keys = json.load(file)

e_key = keys[0]['generated_key_secret'].encode()
BLOCK_SIZE=16
if platform.system() == "Windows":
    init(convert=True)
else:
    init()

print(normal_color + "Welcome To Phoenix Bot - In times of crisis, the wise build bridges while the foolish build barriers.")

class BirdLogger:
    def ts(self):
        return str(datetime.now())[:-7]
    def normal(self,task_id,msg):
        print(normal_color + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))
    def alt(self,task_id,msg):
        print(Fore.MAGENTA + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))
    def error(self,task_id,msg):
        print(Fore.RED + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))
    def success(self,task_id,msg):
        print(Fore.GREEN + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))

class Encryption:
    def encrypt(self,msg):
        IV = Random.new().read(BLOCK_SIZE)
        aes = AES.new(self.trans(e_key), AES.MODE_CFB, IV)
        return base64.b64encode(IV + aes.encrypt(msg.encode("utf-8")))
    def decrypt(self,msg):
        msg = base64.b64decode(msg)
        IV = msg[:BLOCK_SIZE]
        aes = AES.new(self.trans(e_key), AES.MODE_CFB, IV)
        return aes.decrypt(msg[BLOCK_SIZE:])
    def trans(self,key):
        return hashlib.md5(key).digest()

def return_data(path):
  try:
    with open(path,"r") as file:
        data = json.load(file)
    return data
  except FileNotFoundError:
    write_data(path,[])
    with open(path,"r") as file:
        data = json.load(file)
    return data

def get_profile(profile_name):
    profiles = return_data("./data/profiles.json")
    for p in profiles:
        if p["profile_name"] == profile_name:
            try:
                p["card_number"] = (Encryption().decrypt(p["card_number"].encode("utf-8"))).decode("utf-8")
            except ValueError:
                pass
            return p
    return None

def get_proxy(list_name):
    if list_name == "Proxy List" or list_name == "None":
        return False
    proxies = return_data("./data/proxies.json")
    for proxy_list in proxies:
        if proxy_list["list_name"] == list_name:
            return format_proxy(random.choice(proxy_list["proxies"].splitlines()))
    return None

def format_proxy(proxy):
    try:
        proxy_parts = proxy.split(":")
        ip, port, user, passw = proxy_parts[0], proxy_parts[1], proxy_parts[2], proxy_parts[3]
        return {
            "http": "http://{}:{}@{}:{}".format(user, passw, ip, port),
            "https": "https://{}:{}@{}:{}".format(user, passw, ip, port)
        }
    except IndexError:
        return {"http": "http://" + proxy, "https": "https://" + proxy}

def send_webhook(webhook_type,site,profile,task_id,image_url):
    if settings.webhook !="":
        webhook = DiscordWebhook(url=settings.webhook, username="Phoenix Bot", avatar_url="https://i.imgur.com/60G42xE.png")
        if webhook_type == "OP":
            if not settings.webhook_on_order:
                return
            embed = DiscordEmbed(title="Order Placed",color=0x34c693)
        elif webhook_type == "B":
            if not settings.webhook_on_browser:
                return
            embed = DiscordEmbed(title="Complete Order in Browser",color=0xf2a689)
        elif webhook_type == "PF":
            if not settings.webhook_on_failed:
                return
            embed = DiscordEmbed(title="Payment Failed",color=0xfc5151)
        embed.set_footer(text="Via Phoenix Bot",icon_url="https://i.imgur.com/60G42xE.png")
        embed.add_embed_field(name="Site", value=site,inline=True)
        embed.add_embed_field(name="Profile", value=profile,inline=True)
        embed.add_embed_field(name="Task ID", value=task_id,inline=True)
        embed.set_thumbnail(url=image_url)
        webhook.add_embed(embed)
        try:
            webhook.execute()
        except:
            pass

# https://stackoverflow.com/questions/33225947/can-a-website-detect-when-you-are-using-selenium-with-chromedriver
def change_driver(status_signal, loc):
    fin = open(loc, 'rb')
    data = fin.read()
    val = "$" + "".join(random.choices(string.ascii_lowercase, k=3)) + "_" +\
          "".join(random.choices(string.ascii_letters + string.digits, k=22)) + "_"

    result = re.search(b"[$][a-z]{3}_[a-zA-Z0-9]{22}_", data)

    if result is not None:
        status_signal.emit(create_msg("Changing value in Chromedriver", "normal"))
        data = data.replace(result.group(0), val.encode())
        fin.close()
        fin = open(loc, 'wb')
        fin.truncate()
        fin.write(data)
        fin.close()
    else:
        fin.close()

def open_browser(link,cookies):
    threading.Thread(target = start_browser, args=(link,cookies)).start()

def start_browser(link,cookies):
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "eager"
    chrome_options = ChromeOptions()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    driver = Chrome(desired_capabilities=caps, executable_path=driver_path, options=chrome_options)
    driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
        Object.defineProperty(window, 'navigator', {
            value: new Proxy(navigator, {
              has: (target, key) => (key === 'webdriver' ? false : key in target),
              get: (target, key) =>
                key === 'webdriver'
                  ? undefined
                  : typeof target[key] === 'function'
                  ? target[key].bind(target)
                  : target[key]
            })
        })
                  """
            },
    )
    driver.get(link)
    for cookie in cookies:
        driver.add_cookie({
            "name": cookie["name"],
            "value" : cookie["value"],
            "domain" : cookie["domain"]
        })
    driver.get(link)

def random_delay(delay, start, stop):
    """
    Returns the delay argument combined with a random number between start
    and stop dividied by 1000.
    """
    return delay + (random.randint(int(start), int(stop)) / 1000)

def create_msg(msg, status):
    return {"msg": msg, "status": status}