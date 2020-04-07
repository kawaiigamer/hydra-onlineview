import requests,argparse,threading,json,logging,bs4
from parser_db import PostgresDatabase
from typing import List, Tuple
from flask import Flask,request


logging.basicConfig(format='%(funcName)s ->  %(message)s')

parser = argparse.ArgumentParser(description='Parser Service')

parser.add_argument('-b','--base-url', action='store', help='base url', type =str, default= 'http://hydraruzxpnew4af.onion/')
parser.add_argument('-bu','--base-user', action='store', help='username',type =str , default= '')
parser.add_argument('-bp', '--base-password' ,action='store', help='password',type =str, default= '')
parser.add_argument('-r', '--region' ,action='store', help='region id',type =str, default= '2')
parser.add_argument('-c', '--categories' ,action='store', help='categories, ID:Description <space> - splitter',type =str, default= '85:Мефедрон-мука 92:Мефедрон-пудра 84:Мефедрон-кристалл')
parser.add_argument('-tp', '--tor-proxy' ,action='store', help='socks tor proxy',type =str, default= 'socks5h://user:pass@tor-socks-proxy:9150')
parser.add_argument('-db', '--database-con-string' ,action='store', help='database connection string',type =str, default= "postgres://postgres:postgres@postgres:5432/main")
parser.add_argument('-fp', '--flask-port' ,action='store', help='Flask port',type =int, default= 6969)

args = parser.parse_args()

