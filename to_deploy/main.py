import CraftCrypto_Helpers.Helpers
import pyupdater
from pyupdater.client import Client as updateClient
import traceback
from client_config import ClientConfig
from TradeEngine import TradeEngine
from CraftCrypto_Helpers.Helpers import get_store, save_store
import time
import getpass
import os
import zipfile
import distutils
import shutil
import subprocess
import sys


# Starts everything off
def check_for_update(te_name, te_version):
    up_client = updateClient(
        ClientConfig(), refresh=True, progress_hooks=[print_status_info]
    )
    my_update = up_client.update_check(te_name, te_version)
    print(my_update)
    if isinstance(my_update, pyupdater.client.updates.LibUpdate):
        print('Library Found Update.')
    elif isinstance(my_update, pyupdater.client.updates.AppUpdate):
        print('Binary Found Update.')
    else:
        print('No Update Found')
    return my_update


def print_status_info(info):
    total = info.get(u'total')
    downloaded = info.get(u'downloaded')
    status = info.get(u'status')
    per = info.get(u'percent_complete')
    try:
        print('Download ' + per + ' complete')
    except:
        pass


if __name__ == "__main__":
    te_name = 'TradeEngine'
    te_version = '0.3.0'

    try:
        print('Welcome to TradeCraft Lite v' + te_version)
        print('Checking for updates...')

        # uncomment this for automatic updates on packaged versions
        my_update = check_for_update(te_name, te_version)

        if isinstance(my_update, pyupdater.client.updates.LibUpdate):  # AppUpdate, LibUpdate
            print('Library Update Found. Download and restart?')
            msg = input('Enter \'yes\' to update:')
            if msg.strip().upper() == 'YES':
                my_update.download(background=False)
                while not my_update.is_downloaded():
                    time.sleep(.25)
                my_update.extract()
                dir = my_update.update_folder
                print(my_update.update_folder, my_update.filename)
                # opening the zip file in read mode.
                with zipfile.ZipFile(my_update.update_folder + '/' + my_update.filename, "r") as zf:
                    zf.extractall(my_update.update_folder)
                src = my_update.update_folder + '/' + my_update.app_name
                dst = os.getcwd()
                try:
                    shutil.copytree(src, dst, dirs_exist_ok=True, copy_function=shutil.copyfile)
                    shutil.rmtree(src)
                    cmd = os.getcwd() + '/TradeEngine.exe'
                    os.startfile(cmd)
                except shutil.Error:
                    shutil.rmtree(src)
                    print('Could Not Copy all Files. Checking for Binary Update')
                    app_update = check_for_update(te_name, te_version)
                    if isinstance(app_update, pyupdater.client.updates.AppUpdate):  # AppUpdate, LibUpdate
                        print('Binary Update Found. Downloading...')
                        app_update.download(background=False)
                        while not app_update.is_downloaded():
                            time.sleep(.25)
                        app_update.extract_restart()

        elif isinstance(my_update, pyupdater.client.updates.AppUpdate):  # AppUpdate, LibUpdate
            print('Binary Update Found. Download and restart?')
            msg = input('Enter \'yes\' to update:')
            if msg.strip().upper() == 'YES':
                my_update.download(background=False)
                while not my_update.is_downloaded():
                    time.sleep(.25)
                my_update.extract_restart()

        else:
            TE = TradeEngine()
            TE.run()

            store = get_store('Log')
            date = time.strftime('%I:%M:%S %p %m/%d/%y')
            store[date] = {}
            i = 0
            for m in TE.log_msgs:
                store[date][i] = m
                i += 1

            save_store('Log', store)

    except Exception as e:
        if not str(e) == 'Exit':
            # Error Logging
            print('****************** My Errror *************')
            print(e)
            err = traceback.format_exc()
            # print(err)
            store = get_store('ErrorLog')
            tim = time.strftime('%I:%M:%S %p %m/%d/%y')
            store[tim] = {'Error': err}
            save_store('ErrorLog', store)

            store = get_store('Log')
            date = time.strftime('%I:%M:%S %p %m/%d/%y')
            store[date] = {}
            i = 0
            for m in TE.log_msgs:
                store[date][i] = m
                i += 1

            save_store('Log', store)
            # store.put(time.strftime('%I:%M:%S %p %m/%d/%y'), msg=log)
            print('****************** End Errror *************')









