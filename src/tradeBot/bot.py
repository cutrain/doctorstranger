import logging
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
        self.registered_cancelled_callbacks: Dict[int, Callable] = {}
        # logging.basicConfig(level=logging.DEBUG,
        #                     format='%(asctime)s - %(message)s',
        #                     datefmt='%Y-%m-%d %H:%M:%S',
        #                     filename='bond.log',
        #                     filemode='a')
        self.logger = getLogger("TradeBot")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s",
                                      '%Y-%m-%d %H:%M:%S')
        file_handler = logging.FileHandler('TradeBot.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)
        self.skt: Union[None, socket.socket] = None
        self.connection = None
        self.to_write = []
        if mode == 'test':
            self.exchange_hostname = "test-exch-doctorstrange"
            self.port = 25000
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
            self.exchange: IO = self.skt.makefile("r", 1)
            self._say_hello()
        except Exception as e:
            self.logger.warning(e)
            raise e

    def _write(self, message: dict):
        self.to_write.append(f'{json.dumps(message)}\n')
        # self.exchange.write()
        # self.exchange.flush()

    def _read(self) -> Union[Dict, None]:
        data = self.exchange.readline().strip()
        try:
            if len(data) == 0:
                return None
            else:
                return json.loads(data)
        except Exception as e:
            self.logger.warning("error, check following data")
            self.logger.warning(data)
            raise e

    def _listen(self):
        Thread(target=lambda: self._listen_loop()).start()

    def _listen_loop(self):
        while True:
            for m in self.to_write:
                self.skt.send(m.encode('ascii'))
            self.to_write = []
            try:
                message = self._read()
                if message is None:
                    continue
                message_type = message['type']
                self.logger.info(f'receive {message_type}')
                if message_type == 'hello':
                    self._hello(message['symbols'])
                elif message_type == 'open':
                    self._open(message['symbols'])
                elif message_type == 'close':
                    self._close()
                elif message_type == 'error':
                    self._error(message)
                    raise Exception(message)
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
                sleep(0.01)
            except ConnectionResetError or BrokenPipeError as e:
                self.logger.warning(e)
                self.logger.warning("try to reconnect")
                self._connect()

    def _say_hello(self):
        self._write({"type": "hello", "team": self.team_name.upper()})

    def _hello(self, symbols: Dict):
        for symbol in symbols:
            self.security_manager.update_position(symbol['symbol'], symbol['position'])

    def _open(self, symbols: List):
        self.security_manager.open_trading_day(symbols)
        self.registered_filled_callbacks = {}
        self.registered_cancelled_callbacks = {}
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
        buys = [{"price": buy[0], "size": buy[1]} for buy in message['buy']]
        # sell 1 ----> sell N
        sells = [{"price": sell[0], "size": sell[1]} for sell in message['sell']]
        self.security_manager.update_book(symbol, buys, sells)

    def _trade(self, message):
        symbol = message['symbol']
        price = message['price']
        size = message['size']
        self.security_manager.add_trade(symbol, price, size)
        pass

    def _ack(self, message):
        order_id = message['order_id']
        self.logger.info(f'order ACK: {order_id}')
        self.security_manager.ack_order(order_id)

    def _reject(self, message):
        order_id, error = message['order_id'], message['error']
        self.logger.info(f'order Reject: {order_id}, reason: {error}')
        self.security_manager.reject_order(order_id, error)

    def create_buy_sell_order(self, security, price, size,
                              is_sell: bool = None,
                              is_buy: bool = None,
                              after_filled: Callable[[int, int, bool], None] = None) -> int:
        """
        :param timeout: in seconds
        :param security:
        :param price:
        :param size:
        :param is_sell:
        :param is_buy:
        :param after_filled: on_filled(size, price, completed) 当这个order被fill的时候会调用
        :return: order_id
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
        if order_id in self.registered_cancelled_callbacks:
            self.registered_cancelled_callbacks[order_id]()
        self.security_manager.out_trade(order_id)

    def get_trades(self):
        return self.security_manager.get_trades()

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

    def create_convert_order(self, security, size,
                             is_sell: bool = None,
                             is_buy: bool = None,
                             after_filled: Callable[[int, int, bool], None] = None) -> int:
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

    def cancel_order(self, order_id, after_cancelled: Callable = None):
        order_message = {"type": "cancel", "order_id": order_id}
        self._write(order_message)
        self.security_manager.cancel_order(order_id)
        if after_cancelled is not None:
            self.registered_cancelled_callbacks[order_id] = after_cancelled


if __name__ == '__main__':
    bot = TradeBot("DOCTORSTRANGE", hooks={"after_open": lambda: print("open")}, mode="test")
    while True:
        positions = bot.get_positions()
        bot.create_buy_sell_order("BOND", 999, 10, is_sell=True)
        bot.create_buy_sell_order("BOND", 1001, 10, is_buy=True)
        bot.create_convert_order("BAT", 10, is_buy=True)
        bot.create_convert_order("CHE", 2, is_buy=True)
        print('\t'.join([str(positions[sec]) for sec in SecurityManager.securities]))
        sleep(0.3)
