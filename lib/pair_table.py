class Difference:
    pass


class PairTable:
    """
    Table table buffer of broker parsing rates
    """

    def __init__(self, pairs_data):
        self.pairs = pairs_data

    def __call__(self):
        return self.pairs

    def __get__(self, instance, owner):
        return self.pairs

    def __set__(self, instance, value):
        try:
            assert type(value) == dict
            self.pairs = float(value)
        except AssertionError:
            self._type_exception()

    def __sub__(self, other):
        try:
            assert type(self) == type(other)
        except AssertionError:
            self._type_exception()
        # operation result list
        result_list = []
        # make operation
        for pair_name in self.pairs:
            # the same pair was found
            if (pair_name in self.pairs) and (pair_name in other.pairs):
                pair_values = self.set_difference_object(pair_one=self.pairs[pair_name],
                                                         pair_two=other.pairs[pair_name])

                # for p in pair_values:
                #     if (p['diff_percentage'] >= 80) or (p['diff_percentage'] <= -80):
                #         pass
                #         # print()

                for pair in pair_values:
                    pair['pair'] = pair_name
                # input()
                # print()
                result_list += pair_values
        return result_list

    @staticmethod
    def set_difference_object(pair_one, pair_two, percentage_digits=2):
        result_dict = []
        # make list
        if type(pair_one) != list:
            pair_one = [pair_one]
        if type(pair_two) != list:
            pair_two = [pair_two]
        # parse all vars
        for p1 in pair_one:
            for p2 in pair_two:
                # calc and invert difference value
                diff = (p1['price'] - p2['price']) * -1
                # example: percentage increase from 30 to 35
                # (list price - actual price) / list price) * 100%
                diff_percentage = round(diff / p1['price'] * 100, percentage_digits)
                # set different broker name for some reason
                # p1_broker_name, p2_broker_name = p1['broker'], p2['broker']
                # # # BestChange broker to full name
                # if p1_broker_name == 'BestChange':
                #     p1_broker_name = f"{p1['broker']}-{p1['exchange_name']}"
                # make result dict
                result_dict.append({'from_price': p1['price'],
                                    'to_price': p2['price'],
                                    'diff': diff,
                                    'diff_percentage': round(diff_percentage, 2),
                                    'from_object': p1,
                                    'to_object': p2,
                                    })
        # if len(result_dict) == 1:
        #     return result_dict[0]
        # return multiple dict objects
        return result_dict

    @staticmethod
    def set_pair_object(broker, from_ticker, to_ticker, price, **kwargs):
        return {'broker': broker, 'from_ticker': from_ticker, 'to_ticker': to_ticker, 'price': float(price), **kwargs}

    @staticmethod
    def _type_exception():
        TypeError('Not the same type of objects to operate')
