import getpass
import sys
import os
import json
import time

dir_path = '/Users/' + getpass.getuser() + '/Documents/Craft-Crypto/TradeEngine/'


def resource_path():
    '''Returns path containing content - either locally or in pyinstaller tmp file'''
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS)

    return os.path.join(os.path.abspath(".."))


def delete_store(kind):
    store_path = dir_path + kind + '.json'
    os.remove(store_path)


def get_store(kind):
    store_path = dir_path + kind + '.json'

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    if not os.path.exists(store_path):
        blank = {}
        with open(store_path, 'w') as jsonFile:
            json.dump(blank, jsonFile)

    try:
        with open(store_path, 'r') as f:
            store = json.load(f)

        return store
    except Exception as e:
        print('Error in Opening', kind, '. Archiving and creating fresh copy.')
        archive_store(kind)
        try:
            blank = {}
            with open(store_path, 'w') as jsonFile:
                json.dump(blank, jsonFile)
            with open(store_path, 'r') as f:
                store = json.load(f)
            return store
        except Exception as e:
            print('another error', e)
            return False


def save_store(kind, data):
    store_path = dir_path + kind + '.json'

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    try:
        with open(store_path, 'w') as f:
            json.dump(data, f)

    except Exception as e:
        print('Error in Saving', kind, '. Archiving and creating fresh copy.')
        archive_store(kind)
        try:
            with open(store_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print('another save error', e)
            return False


def archive_store(kind):
    store_path = dir_path + kind + '.json'
    a_store_path = dir_path + '/Archive/' + kind + '_' + time.strftime('%I%M%S%p_%m%d%y') + '.json'
    a_dir_path = dir_path + '/Archive/'

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    if not os.path.exists(a_dir_path):
        os.makedirs(a_dir_path)

    if os.path.exists(store_path):
        os.replace(store_path, a_store_path)


def file_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")
    return os.path.join(base_path, relative_path)


def is_float(stng):
    try:
        stng = str(stng).strip('x')
        stng = stng.replace('/', '')
        float(stng)
        if float(stng) == 0:
            return False
        return True
    except:
        return False


def copy_prec(x, y, *args):
    x = f'{float(x):.20f}'
    y = str(y)
    if not '.' in y:
        return x.split('.')[0]

    if '.' in x and '.' in y:
        num_y = len(y) - y.index('.') - 1
        num_x = len(x) - x.index('.') - 1
        if args:
            num_y += args[0]
        if num_x < num_y:
            return x
        else:
            int_dec = x.split('.')
            x = int_dec[0] + '.' + int_dec[1][:num_y]
            return x.rstrip('0')


def sym_to_cp(symbol):
    if '/' in symbol:
        return symbol.split('/')[0], symbol.split('/')[1]

    if 'USDT' in symbol:
        return symbol.split('USDT')[0], 'USDT'

    if 'USD' in symbol:
        return symbol.split('USD')[0], 'USD'

    if 'EUR' in symbol:
        return symbol.split('EUR')[0], 'EUR'

    return symbol[0:-3], 'USD'


if __name__ == '__main__':
    pass

