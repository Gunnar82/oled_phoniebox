import os
import subprocess, re
import datetime
import settings

def get_parent_folder(folder):
    return os.path.dirname(folder)

def has_subfolders(path):
    for file in os.listdir(path):
        d = os.path.join(path, file)
        if os.path.isdir(d):
            return True
    return False


def to_min_sec(seconds):
        mins = int(float(seconds) // 60)
        secs = int(float(seconds) - (mins*60))
        if mins >=60:
            hours = int(float(mins) // 60)
            mins = int(float(mins) - (hours*60))
            return "%d:%2.2d:%2.2d" % (hours,mins,secs)
        else:
            return "%2.2d:%2.2d" % (mins,secs)

def linux_job_remaining(job_name):
        cmd = ['sudo', 'atq', '-q', job_name]
        dtQueue = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode('utf-8').rstrip()
        regex = re.search('(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', dtQueue)
        if regex:
            dtNow = datetime.datetime.now()
            dtQueue = datetime.datetime.strptime(dtNow.strftime("%d.%m.%Y") + " " + regex.group(5), "%d.%m.%Y %H:%M:%S")

            # subtract 1 day if queued for the next day
            if dtNow > dtQueue:
                dtNow = dtNow - datetime.timedelta(days=1)

            return int(round((dtQueue.timestamp() - dtNow.timestamp()) / 60, 0))
        else:
            return -1


def get_folder_of_livestream(url):
    basefolder = settings.AUDIO_BASEPATH_RADIO

    for folder in os.listdir(basefolder):
        d = os.path.join(basefolder, folder)
        if os.path.isdir(d):
           filename = os.path.join(d,'livestream.txt')
           try:
               with open(filename, 'r') as file:
                    data = file.read().replace('\n', '')
               if data == url:
                   return d
           except:
               pass

    return "n/a"


def get_folder(folder,direction = 1):
    parent = get_parent_folder(folder)
    entrys = []
    for folders in os.listdir(parent):
        d = os.path.join(parent, folders)
        if os.path.isdir(d):
            entrys.append(d)
    entrys.sort()
    pos = entrys.index(folder)
    pos += direction

    if pos < 0:
        pos = 0
    if pos > len(entrys) -1:
        pos = len(entrys) -1
    rel_path = os.path.relpath(entrys[pos],settings.AUDIO_BASEPATH_BASE)
    return rel_path


def restart_oled():
    print ("restarting oled service")
    os.system("sudo service oled restart")

