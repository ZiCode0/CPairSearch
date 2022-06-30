import time

from binance import Client
from pythonpancakes import PancakeSwapAPI
from lib.crypto import names
from lib import pair_table as pt
from lib import bestchange_custom as bc

coin = names.CryptoNames()


class Broker:
    def __init__(self):
        self.get_only = True
        self.broker_name = '_empty_'

    def get_pairs(self):
        print(f'[*] {self.broker_name}: get pairs started..')

    def buy_pair(self, name, amount):
        if self.get_only:
            print('[*] Broker mode: read_only')

    def sell_pair(self, name, amount):
        if self.get_only:
            print('[*] Broker mode: read_only')


class BinanceBroker(Broker):
    def __init__(self, api_key, api_secret):
        super(BinanceBroker, self).__init__()
        self.broker_name = 'Binance'
        self.client = Client(api_key, api_secret)
        self.fees = {}
        # print()
        # self.fees = self.client.get_asset_details()

    def _get_fees_details(self, crypto_pairs):
        assets = self.client.get_asset_details()
        for key in assets:
            for pair in crypto_pairs:
                pair_1, pair_2 = coin.get_coin_names_by_pair_name(pair_name=pair)
                if (pair_1 == key) and (pair_2 in coin.stable_coin_names):
                    assets[key]['withdrawFee'] = float(assets[key]['withdrawFee'])
                    # and (pair_1 not in coin.stable_coin_names)
                    assets[key]['withdrawFeeUSD'] = crypto_pairs[pair]['price'] * assets[key]['withdrawFee']
        return assets

    def _get_extra_pairs(self, pair_table):
        """
        Get new extra pair based on stablecoin pairs
        Example: ETH/BUSD and BTC/BUSD => ETH/BTC
        :return:
        """
        pair_with_stable = []
        new_pairs = {}
        # find pairs with stable coins
        for pair in pair_table.pairs:
            # split coi name by parts
            pair_first, pair_second = coin.get_coin_names_by_pair_name(pair_name=pair)
            # find with stable as seconds ticker: BTC/USDT
            if pair_second in coin.stable_coin_names:
                pair_with_stable.append([pair_first, pair_second])
        # parse stable coin based pairs and make new pairs
        for pair_1, stable_1 in pair_with_stable:
            for pair_2, stable_2 in pair_with_stable:
                # skip the same ticker to ticker: ETH/ETH
                if pair_1 == pair_2:
                    continue
                # if new unique pair found
                if pair_1 + pair_2 not in pair_table.pairs:
                    price = pair_table.pairs[pair_1 + stable_1]['price'] / pair_table.pairs[pair_2 + stable_2]['price']
                    new_pairs[pair_1 + pair_2] = pt.PairTable.set_pair_object(broker=self.broker_name,
                                                                              from_ticker=pair_1,
                                                                              to_ticker=pair_2,
                                                                              price=price)
        pair_table.pairs.update(new_pairs)
        return pair_table

    @staticmethod
    def _get_pair_link(pair_ticker: str):
        pair_one, pair_two = coin.get_coin_names_by_pair_name(pair_ticker)
        return f'https://www.binance.com/ru/trade/{pair_one}_{pair_two}'

    def get_pairs(self):
        super(BinanceBroker, self).get_pairs()

        result = self.client.get_all_tickers()
        result_dict = {}
        for pair in result:
            pair_from, pair_to = coin.get_coin_names_by_pair_name(pair['symbol'])
            # if pair exist
            if pair_from and pair_to:
                result_dict[pair['symbol']] = pt.PairTable.set_pair_object(broker=self.broker_name,
                                                                           from_ticker=pair_from,
                                                                           to_ticker=pair_to,
                                                                           price=pair['price'],
                                                                           exchange_link=self._get_pair_link(
                                                                               pair['symbol'])
                                                                           )
        # self.fees = self._get_fees_details(result_dict)

        pair_table = pt.PairTable(pairs_data=result_dict)
        # self.rates = pair_table
        # make extra pairs
        pair_table = self._get_extra_pairs(pair_table=pair_table)
        return pair_table


