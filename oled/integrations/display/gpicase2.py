""" Display hardware or emulator """
import settings

#import framebuffer device
from luma.core.device import linux_framebuffer


def get_display():
    settings.CONTRAST_HANDLE = False

    print("gpicase2")

    device = linux_framebuffer("/dev/fb0",bgr=True)
    device.capabilities(width=640,height=480,rotate=0,mode='RGB')
    return device

def do_nothing(obj):
    pass


def set_fonts():
    import fonts.fonts_640x480