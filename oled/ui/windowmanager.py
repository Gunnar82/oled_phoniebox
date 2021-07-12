"""Manages the currently shown activewindow on screen and passes callbacks for the rotary encoder"""
import asyncio
from datetime import datetime
import settings

class WindowManager():
    def __init__(self, loop, device):
        self.device = device
        self.windows = {}
        self.activewindow = []
        self.loop = loop
        self.screenpower = True
        self.lastinput = datetime.now()
        self.loop.create_task(self._render())
        print("Rendering task created")

    def add_window(self, windowid, window):
        self.windows[windowid] = window
        print(f"Added {windowid} window")

    def set_window(self, windowid):
        if windowid in self.windows:
            try:
                self.activewindow.deactivate()
            except (NotImplementedError, AttributeError):
                pass
            self.activewindow = self.windows[windowid]
            try:
                self.activewindow.activate()
            except (NotImplementedError, AttributeError):
                pass
            print(f"Activated {windowid}")
        else:
            print(f"Window {windowid} not found!")

        

    def clear_window(self):
        print("Show blank screen")
        self.screenpower = False
        self.device.clear()
        #Low-Power sleep mode
        self.device.hide()

    async def _render(self):
        while self.loop.is_running():
            if ((datetime.now() - self.lastinput).total_seconds() >= settings.MENU_TIMEOUT) and self.activewindow.timeout:
                self.set_window(self.activewindow.timeoutwindow)

            if ((datetime.now() - self.lastinput).total_seconds() >= settings.CONTRAST_TIMEOUT):
                self.device.contrast(settings.CONTRAST_DARK)
            else:
                self.device.contrast(settings.CONTRAST_FULL)
            
            if self.activewindow != [] and self.screenpower:
                try:
                    self.activewindow.render()
                except (NotImplementedError, AttributeError):
                    pass
            await asyncio.sleep(0.25)

    def push_callback(self,lp=False):
        if self.screenpower:
            try:
                self.lastinput = datetime.now()
                self.activewindow.push_callback(lp=lp)
            except (NotImplementedError, AttributeError):
                pass
        else:
            self.screenpower = True
            self.device.show()
            self.set_window("idle")

    def turn_callback(self, direction, key=None):
        try:
            self.lastinput = datetime.now()
            self.activewindow.turn_callback(direction,key=key)
        except (NotImplementedError, AttributeError):
            pass
