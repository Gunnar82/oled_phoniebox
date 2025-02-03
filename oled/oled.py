#!/usr/bin/python3
"""Start file for Werkstattradio OLED controller"""
import asyncio
import signal
import sys
import os,shutil
import time
import importlib
from subprocess import call
import argparse

# Funktion zum Argumente parsen
def parse_arguments():
    parser = argparse.ArgumentParser(description="Starte das Programm mit benutzerdefiniertem Log-Level.")
    parser.add_argument('--loglevel-debug', type=str, nargs='*', help='Setze den Debug-Level für bestimmte Module')
    return parser.parse_args()

# Argumente parsen
args = parse_arguments()


from integrations.logging_config import *
from integrations.functions import run_as_service

# Debug-Module global setzen
if args.loglevel_debug:
    configure_debug_modules(args.loglevel_debug)


logger = setup_logger(__name__)


###checke user_settings
def check_or_create_config(filename,samplename):
    try:

        if not os.path.exists(filename):
            logger.info(f"{filename} existiert nicht. Erstelle aus der Vorlage.")
            # Prüfe, ob die Vorlage existiert
            if os.path.exists(samplename):
                # Kopiere die Vorlage in USER_SETTINGS
                shutil.copy(samplename, filename)
                logger.info(f"{filename} wurde aus {samplename} erstellt.")
            else:
                logger.error(f"Vorlage {samplename} existiert nicht.")
    except Exception as error:
       logger.error(f"usersettings Fehler: {filename}: {error}")
       sys.exit (-1)

settings_py = "/home/pi/oledctrl/oled/settings.py"
settings_py_sample = f"{settings_py}.sample"


user_settings_py = "/home/pi/oledctrl/oled/config/user_settings.py"
user_settings_py_sample = f"{user_settings_py}.sample"


file_folder_py = "/home/pi/oledctrl/oled/config/file_folder.py"
file_folder_py_sample = f"{file_folder_py}.sample"


online_py = "/home/pi/oledctrl/oled/config/online.py"
online_py_sample = f"{online_py}.sample"

keypad_4x4_i2c_cfg = "/home/pi/oledctrl/oled/config/keypad_4x4_i2c.py"
keypad_4x4_i2c_cfg_sample = f"{keypad_4x4_i2c_cfg}.sample"

statusled_cfg = "/home/pi/oledctrl/oled/config/statusled.py"
statusled_cfg_sample = f"{statusled_cfg}.sample"

rotary_enc_cfg = "/home/pi/oledctrl/oled/config/rotary_enc.py"
rotary_enc_cfg_sample = f"{rotary_enc_cfg}.sample"

check_or_create_config(user_settings_py,user_settings_py_sample)
check_or_create_config(file_folder_py,file_folder_py_sample)
check_or_create_config(settings_py,settings_py_sample)
check_or_create_config(online_py,online_py_sample)


import settings

import config.user_settings as csettings
import config.file_folder as cfg_file_folder
import integrations.functions as fn
import integrations.playout as playout
import config.shutdown_reason as SR


######
from datetime import datetime
###########################
settings.screenpower = True
settings.shutdown_reason = "changeme"
fn.set_lastinput()
settings.job_t = -1
settings.job_i = -1
settings.job_s = -1
settings.audio_basepath = cfg_file_folder.AUDIO_BASEPATH_MUSIC
settings.currentfolder = settings.audio_basepath
settings.current_selectedfolder=settings.currentfolder
settings.battcapacity = -1
settings.battloading = False
settings.callback_active = False



displays = ["st7789", "ssd1351", "sh1106_i2c", "sh1106_i2c", "emulated","gpicase","gpicase2"]

if not settings.DISPLAY_DRIVER in displays:
    raise Exception("no DISPLAY")

try:
    lib = "integrations.display.%s" % (settings.DISPLAY_DRIVER)
    logger.info(f"Display: {lib}")
    idisplay = importlib.import_module(lib)
    idisplay.set_fonts()
except Exception as error:
    raise Exception(f"DISPLAY init FAILED: {error}")  # Exception verbessern


