""" Playlist menu """	
import settings

import config.colors as colors
import config.symbols as symbols

import time
import requests
import xml.etree.ElementTree as ET

import os
import shutil

from luma.core.render import canvas

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote, unquote


from ui.listbase import ListBase
import time

from integrations.playout import *
from integrations.functions import get_size
from integrations.webrequest import WebRequest

import config.online as cfg_online
import config.file_folder as cfg_file_folder


from integrations.download import *

from integrations.logging_config import *

logger = setup_logger(__name__)


# SSL-Zertifikatswarnungen deaktivieren, nur für HTTPS-URLs
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


class DownloadMenu(ListBase):

    busysymbol = symbols.SYMBOL_CLOUD

    def __init__(self, windowmanager,loop):
        super().__init__(windowmanager, loop, "Download")
        self.direct_play_last_folder = False

        self.timeout = False
        self.contrasthandle = False

        self.info_key_left = False

        self.downloading = False
        self.totalsize = 0
        self.lastplayedfile = ""

    def activate(self):

        self.init_finished = False
        self.progress = {}
        self.items = []
        self.selector = False
        self.download = False
        self.website = cfg_online.ONLINE_URL
        self.url = self.website
        self.baseurl, self.basecwd = split_url(self.website)
        self.clearmenu()
        self.appendsymbol(symbols.SYMBOL_CLOUD)
        self.set_window_busy()

        try:
            self.append_busytext("Suche letzten Onlinetitel...")
            self.url = lastplayed_online()
            self.append_busytext(self.url)

            files,directories, temp = self.get_files_and_dirs_from_listing(self.url, ["mp3"],False)

            if files != []:
                logger.info(f"letztes online: {self.url}")

            if not self.url.endswith('/'): 
                self.append_busytext(f"Endet nicht auf /, setze auf Standard")
                self.append_busytext(self.url)
                logger.warning(f"{self.website} nicht in {self.url}")
                self.url = self.website

            elif not self.url.startswith(self.website): 
                self.append_busytext(f"Basis-Website geändert, setze auf Standard")
                self.append_busytext(self.website)
                logger.warning(f"{self.website} nicht in {self.url}")
                self.url = self.website

        except Exception as error:
            logger.error(f"activate: {error}")
            self.append_busytext(f"Fehler: {error}")
            time.sleep(3)
            self.position = -1

        self.loop.run_in_executor(None,self.execute_init)

    def deactivate(self):
        logger.info("deactivate")


    def push_callback(self,lp=False):
        if self.counter in [ -1, -2]:
            self.windowmanager.set_window(self.window_on_back)
        else:
            if not self.is_comment() and not self.is_heading():

                self.loop.run_in_executor(None,self.push_handler)



    def turn_callback(self, direction, key=None):
        super().turn_callback(direction,key)

        #Download abbrechen, falls aktiv
        if self.downloading: self.canceled = True

    def execute_init(self):
        # Verbinungsversuch mit zuletzt abgespieltem Titel, ob vorhanden
        try:
            r = check_url_reachability(self.url)

            if r != 200:
                logger.error(f"execute_init: Verbindungsfehler letzter Onlinetitel {r}: {self.url}")
                self.append_busytext(f"Verbindungsfehler {r}:")
                self.append_busytext(self.url)

                if r > 200:
                    self.append_busytext("Setze auf Standard:")
                    self.append_busytext(self.website)
                    self.url = self.website
                    if not self.check_website_return(self.url):
                        self.append_busytext(f"Gebe auf! Taste drücken!")
                        return
                else:
                    return

            else: #r == 200:
                logger.info(f"execute_init: erfolg {r}: {self.url}")

        except Exception as error:
            logger.error(f"execute_init: exception: Verbindungsfehler {error}")
            self.append_busyerror(f"Verbindungsfehler {error}:")
            self.append_busyerror(self.url)

            self.url = self.website

            # Verbindungsversuch mit Website
            if not self.check_website_return(self.url):
                self.append_busytext(f"Gebe auf! Taste drücken!")
                return

        temp, self.cwd = split_url(self.url)
        print (f"cwd: {self.cwd}")
        self.append_busytext(f"Erfolgreich:")
        self.append_busytext(self.url)

        self.init_finished = True

        self.set_window_busy(False)

        if self.direct_play_last_folder:
            self.direct_play_last_folder = False
            self.url = construct_url(self.cwd,self.baseurl)
            self.items, directories, self.totalsize = self.get_files_and_dirs_from_listing(self.url)
            if not folders:
                self.playfolder()
        else:
            self.on_key_left(clear_busymenu = False)

    def check_website_return(self,url):
        try:
            self.append_busytext("Prüfe URL:")
            self.append_busytext(url)
            r1 = check_url_reachability(url)
            if r1 != 200:
                raise Exception(f"Keine Verbindung! Fehler {r1})")
            else:
                return True
        except Exception as error:
            logger.info(f"check_website_return: exception: {error}")
            self.append_busyerror(f"Fehler: {error}")
            return False


    def downloadfolder(self):
        try:
            self.canceled = False
            self.set_window_busy(render_progressbar = True)

            logger.debug(f"start downloadfolder")
            self.downloading = True
            self.handle_key_back = False
            self.totaldownloaded = 0
            settings.callback_active = True
            uri = get_relative_path(self.basecwd,get_unquoted_uri(self.url))
            logger.debug(f"downloadfolder: uri: {uri}")
            destdir = os.path.join(cfg_file_folder.AUDIO_BASEPATH_BASE,uri)
            logger.debug(f"downloadfolder: destdir: {destdir}")

            try:
                if not os.path.exists(destdir): os.makedirs(destdir)
            except Exception as error:
                logger.error(f"downloadfolder: error {error}")
            for item in self.items:
                self.clear_busymenu()

                url = construct_url_from_local_path(self.baseurl,self.cwd,item)

                logger.debug(f"downloadfolder: url: {url}")

                destination = os.path.join(destdir, stripitem(item))

                logger.debug(f"downloadfolder: destination: {destination}")

                self.append_busytext("Download %2.2d von %2.2d" % (self.items.index(item) + 1,len(self.items))) 
                self.append_busytext(item)
                self.append_busytext("Abbruch mit beliebiger Taste") 

                try:
                    self.download_file(url,destination)
                    if self.canceled:
                        logger.info("downloadfolder: Abbruch")
                        self.append_busytext("Abbruch! Bitte warten...")
                        break

                except Exception as error:
                    logger.error(f"downloadfolder: {error}")

        except Exception as error:
            logger.error(f"downloadfolder: {error}")
            self.append_busyerror(error)
        finally:
            self.set_window_busy(False)
            self.downloading = False
            self.canceled = False
            self.handle_key_back = True
            settings.callback_active = False


    def playfolder(self):
        self.set_window_busy()

        try:
            directory = os.path.join(cfg_file_folder.AUDIO_BASEPATH_ONLINE,get_relative_path(self.basecwd,self.cwd))
            logger.info(f"playfolder {directory}")
            self.append_busytext(f"Abspielen: {directory}")

            create_or_modify_folder_conf(directory,getpos_online(self.baseurl,self.cwd))
        except Exception as error:
            logger.error (error)
            logger.append_busyerror(error)

        self.append_busytext("Speichere Online-Titel in zuletzt gespielt")

        try:
            with open(cfg_file_folder.FILE_LAST_ONLINE,"w") as f:
                f.write(self.url)
        except Exception as error:
            self.append_busyerror(error)
        if not os.path.exists(directory): os.makedirs(directory)

        try:
            filename = os.path.join(directory,"livestream.txt")
            with open(filename,"w") as ofile:
                for item in self.items:
                    additem = construct_url_from_local_path(self.baseurl,self.cwd,item) + '\n'
                    ofile.write(additem)
            self.append_busytext(f"Titelhinzugefügt: {item}")

            foldername = directory[len(cfg_file_folder.AUDIO_BASEPATH_BASE):]
            self.append_busytext(f"Starte playout {foldername}")
            pc_playfolder(foldername)
            self.windowmanager.set_window("idle")
        except Exception as error:
            self.append_busyerror(error)
        finally:
            self.set_window_busy(False)

    def push_handler(self,button = '*'):
        try:

            if not self.init_finished:
                self.windowmanager.set_window(self.window_on_back)
                return

            if self.selector:
                if self.downloading:
                    self.canceled = True
                    return
                logger.debug(f"Untermenü aktiv: {self.position}")
                if self.position == 0:
                    logger.debug(f"Untermenü aktiv: {self.position}, abspielen")
                    self.playfolder()
                elif self.position == 1:
                    logger.debug(f"Untermenü aktiv: {self.position}, starte download")
                    self.loop.run_in_executor(None, self.downloadfolder)
                elif self.position == 2 and self.selector:
                    self.menu = []
                    for items in self.items: self.menu.append([item])
                elif self.position == -1 and self.selector:
                    self.selector = False
                elif self.position == 3:
                    self.set_window_busy()

                    destdir = cfg_file_folder.AUDIO_BASEPATH_BASE + '/' + self.url[len(cfg_online.ONLINE_URL):]
                    if not os.path.exists(destdir):
                        self.append_busytext(f"lokal nicht gefunden: {destdir}")
                    else:
                        try:
                            shutil.rmtree(destdir)
                            self.append_busytext(f"erfolgreich: {destdir}")
                        except FileNotFoundError:
                            self.append_busytext(f"nicht gefunden: {destdir}")
                        except PermissionError:
                            self.append_busytext(f"Fehlerhafte Berechrigung: {destdir}")
                        except Exception as error:
                            self.append_busytext(f"Fehler: {error}")
                    self.set_window_busy(False)

            else:
                if self.downloading:
                    self.canceled = True
                    return

                self.set_window_busy()

                if not self.cwd.endswith('/'): self.cwd += '/'

                selected_item = get_first_or_self(self.menu[self.position])
                self.title = stripitem(selected_item)


                self.append_busytext()
                self.append_busytext(selected_item)

                logger.debug(f"push_handler {selected_item}")

                self.cwd += stripitem(selected_item)

                if not self.cwd.endswith('/'): self.cwd += '/'

                self.url = construct_url_from_local_path(self.baseurl,self.cwd)

                logger.info(f"Wechsle zu {self.url}")
                self.append_busytext("Neue URL:")
                self.append_busytext(self.url)

                self.items,directories,self.totalsize = self.get_files_and_dirs_from_listing(self.url, ["mp3"])

                time.sleep(0.5)

                if directories != []:
                    logger.debug(f"Verzeichnisse gefunden: {directories}")
                    self.create_menu_from_directories(directories)
                else:
                    logger.debug(f"Verzeichnis ausgewählt: {self.cwd}")
                    self.append_busytext("Deteien gefunden")

                    self.selector = True

                    try:
                        posstring = getpos_online(self.baseurl,self.cwd)
                        logger.debug(f"getpos_online: {posstring}")
                        if posstring[0] == "POS":
                            online_file = posstring[1]
                            online_pos = "Zeit:  %s " % (posstring[2])

                        else:
                            online_file = ""
                            online_pos = ""
                    except Exception as error:
                        logger.error(f"getpos_online: {error}")
                        online_file = ""
                        online_pos = ""

                    try:
                        current_pos = "Fortschritt: %s" % (self.progress[self.items[self.position]])
                    except:
                        current_pos = "Fortschritt nicht verfügbar"

                    self.menu = []
                    self.menu.append(["Abspielen"])
                    self.menu.append(["Herunterladen"])
                    self.menu.append(["informationen"])
                    self.menu.append(["Lokal löschen"])
                    self.menu.append([""])
                    #if online_file in self.items:
                    #    self.menu.append(["Aktueller Titel :%2.2d " %  (self.items.index(online_file) + 1)])
                    self.menu.append(["Anzahl Titel :%2.2d " %  (len(self.items))])
                    self.menu.append(["Gesamtgröße %s" % (get_size(self.totalsize))])
                    #self.menu.append([current_pos])
                    #self.menu.append([f"Datei: {online_file}"])
                    #self.menu.append([online_pos])

                self.set_window_busy(False)

        except Exception as error:
            logger.error(f"push_handler: exception: {error}")

        finally:
            time.sleep(0.5)

            self.position = -1

    def on_key_left(self, clear_busymenu = True):
        try:
            self.set_window_busy(clear_busymenu = clear_busymenu, with_symbol = clear_busymenu)

            self.append_busytext("Lese Verzeichnis")

            self.selector = False
            logger.debug(f"derzeitiges Verzeichnis: {self.cwd}")
            last = get_current_directory(self.cwd)

            self.cwd = get_parent_directory(self.cwd)

            self.title = get_current_directory(self.cwd)

            self.append_busytext(self.cwd)

            logger.debug(f"neues Verzeichnis: {self.cwd}")

            if len(self.cwd) <= len(self.basecwd):
                self.cwd = self.basecwd
                last = "_-__"

            self.url = construct_url(self.cwd,self.baseurl)

            self.append_busytext("Prüfe URL")
            self.append_busytext(self.url)

            files, directories,self.totalsize = self.get_files_and_dirs_from_listing(self.url, ["mp3"])

            time.sleep(1)

            self.create_menu_from_directories(directories)

            self.position = find_element_or_formatted_position(self.menu,last)[0]

            try:
                if len(self.cwd) > len (self.basecwd):
                    self.basetitle = self.cwd[pos+1:]
                else:
                    self.basetitle = "Online"
            except Exception as error:
                self.basetitle = self.windowtitle
        finally:
                self.set_window_busy(False)


    def download_file(self,url, local_path):
        # Den Inhalt der Datei herunterladen und den Fortschritt anzeigen
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Überprüfen, ob die Anfrage erfolgreich war

        # Dateigröße ermitteln
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte

        # Datei speichern
        totaldlfile = 0
        with open(local_path, 'wb') as file:
            for data in response.iter_content(block_size):
                totaldlfile += len(data)
                self.totaldownloaded += len(data)
                #dl_progress = totaldlfile / total_size_in_bytes * 100
                try:
                    self.busyprogressbarpos = self.totaldownloaded / self.totalsize # float zahl
                except:
                    pass

                file.write(data)

                self.set_lastbusytextline("%s / %s, %s / %s" % ( get_size(totaldlfile), get_size(total_size_in_bytes), get_size(self.totaldownloaded), get_size(self.totalsize)))

                if self.canceled:
                    break


    def create_menu_from_directories(self,directories):
        for i in range(len(directories)):
            directory = directories[i]
            url = construct_url(directory[0],self.url)
            logger.debug(f"prüfe {directory} {self.url}: {url}")

            if uri_exists_locally(url,self.website,cfg_file_folder.AUDIO_BASEPATH_BASE):
                directories[i][0] = f"{directories[i][0]} \u2302"

            pos = self.get_online_pos(url) #,cfg_file_folder.AUDIO_BASEPATH_BASE)

            if pos != "":
                directories[i].append(pos)
        self.menu = directories



    def get_files_and_dirs_from_listing(self, url, allowed_extensions, get_filesize=True):
        """Extrahiere Dateien und Verzeichnisse aus dem XML-Listing, einschließlich Dateigröße."""
        try:
            logger.debug(f"Verzeichnis-URL: {url}")
            if not url.endswith('/'):
                url += '/'
            parsed_url = urlparse(url)

            # Zertifikatsprüfung nur bei HTTPS-URLs deaktivieren
            response = WebRequest(url)
        except Exception as e:
            # Fehler bei der HTTP-Anfrage abfangen
            logger.info(f"Error fetching {url}: {e}")
            return [], [], 0

        # XML parsen
        root = ET.fromstring(response.get_response_text())

        files = []
        directories = []
        total_size = 0

        self.append_busytext()

        for file_element in root.findall('file'):
            filename = unquote(file_element.text.strip())
            file_size = int(file_element.get('size', 0))
            logger.debug(f"Datei gefunden: '{filename}', Größe: {file_size} bytes")

            if any(filename.endswith(ext) for ext in allowed_extensions):
                self.append_busytext(f"Datei: {filename}", use_last=True)
                files.append(filename)
                total_size += file_size

        for dir_element in root.findall('directory'):
            directory_name = unquote(dir_element.text.strip())
            logger.debug(f"Verzeichnis gefunden: '{directory_name}'")
            self.append_busytext(f"Ordner: {directory_name}")
            directories.append([directory_name, 'x'])

        return files, directories, total_size

    def get_online_pos(self,url):
        try:
            #url = urljoin(url,onlinepath)
            temp, uri = split_url(url)

            if not uri.endswith('/'): uri += '/'
            logger.debug(f"get_pos_online: uri: {uri}, url: {url}")

            folderinfo = getpos_online(self.baseurl,uri)
            logger.debug(f"get_online_pos: folderinfo: {folderinfo}")
            if len(folderinfo) >= 6 and folderinfo[0] == "POS":
                song = int(float(folderinfo[3]))
                length = int(float(folderinfo[4]))
                prozent = (song - 1) / length * 100
                progress = "%2.2d%%"  % (prozent)
                return progress
            else:
                return ""
        except Exception as error:
            logger.error(f"fet_online_pos: {error}")
            return ""
