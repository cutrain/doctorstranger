# Jane Street ETC

*utils.py* : Strategy Class

*connection.py* : TCP sockets, tradebot

*main.py* : process manage, market interface

*cache.py* : save competition data

#### start
run as a process manage backend
```bash
python main.py
```

#### run a strategy
```bash
./manage.py start strategy.py
```

#### list a process
```
./manage.py list
```

#### stop a strategy
```bash
./manage.py stop <strategy_id>
```

