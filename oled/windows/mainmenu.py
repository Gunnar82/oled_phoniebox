""" Main menu """
from ui.windowbase import WindowBase
from luma.core.render import canvas
from PIL import ImageFont
import settings

class Mainmenu(WindowBase):
    faicons = ImageFont.truetype(settings.FONT_ICONS, size=18)
    faicons = ImageFont.truetype(settings.FONT_ICONS, size=18)
    def __init__(self, windowmanager):
        super().__init__(windowmanager)
        self.counter = 0

    def render(self):
        with canvas(self.device) as draw:
            #rectangle as selection marker
            if self.counter < 3: #3 icons in one row
                y_coord = 2
                x_coord = 7 + self.counter * 35
            else:
                y_coord = 35
                x_coord = 6 + (self.counter - 3) * 35
            draw.rectangle((x_coord, y_coord, x_coord+25, y_coord+25), outline=255, fill=0)

            #icons as menu buttons
            draw.text((11, 6), text="\uf0a8", font=Mainmenu.faicons, fill="white") #back
            draw.text((44, 6), text="\uf001", font=Mainmenu.faicons, fill="white") #radio
            draw.text((83, 6), text="\uf1c7", font=Mainmenu.faicons, fill="white") #playlists
            draw.text((11, 39), text="\uf02d", font=Mainmenu.faicons, fill="white") #infos
            draw.text((44, 39), text="\uf293", font=Mainmenu.faicons, fill="white") #infos
            draw.text((83, 39), text="\uf011", font=Mainmenu.faicons, fill="white") #shutdown

    def push_callback(self):
        if self.counter == 0:
            self.windowmanager.set_window("idle")
        elif self.counter == 1:
            self.windowmanager.set_window("radiomenu")
        elif self.counter == 2:
            self.windowmanager.set_window("foldermenu")
        elif self.counter == 3:
            self.windowmanager.set_window("infomenu")
        elif self.counter == 4:
            self.windowmanager.set_window("headphonemenu")
        elif self.counter == 5:
            self.windowmanager.set_window("shutdownmenu")

    def turn_callback(self, direction):
        if self.counter + direction <= 5 and self.counter + direction >= 0:
            self.counter += direction
