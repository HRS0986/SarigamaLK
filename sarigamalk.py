import re
import os
import eyed3
import requests as r
from tqdm import tqdm
from random import choice
from threading import Thread
from art import tprint, text2art
from colorama import init, Fore, Style
from typing import List, Dict, Tuple


# initialize colorama module
init(convert=True)

title_links: Dict[str, Tuple[str]] = {}
playlist_links: Dict[str, Tuple[str]] = {}
artist_links: Dict[str, Tuple[str]] = {}

HOME_URL = 'https://sarigama.lk'
LATEST_URL = 'https://sarigama.lk/playlist/latest/1a08d372-f979-4654-b180-f04e5e10c336'
TRENDING_URL = 'https://sarigama.lk/playlist/trending/22adef1a-18c7-40a4-96d5-8f93ea1d7708'
DEFAULT_ART_URL = 'https://sarigama.lk/img/default/song.png'

CWD: str = os.getcwd()
search_ptn: str = ''
failed = True

'''
Samples
Album Art - https://sarigama.lk/img/songs/appsong-68gtxkku5a5ovgfz.jpg
Playlist - https://sarigama.lk/playlist/appachchi-thaththa/a35b4d46-0632-458d-88c5-6ef41c39413f
Artist - https://sarigama.lk/artist/sanuka-wickramasinghe/a22b4ecf-c1c1-4bed-b6aa-77df464bf02d
Song - https://sarigama.lk/sinhala-song/sanuka-wickramasinghe/dewliye-theme-song/de7c1755-7539-4b9b-966e-2f1f82b914d7
Search - https://sarigama.lk/api/v1/search/mas/{query}
'''

def download(song_url: str, path: str):

    track_data: List[str] = song_url.split('/')
    artist: str = ' '.join(track_data[4].split('-')).title()
    title: str = ' '.join(track_data[5].split('-')).title()
    track_name: str = f'{title} - {artist}.mp3'

    try:
        res = r.get(song_url)

        if res.status_code == 200:

            textRes = res.text
            
            artPTN = r' <meta name="thumbnail" content="([a-z:0-9//\-\.]+)"'
            art_reo = re.compile(artPTN, flags=re.I)
            art_url: str = art_reo.findall(textRes)[0]

            # Album art downloading
            art_name = ''
            art_name = path+'coverart.jpg'

            # if art_url != DEFAULT_ART_URL:
            thread = Thread(target=download_art, args=(art_url, path, art_name))
            thread.start()

            # download_art(art_url, path, art_name)                        

            PTN = r'(https://sarigama\.lk/files/[a-z0-9=\-\?/]+)'
            reo = re.compile(PTN, flags=re.I)
            songlink: str = reo.findall(textRes)[0]
            
            cookies: List[str] = res.headers['Set-Cookie'].split(';')
            XSRF: str = cookies[0]
            LRVL: str = cookies[3].split()[1]
            cookies: str = f'{XSRF};{LRVL};'
            headers: Dict[str, str] = {'cookie': cookies}

            mp3 = r.get(songlink, headers=headers, stream=True)

            if mp3.status_code == 200:

                mp3_length = int(mp3.headers['content-length'])
                block_size: int = 1024

                print(Fore.CYAN+f'\nDownloading {track_name}')
                bar = tqdm(total=mp3_length, unit='iB', unit_scale=True)

                track_name: str = path + '\\' + track_name
               
                with open(track_name, 'wb') as song:
                    for data in mp3.iter_content(block_size):
                        bar.update(len(data))
                        song.write(data)
                    bar.close()
                
                if mp3_length != 0 and bar.n != mp3_length:
                    print(Fore.RED+"ERROR, Something went wrong"+Fore.RESET)

                else:
                    thread.join()
                    setID3(track_name, title, artist, art_name)

                    if art_url != DEFAULT_ART_URL:                
                        os.remove(art_name)

                    print(Fore.GREEN+f'Downloaded {track_name} \n'+Fore.RESET)
                    global failed
                    failed = False

            else:
                print(Fore.RED+f'Error Occured while requesting mp3 : {mp3.status_code}'+Fore.RESET)
                main_input()            

            # main_input()

        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)
            main_input()

    except KeyboardInterrupt:
        print(Fore.RED+'\n[!] Task cancelled by user.'+Fore.RESET)
        main_input()

    except Exception as e:
        print(Fore.RED+f'Somthing went wrong : {e}'+Fore.RESET)
        main_input()


def download_art(art_url: str, path: str, art_name: str):
    try:
        if art_url != DEFAULT_ART_URL:
            art = r.get(art_url)
            if art.status_code == 200:
                with open(art_name, 'wb') as cover:
                    cover.write(art.content)
 
    except Exception as e:
        pass


