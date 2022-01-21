import CraftCrypto_Helpers.Helpers
import pyupdater
from pyupdater.client import Client as updateClient
import traceback
from client_config import ClientConfig
from TradeEngine import TradeEngine
from CraftCrypto_Helpers.Helpers import get_store, save_store
import time
import getpass


# Starts everything off
def check_for_update():
    up_client = updateClient(
        ClientConfig(), refresh=True, progress_hooks=[print_status_info]
    )
    app_update = up_client.update_check(tcl_name, tcl_version)
    # print(app_update)
    if isinstance(app_update, pyupdater.client.updates.AppUpdate):
        print('App Found Update.')
    else:
        print('No Update Found')
    return app_update


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
    tcl_name = 'TradeEngine'
    tcl_version = '0.0.1'

    try:
        print('Welcome to TradeCraft Lite v' + tcl_version)
        print('Checking for updates...')

        # uncomment this for automatic updates on packaged versions
        # app_update = check_for_update()
        # if isinstance(app_update, pyupdater.client.updates.AppUpdate):  # AppUpdate, LibUpdate
        #     print('Update Found. Download and restart?')
        #     msg = input('Enter \'yes\' to update:')
        #     if msg.strip().upper() == 'YES':
        #         data = app_update.download(background=True)
        #         while not app_update.is_downloaded():
        #             time.sleep(.25)
        #         data.extract_restart()
        # else:
        # Need to indent this for packaged version
        TE = TradeEngine()
        TE.run()

        store = get_store('Log')
        log = []
        add_line = False
        smaller = []
        msg = ''
        for m in TE.msgs:
            msg += m['text'] + '\n'

        store[time.strftime('%I:%M:%S %p %m/%d/%y')] = msg
        save_store('Log', store)

    except Exception as e:
        if not str(e) == 'Exit':
            # Error Logging
            print('****************** My Errror *************')
            print(e)
            err = traceback.format_exc()
            # print(err)
            store = get_store('ErrorLog')
            log = []
            add_line = False
            smaller = []
            tim = time.strftime('%I:%M:%S %p %m/%d/%y')
            store[tim] = err
            msg = ''
            for m in TE.msgs:
                msg += m['text'] + '\n'

            store[tim + ' LOG'] = msg
            save_store('ErrorLog', store)
            # store.put(time.strftime('%I:%M:%S %p %m/%d/%y'), msg=log)
            print('****************** End Errror *************')









