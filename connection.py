import socket
import src.tradeBot.bot as bot





fake_book = {
    'a':{
        'stock':(
            [(12,1),(11,1),(10,1),(9,1),(8,1)],
            [(13,1),(14,1),(15,1),(16,1),(17,1)],
        )
    },
    'b':{
        'stock':(
            [(12,2),(11,2),(10,2),(9,2),(8,2)],
            [(13,2),(14,2),(15,2),(16,2),(17,2)],
        )
    }
}
fake_stock = {
    'a':100,
    'b':200,
}

def book(ticket):
    # TODO
    return fake_book[ticket]

def get_buy_book(ticket):
    # NOTE: make sure the but/sell price order
    # TODO
    return book(ticket)['stock'][0]

def get_sell_book(ticket):
    # TODO
    return book(ticket)['stock'][1]

def get_position(ticket):
    return fake_stock[ticket]

def buy(ticket, stock):
    # TODO
    pass

def sell(ticket, stock):
    # TODO
    pass

