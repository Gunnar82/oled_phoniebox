""" Mopidy/MPD integration """
import asyncio
import time
import concurrent.futures
import musicpd
import settings # pylint: disable=import-error
import os

class MopidyControl():
    def __init__(self, loop):
        self.client = musicpd.MPDClient()
        self.loop = loop
        self.connected = False
        self.radiostations = []
        self.playlists = []
        self.nowplaying = {}
        self.status = {}
        self.loadedplaylist = ""
        self._connectionlost()

    def connect(self):
        print("Connecting to Mopidy...")
        #try to disconnect, in case the connection is in an unknown state
        try:
            self.client.disconnect()
        except musicpd.ConnectionError:
            pass

        while not self.connected:
            try:
                self.client.connect(settings.MPD_IP, settings.MPD_PORT)
            except musicpd.ConnectionError:
                print("No connection possible, trying again...")
                time.sleep(10)
            else:
                print(f"Connected to MPD Version {self.client.mpd_version}")
                self.connected = True
                self.loop.create_task(self._refresh_content())
                self.loop.create_task(self._update())
                self.loop.create_task(self._update_vol())

    def _connectionlost(self):
        self.connected = False
        executor = concurrent.futures.ThreadPoolExecutor()
        self.loop.run_in_executor(executor, self.connect)

    async def _update(self):
        while self.loop.is_running() and self.connected:
            try:
                self.nowplaying = self.client.currentsong()
            except musicpd.ConnectionError:
                print("Error updating mopidy status, no connection!")
                self._connectionlost()

            await asyncio.sleep(3)



    async def _update_vol(self):
        while self.loop.is_running() and self.connected:
            try:
                self.status = self.client.status()
            except musicpd.ConnectionError:
                print("Error updating mopidy status, no connection!")
                self._connectionlost()

            await asyncio.sleep(1)


    async def _refresh_content(self):
        while self.loop.is_running() and self.connected:
            await self._refresh_playlists()
            await asyncio.sleep(600)


    async def _refresh_radiostations(self):
        #Load Radio stations
        try:
            playlistfile = open(settings.STATIONSPLAYLIST)
        except FileNotFoundError:
            print("Error loading radio stations: File does not exist.")
        else:
            #Check if it is a non-broken m3u8/m3u file
            line = playlistfile.readline()
            if not line.startswith('#EXTM3U'):
                print("Error loading radio stations: The m3u8 file is invalid!")
                return None

            self.radiostations = []
            for line in playlistfile:
                line = line.strip()
                if line.startswith('#EXTINF:'):
                    # EXTINF line with information about the station
                    title = line.split('#EXTINF:')[1].split(',',1)[1]
                    self.radiostations.append(title)

            playlistfile.close()

    async def _refresh_playlists(self):
        #Load playlists
        try:
            playlists = self.client.listplaylists()
            #mypath = "/home/pi/RPi-Jukebox-RFID/shared/audiofolders/"
            #playlists = [d for d in os.listdir(mypath) if os.path.isdir(os.path.join(mypath,d))]
            #print (playlists)
        except musicpd.ConnectionError:
            print("Error loading playlists, no connection!")
            self._connectionlost()
        else:
            self.playlists = []
            for playlist in playlists:
                self.playlists.append(playlist["playlist"])


    def playpause(self):
        try:
            if self.status["state"] == "play":
                self.client.pause()
            else:
                self.client.play()
        except musicpd.ConnectionError:
            self._connectionlost()

    def next(self):
        try:
            self.client.next()
        except musicpd.ConnectionError:
            self._connectionlost()

    def previous(self):
        try:
            self.client.previous()
        except musicpd.ConnectionError:
            self._connectionlost()

    def stop(self):
        try:
            self.client.stop()
        except musicpd.ConnectionError:
            self._connectionlost()

    def playradiostation(self, stationid):
        #Start stream in background
        executor = concurrent.futures.ThreadPoolExecutor()
        self.loop.run_in_executor(executor, self._playradiostation, stationid)

    def _playradiostation(self, stationid):
        try:
            #self.client.clear()
            #os.system("/home/pi/RPi-Jukebox-RFID/scripts/playout_controls.sh -c=playerstop")
            os.system("sudo /home/pi/RPi-Jukebox-RFID/scripts/rfid_trigger_play.sh -d=\"%s\"" % settings.RADIO_PLAYLIST)
            #self.client.load("GBRadio")
            #self.loadedplaylist = "GBRadio"
        except musicpd.ConnectionError:
            self._connectionlost()
        try:
            self.client.play(stationid)
            print(f"Playing ID {stationid} ({self.radiostations[stationid]})")
        except musicpd.ConnectionError:
            self._connectionlost()


    def loadplaylist(self, name):
        try:
            #self.client.clear()
            #self.client.load(name)
            #self.client.play()
            rootdir =  "/home/pi/RPi-Jukebox-RFID/shared/audiofolders/"
            recursive = ""
            for file in os.listdir(rootdir):
                d = os.path.join(rootdir, file)
                if os.path.isdir(d):
                    recursive = "-v='recursive'"
            os.system("sudo /home/RPi-Jukebox-RFID/scripts/rfid_trigger_play.sh -d=\"%s\" %s" % (name,recursive))

            self.loadedplaylist = name
            print(f"Loaded and playing Playlist {name}")
        except musicpd.ConnectionError:
            self._connectionlost()
