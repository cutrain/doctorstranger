import time
from utils import Strategy, buy, sell,get_books, get_trades
from src.security.securityManager import SecurityManager as sm

tic = sm.securities[0]

class SimpleStrategy(Strategy):
    def strategy(self, ticket):
        import random
        a = random.randint(1,2)
        b = random.randint(1,5)
        print(get_trades())
        time.sleep(5)
        # print(get_books())
        # import time
        # time.sleep(5)
        if a == 1:
            buy(ticket, 1000-b, 1)
        else:
            sell(ticket, 1000+b, 1)


a = SimpleStrategy('strategy1', 'random buy and sell')
a('BOND')


