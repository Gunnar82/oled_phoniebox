import os
import settings
import requests
import urllib.parse

import config.file_folder as cfg_file_folder
import config.online as cfg_online

from integrations.functions import run_command
from integrations.download import get_parent_directory_of_url

from urllib.parse import urljoin

def pc_prev():
    run_command("%s -c=playerprev" % (cfg_file_folder.PLAYOUT_CONTROLS))
def pc_next():
    run_command("%s -c=playernext" % (cfg_file_folder.PLAYOUT_CONTROLS))
def pc_stop():
    run_command("%s -c=playerstop" % (cfg_file_folder.PLAYOUT_CONTROLS))

def pc_play(pos = 0):
    run_command("%s -c=playerplay -v=%d" % (cfg_file_folder.PLAYOUT_CONTROLS, pos))

def pc_mute():
    run_command("%s -c=mute" % (cfg_file_folder.PLAYOUT_CONTROLS))

def pc_toggle():
    run_command("%s -c=playerpause" % (cfg_file_folder.PLAYOUT_CONTROLS))

def pc_shutdown():
    run_command("%s -c=shutdown" % (cfg_file_folder.PLAYOUT_CONTROLS))

def pc_reboot():
    print("Reboot down system")
    run_command("%s -c=reboot" % (cfg_file_folder.PLAYOUT_CONTROLS))


def pc_seek0():
    print("mpc seek 0")
    run_command("mpc seek 0")

def savepos():
    run_command("%s -c=savepos" % (cfg_file_folder.RESUME_PLAY))

def savepos_online(nowplaying):
    try:
        #url = get_parent_directory_of_url(nowplaying.filename)
        data = {'url' : url, 'pos' : str(nowplaying._elapsed), 'song' : str(nowplaying._song), 'length' : str(nowplaying._playlistlength)}
        if nowplaying.input_is_online:
            r = requests.post(cfg_online.ONLINE_SAVEPOS,data=data,timeout=8)

    except Exception as error:
        print (error)

def getpos_online(baseurl,cwd):
    url = urljoin(baseurl,urllib.parse.quote(cwd))
    data = {'url' : url}
    try:
        r = requests.post("%sgetpos.php" % (cfg_online.ONLINE_SAVEPOS),data=data)
        response = r.content.decode()
        vals = response.split("|")
        vals.append(url)
        return vals

    except:
        return ["ERREXP"]

def add_leading_slash(folder):
    return folder if folder[0] == '/' else '/%s' % (folder)

def checkfolder(playfile):
    try:
        lastfile=add_leading_slash(open(playfile).read().replace("\n",""))
        if not os.path.isdir(cfg_file_folder.AUDIO_BASEPATH_BASE + lastfile):
            return 2
        return 0
    except:
        return 1

def playlast_checked(playfile):
    lastfile=add_leading_slash(open(playfile).read().replace("\n",""))

    pc_playfolder(lastfile)

def pc_volup(step=5):
    run_command("mpc vol  +%d" % (step))
#    run_command("sudo /home/pi/RPi-Jukebox-RFID/scripts/playout_controls.sh -c=volumeup -v=%d" % (step))

def pc_voldown(step=5):
    run_command("mpc vol -%d" % (step))
#    run_command("sudo /home/pi/RPi-Jukebox-RFID/scripts/playout_controls.sh -c=volumedown -v=%d" % (step))


def pc_playfolder(folder=cfg_file_folder.AUDIO_BASEPATH_RADIO):
    run_command("sudo /home/pi/RPi-Jukebox-RFID/scripts/rfid_trigger_play.sh -d=\"%s\"" % (folder))

def pc_shutdown():
    run_command("sudo /home/pi/RPi-Jukebox-RFID/scripts/playout_controls.sh -c=shutdown")

def pc_enableresume(folder=""):
    if folder != "":
        print("%s -c=enableresume -d=\"%s\"" % (cfg_file_folder.RESUME_PLAY,folder))

def pc_disableresume(folder=""):
    if folder != "":
        run_command("%s -c=disableresume -d=\"%s\"" % (cfg_file_folder.RESUME_PLAY,folder))
