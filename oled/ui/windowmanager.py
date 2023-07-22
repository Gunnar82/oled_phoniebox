"""Manages the currently shown activewindow on screen and passes callbacks for the rotary encoder"""
import settings
import asyncio

from integrations.logging import *

from datetime import datetime
from integrations.rfidwatcher import RfidWatcher

class WindowManager():
    def __init__(self, loop, device):
        self._looptime = 2
        self._RENDERTIME = 0.25

        self.looptime = self._looptime
        self.device = device
        self.windows = {}
        self.activewindow = []
        self.loop = loop
        settings.lastinput = datetime.now()
        self._lastcontrast = settings.CONTRAST_FULL
        self.loop.create_task(self._render())
        self.lastrfidate = datetime(2000,1,1)

        self.rfidwatcher = RfidWatcher()
        self.rfidwatcher.start()


        log(lINFO,"Rendering task created")

    def add_window(self, windowid, window):
        self.windows[windowid] = window
        log(lINFO,f"Added {windowid} window")

    def set_window(self, windowid):
        if windowid in self.windows:
            try:
                self.activewindow.deactivate()
            except (NotImplementedError, AttributeError):
                pass
            self.activewindow = self.windows[windowid]
            try:
                self.rendertime = self.activewindow._rendertime
                self.activewindow.busy = False
                self.activewindow.activate()
            except (NotImplementedError, AttributeError):
                pass
            log(lINFO,f"Activated {windowid}")
        else:
            log(lINFO,f"Window {windowid} not found!")

    def show_window(self):
        settings.screenpower = True
        self.device.show()


    def clear_window(self):
        log(lDEBUG,"Show blank screen")
        settings.screenpower = False
        self.device.clear()
        #Low-Power sleep mode
        self.device.hide()

    async def _render(self):
        while self.loop.is_running():
            if ((datetime.now() - settings.lastinput).total_seconds() >= settings.MENU_TIMEOUT) and self.activewindow.timeout:
                self.set_window(self.activewindow.timeoutwindow)

            if self.activewindow.contrasthandle:
                log(lDEBUG2,"contrasthandle")
                if (datetime.now() - settings.lastinput).total_seconds() >= settings.DARK_TIMEOUT:
                    self.rendertime = settings.DARK_RENDERTIME
                    self.looptime = int (settings.DARK_RENDERTIME // 2)

                    contrast = settings.CONTRAST_BLACK

                elif  (datetime.now() - settings.lastinput).total_seconds() >= settings.CONTRAST_TIMEOUT:
                    self.looptime = settings.CONTRAST_RENDERTIME
                    self.rendertime = settings.CONTRAST_RENDERTIME
                    log(lDEBUG2,"contrast_timeout")
                    if settings.DISABLE_DISPLAY:
                        if settings.screenpower:
                            log(lDEBUG,"disable Display")
                            self.clear_window()
                    else:
                        contrast = settings.CONTRAST_DARK

                else:
                    contrast = settings.CONTRAST_FULL
                    self.rendertime = self.activewindow._rendertime
                    self.looptime = self._looptime



            if self._lastcontrast != contrast and settings.CONTRAST_HANDLE:
                self._lastcontrast = contrast
                if settings.CONTRAST_HANLDE:
                    self.device.contrast(contrast)

            if self.activewindow != []:
                count = 0
                while (contrast == settings.CONTRAST_BLACK) and (count < 4 * settings.DARK_RENDERTIME) and ((datetime.now() - settings.lastinput).total_seconds() >= settings.CONTRAST_TIMEOUT):
                    count += 1
                    await asyncio.sleep(0.25)

                if self.rfidwatcher.get_state():
                    self.show_window()
                    self.lastrfidate = datetime.now()

                if settings.screenpower and not settings.callback_active:
                    try:
                        if not settings.callback_active:
                            if (datetime.now() - self.lastrfidate).total_seconds() < 3:
                                log(DEBUG,"render rfid symbol")
                                self.activewindow.busysymbol = settings.SYMBOL_CARD_READ
                                self.activewindow.render()
                                self.activewindow.renderbusy()
                                self.activewindow.busysymbol = settings.SYMBOL_SANDCLOCK
                            elif self.activewindow.busy:
                                log(lDEBUG,"render busy symbol")
                                self.rendertime = self.activewindow.busyrendertime
                                self.activewindow.renderbusy()
                                self.activewindow.render()
                            else:
                                self.activewindow.busysymbol = settings.SYMBOL_SANDCLOCK
                                self.activewindow.render()
                    except (NotImplementedError, AttributeError):
                        log(lERROR,"render error")

            iTimerCounter = 0 
            while (((datetime.now() - settings.lastinput).total_seconds() < self.activewindow.busyrendertime) and (iTimerCounter < self.rendertime / self._RENDERTIME)):
                log(lDEBUG2,"renderloop: %d"%(iTimerCounter+1))
                iTimerCounter += 1
                await asyncio.sleep(self._RENDERTIME)

            await asyncio.sleep(self._RENDERTIME)

    def push_callback(self,lp=False):
        settings.lastinput = datetime.now()
        settings.staywake = False
        if settings.screenpower:
            self.activewindow.busy = True

            try:
                self.device.contrast(settings.CONTRAST_FULL)
                self.activewindow.push_callback(lp=lp)
            except (NotImplementedError, AttributeError):
                log(lERROR,"window_manager: push_callback error")
            finally:
                self.activewindow.busy = False
                self.activewindow.busysymbol = settings.SYMBOL_SANDCLOCK

        else:
            settings.screenpower = True
            self.device.show()
            self.set_window("idle")

    def turn_callback(self, direction, key=None):
        try:
            self.activewindow.busy = True
            settings.screenpower = True
            #self.device.show()
            settings.lastinput = datetime.now()
            self.device.contrast(settings.CONTRAST_FULL)
            if key == '#':
                log(lINFO,"activate window_on_back: %s" % (self.activewindow.window_on_back))
                self.set_window(self.activewindow.window_on_back)
            else:
                self.activewindow.turn_callback(direction,key=key)
        except (NotImplementedError, AttributeError):
            log(lERROR,"window_manager: turn_callback error")
        finally:
            self.activewindow.busy = False

    def __del__(self):
        self.rfidwatcher.stop()