# Get download path from user
def save_path() -> str:

    try:
        print(Fore.LIGHTYELLOW_EX+'[!] Enter path to save mp3. Just press enter to save mp3 in current directory.')
        path: str = input(Fore.LIGHTGREEN_EX+'[+] Save Path (without file name) :').strip()

        if not path:
            return CWD

        is_valid_path = os.path.isdir(path)

        if not is_valid_path:
            os.mkdir(path)
        
        return path

    except KeyboardInterrupt:
        os.system('CLS')
        exit()

    except OSError as e:
        print(Fore.RED+'Error : {e}\n'+Fore.RESET)
        save_path()


def setID3(mp3_path:str, title:str, artist:str, cover_art_path:str):    
    
    mp3 = eyed3.load(mp3_path)
    mp3.tag._images.remove('')   
    mp3.tag.title = title
    mp3.tag.artist = artist
    mp3.tag.album = title

    if cover_art_path: 
        # 3 is for front cover
        mp3.tag.images.set(3, open(cover_art_path,'rb').read(), 'image/jpeg')

    mp3.tag.save()


# Verify the command entered by user in main input section
def verify_command(url: str) -> str:

    # 'https://sarigama.lk/artist/sanuka-wickramasinghe/a22b4ecf-c1c1-4bed-b6aa-77df464bf02d'
    ARTIST_PTN = r'https://sarigama\.lk/artist/[a-z0-9\-]+/[a-z0-9\-]+'
    artist_regex = re.compile(ARTIST_PTN, flags=re.I)

    # 'https://sarigama.lk/sinhala-song/sanuka-wickramasinghe/dewliye-theme-song/de7c1755-7539-4b9b-966e-2f1f82b914d7'
    SONG_PTN = r'https://sarigama\.lk/sinhala-song/[a-z0-9\-]+/[a-z0-9\-]+/[a-z0-9\-]+'
    song_regex = re.compile(SONG_PTN, flags=re.I)

    # 'https://sarigama.lk/playlist/appachchi-thaththa/a35b4d46-0632-458d-88c5-6ef41c39413f'
    PLAYLIST_PTN = r'https://sarigama\.lk/playlist/[a-z0-9\-]+/[a-z0-9\-]+'
    playlist_regex = re.compile(PLAYLIST_PTN, flags=re.I)

    searchPTN = r'search ([a-z ]+ ?)'
    search_regex = re.compile(searchPTN, flags=re.I)

    if artist_regex.match(url):
        return 'Artist'

    if song_regex.match(url):
        return 'Song'

    if playlist_regex.match(url):
        return 'Playlist'

    if url.lower() == 'trending':
        return 'Trending'

    if url.lower() == 'latest':
        return 'Latest'

    if url.lower() == 'playlists':
        return 'Playlists'

    if url.lower() == 'top artists':
        return 'Top'

    if url.lower() == 'help':
        return 'Help'

    # Search Query Verify
    if search_regex.match(url):
        qtype = 's'
        qstring: str = search_regex.findall(url)[0]
        query = qstring
        
        if qstring.split()[-1] == 'a':
            qtype = 'a'
            query = qstring[:-2]

        global search_ptn
        search_ptn = query+'-'+qtype        
        return 'Search'

    else:
        return 'Invalid'


# Extract song titles from artist/playlist page 
# Store song title and it's url (and artist if a playlist) in title_links dictionary
def extract_songs_titles(artist_url: str, playlist: bool = False):
    
    try:
        res = r.get(artist_url)

        if res.status_code == 200:

            textRes = res.text
            
            PTN = r'<a target="_blank" href="(https://sarigama.lk/sinhala-song/[a-z0-9\.:\/-]+)'
            reo = re.compile(PTN, flags=re.I)
            songlinks = reo.finditer(textRes)

            global title_links
            
            for i, link in enumerate(songlinks, 1):
                title1: str = link.groups()[0]
                title2: str = title1.split('/')[5]
                title: str = ' '.join(title2.split('-')).title()
                
                if playlist:
                    artist: str = ' '.join(title1.split('/')[4].split('-')).title()                                    
                    title_links[str(i)] = (title, link.groups()[0], artist)
                
                else:
                    title_links[str(i)] = (title, link.groups()[0])

        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)
            main_input()

    except r.exceptions.ConnectionError as e:
        raise Exception(Fore.RED+f'Check Your Internet Connection'+Fore.RESET)


