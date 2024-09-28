""" Shutdown menu """
from ui.listbase import ListBase
from luma.core.render import canvas

import settings

import config.colors as colors
import config.symbols as symbols

import os

import time
import asyncio

from integrations.logging_config import *

logger = setup_logger(__name__)

 
class Bluetoothmenu(ListBase):

    new_busyrender = True

    def __init__(self, windowmanager,loop,bluetooth,title):
        super().__init__(windowmanager,loop,title)
        self.bluetooth = bluetooth
        self.window_on_back = "headphonemenu"
        self.handle_left_key = False

        self.selector = False
        self.generate = False
        self.timeout = False
        self.selected_device = []

    def deactivate(self):
        self.active = False
        self.bluetooth.stop_scan()

        self.bluetooth.stop_bluetoothctl()


    def activate (self):
        self.selector = False
        self.active = True
        self.show_paired = True
        self.bluetooth.start_bluetoothctl()
        self.generate = True
        self.loop.create_task(self.gen_menu())

    async def gen_menu(self):
        while self.loop.is_running() and self.active:
            if self.generate:

                self.menu = []


                if self.selector:
                    self.menu.append(["Abbrechen",symbols.SYMBOL_SANDCLOCK])
                    self.menu.append(["Auswählen",symbols.SYMBOL_PASS])
                    self.menu.append(["Löschen",symbols.SYMBOL_FAIL])

                else:
                    self.menu.append(["aktualisieren...",symbols.SYMBOL_REFRESH])
                    self.menu.append(["","c"])
                    if self.show_paired:
                        self.menu.append(["> gekoppelte Geräte:","c"])

                        for device in self.bluetooth.get_paired_devices():
                            self.menu.append([device['name'],symbols.SYMBOL_BLUETOOTH_OFF,device['mac_address']])
                    else:
                        self.menu.append(["neue Geräte:","h"])

                        for device in self.bluetooth.get_discoverable_devices():

                            self.menu.append([device['name'],symbols.SYMBOL_BLUETOOTH_ON,device['mac_address']])

                    self.generate = False

            await asyncio.sleep(1)

    #def push_callback(self,lp=False):
    def push_handler(self):
        try:
            self.set_window_busy()
            if not self.selector:

                if (self.position == 0):
                    self.show_paired = False
                    self.append_busytext("Starte Suche...")
                    self.bluetooth.start_scan()

                elif self.menu[self.position][1] == symbols.SYMBOL_BLUETOOTH_ON:
                    device = self.menu[self.position]
                    self.append_busytext(f"Paare Gerät {device[0]}...")
                    self.bluetooth.pair(device[2])
                    self.bluetooth.trust(device[2])
                    self.show_paired = True
                else:
                    self.selected_device = self.menu[self.position]

                    self.selector = True
                    self.position = 0

            else:
                if self.selected_device[1] == symbols.SYMBOL_BLUETOOTH_OFF:

                    if self.position == 1:
                        self.append_busytext(f"Setze Bluetooth-Gerät {self.selected_device[0]}...")

                        self.bluetooth.set_alsa_bluetooth_mac(self.selected_device[2],self.selected_device[0])
                    elif self.position == 2:
                        self.append_busytext(f"Lösche Bluetooth-Gerät {self.selected_device[0]}...")

                        self.bluetooth.remove(self.selected_device[2])

                    self.selected_device = []
                self.selector = False

                self.position = 0

            self.generate = True

        except Exception as error:
            self.append_busyerror(error)
        finally:
            self.set_window_busy(False)