from integrations.mopidy import MopidyControl
from integrations.musicmanager import Musicmanager
from ui.windowmanager import WindowManager
import windows.idle
import windows.info
import windows.headphone
import windows.mainmenu
import windows.playbackmenu
import windows.playlistmenu
import windows.foldermenu
import windows.shutdownmenu
import windows.folderinfo
import windows.radiomenu
import windows.start
import windows.ende
import windows.getvalue
import windows.download as wdownload
import windows.lock as wlock
import windows.system as wsystem
import windows.snake as wsnake


try:
    bluetooth_enabled = False


    if csettings.BLUETOOTH_ENABLED:
        import integrations.bluetooth
        import windows.bluetooth
        bluetooth_enabled = True
        mybluetooth = integrations.bluetooth.BluetoothOutput()
        logger.info ("Bluetooth gestartet")

except Exception as error:
    bluetooth_enabled = False
    mybluetooth = None


    logger.error(f"Bluetooth: {error}")



#Systemd exit
def handle_signal(loop, signal_name):
    print(f"{signal_name} empfangen, beende...")

    loop.stop()
    sys.exit(0)

#signal.signal(signal.SIGTERM, gracefulexit)

def main():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, handle_signal, loop,"SIGINT")
    loop.add_signal_handler(signal.SIGTERM, handle_signal, loop,"SIGTERM")
    #shutdown reason default
    settings.shutdown_reason = SR.SR1

    #Display = real hardware or emulator (depending on settings)
    display = idisplay.get_display()

    #screen = windowmanager
    windowmanager = WindowManager(loop, display)

    #Software integrations
    mopidy = MopidyControl(loop)
    #def airplay_callback(info, nowplaying):
    #    musicmanager.airplay_callback(info, nowplaying)
    #shairport = ShairportMetadata(airplay_callback)
    musicmanager = Musicmanager(mopidy)

    ###processing nowplaying
    import integrations.nowplaying as nowplaying

    _nowplaying = nowplaying.nowplaying(loop,musicmanager,windowmanager,mybluetooth)

    #callback_setup
    def turn_callback(direction,_key=False):
        windowmanager.turn_callback(direction, key=_key)

    def push_callback(_lp=False):
        windowmanager.push_callback(lp=_lp)


    ###GPICase
    if "gpicase" in settings.INPUTS:
        from integrations.inputs.gpicase import pygameInput

        print ("Using pyGameInput")
        mypygame = pygameInput(loop, turn_callback, push_callback,windowmanager,_nowplaying)

    #Import all window classes and generate objects of them
    loadedwins = []


    loadedwins.append(windows.start.Start(windowmanager, loop, mopidy,mybluetooth))
    loadedwins.append(windows.idle.Idle(windowmanager, loop, _nowplaying))
    loadedwins.append(windows.playbackmenu.Playbackmenu(windowmanager, loop, _nowplaying))
    loadedwins.append(windows.mainmenu.Mainmenu(windowmanager,loop,"Hauptmenü"))
    loadedwins.append(windows.info.Infomenu(windowmanager,loop))
    if bluetooth_enabled: loadedwins.append(windows.headphone.Headphonemenu(windowmanager,loop,mybluetooth,"Audioausgabe"))
    if bluetooth_enabled: loadedwins.append(windows.bluetooth.Bluetoothmenu(windowmanager,loop,mybluetooth,"Bluetoothmenu"))
    loadedwins.append(windows.playlistmenu.Playlistmenu(windowmanager, loop, musicmanager))
    loadedwins.append(windows.foldermenu.Foldermenu(windowmanager,loop))
    loadedwins.append(windows.radiomenu.Radiomenu(windowmanager,loop))
    loadedwins.append(windows.folderinfo.FolderInfo(windowmanager, loop))
    loadedwins.append(windows.getvalue.GetValue(windowmanager, loop))
    loadedwins.append(windows.ende.Ende(windowmanager, loop,_nowplaying))
    loadedwins.append(windows.shutdownmenu.Shutdownmenu(windowmanager, loop, mopidy,_nowplaying,"Powermenü"))
    loadedwins.append(wdownload.DownloadMenu(windowmanager,loop,mopidy))
    loadedwins.append(wsnake.SnakeGame(windowmanager,loop))
    loadedwins.append(wlock.Lock(windowmanager,loop,_nowplaying))
    loadedwins.append(wsystem.SystemMenu(windowmanager,loop,"Systemeinstellungen"))
    for window in loadedwins:
        windowmanager.add_window(window.__class__.__name__.lower(), window)

    #Load start window
    windowmanager.set_window("start")


    #init Inputs

    ####Bluetooth Keys Input####
    if "btkeys" in settings.INPUTS:
        from integrations.inputs.btkeys import BluetoothKeys

        mbtkeys = BluetoothKeys(loop, turn_callback, push_callback, mybluetooth)


    ####keyboard control
    if "keyboard" in settings.INPUTS:
        from integrations.inputs.keyboard import KeyboardCtrl

        mKeyboard = KeyboardCtrl(loop, turn_callback, push_callback)

    ### KEYPAD 4x4 MCP23017 I2C

    if "keypad4x4" in settings.INPUTS:
        check_or_create_config(keypad_4x4_i2c_cfg,keypad_4x4_i2c_cfg_sample)
        import config.keypad_4x4_i2c as keypad_4x4_i2c_config

        from integrations.inputs.keypad_4x4_i2c import keypad_4x4_i2c

        mKeypad = keypad_4x4_i2c(loop, keypad_4x4_i2c_config.KEYPAD_ADDR, keypad_4x4_i2c_config.KEYPAD_INTPIN, turn_callback, push_callback)


    ###Rotaryencoder Setup
    if "rotaryenc" in settings.INPUTS:
        check_or_create_config(rotary_enc_cfg,rotary_enc_cfg_sample)
        import config.rotary_enc as rotary_enc_config

        from integrations.inputs.rotaryencoder import RotaryEncoder

        print ("Rotaryconctroller")
        rc = RotaryEncoder(loop, turn_callback, push_callback,clk=rotary_enc_config.PIN_CLK,dt=rotary_enc_config.PIN_DT,sw=rotary_enc_config.PIN_SW)


    ####Powercontroller Init
    haspowercontroller = False
    if "powercontroller" in settings.INPUTS:
        from integrations.inputs.powercontroller import PowerController

        haspowercontroller = True
        try:
            print ("Poweronctroller")
            pc = PowerController(loop, turn_callback, push_callback)
            haspowercontroller = False
        except:
            haspowercontroller = False
            logger.error(f"Power controller init failed: {e}")  # Fehlerbehandlung verbessern

    #### pirateaudio init
    if "pirateaudio" in settings.INPUTS:
        from integrations.inputs.pirateaudio import PirateAudio
        pirateaudio = PirateAudio(loop, turn_callback, push_callback)