# Display artist's songs and perform downloads
def artist_action(artist_url: str):

    artist: str = ' '.join(artist_url.split('/')[4].split('-')).title()

    try:
        extract_songs_titles(artist_url)

        print(Fore.LIGHTYELLOW_EX)
        print('\n[!] Artist :', artist)
        print('[!] Available Song List')

        for k, v in title_links.items():
            print(f'\t{k}.{v[0]}')

        print('\n[!] Enter song number that you wish to download. Enter 0 to download all')

        validate_song_no()

    except Exception as e:
        print('Error:', e)


# Validate song number in playlist or artist song list
def validate_song_no():

    try:
        print(Fore.LIGHTGREEN_EX)
        track_no = input('[+] Song Numbers:').strip().split()
       
        global playlist_links
        global artist_links

        if track_no[0].lower() == 'main':            
            playlist_links.clear()
            artist_links.clear()
            main_input()

        else:        
           
            if len(track_no) == 1 and track_no[0] not in title_links.keys():
                print(Fore.RED+'[!] Invalid Number\n'+Fore.RESET)
                validate_song_no()

            else:

                global path
                path = save_path()

                        
                if track_no[0] == '0':
                    for song in title_links.values():
                        link = song[1]
                        download(link, path)
                        
                else:
                    for n in track_no:                    
                        if n in title_links.keys():
                            download(title_links[n][1], path)                            

                if failed:
                    print(Fore.RED+'[!] Invalid Numbers\n'+Fore.RESET)
                    validate_song_no()

                else:
                    main_input()

    except KeyboardInterrupt:
        os.system('CLS')
        exit()


# Extract playlists from HOME_URL
def extract_playlists():

    PTN = r'<a href="(https://sarigama\.lk/playlist/[a-z0-9\-/\.]+)" class="play"'
    reo = re.compile(PTN, flags=re.I)

    try:
        res = r.get(HOME_URL)

        if res.status_code == 200:
            textRes = res.text
            pl = reo.finditer(textRes)

            global playlist_links

            print(Fore.LIGHTYELLOW_EX+'[!] Playlists From Sarigama.LK')
            for i, link in enumerate(pl, 1):
                playlist_url: str = link.groups()[0]
                playlist_name: str = ' '.join(playlist_url.split('/')[4].split('-')).title()
                no = str(i)
                playlist_links[no] = (playlist_name, playlist_url)
                print(f'\t{no}.{playlist_name}')

            validate_no()

        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)

    except Exception as e:
        print(Fore.RED+f'[!] Something went wrong : {e}'+Fore.RESET)


# Display help 
def usage():
    
    print(Fore.LIGHTYELLOW_EX+'\n ----------------------------------[ HOW TOT USE ]----------------------------------\n')
    print('   [!] Downloading')
    print("      [!] Enter song url to download song directly.")
    print("      [!] Enter playlist url to download songs in playlist")
    print("      [!] Enter artist url to download songs of artist\n\n")
    print("   [!] Brwosing")
    print("      [!] Enter 'playlists' to get list of playlists")
    print("      [!] Enter 'trending' to get list of trending songs on sarigama.lk")
    print("      [!] Enter 'latest' to get list of latest songs on sarigama.lk")
    print("      [!] Enter 'top artists' to get list of top artists on sarigama.lk\n\n")
    print("   [!] Searching Songs And Artists")
    print("      [!] Enter 'search <query>' to search song")
    print("         [!] Ex:- Enter search sar to search songs starting with 'sar'\n")    
    print("      [!] Enter 'search <query> a' to search artist ")
    print("         [!] Ex:- Enter search sar a to search artists starting with 'sar'\n\n")
    print("   [!] Enter 'exit' to exit")
    print("   [!] Enter 'main' to return to main input")
    print("\n-------------------------------[ By Hirusha Fernando ]-------------------------------")

    main_input()


# Display playlists's songs and perform downloads
def playlist_action(playlist_url: str):

    playlist: str = ' '.join(playlist_url.split('/')[4].split('-')).title()

    try:
        extract_songs_titles(playlist_url, True)

        print(Fore.LIGHTYELLOW_EX)
        print('\n[!] Playlist :', playlist)
        print('[!] Available Song List')

        for k, v in title_links.items():            
            print(f'\t{k}.{v[0]} By {v[2]}')

        print('\n[!] Enter song number that you wish to download. Enter 0 to download all')

        validate_song_no()

    except Exception as e:
        print(Fore.RED+f'[!] Error : {e}\n'+Fore.RESET)
        main_input()


# Validate user input when playlist selection or top artist selection
def validate_no(artist: bool = False):

    global playlist_links
    global artist_links

    param = artist
    check_in: dict = artist_links if artist else playlist_links
    action = artist_action if artist else playlist_action
    disp: str = 'Artist' if artist else 'Playlist'

    try:
        print(Fore.LIGHTGREEN_EX)
        n = input(f'[!] {disp} Number : ').strip()
        
        if n.lower() == 'main':            
            playlist_links.clear()
            artist_links.clear()
            main_input()

        elif not n in check_in.keys():
            print(Fore.RED+'[!] Invalid Number\n'+Fore.RESET)
            validate_no(param)

        else:            
            action(check_in[n][1])

    except KeyboardInterrupt:
        os.system('CLS')
        exit()


