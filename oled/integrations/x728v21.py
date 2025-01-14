import struct
import smbus
import sys
import time
import RPi.GPIO as GPIO
#import integrations.playout as playout
import settings

import config.symbols as symbols
import config.shutdown_reason as SR
import asyncio
from datetime import datetime

from integrations.logging_config import *
from integrations.functions import restart_oled
logger = setup_logger(__name__)


class x728:

    GPIO_BUTTON  = 5 # INPUT BUTTON PRESSED
    GPIO_BOOT	= 12
    GPIO_POWERFAIL = 6
    GPIO_BUZZER = 20 # BUZZER
    GPIO_LED     = 26 #


    def __init__(self,loop,windowmanager,led):
        # Global settings
        self.led = led
        self.loop = loop
        self.windowmanager = windowmanager
        self.voltage = 0
        self.capacity = 0
        self.oldvoltage = 0
        self.oldcapacity = -1
        self.loading = False
        self.I2C_ADDR    = 0x36

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.GPIO_POWERFAIL, GPIO.IN)
        GPIO.setup(self.GPIO_BUTTON, GPIO.IN)

        GPIO.setup(self.GPIO_BOOT, GPIO.OUT)
        GPIO.output(self.GPIO_BOOT, GPIO.HIGH)

        GPIO.add_event_detect(self.GPIO_POWERFAIL, GPIO.BOTH, callback=self.gpio_callback, bouncetime=100)
        GPIO.add_event_detect(self.GPIO_BUTTON, GPIO.BOTH, callback=self.gpio_callback, bouncetime=100)

        self.gpio_callback(self.GPIO_POWERFAIL)

        self.bus = smbus.SMBus(1) # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

        self.loop.create_task(self._handler())


    async def _handler(self):
        while self.loop.is_running():
            try:
                self.readVoltage()
                self.readCapacity()

                settings.battcapacity = self.capacity
                symbols.SYMBOL_BATTERY = self.getSymbol()

            except:
                print ("err x728")

            await asyncio.sleep (10)

    def gpio_callback (self,channel):
        status = GPIO.input(channel) == 1 # GPIO_POWERFAIL: 0 == angeschlossen, 1 = ohne Kabel
        logger.debug(f"handle GPIO {channel}, status: {status}")

        if channel == self.GPIO_POWERFAIL:
            self.get_powerfail_state(status)
        elif channel == self.GPIO_BUTTON:
            self.button_pressed = status
            if status:
                self.button_pressed_time = time.monotonic()
                self.loop.run_in_executor(None,self._handle_button_pressed)

    def _handle_button_pressed(self):

        handling = True

        while self.loop.is_running() and handling:
            timediff = time.monotonic() - self.button_pressed_time

            logger.debug(f"handle_button_pressed: timediff {timediff}, pressed: {self.button_pressed} ")

            if  timediff >= 6 and self.button_pressed:
                if self.led is not None:
                    self.led.set_permanent()

                logger.debug("> 4 sek: shutdown")
                handling = False
                settings.shutdown_reason = SR.SR2
                self.windowmanager.set_window("ende")

            elif timediff > 2 and timediff < 6:
                if self.button_pressed:
                    if self.led is not None:
                        self.led.set_dark()
                else:
                    logger.debug("> 2 && < 6 sek: reboot")
                    handling = False
                    restart_oled()

            time.sleep(1)

    def readVoltage(self):
         read = self.bus.read_word_data(self.I2C_ADDR, 2)
         swapped = struct.unpack("<H", struct.pack(">H", read))[0]
         self.voltage = swapped * 1.25 /1000/16


    def readCapacity(self):

         read = self.bus.read_word_data(self.I2C_ADDR, 4)
         swapped = struct.unpack("<H", struct.pack(">H", read))[0]
         self.capacity = swapped/256


    def get_powerfail_state(self,status):
        logger.debug(f"Powerfail ist {status}")
        settings.battloading = not status

    def getSymbol(self):
        if self.capacity < 10:
            return "\uf244"
        elif self.capacity < 30:
            return "\uf243"
        elif self.capacity < 60:
            return "\uf242"
        elif self.capacity < 90:
             return "\uf241"
        else:
            return "\uf240"

    def shutdown(self):
        logger.debug("x728 shutdown")
