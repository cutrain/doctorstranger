from logging import getLogger
import socket
import json
from threading import Thread
from time import sleep
from typing import Union, IO, Dict, List, Callable

from src.security.securityManager import SecurityManager, Book


class TradeBot:
    def __init__(self, team_name, hooks: Dict[str, Callable] = None, mode="test"):
        """
        :param team_name: 队伍的名字
        :param hooks: 生命周期钩子，目前只有"after_open"这一个 {"after": Callable}
        """
        self.security_manager = SecurityManager()
        self.team_name: str = team_name
        self.hooks = {} if hooks is None else hooks
        self.registered_filled_callbacks: Dict[int, Callable[[int, int, bool], None]] = {}
        self.logger = getLogger("TradeBot")
        self.skt: Union[None, socket.socket] = None
        self.connection = None
        if mode == 'test':
            self.exchange_hostname = "test-exch-doctorstrange"
            self.port = 25002
        elif mode == 'prod':
            self.exchange_hostname = "production"
            self.port = 25000
        else:
            raise Exception(f"unknown mode {mode}")
        self._connect()
        self._listen()

    def _connect(self):
        try:
            self.skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.logger.info("try to connect to the server")
            self.skt.connect((self.exchange_hostname, self.port))
            self.exchange: IO = self.skt.makefile("rw", 1024)
            self._say_hello()
        except Exception as e:
            self.logger.warning(e)
            raise e

    def _write(self, message: dict):
        self.exchange.write(f'{json.dumps(message)}\n')
        self.exchange.flush()

    def _read(self) -> dict:
        data = self.exchange.readline()
        return json.loads(data)

    def _listen(self):
        Thread(target=lambda: self._listen_loop()).start()

    def _listen_loop(self):
        while True:
            try:
                message = self._read()
                message_type = message['type']
                if message_type == 'hello':
                    self._hello(message['symbols'])
                elif message_type == 'open':
                    self._open(message['symbols'])
                elif message_type == 'close':
                    self._close()
                elif message_type == 'error':
                    self._error(message)
                elif message_type == 'book':
                    self._book(message)
                elif message_type == 'trade':
                    self._trade(message)
                elif message_type == 'ack':
                    self._ack(message)
                elif message_type == 'reject':
                    self._reject(message)
                elif message_type == 'fill':
                    self._fill(message)
                elif message_type == 'out':
                    self._out(message)
                # 0.1s的tick会不会太慢
                sleep(0.1)
            except ConnectionResetError or BrokenPipeError as e:
                self.logger.warning(e)
                self.logger.warning("try to reconnect")
                self._connect()
            except Exception as e:
                self.logger.warning(e)

    def _say_hello(self):
        self._write({"type": "hello", "team": self.team_name.upper()})

    def _hello(self, symbols: Dict):
        for symbol in symbols:
            self.security_manager.update_position(symbol['symbol'], symbol['position'])

    def _open(self, symbols: List):
        self.security_manager.open_trading_day(symbols)
        if "after_open" in self.hooks:
            self.hooks["after_open"]()

    def _close(self):
        self.security_manager.close_trading_day()
        pass

    def _error(self, message):
        self.logger.warning(message)

    def _book(self, message):
        symbol = message['symbol']
        # buy N ----> buy 1
        buys = [{"price": buy[0], "size": buy[1]} for buy in message['buys']]
        # sell 1 ----> sell N
        sells = [{"price": sell[0], "size": sell[1]} for sell in message['sells']]
        self.security_manager.update_book(symbol, buys, sells)

    def _trade(self, message):
        # TODO
        # https://github.com/brgirardeau/etc/blob/master/tradebot.py
        # line: 129 self.other_trades.append(message)
        # line: 66 self.other_trades = [] # {"type":"trade","symbol":"SYM","price":N,"size":N}
        # 其他地方哪也没用到 似乎是记录了不属于自己的trade？
        symbol = message['symbol']
        pass

    def _ack(self, message):
        order_id = message['order_id']
        self.logger.info(f'ACK: {order_id}')
        self.security_manager.ack_order(order_id)

    def _reject(self, message):
        order_id, error = message['order_id'], message['error']
        self.logger.info(f'Reject: {order_id}, reason: {error}')
        self.security_manager.reject_order(order_id, error)

    def _fill(self, message):
        order_id = message["order_id"]
        symbol = message["symbol"]
        direction = message["dir"]
        price = message["price"]
        size = message["size"]
        completed = self.security_manager.fill_order(order_id, price, size)
        if order_id in self.registered_filled_callbacks:
            self.registered_filled_callbacks[order_id](size, price, completed)

    def _out(self, message):
        order_id = message['order_id']
        # TODO 不知道是干嘛的

    def get_positions(self) -> Dict[str, int]:
        """
        :return: returned_val[security_name] 是当前该股仓位
        """
        return self.security_manager.get_positions()

    def get_newest_books(self) -> Dict[str, Book]:
        """
        :return: returned_val[security_name] 是当前该股Book信息
        """
        return self.security_manager.get_newest_books()

    def create_buy_sell_order(self, security, price, size,
                              is_sell: bool = None,
                              is_buy: bool = None,
                              after_filled: Callable[[int, int, bool], None] = None):
        """
        :param security:
        :param price:
        :param size:
        :param is_sell:
        :param is_buy:
        :param after_filled: on_filled(size, price, completed) 当这个order被fill的时候会调用
        :return:
        """
        if is_sell is None and is_buy is None:
            raise Exception("direction not specified")
        elif is_sell is not None and is_buy is not None:
            raise Exception("cannot specify two directions")
        order_id = self.security_manager.next_order_id()
        order_message = {
            "type": "add",
            "order_id": order_id,
            "symbol": security,
            "dir": "SELL" if is_sell else "BUY",
            "price": price,
            "size": size,
        }
        self._write(order_message)
        self.security_manager.create_order(order_message)
        if after_filled is not None:
            self.registered_filled_callbacks[order_id] = after_filled
        return order_id

    def create_convert_order(self, security, size,
                             is_sell: bool = None,
                             is_buy: bool = None,
                             after_filled: Callable[[int, int, bool], None] = None):
        """
        :param security:
        :param size:
        :param is_sell:
        :param is_buy:
        :param after_filled: on_filled(size, price, completed)  当这个order被fill的时候会调用
        :return:
        """
        if is_sell is None and is_buy is None:
            raise Exception("direction not specified")
        elif is_sell is not None and is_buy is not None:
            raise Exception("cannot specify two directions")
        order_id = self.security_manager.next_order_id()
        order_message = {
            "type": "convert",
            "order_id": order_id,
            "symbol": security,
            "dir": "SELL" if is_sell else "BUY",
            "size": size,
        }
        self._write(order_message)
        self.security_manager.create_order(order_message)
        if after_filled is not None:
            self.registered_filled_callbacks[order_id] = after_filled
        return order_id


if __name__ == '__main__':
    bot = TradeBot("AAA", hooks={"after_open": lambda: print("open")})
    while True:
        positions = bot.get_positions()
        print('\t'.join([str(positions[sec]) for sec in SecurityManager.securities]))
        sleep(0.3)
