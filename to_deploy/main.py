# -----------------------------------------------------------------------------
# Copyright (c) 2022 Tom McLaughlin @ Craft-Crypto, LLC
#
# Other libraries used in the project:
#
# Copyright (c) 2015-2019 Digital Sapphire - PyUpdater
# Copyright (c) 2017 Igor Kroitor - ccxt
# Copyright (c) 2018 P G Jones - hypercorn
# Copyright (c) 2017 P G Jones - quart
# Copyright (c) 2007 vxgmichel - aioconsole
# Copyright (c) 2013-2021 Aymeric Augustin and contributors - websockets
# Copyright (c) 2017-2018 Alex Root Junior - aiogram
# Copyright (c) 2022 Craft-Crypto, LLC - Craft-Crypto Helpers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

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
import win32con

# Starts everything off
def check_for_update(te_name, te_version):
    up_client = updateClient(
        ClientConfig(), refresh=True, progress_hooks=[print_status_info]
    )
    my_update = up_client.update_check(te_name, te_version)
    # print(my_update)
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
    te_version = '1.0.18'

    try:
        print(f'Welcome to {te_name} v{te_version}')
        print('Checking for updates...')

        # uncomment this for automatic updates on packaged versions
        my_update = check_for_update(te_name, te_version)

        if my_update:
            print('App Update Found. Download and restart?')
            msg = input('Enter \'yes\' to update:')
            if msg.strip().upper() == 'YES':
                print('*****Please Wait and Let App Restart By Itself.')
                print('*****You May Be Prompted by Your System to Allow TradeEngine to Update.')
                print('*****If Persistent Errors Occur, Please Redownload Installer from craft-crypto.com.')
                print('*****Otherwise, Contact Us at brewers@craft-crypto.com')
                if isinstance(my_update, pyupdater.client.updates.LibUpdate):  # AppUpdate, LibUpdate
                    my_update.download(background=False)
                    while not my_update.is_downloaded():
                        time.sleep(.5)
                    my_update.extract()
                    dir = my_update.update_folder
                    # print(my_update.update_folder, my_update.filename)
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









