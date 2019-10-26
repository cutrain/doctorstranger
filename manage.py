#!/usr/bin/env python
import os
import sys
import json
import argparse
import requests

url = 'http://localhost:8121'

def newp():
    global sid
    param = {
        'pid':10,
        'name':'etc',
    }
    r = requests.post(url + '/new_strategy', data=param)
    print('make process')
    print(r.text)
    sid = json.loads(r.text)['sid']
    return sid

def lis():
    r = requests.post(url + '/list')
    info = json.loads(r.text)
    print(info['info'])

def isalive(sid):
    param = {
        'sid':sid,
    }
    r = requests.post(url + '/isalive', data=param)
    print('check alive, sid:{}'.format(sid))
    print(r.text)

def stop(sid):
    param = {
        'sid':sid,
    }
    r = requests.post(url + '/stop', data=param)
    print('stop process ,sid:{}'.format(sid))
    print(r.text)

def clean():
    r = requests.post(url + '/clean')
    info = json.loads(r.text)
    print(info['info'])

def test():
    print('1')
    sid = newp()
    print('2')
    lis()
    print('3')
    isalive(sid)
    print('4')
    lis()
    print('5')
    stop(sid)
    print('6')
    isalive(sid)
    print('7')
    lis()
    print('8')
    isalive(sid)
    print('9')
    clean()
    print('10')
    lis()
    print('11')

def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', type=str, choices=['start', 'stop', 'isalive', 'list', 'clean', 'test'])
    parser.add_argument('sid_or_filename', type=str, nargs='*')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_cli()
    op = args.operation
    sid_or_filename = args.sid_or_filename
    print(op, sid_or_filename)
    if op == 'start':
        for filename in sid_or_filename:
            if '.py' in filename:
                os.system('nohup python {} & echo $!'.format(filename))
            else:
                print('should start a python file, got:{}'.format(filename))
    elif op == 'stop':
        for sid in sid_or_filename:
            stop(sid)
    elif op == 'isalive':
        for sid in sid_or_filename:
            isalive(sid)
    elif op == 'list':
        lis()
    elif op == 'clean':
        clean()
    elif op == 'test':
        test()
    else:
        raise NotImplementedError



