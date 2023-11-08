""" Start screen """
from ui.windowbase import WindowBase
from luma.core.render import canvas
from PIL import ImageFont
import settings, colors, symbols
import time,random
import asyncio

from datetime import datetime

class Lock(WindowBase):
    font = ImageFont.truetype(settings.FONT_TEXT, size=settings.FONT_SIZE_L)
    fontawesome = ImageFont.truetype(settings.FONT_ICONS, size=settings.FONT_SIZE_XXL)

    def __init__(self, windowmanager,loop):
        super().__init__(windowmanager)

        self.timeout = False
        self.window_on_back = "none"
        self.busyrendertime = 0.25

        self.loop = loop
        self.windowmanager = windowmanager
        self.timeout = False
        self.unlockcodes = []

        self.unlockcodes.append( ['up','down','left','right','start','select','x','y','hl','hr'])
        self.unlockcodes.append( ['1','2','3','4','5','6','7','8','9','0','a','b','c','d'] )
        self.unlockindex = -1

        self.currentkey = 0

    async def set_idle(self):
        await asyncio.sleep(3)
        self.windowmanager.set_window("idle")

    def activate(self):
        self.unlockcode = []

        if "gpicase" in settings.INPUTS: self.unlockindex = 0
        elif "keypad4x4" in settings.INPUTS: self.unlockindex = 1

        if self.unlockindex == -1:
            self.windowmanager.set_window("idle")
        else:
            for r in range(0,4):
                length = len(self.unlockcodes[self.unlockindex])
                pos = random.randint(0,length-1)
                char = self.unlockcodes[ self.unlockindex ][pos]

                self.unlockcode.append(char)
                try:
                    self.unlockcodes[ self.unlockindex ].remove(char)
                except:
                    pass
        print (self.unlockcodes[self.unlockindex])
        self.currentkey = 0
        self.busytext1 = "Tastensperre"
        self.busytext3 = "System entsperren mit"

        self.busysymbol=symbols.SYMBOL_LOCKED
        self.genhint()

    def render(self):
        self.renderbusy()

    def push_callback(self,lp=False):
        pass

    def turn_callback(self,direction, key=None):
        if key == '6': key = 'right'
        elif key == '2': key = 'up'
        elif key == '8': key = 'down'
        elif key == '4': key = 'left'

        if key.lower() == self.unlockcode[self.currentkey].lower():
            self.busysymbol = symbols.SYMBOL_PASS
            self.currentkey += 1
        else:
            self.busysymbol = symbols.SYMBOL_FAIL
            self.currentkey = 0

        if self.currentkey >= len(self.unlockcode):
             self.currentkey = 0 
             self.set_busy("Gerät entsperrt",symbols.SYMBOL_UNLOCKED)

             self.loop.create_task(self.set_idle())

        else:
            self.genhint()

    def genhint(self):
        for r in range(len(self.unlockcode)):
            if r == self.currentkey:
                self.unlockcode[r] = self.unlockcode[r].upper()
            else:
                self.unlockcode[r] = self.unlockcode[r].lower()
        self.busytext2 = ' '.join(self.unlockcode)



    def deactivate(self):
            self.power_timer = False

