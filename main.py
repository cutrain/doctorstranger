import os
import json
import time
from flask import Flask, request
from collections import defaultdict

import src.tradeBot.bot as bot

debug = True

team_name = 'Doctor Strange'.upper()
host = 'localhost'
port = 8121

trade = bot.TradeBot(team_name)

process_manager = defaultdict(lambda:{
    'pid':0,
    'name':'none',
    'status':'none',
})

app = Flask(__name__)

def check_pid(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


@app.route('/new_strategy', methods=['POST'])
def new_strategy():
    pid = int(request.form.get('pid', 0))
    name = request.form.get('name', 'unknown')
    note = request.form.get('note', 'None')
    if pid == 0:
        print('pid is 0, there some wrong')
        return {
            'status':'fail',
        }
    cnt = 0
    while True:
        sid = name + str(cnt)
        if sid not in process_manager:
            break
        cnt += 1
    process_manager[sid] = {
        'pid':pid,
        'name':name,
        'status':'alive',
    }
    return {
        'status':'ok',
        'sid':sid,
    }

@app.route('/isalive', methods=['POST'])
def is_alive():
    sid = request.form.get('sid', '0')
    if sid == '0' and sid not in process_manager:
        print('alive: get sid 0')
        return {
            'status':'{} not found'.format(sid),
        }
    p_status = process_manager[sid]
    status = p_status['status']
    if status == 'stop_but_still_running' and not check_pid(p_status['pid']):
        p_status['status'] = 'stop'
    elif status != 'alive' and check_pid(p_status['pid']):
        p_status['status'] = 'stop_but_still_running'
    elif status == 'alive' and not check_pid(p_status['pid']):
        p_status['status'] = 'stoped_by_error'

    return {
        'status': p_status['status'],
    }

@app.route('/stop', methods=['POST'])
def stop():
    sid = request.form.get('sid', '0')

    if sid == 'all':
        for key, val in process_manager.items():
            val['status'] = 'stop'
        return {
            'status':'ok',
            'info':'stop all',
        }

    if sid == '0' and sid not in process_manager:
        print('stop: get sid 0')
        return {
            'status':'not found',
        }
    process_manager[sid]['status'] = 'stop'
    return {
        'status':'ok',
    }

@app.route('/list', methods=['POST'])
def list_strategy():
    ret = 'List all process:\n'
    keys = process_manager.keys()
    for key in keys:
        val = process_manager[key]
        if val['status'] == 'stop_but_still_running' and not check_pid(val['pid']):
            val['status'] = 'stop'
        elif val['status'] != 'alive' and check_pid(val['pid']):
            val['status'] = 'stop_but_still_running'
        elif val['status'] == 'alive' and not check_pid(val['pid']):
            val['status'] = 'stoped_by_error'
        ret += 'sid:{} pid:{} name:{} status:{}\n'.format(
            key, val['pid'], val['name'], val['status'])
    print(ret)
    print('-'*100)
    return {
        'info':ret,
    }

@app.route('/clean', methods=['POST'])
def clean():
    ret = 'Clean stoped process:\n'
    pop_keys = []
    for key,val in process_manager.items():
        if val['status'] is not 'alive':
            pop_keys.append(key)
            ret += 'sid:{} remove from list\n'.format(key)
    for key in pop_keys:
        process_manager.pop(key, None)
    print(ret)
    return {
        'info':ret,
    }

@app.route('/buy', methods=['POST'])
def buy():
    ticket = request.form.get('ticket', None)
    price = request.form.get('price', None)
    size = request.form.get('size', None)
    # TODO
    return {
        'status':'ok',
    }

@app.route('/sell', methods=['POST'])
def sell():
    ticket = request.form.get('ticket')
    stock = request.form.get('stock')
    # TODO
    return {
        'status':'ok',
    }

@app.route('/get_books', methods=['POST'])
def get_books():
    ticket = request.form.get('ticket', 'none')
    if ticket != 'none':
        return trade.get_newest_books()[ticket]
    return trade.get_newest_books()

@app.route('/get_positions', methods=['POST'])
def get_positions():
    ticket = request.form.get('ticket', 'none')
    if ticket != 'none':
        return trade.get_positions()[ticket]
    return trade.get_positions()


if __name__ == '__main__':
    app.run(host=host, port=port, debug=debug)



