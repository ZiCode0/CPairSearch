import sys
from io import TextIOWrapper
from zipfile import ZipFile
from urllib.request import urlretrieve
import os
import platform
import time


def best_change_get(targets: list):
    def creation_date(path_to_file):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See https://stackoverflow.com/a/39501288/1709587 for explanation.
        """
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    class Rates:
        def __init__(self):
            super().__init__()

        @staticmethod
        def get(text):
            data = []
            for row in text.splitlines():
                val = row.split(';')
                try:
                    data.append({
                        'give_id': int(val[0]),
                        'get_id': int(val[1]),
                        'exchange_id': int(val[2]),
                        'rate': float(val[3]) / float(val[4]),
                        'reserve': float(val[5]),
                        'reviews': val[6],
                        'min_sum': float(val[8]),
                        'max_sum': float(val[9]),
                        'city_id': int(val[10]),
                    })
                except ZeroDivisionError:
                    # Error rate N:0 and 0 division error
                    pass
            return data

    class Currencies:
        def __init__(self):
            super().__init__()

        @staticmethod
        def get(text):
            data = {}
            for row in text.splitlines():
                val = row.split(';')
                data[int(val[0])] = {
                    'id': int(val[0]),
                    'pos_id': int(val[1]),
                    'name': val[2],
                }
            data = dict(sorted(data.items(), key=lambda x: x[1]['name']))
            return data

    class Exchangers:
        def __init__(self):
            super().__init__()

        @staticmethod
        def get(text):
            data = {}
            for row in text.splitlines():
                val = row.split(';')
                data[int(val[0])] = {
                    'id': int(val[0]),
                    'name': val[1],
                    'wmbl': int(val[3]),
                    'reserve_sum': float(val[4]),
                }
            data = dict(sorted(data.items()))
            return data

    class Cities:
        def __init__(self):
            super().__init__()

        @staticmethod
        def get(text):
            data = {}
            for row in text.splitlines():
                val = row.split(';')
                data[int(val[0])] = {
                    'id': int(val[0]),
                    'name': val[1],
                }
            data = dict(sorted(data.items(), key=lambda x: x[1]['name']))
            return data

    __version = None
    __filename = 'info.zip'
    __url = 'http://api.bestchange.ru/info.zip'
    __enc = 'windows-1251'

    __file_currencies = 'bm_cy.dat'
    __file_exchangers = 'bm_exch.dat'
    __file_rates = 'bm_rates.dat'
    __file_cities = 'bm_cities.dat'

    _cache = False
    _cache_seconds = 15
    _cache_path = './' + __filename
    # _exchangers_reviews = exchangers_reviews
    _split_reviews = False

    # targets: rates, currencies, exchangers, cities, reviews
    targets_dict = {'rates': [__file_rates, Rates],
                    'currencies': [__file_currencies, Currencies],
                    'exchangers': [__file_exchangers, Exchangers],
                    'cities': [__file_cities, Cities],
                    }

    try:
        if os.path.isfile(_cache_path) \
                and time.time() - creation_date(_cache_path) < _cache_seconds:
            filename = _cache_path
        else:
            filename, headers = urlretrieve(__url, _cache_path if _cache else None)
    except Exception as ex:
        print(ex)
        return best_change_get(targets)
    else:
        zip_file = ZipFile(filename)

        result_buffer = []
        for target in targets:
            if target in targets_dict:
                # try to read by zip path
                zf_buffer = zip_file.open(targets_dict[target][0])
                # get zip text
                tmp_text = TextIOWrapper(zf_buffer, encoding=__enc).read()
                # init table object
                table_object = targets_dict[target][1].get(tmp_text)
                # append to result buffer
                result_buffer.append(table_object)
                del zf_buffer, tmp_text, table_object

        # free memory
        del zip_file, filename, headers
        if '_io' in sys.modules:
            del sys.modules['_io']
        if 'zipfile' in sys.modules:
            del sys.modules['zipfile']
        if 'request' in sys.modules:
            del sys.modules['request']

        if not result_buffer:
            return best_change_get(targets=targets)

        return result_buffer


if __name__ == '__main__':
    while True:
        result = best_change_get(targets=['rates', 'exchangers'])
        print()
