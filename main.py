import flask
import requests.exceptions
from flask_cors import cross_origin
from flask import Flask, request

import threading
import time

from lib import config
from lib import broker
from lib import db

app = Flask('Crypto')
ldb = db.LocalDb()
conf = config.EnvConfig()
parsing_in_process = False
parsing_works = False
sleep_timer = 30  # sleep time in seconds
http_port = 5000

# filter conditions
max_difference_in_percent = 30
min_difference_in_percent = 4


def threaded(f, daemon=False):
    import queue

    def wrapped_f(q, *args, **kwargs):
        """this function calls the decorated function and puts the
        result in a queue"""
        ret = f(*args, **kwargs)
        q.put(ret)

    def wrap(*args, **kwargs):
        """this is the function returned from the decorator. It fires off
        wrapped_f in a new thread and returns the thread object with
        the result queue attached"""

        q = queue.Queue()

        t = threading.Thread(target=wrapped_f, args=(q,) + args, kwargs=kwargs)
        t.daemon = daemon
        t.start()
        t.result_queue = q
        return t

    return wrap


@threaded
def start_function(fn):
    return fn()


def make_record_idx(record):
    """
    Make record string-based index names
    :param record:
    :return:
    """
    # BestChange FIRST
    if record['from_object']['broker'] == 'BestChange':
        parts = [record['pair'],
                 record['from_object']['broker'],
                 record['from_object']['exchange_name'],
                 record['to_object']['broker']]
    # BestChange SECOND
    elif record['to_object']['broker'] == 'BestChange':
        parts = [record['pair'],
                 record['from_object']['broker'],
                 record['to_object']['broker'],
                 record['to_object']['exchange_name']]
    # OTHER
    else:
        parts = [record['pair'],
                 record['from_object']['broker'],
                 record['to_object']['broker']]
    # JOIN STRING
    return '-'.join(parts)


var = {'base_stable_coin': 'BUSD',
       'to_exclude': [],
       'brokers': {i.broker_name: i for i in
                   [broker.BinanceBroker(api_key=conf.get('BINANCE_KEY'),
                                         api_secret=conf.get('BINANCE_SECRET')),
                    broker.PancakeSwapBroker(),
                    broker.BestChangeBroker()
                    ]
                   },
       'pairs': {},
       'diff': [],
       'pair_info': {}
       }


def record_conditions_passed(record, record_id):
    # range of percentage MAX >= x >= MIN
    if max_difference_in_percent >= record['diff_percentage'] >= min_difference_in_percent:
        # if id_name not in exclude
        if record_id not in var['to_exclude']:
            return True
    # if conditions was not passed
    return False


def export_results(data, method='console', export_count=30):
    if method == 'console':
        import pandas as pd
        df = pd.DataFrame(data=data)
        export_part = df.head(export_count)
        export_part.style.format("{:.1f}").hide_columns(["index"])
        export_part.style.set_properties(**{'text-align': 'center'})
        print(export_part)


