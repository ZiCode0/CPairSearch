import json
import requests

data_url = 'https://raw.githubusercontent.com/crypti/cryptocurrencies/master/cryptocurrencies.json'


class CryptoNames:
    def __init__(self):
        self.crypto_list = self.update_names()
        self.pair_name_format = '{to_ticker}{from_ticker}'
        self.stable_coin_names = ['BUSD', 'USDT', 'TUSD', 'USDC', 'UST',
                                  'DAI', 'USDP', 'USDN', 'FEI', 'HUSD',
                                  'FRAX', 'LUSD', 'TRIBE', 'USDX', 'GUSD',
                                  'SUSD', 'EURS', 'CUSD', 'RSV', 'USDK']  # define stable coin tickers

    @staticmethod
    def update_names():
        """
        Return list of known crypto names
        :return:
        """
        json_path = 'crypto.json'
        try:
            response = requests.get(data_url)
            with open(json_path, '+w') as f:
                result_dict = response.json()
                json.dump(result_dict, f)
                return list(result_dict.keys())
        except:
            with open(json_path, 'r') as f:
                result_dict = json.load(f)
                return list(result_dict.keys())

    def get_coin_names_by_pair_name(self, pair_name):
        # match buffer
        matches = []
        # go with "split at" index
        for idx in range(1, len(pair_name)):
            # set ticker buffers
            from_buffer = pair_name[idx:]
            to_buffer = pair_name[:idx]
            # check pair exist
            if (from_buffer in self.crypto_list) and (to_buffer in self.crypto_list):
                # add to match buffer
                matches.append([to_buffer, from_buffer])
        # check 1 pair found
        try:
            assert len(matches) == 1
            # return first match
            return matches[0]  # from_buffer, to_buffer
        except AssertionError:
            return None, None


if __name__ == '__main__':
    cn = CryptoNames()
    pair = cn.get_coin_names_by_pair_name('BTCLTC')
    # ss = update_names()
    print()
