import os
import json
import requests
from connection import buy, sell, get_buy_book, get_sell_book, get_stock

url = 'http://localhost:8121'
alive_url = url + '/isalive'
start_url = url + '/new_strategy'

class DuplicateStrategyException(Exception):
    pass

class Strategy(object):
    def __init__(self, name, note='none'):
        self.name = name
        self.alive = False
        self.sid = 'none'
        self.note = note

    def __call__(self, *args, **kwargs):
        if self.alive:
            raise DuplicateStrategyException(
                'Strategy: {} is alive, will not start another'.format(self.name)
            )

        if self.check_runable():
            self.alive = True
            r = requests.post(start_url, data={
                'pid':os.getpid(),
                'name':self.name,
                'note':self.note,
            })
            self.sid = json.loads(r.text)['sid']
            print('pid:{}'.format(os.getpid()))
            print('get sid:{}'.format(self.sid))
            self.start_strategy(*args, **kwargs)

    def check_alive(self):
        if self.alive is False:
            return False
        try:
            r = requests.post(alive_url, data={'sid':self.sid})
            data = json.loads(r.text)
            status = data['status']
            return status == 'alive'
        except Exception as e:
            print('got except', e)
            return False


    def start_strategy(self, *args, **kwargs):
        while self.check_alive():
            self.strategy(*args, **kwargs)

    def strategy(self, *args, **kwargs):
        raise NotImplementedError

    def check_runable(self):
        return True

    def start(self, *args, **kwargs):
        self(*args, **kwargs)

    def stop(self):
        self.alive = False

