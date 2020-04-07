import requests,argparse,json
from datetime import datetime, timedelta
from flask import Flask, send_from_directory,redirect,request

parser = argparse.ArgumentParser(description='Web Service')

parser.add_argument('-p', '--parser-url' ,action='store', help='parser-url',type =str, default= 'parser:6969')

args = parser.parse_args()

server = Flask(__name__)

def stowages_statistics(parserd_stowages : json, statistics_by_weight = [1,2,3], statistics_by_type = ['Прикоп','Магнит','Тайник'] ):
    glob = dict()
    glob['date_from'] = datetime.strftime(datetime.now() - timedelta(hours=24), "%Y.%m.%d %H:%M:%S")
    glob['date_to'] = datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S")
    glob['locations'] = dict()
    results = glob['locations']
    for stowage in parserd_stowages:
        l = stowage.get('location')
        if not l in results:
            results[l] = dict()
            results[l]['momental_positions'] = 0
            results[l]['all_weight'] = 0
            results[l]['total_price'] = {'btc': 0, 'rub': 0}
            results[l]['shops'] = set()
            results[l]['types'] = { t : 0 for t in statistics_by_type}
            if len(statistics_by_weight) > 0:
                results[l]['avr_prices'] = dict()
                for w in statistics_by_weight:
                    results[l]['avr_prices'][w] = {'btc': 0, 'rub': 0, 'count': 0}

        stowage_weight = float(stowage.get('weight'))
        stowage_price_btc = float(stowage.get('btc'))
        stowage_price_rub = float(stowage.get('rub'))

        results[l]['momental_positions'] += 1
        results[l]['shops'].add(stowage.get('uid'))
        results[l]['total_price']['btc'] += stowage_price_btc
        results[l]['total_price']['rub'] += stowage_price_rub
        results[l]['all_weight'] += stowage_weight
        if stowage_weight in statistics_by_weight:
            results[l]['avr_prices'][stowage_weight]['btc'] += stowage_price_btc
            results[l]['avr_prices'][stowage_weight]['rub'] += stowage_price_rub
            results[l]['avr_prices'][stowage_weight]['count'] += 1

        for type_word in statistics_by_type:
            if type_word in stowage.get('types'): results[l]['types'][type_word] += 1

    for k in results.keys():
        results[k]['shops'] = len(results[k]['shops'])
        results[k]['total_price']['btc'] = round(results[k]['total_price']['btc'],9)
        results[k]['total_price']['rub'] = round(results[k]['total_price']['rub'], 2)
        for w in statistics_by_weight:
            c = results[k]['avr_prices'][w]['count']
            if c != 0:
             results[k]['avr_prices'][w] = {'rub': round (results[k]['avr_prices'][w]['rub'] / c,2), 'btc': round ( results[k]['avr_prices'][w]['btc'] / c,9)}

    return json.dumps(glob,ensure_ascii=False, default=str)


@server.route('/statistics', methods=['GET'])
def mainpage():
     return send_from_directory('.','statistics.html')

@server.route('/getcaptcha/', methods=['GET'])
def get_captcha():
     return requests.get('http://{}/getcaptcha/'.format(args.parser_url)).text

@server.route('/solve/', methods=['POST'])
def has_captcha():
     requests.post('http://{}/solvecaptcha/'.format(args.parser_url),data = {'answer': request.form.get('answer')})
     return redirect('/statistics')

@server.route('/view/<stuff>', methods=['GET'])
def view(stuff):
     return stowages_statistics( requests.get('http://{}/stowages/{}'.format(args.parser_url,stuff)).json() )

@server.route('/getcategories', methods=['GET'])
def getcategories():
     return requests.get('http://{}/{}'.format(args.parser_url,"categories/")).text

server.run(debug=False,host='0.0.0.0',port = 6969)
