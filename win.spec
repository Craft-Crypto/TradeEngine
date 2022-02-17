# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['C:\\Users\\tommc\\PycharmProjects\\TradeEngine\\to_deploy\\main.py'],
             pathex=['C:\\Users\\tommc\\PycharmProjects\\TradeEngine\\to_deploy\\', 'C:\\Users\\tommc\\PycharmProjects\\TradeCraft\\to_deploy'],
             binaries=[],
             datas=[],
             hiddenimports=['websockets.legacy',
                            'websockets.legacy.client',],
             hookspath=['c:\\users\\tommc\\documents\\pythonenvironments\\tradeengine\\lib\\site-packages\\pyupdater\\hooks'],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          embed_manifest=False,
          name='win',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon='C:\\Users\\tommc\\PycharmProjects\\TradeEngine\\to_deploy\\TE.ico',)

coll = COLLECT(exe,
               Tree('C:\\Users\\tommc\\PycharmProjects\\TradeEngine\\to_deploy\\'),
               a.binaries,
               a.zipfiles,
               a.datas,
               *[],
               strip=False,
               upx=True,
               upx_exclude=[],
               name="win")