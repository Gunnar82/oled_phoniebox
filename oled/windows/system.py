""" Playlist menu """
import settings

import config.colors as colors
import config.symbols as symbols

from luma.core.render import canvas

import re
import imp
import time
import requests
import htmllistparse
import subprocess,os
import asyncio
import shutil
import importlib
import qrcode

from ui.listbase import ListBase
import time
import integrations.playout as playout

from integrations.functions import *

import config.online as cfg_online
import config.file_folder as cfg_file_folder
import config.services as cfg_services


import config.user_settings



class SystemMenu(ListBase):

    qr_width = settings.DISPLAY_HEIGHT if settings.DISPLAY_HEIGHT < settings.DISPLAY_WIDTH else settings.DISPLAY_WIDTH
    timeout = False
    new_busyrender = True

    def create_qr(self):

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=1,
        )

    
        ssid = self.hostapd_ssid.split('=',1)[1]
        psk = self.hostapd_psk.split('=',1)[1]
        wifi_format = f"WIFI:T:WPA;S:{ssid};P:{psk};H:false;;"
        qr.add_data(wifi_format)
        qr.make(fit=True)
        img = None
        img = qr.make_image(fill='black', back_color='white')
        return img.resize((self.qr_width,self.qr_width))

    def refresh_values(self):
        self.hostapd_status = get_hostapd_file_status()
        self.hostapd_ssid = get_hostapd_ssid()
        self.hostapd_psk = get_hostapd_psk()
        self.firewall_status = str(get_firewall_state())

    def __init__(self, windowmanager,loop,title):
        super().__init__(windowmanager, loop, title)
        self.refresh_values()

        self.handle_left_key = False
        self.processing = False
        self.totalsize = 0

        # QR-Code generieren

        self.menu.append(["Update Radiosender"])                   # Eintrag 0
        self.menu.append(["Lösche Online-Ordner"])                 # Eintrag 1
        self.menu.append(["Lösche Online-Status Online"])          # Eintrag 2

        self.menu.append(["Lösche Hörspielstatus"])                # Eintrag 3
        self.menu.append(["Lösche Musikstatus"])                   # Eintrag 4
        self.menu.append(["Lösche Radiostatus"])                   # Eintrag 5
        self.menu.append(["Lösche Onlinestatus"])                  # Eintrag 6

        self.menu.append(["Update OLED"])                          # Eintrag 7

        self.menu.append(["WLAN: aus"])                            # Eintrag 8
        self.menu.append(["WLAN: an"])                             # Eintrag 9

        self.menu.append([""])                                     # Eintrag 11
        self.menu.append(["aktivieren"])                           # Eintrag 12
        self.menu.append(["deaktivieren"])                         # Eintrag 13

        self.menu.append([""])                                     # Eintrag 14
        self.menu.append(["EIN"])                                  # Eintrag 15
        self.menu.append(["AUS"])                                  # Eintrag 16

        self.menu.append([""])                                     # Eintrag 17
        self.menu.append(["aktivieren"])                           # Eintrag 18
        self.menu.append(["deaktivieren"])                         # Eintrag 19

        self.menu.append([""])                                     # Eintrag 20

        self.menu.append(["beenden"])                              # Eintrag 21
        self.menu.append(["starten"])                              # Eintrag 22
        self.menu.append(["deaktivieren"])                         # Eintrag 23
        self.menu.append(["aktivieren"])                           # Eintrag 24

        self.menu.append(["WLAN QR anzeigen"])                     # Eintrag 25
        self.menu.append(["ssid"])                                 # Eintrag 26
        self.menu.append(["psk"])                                  # Eintrag 27
        self.menu.append(["Dienste neustarten:", "h"])             # Eintrag 28

        for srv in cfg_services.RESTART_LIST:
            self.menu.append(["%s" % (srv)])

    def activate(self):
        self.cmd = ""
        self.showqr = False

    def deactivate(self):
        self.showqr = False
        self.qrimage = None

    def exec_command(self):
        try:

            self.processing = True
            if self.position == 14:
                enable_firewall()
            elif self.position == 15:
                disable_firewall()
            else:
                self.append_busytext(self.menu[self.position][0])
                self.append_busytext(self.cmd)
                if run_command(self.cmd) == True:
                    self.append_busytext("Erfolgreich!")
                else:
                    self.append_busyerror()
        except Exception as error:
            self.appendbusyerror(error)
        finally:
            self.append_busytext("Abgeschlossen!")
            time.sleep(2)
            importlib.reload(config.user_settings)

            self.refresh_values()
            self.processing = False
            self.set_window_busy(False)


    async def push_handler(self,button = '*'):
        if self.showqr:
            self.showqr = False
            self.timeout = True
            self.contrasthandle = True

            return

        self.cmd = ""

        self.set_window_busy()
        self.append_busytext()

        if self.position == 0:
            if cfg_online.UPDATE_RADIO:
                self.cmd = "wget  --no-verbose --no-check-certificate  -r %s  --no-parent -A txt -nH -P %s/" %(cfg_online.ONLINE_RADIO_URL,cfg_file_folder.AUDIO_BASEPATH_BASE)

            else:
                self.append_busytext("Online Updates deaktiviert!")

        elif self.position == 1:
            delete_local_online_folder()

        elif self.position == 2:
            self.cmd = "wget  --no-verbose --no-check-certificate %sdeletepos.php?confirm=true -O-" %(cfg_online.ONLINE_SAVEPOS)

        elif self.position >=3 and self.position <= 6:
            if self.position == 3:
                what = cfg_file_folder.FILE_LAST_HOERBUCH
            elif self.position == 4:
                what = cfg_file_folder.FILE_LAST_MUSIC
            elif self.position == 5:
                what = cfg_file_folder.FILE_LAST_RADIO
            else:
                what = cfg_file_folder.FILE_LAST_ONLINE

            self.cmd = "sudo rm %s" % (what)


        elif self.position == 7:

            self.cmd = ["git pull", "sudo pip3 install -r requirements.txt", "sudo systemctl restart oled"]

        elif self.position == 8:
            self.cmd = "sudo ip link set wlan0 down"

        elif self.position == 9:
            self.cmd = "sudo ip link set wlan0 up"

        elif self.position == 11:
            self.cmd = f"sed -i 's/AUTO_ENABLED=False/AUTO_ENABLED=True/g' {cfg_file_folder.FILE_USER_SETTINGS}"

        elif self.position == 12:
            self.cmd = f"sed -i 's/AUTO_ENABLED=True/AUTO_ENABLED=False/g' {cfg_file_folder.FILE_USER_SETTINGS}"


        elif self.position == 17:
            self.cmd = f"sed -i 's/BLUETOOTH_AUTOCONNECT=False/BLUETOOTH_AUTOCONNECT=True/g' {cfg_file_folder.FILE_USER_SETTINGS}"

        elif self.position == 18:
            self.cmd = f"sed -i 's/BLUETOOTH_AUTOCONNECT=True/BLUETOOTH_AUTOCONNECT=False/g' {cfg_file_folder.FILE_USER_SETTINGS}"


        elif self.position == 20:
            self.cmd = "sudo systemctl stop hostapd"

        elif self.position == 21:
            self.cmd = "sudo systemctl start hostapd"

        elif self.position == 22:
            self.cmd = "echo \"disabled\" > /home/pi/oledctrl/oled/config/hotspot"

        elif self.position == 23:
            self.cmd = "echo \"enabled\" > /home/pi/oledctrl/oled/config/hotspot"
        elif self.position == 24:
            self.showqr = True
            self.timeout = False
            self.contrasthandle = False

            self.qrimage = self.create_qr()

        elif self.position == 25:
            self.cmd = "sudo sed -i \"s/^ssid=.*/ssid=pb_`tr -dc 'A-Za-z0-9' </dev/urandom | head -c 7`/\" \"/etc/hostapd/hostapd.conf\""

        elif self.position == 26:
            self.cmd = "sudo sed -i \"s/^wpa_passphrase=.*/wpa_passphrase=`tr -dc 'A-Za-z0-9' </dev/urandom | head -c 10`/\" \"/etc/hostapd/hostapd.conf\""

        elif self.position > 27:
            self.cmd = "sudo systemctl restart %s" % (self.menu[self.position][0])


        self.loop.run_in_executor(None,self.exec_command)


    def render(self):

        if not self.showqr:
            self.menu[10] = [f"Firewall AUTO_ENABLED ({config.user_settings.AUTO_ENABLED}):","h"]
            self.menu[13] = ["Firewall Status: %s " % ("AUS" if "deny" not in self.firewall_status else "EIN"),"h"]
            self.menu[16] = [f"Bluetooth_Autoconnect ({config.user_settings.BLUETOOTH_AUTOCONNECT}):","h"]
            self.menu[19] = [f"hostapd (aktiviert: {self.hostapd_status}):", "h"]
            self.menu[25] = [self.hostapd_ssid]
            self.menu[26] = [self.hostapd_psk]

            super().render()
        else:
            try:
                with canvas(self.device) as draw:
                    draw.bitmap(((settings.DISPLAY_WIDTH - self.qr_width) // 2,0), self.qrimage)
            except:
                self.showqr = False