# Extract top artist names and urls in Sarigama.LK   
def top_artist():

    PTN = r'<a href="(https://sarigama\.lk/artist/[a-z0-9\-]+/[a-z0-9\-]+)" class="hidden'
    reo = re.compile(PTN, flags=re.I)

    try:
        res = r.get(HOME_URL)

        if res.status_code == 200:
            textRes = res.text

            global artist_links

            artists = reo.finditer(textRes)

            print(Fore.LIGHTYELLOW_EX+'[!] Top Artists On Sarigama.LK')
            for i, artist in enumerate(artists, 1):
                artist_url: str = artist.groups()[0]
                name: str = ' '.join(artist_url.split('/')[4].split('-')).title()
                no = str(i)
                artist_links[no] = (name, artist_url)
                print(f'\t{i}.{name}')

            validate_no(True)

        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)

    except Exception as e:
        print(Fore.RED+f'[!] Something went wrong : {e}'+Fore.RESET)


# Invalid input in main_input() function
def invalid():
    print(Fore.RED+'[!] Invalid Input\n')
    main_input()


def search():    
    qstring: str = search_ptn.split('-')[0]
    qtype: str = search_ptn.split('-')[1]
    query_url = f'https://sarigama.lk/api/v1/search/mas/{qstring}'

    try:
        res = r.get(query_url)

        if res.status_code == 200:
            json_res = res.json()
            
            print(Fore.LIGHTYELLOW_EX+'\n[!] Search Result:')

            result_count = 1

            if qtype == 's' :               
                songs: List[dict] = json_res['songs']['hits']['hits']
                for i,song in enumerate(songs, 1):
                    track_info: dict = song['_source']
                    title: str = track_info['title']
                    track_url: str = track_info['url']
                    track_artist_data = track_info['main_artists']
                    track_artists = []

                    for x in track_artist_data:
                        track_artists.append(x['name'])

                    track_artists: str = ' And '.join(track_artists)
                    title_links[str(i)] = (title, track_url, track_artists)

                    print(f'\t{i}.{title} By {track_artists}')
                                
                if len(title_links) == 0:
                    result_count = 0
                    print('[!] Nothing Found')
                
                if result_count == 1:
                    validate_song_no()
                else:
                    main_input()
                    
            else:
                artists: List[dict] = json_res['artists']['hits']['hits']
                for i,artist in  enumerate(artists, 1):
                    artist_info: dict = artist['_source']
                    name: str = artist_info['name']
                    artist_url: str = artist_info['url']
                    artist_links[str(i)] = (name, artist_url)

                    print(f'\t{i}.{name}')

                if len(artist_links) == 0:
                    result_count = 0
                    print('[!] Nothing Found')

                if result_count == 1:
                    validate_no(True)
                else:
                    main_input()

        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)
            main_input()

    except KeyboardInterrupt:
        os.system('CLS')
        exit()

    except Exception as e:
        print(Fore.RED+f'[!] Something went wrong : {e}'+Fore.RESET)
        main_input()


def download_with_direct_link(url: str):
    path: str = save_path()
    download(url, path)
    main_input()


def main_input():

    try:
        print(Fore.LIGHTGREEN_EX)
        sarigamalk_url = input('[+] Sarigama.LK : ').strip()

        actions = {
            'Artist': artist_action, 
            'Song': download_with_direct_link, 
            'Playlist': playlist_action,
            'Search': lambda x: search(),
            'Top': lambda x: top_artist(), 
            'Invalid': lambda x: invalid(),
            'Trending': lambda x: playlist_action(TRENDING_URL), 
            'Latest': lambda x: playlist_action(LATEST_URL), 
            'Playlists': lambda x: extract_playlists(),            
            'Help':lambda x: usage(),
            'Exit':lambda x: exit()
            }

        url_status = verify_command(sarigamalk_url)
        actions[url_status](sarigamalk_url)

    except KeyboardInterrupt:
        os.system('CLS')
        exit()


# Statring function
def display_title():
    os.system('CLS')
    print(choice([Fore.LIGHTMAGENTA_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX]))
    tprint('Sarigama.LK', choice(["clossal", "banner3-d", "georgiall"]))
    print(Fore.RESET)
    print(Fore.LIGHTYELLOW_EX+"[!] Enter 'help' to get help\n")
    main_input()


if __name__ == '__main__':    
    display_title()
