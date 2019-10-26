import json
import requests as rq
url = 'http://localhost:8121'
cb_url = url + '/convert_buy'
cs_url = url + '/convert_sell'
b_url = url + '/buy'
s_url = url + '/sell'
book_url = url + '/get_books'
posi_url = url + '/get_positions'
trade_url = url + '/get_trades'


def buy(security, price, size):
    params = {
        'ticket':security,
        'price':price,
        'size':size,
    }
    r = rq.post(b_url, data=params)
    data = json.loads(r.text)
    return data

def sell(security, price, size):
    params = {
        'ticket':security,
        'price':price,
        'size':size,
    }
    r = rq.post(s_url, data=params)
    data = json.loads(r.text)
    return data

def convert_buy(security, size):
    params = {
        'ticket':security,
        'size':size,
    }
    r = rq.post(cb_buy, data=params)
    data = json.loads(r.text)
    return data

def convert_sell(security, size):
    params = {
        'ticket':security,
        'size':size,
    }
    r = rq.post(cb_sell, data=params)
    data = json.loads(r.text)
    return data

def get_books(ticket=None):
    params = {}
    if ticket is not None:
        params['ticket'] = ticket
    r = rq.post(book_url, data=params)
    print(r)
    data = json.loads(r.text)
    return data

def get_positions(ticket=None):
    params = {}
    if ticket is not None:
        params['ticket'] = ticket
    r = rq.post(posi_url, data=params)
    data = json.loads(r.text)
    return data

def get_trades():
    r = rq.post(trade_url)
    data = json.loads(r.text)
    return data
