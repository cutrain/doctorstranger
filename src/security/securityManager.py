import os
from datetime import datetime as dt
from typing import Dict, List, Union, NamedTuple

BookPair = NamedTuple('BookPair', [('price', int), ('size', int)])
Convertible = NamedTuple('Convertible',
                         [('from', str), ('from_size', int), ('to', List[str]), ('to_sizes', List[int]), ('fee', int)])


def timestamp_now():
    return dt.timestamp(dt.now())


class Book:
    def __init__(self, buys, sells, timestamp):
        self.buys: List[BookPair] = [BookPair(buy['price'], buy['size']) for buy in buys]
        self.sells: List[BookPair] = [BookPair(sell['price'], sell['size']) for sell in sells]
        self.timestamp = timestamp


class SecurityManager:
    BOND = "BOND"
    A = "BDU"
    B = "ALI"
    C = "TCT"
    D = "CAR"
    X = "BAT"
    Y = "CHE"
    securities = [BOND, A, B, C, D, X, Y]
    convertibles = {
        X: Convertible(X, 10, [BOND, A, B, C], [3, 2, 3, 2], 100),
        Y: Convertible(Y, 1, [D], [1], 10)
    }

    def __init__(self):
        self.available_securities = SecurityManager.securities
        self.positions = {name: 0 for name in SecurityManager.securities}
        self.historical_books: Dict[str, List[Book]] = {name: [] for name in SecurityManager.securities}
        self.book_indices: Dict[str, int] = {name: None for name in SecurityManager.securities}
        self.orders = {
            "wait": [],
            "confirmed": [],
            "filled": [],
            "rejected": [],
        }

        self.order_id = self._restore_order_id()

    def update_position(self, name, position):
        self.positions[name] = position

    def get_positions(self):
        return self.positions

    def open_trading_day(self, available_securities):
        self.available_securities = available_securities
        self.positions = {name: 0 for name in SecurityManager.securities}
        self.historical_books = {name: [] for name in SecurityManager.securities}
        self.book_indices = [None for _ in SecurityManager.securities]
        self.orders = {
            "wait": [],
            "confirmed": [],
            "filled": [],
            "rejected": [],
        }
        pass

    def close_trading_day(self):
        pass

    def update_book(self, symbol: str, buys, sells):
        self.historical_books[symbol].append(Book(buys, sells, timestamp_now()))
        if self.book_indices[symbol] is None:
            self.book_indices[symbol] = 0
        else:
            self.book_indices[symbol] = 1 + self.book_indices[symbol]
        pass

    def get_newest_books(self) -> Dict[str, Book]:
        to_return = {}
        for (idx, name) in enumerate(SecurityManager.securities):
            books = self.historical_books[name]
            newest_idx = self.book_indices[idx]
            to_return[name] = None if newest_idx is None else books[newest_idx]
        return to_return

    def next_order_id(self):
        self.order_id += 1
        self._save_order_id()
        return self.order_id

    @staticmethod
    def _restore_order_id():
        try:
            with open(os.path.join("resources", "order_id.txt")) as f:
                line = f.readline().strip()
                order_id = int(line)
                return order_id
        except:
            return 0

    def _save_order_id(self):
        with open(os.path.join("resources", "order_id.txt"), 'w') as f:
            f.write(f'{self.order_id}\n')

    def create_order(self, order_message):
        order_type = order_message['type']
        order_id = order_message['order_id']
        security = order_message['symbol']
        direction = order_message['dir']
        price = order_message['price']
        size = order_message['size']
        self.orders['wait'].append({
            "order_id": order_id,
            "type": order_type,
            "security": security,
            "direction": direction,
            "price": price,
            "size": size,
            "timestamp": timestamp_now(),
        })

    def ack_order(self, order_id):
        for (idx, order) in enumerate(self.orders['wait']):
            if order['order_id'] == order_id:
                order['fills'] = []
                self.orders['confirmed'].append(order)
                self.orders['wait'].pop(idx)
                break

    def reject_order(self, order_id, reason):
        for (idx, order) in enumerate(self.orders['wait']):
            if order['order_id'] == order_id:
                order['reason'] = reason
                self.orders['confirmed'].append(order)
                self.orders['rejected'].pop(idx)
                break

    def fill_order(self, order_id, price, size) -> bool:
        for order_set in ["confirmed", "wait"]:
            for (idx, order) in enumerate(self.orders[order_set]):
                if order['order_id'] == order_id:
                    order['fills'].append({
                        "price": price,
                        "size": size,
                        "timestamp": timestamp_now()
                    })
                    order_type = order['type']
                    direction = order['direction']
                    security = order['security']
                    if order_type == "add":
                        if direction == "SELL":
                            self.positions[security] -= size
                        elif direction == "BUY":
                            self.positions[security] += size
                        else:
                            raise Exception(f"unknown order direction {direction}")
                    elif order_type == "convert":
                        if direction == "SELL":
                            self.positions[security] -= size
                            for (sec, to_size) in zip(SecurityManager.convertibles[security].to,
                                                      SecurityManager.convertibles[security].to_sizes):
                                self.positions[sec] += size / SecurityManager.convertibles[security].from_size * to_size

                        elif direction == "BUY":
                            self.positions[security] += size
                            for (sec, to_size) in zip(SecurityManager.convertibles[security].to,
                                                      SecurityManager.convertibles[security].to_sizes):
                                self.positions[sec] -= size / SecurityManager.convertibles[security].from_size * to_size
                        else:
                            raise Exception(f"unknown order direction {direction}")
                    else:
                        raise Exception(f"unknown order type {order_type}")

                    filled = sum([x['size'] for x in order['fills']]) == order['size']
                    if filled:
                        self.orders['filled'].append(order)
                        self.orders[order_set].pop(idx)
                    else:
                        if order_set == "wait":
                            # 没经过ACK直接fill了，肯定哪里出了问题，但是没那么重要
                            self.orders['confirmed'].append(order)
                            self.orders['wait'].pop(idx)
                    return filled
        raise Exception(f"order {order_id} not found")


if __name__ == '__main__':
    bk = Book([{
        'price': 50,
        'size': 10,
    }], [{
        'price': 55,
        'size': 15,
    }], timestamp_now())
    manager = SecurityManager()
    pass
