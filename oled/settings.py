"""
Software settings
"""

RADIO_PLAYLIST = "GBRadio"

MENU_TIMEOUT = 10

CONTRAST_TIMEOUT = 30
CONTRAST_FULL = 245
CONTRAST_DARK = 32

PLAYOUT_CONTROLS = "/home/pi/RPi-Jukebox-RFID/scripts/playout_controls.sh"


STATIONSPLAYLIST = "/home/pi/RPi-Jukebox-RFID/playlists/GBRadio.m3u"
EMULATED = False

#Pins for rotary encoder
PIN_CLK = 5
PIN_DT = 7
PIN_SW = 12

#Settings for the connection to Mopidy
MPD_IP = "localhost"
MPD_PORT = 6600

#Font files (TrueType)
FONT_ICONS = "fonts/fontawesome.otf"
FONT_TEXT = "fonts/arial.ttf"
FONT_CLOCK = "fonts/calibri.ttf"


#BluetoothKopfhoerer
BT_HF_MAC = "4A:F5:FF:38:28:D5"

ALSA_DEV_LOCAL="hifiberrydac"
ALSA_DEV_BT="btheadphones"

INTPIN=2