import os
import settings

def pc_prev():
    os.system("%s -c=playerprev" % (settings.PLAYOUT_CONTROLS))
def pc_next():
    os.system("%s -c=playernext" % (settings.PLAYOUT_CONTROLS))
def pc_stop():
    os.system("%s -c=playerstop" % (settings.PLAYOUT_CONTROLS))

def savepos():
    os.system("%s -c=savepos" % (settings.PLAYOUT_CONTROLS))

def pc_playfolder(folder=settings.AUDIO_BASEPATH_RADIO):
    os.system("sudo /home/pi/RPi-Jukebox-RFID/scripts/rfid_trigger_play.sh -d=\"%s\"" % (folder))
