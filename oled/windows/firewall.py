""" Shutdown menu """
from ui.menubase import MenuBase
from luma.core.render import canvas
from PIL import ImageFont
import settings
import socket
import subprocess
import os
import asyncio
import re

class Firewallmenu(MenuBase):
    font = ImageFont.truetype(settings.FONT_TEXT, size=settings.FONT_SIZE_SMALL)
    faicons = ImageFont.truetype(settings.FONT_ICONS, size=settings.FONT_SIZE_XL)

    def __init__(self, windowmanager,loop):
        super().__init__(windowmanager,loop,"Firewall")
        self.counter = 0
        self.changerender = True
        self._ufw_status = "n/a"
        self.descr.append(["Firewall EIN","\uf1cb"])
        self.descr.append(["Firewall AUS","\uf1cb"])
    #def render(self):
    #    with canvas(self.device) as draw:
            #draw.text(((settings.DISPLAY_WIDTH - self.mwidth) / 2,1), text=self.descr, font=Firewallmenu.font, fill="white")

    #        draw.text((20, 20), text=self._ufw_status, font=Firewallmenu.font, fill="white")



    async def push_handler(self):
        await asyncio.sleep(1)
        if self.counter == 1:
            for srv in settings.ufw_services_allow:
                os.system("sudo ufw deny %s" % (srv))
        elif self.counter == 2:
            for srv in settings.ufw_services_allow:
                os.system("sudo ufw allow %s" % (srv))


    def activate(self):
        self._active = True
        self.loop.create_task(self._get_firewallstatus())

    def deactivate(self):
        self._active = False


    async def _get_firewallstatus(self):
        while self.loop.is_running() and self._active:
            try:
                subprocess_result = subprocess.Popen("sudo ufw status numbered | grep '\[' | cut -d ']' -f 2",shell=True,stdout=subprocess.PIPE)
                subprocess_output = subprocess_result.communicate()[0],subprocess_result.returncode
                self._ufw_status = subprocess_output[0].decode('utf-8')
                self._ufw_status = re.sub(' +',' ', self._ufw_status)
                self._ufw_status = self._ufw_status.replace("ALLOW IN"," allow")
                self._ufw_status = self._ufw_status.replace("DENY IN"," deny")

                self._ufw_status = self._ufw_status.replace("Anywhere","")



            except:
                self._ufw_status = "n/a"

            await asyncio.sleep(3)