# end init inputs

    ######Status LED
    if "statusled" in settings.INPUTS:
        check_or_create_config(statusled_cfg,statusled_cfg_sample)

        import config.statusled as statusled_config

        import integrations.statusled as statusled

        led = statusled.statusled(loop,musicmanager,pin=statusled_config.STATUS_LED_PIN,always_on=statusled_config.STATUS_LED_ALWAYS_ON)
    else:
        led = None

    ####x728V2.1
    if "x728" in settings.INPUTS:
        import integrations.x728v21 as x728v21
        x728 = x728v21.x728(loop,windowmanager,led)


    ###main
    try:
        loop.run_forever()
        mopidy.stop()
    except (KeyboardInterrupt, SystemExit):
        logger.error("main Loop exiting")
        loop.stop()
    finally:
        loop.close()

    ####BTkeys Cleanup####
    try:
        if "btkeys" in settings.INPUTS:
            mbtkeys.btkeystask.cancel
    except Exception as error:
        print (f"btkeys cleanup error: {error}")

    ####x728 Cleanup
    if "x728" in settings.INPUTS:
        print ("shutdown x728")
        x728.shutdown()

    ###GPICase
    if "gpicase" in settings.INPUTS:
        mypygame.quit()

    if run_as_service():

        if settings.shutdown_reason in [SR.SR2, SR.SR5]:
            if haspowercontroller:
                if pc.ready:
                    pc.shutdown()

            logger.error(f"Shutting down system: {settings.shutdown_reason}")
            silent=True if settings.shutdown_reason == SR.SR5 else False
            playout.pc_shutdown(silent)

        elif settings.shutdown_reason == SR.SR3:
            playout.pc_reboot()
    else:
        logger.error (f"nicht als Dienst gestartet - nur beenden, eigentlich: {settings.shutdown_reason}")


if __name__ == '__main__':
    main()
    if "rotaryenc" in settings.INPUTS:
        RotaryEncoder.cleanup()
    sys.exit(0)