class PancakeSwapBroker(Broker):
    def __init__(self):
        super(PancakeSwapBroker, self).__init__()
        self.broker_name = 'PancakeSwap'
        self.client = PancakeSwapAPI()
        self.base_coin = 'BUSD'

    def get_pairs(self):
        super(PancakeSwapBroker, self).get_pairs()

        request_dict = self.client.tokens()['data']
        result_dict = {}
        for contract_name, pair_dict in request_dict.items():
            ticker_full_name = pair_dict['symbol'] + self.base_coin
            result_dict[ticker_full_name] = pt.PairTable.set_pair_object(broker=self.broker_name,
                                                                         from_ticker=pair_dict['symbol'],
                                                                         to_ticker=self.base_coin,
                                                                         # price=pair_dict['price'],
                                                                         **pair_dict)
            result_dict[ticker_full_name]['contract'] = contract_name
        # make result pair table instance
        pair_table = pt.PairTable(pairs_data=result_dict)
        # self.rates = pair_table
        return pair_table


class BestChangeBroker(Broker):
    def __init__(self):
        super(BestChangeBroker, self).__init__()
        self.broker_name = 'BestChange'
        self.exchange = None
        self.currency = None
        self.city = None

    def _get_currency_ticker(self, cur_id, check_is_crypto=False):
        name = self.currency[cur_id]['name']
        s = name[name.find('(') + 1:name.find(')')]
        # if no parentheses was not found
        if s == name[:-1]:
            # return normal name
            if check_is_crypto:
                return name, False
            else:
                return name
        # return ticker name
        if check_is_crypto:
            return s, True
        else:
            return s

    def _get_exchange_name(self, exchange_id):
        return self.exchange[exchange_id]['name']

    @staticmethod
    def _get_redirect_url(exchange_id):
        return f'https://www.bestchange.ru/click.php?id={exchange_id}'

    def _get_crypto_pairs(self, rates):
        result_buffer = {}
        for rate_record in rates:
            # get pair details
            from_ticker, from_crypto = self._get_currency_ticker(cur_id=rate_record['get_id'],
                                                                 check_is_crypto=True)
            to_ticker, to_crypto = self._get_currency_ticker(cur_id=rate_record['give_id'],
                                                             check_is_crypto=True)
            # if crypto pair found
            if from_crypto and to_crypto:
                pair_ticker = from_ticker + to_ticker
                # init empty buffer
                if pair_ticker not in result_buffer:
                    result_buffer[pair_ticker] = []
                # add rate
                # # set price key
                price = rate_record['rate']
                # # make record copy
                rec_copy = rate_record.copy()
                # # delete unnecessary information
                del rec_copy['give_id'], rec_copy['get_id'], rec_copy['rate'], rec_copy['city_id']
                # new pair record
                new_record = pt.PairTable.set_pair_object(broker=self.broker_name,
                                                          from_ticker=from_ticker,
                                                          to_ticker=to_ticker,
                                                          price=price,
                                                          **rate_record)
                del rec_copy

                # add extra fields to dict
                new_record['exchange_name'] = self._get_exchange_name(exchange_id=new_record['exchange_id'])
                new_record['exchange_link'] = self._get_redirect_url(exchange_id=new_record['exchange_id'])
                # # add to buffer
                result_buffer[pair_ticker].append(new_record)
        return result_buffer

    def get_pairs(self):
        super(BestChangeBroker, self).get_pairs()
        self.exchange, self.currency, self.city, _rates = bc.best_change_get(targets=['exchangers',
                                                                                      'currencies',
                                                                                      'cities',
                                                                                      'rates'])
        # get crypto pair from array
        crypto_rates = self._get_crypto_pairs(_rates)
        del _rates
        # make result pair table instance
        result_dict = pt.PairTable(pairs_data=crypto_rates)
        return result_dict

    def get_pair(self):
        pass


if __name__ == '__main__':
    while True:
        from lib import bestchange_custom as bc

        bx = BestChangeBroker()
        prs = bx.get_pairs()
        time.sleep(1)
