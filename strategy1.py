from utils import Strategy, buy, sell

class SimpleStrategy(Strategy):
    def strategy(self, ticket):
        import random
        a = random.randint(1,2)
        if a == 1:
            buy(ticket, 1)
        else:
            sell(ticket, 1)


a = SimpleStrategy('strategy1', 'random buy and sell')
a('tic1')