class AccessContext():

    headers = {
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Accept': '*/*',
              }

    def __init__(self,base : str, proxy : str, region : str,timeout : int = 100):
        self.base = base
        self.region = region
        self.timeout = timeout
        self.s = requests.Session()
        self.s.proxies.update(dict(http=proxy, https=proxy))
        self.s.headers.update(self.headers)
        self.state = -1
        self.captcha = '0'
        self.answer = ''
        self.captcha_value = 0

    def parse_catalog_page(self,full_url : str) -> List[str]:
        raw = self.get_page(full_url)
        soup = bs4.BeautifulSoup(raw, 'lxml')
        products = soup.findAll("div", {"class": "title"})
        l = []
        for p in products:
            try:
                l.append(p.find('a').get('href'))
            except:
                pass
        if len(l) == 0: return None
        return l

    def get_all_products_from_catalog(self, category : str) -> List[str]:
        counter = 1
        links = []
        while True:
            action_lock.acquire()
            url = "{}catalog/{}?region_id={}&type=momental&page={}".format(self.base,category,self.region,counter)
            logging.warning("Results: %d Parsing %s",len(links), url)
            l = self.parse_catalog_page(url)
            action_lock.release()
            if l is None:
                break
            links.extend(l)
            counter += 1
        return links

    def parse_product_page(self,url : str) -> List[Tuple]:
        raw = self.get_page(self.base + url)
        soup = bs4.BeautifulSoup(raw, 'lxml')
        stowages = soup.findAll("li", {"class": "momental momental-region-" + self.region})
        results = []
        for stowage in stowages:
            try:
                location = stowage.find("div", {"class": "text-muted subregion"}).getText().strip()
                location_types = stowage.find("div", {"class": "av_storage"}).getText().strip()
                _ = stowage.find("div", {"class": "av_nal"}).getText().strip().split(' ')
                weight = float(_[0])
                weight_type = _[1]
                _ = stowage.find("div", {"class": "av_price"}).getText().strip().replace("\n", '').split('/')
                price_rub = int(_[0].replace(" руб ", '').replace(" ", ''))
                price_btc = float(_[1].replace(" BTC", '').replace(" ", ''))
                results.append(
                    (location, location_types, weight, weight_type, price_rub, price_btc)
                )
            except:
                pass
        return results

    def get_page(self,page : str) -> str:
        resp = self.s.get(page,timeout = self.timeout)
        if 'Вы не робот' in resp.text:
            self.captcha, self.captcha_value = self.get_b64_captcha(resp.text)
            self.state = 0
            logging.warning("First captcha required, waiting for solve")
            action_lock.acquire()
            logging.warning("Captcha solved: %s" , self.answer)
            resp2 = self.s.post(self.base + 'gate', timeout=self.timeout, data = {'captcha': self.answer, 'captchaData' : self.captcha_value, 'ret' : '/'})
            if '!-- Шапка --' in resp2.text:
                logging.warning("First captcha valid")
            else:
                logging.warning("First captcha not valid")
            return self.get_page(page)
        if 'Забыли пароль?' in resp.text:
            logging.warning("Second captcha required, waiting for solve")
            self.captcha, self.captcha_value = self.get_b64_captcha(resp.text)
            action_lock.acquire()
            self.state = 0
            logging.warning("Captcha solved: %s", self.answer)
            resp2 = self.s.post(self.base + 'login', timeout=self.timeout,
                                data={
                                       '_token': '',
                                       'login': args.base_user,
                                       'password': args.base_password,
                                       'captcha': self.answer,
                                       'captchaData' : self.captcha_value  })
            if 'Забыли пароль?' in resp2.text:
                logging.warning("Second captcha not valid")
                return self.get_page(page)
            else:
                logging.warning("Second captcha valid")
                self.state = 1
                return self.get_page(page)
        return resp.text

    def get_b64_captcha(self,raw : str) -> Tuple[str,str]:
        soup = bs4.BeautifulSoup(raw, 'lxml')
        image = soup.find("img", {"alt": "Captcha image"}).get('src')
        val = soup.find("input", {"name": "captchaData"}).get('value')
        return (image,val)


def main_dayly_task():
    catalog_categories = [ task.split(':') for task in args.categories.split(' ')]
    logging.warning("Parsing %d categories", len(catalog_categories))
    products = []
    for category_id, category_name in catalog_categories:
          products.clear()
          logging.warning("Strarting parse category -> %s", category_name)
          products = context.get_all_products_from_catalog(category_id)
          logging.warning("Products added from category %s -> %d", category_name, len(products))
          counter = 0
          for product in products:
              counter += 1
              logging.warning("Trying get (%d/%d) page -> %s", counter, len(products), product)
              try:
               stowages = context.parse_product_page(product)
               logging.warning("%d stowages found",  len(stowages))
               for stowage in stowages:
                   db.add_or_update_stowage(product,category_name,stowage[0],stowage[1],stowage[2],stowage[3],stowage[4],stowage[5])
              except Exception as e:
                    logging.warning("Error with parsing %s -> %s", product,str(e))
          logging.warning("Products parsed %d, from %s category", len(products), category_name)
    db.delete_older_then(1)


def main():
    while True:
     try:
       logging.warning("Starting main task")
       main_dayly_task()
     except Exception as e:
       logging.warning("Exception in main task -> %s",str(e))

context = AccessContext(args.base_url,args.tor_proxy,args.region)
action_lock = threading.Semaphore(1)
db = PostgresDatabase(args.database_con_string)
server = Flask(__name__)


@server.route('/stowages/<stuff>', methods=['GET'])
def json_stowages_output(stuff):
    results = []
    for stowage in db.get_all_stowages_type(stuff,10000):
        new = {}
        for s,d in zip(stowage,['uid','date','stuff','location','types','weight','weight_type','rub','btc','product_id']):
            new[d] = s
        results.append(new)
    return json.dumps(results,ensure_ascii=False, default=str)


@server.route('/getcaptcha/', methods=['GET'])
def captcha_output():
     if context.state == 0:
         return context.captcha
     else:
         return '0'


@server.route('/solvecaptcha/', methods=['POST'])
def captcha_input():
    context.answer = request.form.get('answer')
    action_lock.release()
    return "OK"


@server.route('/categories/', methods=['GET'])
def categories():
    return json.dumps(db.get_unique_stuff(),ensure_ascii=False, default=str)


threading.Thread(target=main).start()
server.run(debug=False,host='0.0.0.0',port = args.flask_port)