def parser():
    global parsing_in_process, parsing_works
    parsing_works = True
    while parsing_works:
        parsing_in_process = True

        def body():
            # del diff_array, diff_record, var['diff'], var['pairs'], var['pair_info'], \
            #     x_broker_pairs, x_broker_name, y_broker_pairs, y_broker_name

            # init
            # brokers =
            try:
                var['brokers'] = {i.broker_name: i for i in
                                  [broker.BinanceBroker(api_key=conf.get('BINANCE_KEY'),
                                                        api_secret=conf.get('BINANCE_SECRET')),
                                   broker.PancakeSwapBroker(),
                                   broker.BestChangeBroker()
                                   ]
                                  }
            except requests.exceptions.ConnectionError:
                return 0
            # del brokers

            # empty temp var
            var['pairs'] = {}  # pairs
            var['diff_new'] = []  # temp buffer difference table
            var['pair_info_new'] = {}  # additional pair information
            # load pairs for each broker using ASYNC
            _buff_broker_pairs = {val.broker_name: start_function(val.get_pairs) for _, val in var['brokers'].items()}
            var['pairs'] = {key: _buff_broker_pairs[key].result_queue.get()
                            for key in _buff_broker_pairs}
            del _buff_broker_pairs
            # load pairs for each broker using SYNC
            # var['pairs'] = {key.broker_name: key.get_pairs() for key in brokers}

            # get count of pairs
            # var_range = len(var['pairs'])

            # parse brokers
            for x_broker_name, x_broker_pairs in var['pairs'].items():
                for y_broker_name, y_broker_pairs in var['pairs'].items():
                    # if not the same broker
                    if x_broker_name != y_broker_name:
                        # calc difference table
                        diff_array = x_broker_pairs - y_broker_pairs
                        # if not empty
                        if diff_array:
                            # buffer part code dict id name
                            # id_name = f'{x_broker_name}-{y_broker_name}-{pair}'
                            # calc and add buffer part
                            for diff_record in diff_array:
                                # make idx name
                                id_name = make_record_idx(record=diff_record)
                                # exclude condition function
                                if not record_conditions_passed(record=diff_record, record_id=id_name):
                                    continue

                                # obj_from = diff_record.pop('from_object')
                                # obj_to = diff_record.pop('to_object')
                                obj_from = diff_record['from_object']
                                obj_to = diff_record['to_object']
                                var['pair_info_new'][id_name] = {'from': obj_from, 'to': obj_to}
                                var['diff_new'].append(
                                    {'index': id_name,
                                     'from_ex': x_broker_name, 'to_ex': y_broker_name, **diff_record})
                                # var['diff'][f] =  [{'from_ex': x_broker_name, 'to_ex': y_broker_name, **i}
                                # for i in diff_array]
            var['diff'] = var['diff_new']
            var['pair_info'] = var['pair_info_new']
            del var['diff_new'], var['pair_info_new']
        body()

        # del var['brokers']
        parsing_in_process = False
        # export_results(data=var['diff'], method='console', export_count=30)

        print(f'Sleep {sleep_timer} sec..')
        time.sleep(sleep_timer)
    print('Parser stopped..')


@app.route('/api/get/table', methods=['GET'])
@cross_origin()
def get_diff_table():
    """
    Get difference with http request
    :return: difference table result
    """
    response = flask.jsonify([])
    if var['diff']:
        try:
            # take part as page if needed arguments
            if ('page_size' in request.args) and ('page_number' in request.args):
                page_start_index = (int(request.args['page_number']) - 1) * int(request.args['page_size'])
                page_stop_index = page_start_index + int(request.args['page_size'])
                response = flask.jsonify(var['diff'][page_start_index:page_stop_index])
            # take all objects
            else:
                response = flask.jsonify(var['diff'])
        except:
            pass
    return response


@app.route('/api/set/exclude/<target>', methods=['POST'])
@cross_origin()
def exclude_exchange_or_pair_record(target):
    try:
        response = {'code': 404}

        # exclude broker+exchange
        if target == 'exchange':
            if request.args['id']:
                exchange_parts = request.args['id'].split('-')
                # check if exchange base of id(first part) exist
                if exchange_parts[0] in var['brokers'].keys():
                    # save rule record
                    if ldb.exclude_add(target_rule=request.args['id']):
                        response = {'code': 200}

        # exclude pair
        elif target == 'pair':
            if request.args['id']:
                pass

        return flask.jsonify(response)

    except Exception as ex:
        response = {'code': 500, 'error': str(ex)}
        flask.jsonify(response)


# @app.route('/api/get/info/<index>', methods=['GET'])
# @cross_origin()
# def get_additional_info(index):
#     """
#     Thread push server router
#     :return: push server result
#     """
#
#     def make_clickable(val):
#         # target _blank to open new window
#         return '<a target="_blank" href="{}">{}</a>'.format(val, val)
#
#     try:
#
#         data = var['pair_info'][index]
#         return flask.jsonify(data)
#     except Exception as ex:
#         response = {'error': f'{ex.__class__.__name__}: {str(ex)}'}
#         print(str(ex))
#         return flask.jsonify(response)
#     # return auth_answer


if __name__ == '__main__':
    # parser()
    parser_thread = threading.Thread(target=parser, )
    parser_thread.start()

    # start web transport server
    app.run('127.0.0.1', http_port)
