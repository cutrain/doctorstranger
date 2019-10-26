import json
import os
import pandas as pd


def get_books(path):
    books = []
    with open(path) as f:
        lines = [x.strip() for x in f.readlines() if len(x.strip()) > 0]
        for line in lines:
            book = json.loads(line)

            buys, sells, timestamp = book['buys'], book['sells'], book['timestamp']
            buy0 = buys[0] if len(buys) > 0 else [None, None]
            buy1 = buys[1] if len(buys) > 1 else [None, None]
            sell0 = sells[0] if len(sells) > 0 else [None, None]
            sell1 = sells[1] if len(sells) > 1 else [None, None]
            overwrite = len(books) > 0 and books[-1][4] == timestamp
            if overwrite:
                books[-1] = (buy0, buy1, sell0, sell1, timestamp)
            else:
                books.append((buy0, buy1, sell0, sell1, timestamp))
    return books


def get_trades(path):
    trades = []
    with open(path) as f:
        lines = [x.strip() for x in f.readlines() if len(x.strip()) > 0]
        for line in lines:
            (price, size, timestamp) = json.loads(line)
            fill = len(trades) > 0 and trades[-1][2] == timestamp
            if fill:
                trades[-1][0] += price * size
                trades[-1][1] += size
            else:
                trades.append([price * size, size, timestamp])
    return [(total // total_size, total_size, timestamp) for (total, total_size, timestamp) in trades]


def main():
    history_directory = "/home/ubuntu/doctorstranger/histories"
    available_date_ids = {1, 2, 3, 4, 5}
    securities = {
        "BOND",
        "BDU",
        "ALI",
        "TCT",
        "CAR",
        "BAT",
        "CHE",
    }
    for d in available_date_ids:
        for s in securities:
            books = get_books(os.path.join(history_directory, str(d), f'{s}_books.list'))
            trades = get_trades(os.path.join(history_directory, str(d), f'{s}_trades.list'))

            lines = []
            ptr = 0
            for (buy0, buy1, sell0, sell1, timestamp) in books:
                use_last = True
                while ptr < len(trades):
                    if trades[ptr][2] == timestamp:
                        lines.append([*buy0, *buy1, *sell0, *sell1, timestamp, ptr])
                        use_last = False
                        break
                    elif trades[ptr][2] < timestamp:
                        ptr += 1
                        continue
                    else:
                        lines.append([*buy0, *buy1, *sell0, *sell1, timestamp, ptr - 1 if ptr - 1 >= 0 else ptr])
                        use_last = False
                        break
                if use_last:
                    lines.append([*buy0, *buy1, *sell0, *sell1, timestamp, len(trades) - 1])
                avg_price, size, _ = trades[lines[-1][-1]]
                lines[-1].append(avg_price)
                lines[-1].append(size)
            df = pd.DataFrame(lines, columns=[
                'buy1_price',
                'buy1_size',
                'buy2_price',
                'buy2_size',
                'sell1_price',
                'sell1_size',
                'sell2_price',
                'sell2_size',
                'timestamp',
                'idx',
                'avg_price',
                'size'
            ])
            df.to_csv(os.path.join(history_directory, 'results', f'{d}_{s}.csv'))


if __name__ == '__main__':
    main()
