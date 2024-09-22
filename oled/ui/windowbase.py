""" View class to inherit other views from """

import settings

import config.colors as colors
import config.symbols as symbols

import asyncio

from PIL import ImageFont
from luma.core.render import canvas

from datetime import datetime

busyfont = ImageFont.truetype(settings.FONT_TEXT, size=settings.WINDOWBASE_BUSYFONT)
busyfaicons = ImageFont.truetype(settings.FONT_ICONS, size=settings.WINDOWBASE_BUSYFAICONS)
busyfaiconsbig = ImageFont.truetype(settings.FONT_ICONS, size=settings.WINDOWBASE_BUSYFAICONSBIG)


class WindowBase():
    changerender = False
    fontheading = ImageFont.truetype(settings.FONT_TEXT, size=settings.WINDOWBASE_HEADING_SIZE)
    timeout = True
    contrasthandle = True
    windowtitle = "untitled"
    timeoutwindow="idle"
    window_on_back = "mainmenu"
    busysymbol = symbols.SYMBOL_SANDCLOCK
    busytext1 = settings.PLEASE_WAIT
    busytext2 = ""
    busytext3 = ""
    busytext4 = ""
    busyrendertime = 3
    _rendertime = 0.25
    counter = 0
    page = 0


    def __init__(self, windowmanager,loop):
        self.start_busyrendertime = datetime.now()
        self.loop = loop
        self.windowmanager = windowmanager
        self.device = self.windowmanager.device


    def clear_window(self):
        self.device.clear()

    def set_busy(self,busytext1,busysymbol=symbols.SYMBOL_SANDCLOCK,busytext2="", busyrendertime=3,busytext3="",set_window_to="none"):

        self.busytext1 = busytext1
        self.busysymbol = busysymbol

        self.busytext3 = busytext3
        if busyfont.getsize(busytext2)[0] > settings.DISPLAY_WIDTH:
            pos = len(busytext2) // 2
            self.busytext4 = busytext2[:pos]
            self.busytext2 = busytext2[pos:]

        else:
            self.busytext4 = ""
            self.busytext2 = busytext2

        self.busyrendertime = busyrendertime

        self.start_busyrendertime = datetime.now()
        self.busy = True

        if set_window_to != "none":
            self.loop.create_task(self.set_window(set_window_to))

    def renderbusy(self,symbolcolor = colors.COLOR_RED, textcolor1=colors.COLOR_WHITE, textcolor2=colors.COLOR_WHITE):
        with canvas(self.device) as draw:
            self.renderbusydraw(draw,symbolcolor,textcolor1,textcolor2)

    def renderbusydraw(self, draw, symbolcolor = colors.COLOR_RED, textcolor1=colors.COLOR_WHITE, textcolor2=colors.COLOR_WHITE):
        mwidth1,mheight1 = busyfont.getsize(self.busytext1)
        draw.text(((settings.DISPLAY_WIDTH - mwidth1) / 2, 5), text=self.busytext1, font=busyfont, fill=textcolor1)

        if (self.busytext3 != ""):
            mwidth3,mheight3 = busyfont.getsize(self.busytext3)
            draw.text(((settings.DISPLAY_WIDTH - mwidth3) / 2, mheight1 + 3), text=self.busytext3, font=busyfont, fill=textcolor2) #sanduhr

        if (self.busytext2 != ""):
            mwidth2,mheight2 = busyfont.getsize(self.busytext2)
            draw.text(((settings.DISPLAY_WIDTH - mwidth2) / 2, settings.DISPLAY_HEIGHT - mheight2 - 3), text=self.busytext2, font=busyfont, fill=textcolor2) #sanduhr

        if (self.busytext4 != ""):
            mwidth4,mheight4 = busyfont.getsize(self.busytext4)
            draw.text(((settings.DISPLAY_WIDTH - mwidth4) / 2, settings.DISPLAY_HEIGHT - mheight2 - 3  - mheight4 - 3), text=self.busytext4, font=busyfont, fill=textcolor2) #sanduhr

        mwidth,mheight = busyfaiconsbig.getsize(self.busysymbol)
        draw.text(((settings.DISPLAY_WIDTH - mwidth) / 2, (settings.DISPLAY_HEIGHT - mheight) / 2), text=self.busysymbol, font=busyfaiconsbig, fill=symbolcolor) #sanduhr

    async def set_window(self,windowid):
        await asyncio.sleep(3)
        self.windowmanager.set_window(windowid)

    def activate(self):
        self.clear_window()

    def deactivate(self):
        raise NotImplementedError()

    def render(self):
        raise NotImplementedError()

    def push_callback(self,lp=False):
        raise NotImplementedError()

    def turn_callback(self, direction, key=None):
        raise NotImplementedError()
