import json
import time
import socket
from connection import all_tickets, book
import sqlite3

test = True
gap = 0.001

def init():
    for i in all_tickets:
        conn = sqlite3.connect(i+'.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE books
                  (buy_book, sell_book)''')
        conn.commit()
        conn.close()

class SOCKET_NAME:
    BOOK = 'book'


team_name = 'pikachu'
exchange_hostname = 'test-exch-' + 'production'
port = 25000

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write('\n')

def read_from_exchange(exchange):
    return json.loads(exchange.readline())

def save(db, data):
    if not isinstance(data, str):
        data = json.dumps(data)
    c = db.cursor()
    c.execute("INSERT INTO books VALUES {}".format(str(data)))
    db.commit()

if __name__ == '__main__':
    if test:
        exchange = connect()
        write_to_exchange(exchange, {
            'type':'hello',
            'team': team_name.upper()
        })
        hello_from_exchange = read_from_exchange(exchange)
    else:
        dbs = {
        }
        for i in all_tickets:
            dbs[i] = sqlite3.connect(i+'.db')
        while True:
            time.sleep(gap)
            for i in all_tickets:
                write_to_exchange(execute, {
                    'type':SOCKET_NAME.BOOK,
                    'ticket':i,
                    'team':team_name.upper()
                })
                data = read_from_exchange(exchange)
                save(dbs[i], data)

