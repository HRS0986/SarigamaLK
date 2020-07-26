import requests as r
import re
import os
from colorama import init, Fore, Style
from tqdm import tqdm
from art import tprint


init(convert=True)

title_links = {}
playlist_links = {}
top_artist_links = {}

HOME_URL = 'https://sarigama.lk'

def download(song_url=''):

    track_data = song_url.split('/')
    artist = ' '.join(track_data[4].split('-')).title()
    title = ' '.join(track_data[5].split('-')).title()
    track_name = f'{title} - {artist}.mp3'

    try:
        res = r.get(song_url)

        if res.status_code == 200:
            
            textRes = res.text
            PTN = r'(https://sarigama.lk/files/[a-z0-9=\-\?/]+)'
            reo = re.compile(PTN, flags=re.I)
            songlink = reo.findall(textRes)[0]

            cookies = res.headers['Set-Cookie'].split(';')
            XSRF = cookies[0]
            LRVL = cookies[3].split()[1]
            cookies = f'{XSRF};{LRVL};'
            headers = {'cookie':cookies}
            
            mp3 = r.get(songlink, headers=headers, stream=True)

            if mp3.status_code == 200:
                
                mp3_length = int(mp3.headers['content-length'])
                block_size = 1024

                print(Fore.CYAN+f'\nDownloading {track_name}')
                bar=tqdm(total=mp3_length, unit='iB', unit_scale=True)

                with open(track_name, 'wb') as song:
                    for data in mp3.iter_content(block_size):
                        bar.update(len(data))
                        song.write(data)
                    bar.close()

                if mp3_length != 0 and bar.n != mp3_length:
                    print(Fore.RED+"ERROR, Something went wrong"+Fore.RESET)

                else:
                    print(Fore.GREEN+f'{track_name} Downloaded.'+Fore.RESET)

            else:
                print(Fore.RED+f'Error Occured while requesting mp3 : {mp3.status_code}'+Fore.RESET)

        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)

    except Exception as e:
        print(Fore.RED+f'Somthing went wrong : {e}'+Fore.RESET)


def check_url(url) -> str:
    
    #'https://sarigama.lk/artist/sanuka-wickramasinghe/a22b4ecf-c1c1-4bed-b6aa-77df464bf02d'
    ARTIST_PTN = r'https://sarigama\.lk/artist/[a-z0-9\-]+/[a-z0-9\-]+'
    artist_regex = re.compile(ARTIST_PTN, flags=re.I)

    #'https://sarigama.lk/sinhala-song/sanuka-wickramasinghe/dewliye-theme-song/de7c1755-7539-4b9b-966e-2f1f82b914d7'
    SONG_PTN = r'https://sarigama\.lk/sinhala-song/[a-z0-9\-]+/[a-z0-9\-]+/[a-z0-9\-]+'
    song_regex = re.compile(SONG_PTN, flags=re.I)

    #'https://sarigama.lk/playlist/appachchi-thaththa/a35b4d46-0632-458d-88c5-6ef41c39413f'
    PLAYLIST_PTN = r'https://sarigama\.lk/playlist/[a-z0-9\-]+/[a-z0-9\-]+'
    playlist_regex = re.compile(PLAYLIST_PTN, flags=re.I)

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
    
    else:
        return 'Invalid'
    

# Extract song titles from artist/playlist page and store song title and it's url (and artist if a playlist) in title_links dictionary
def extract_songs_titles(artist_url, playlist=False):

    try:
        res = r.get(artist_url)

        if res.status_code == 200:
        
            textRes = res.text

            PTN = r'<a target="_blank" href="([a-z0-9\.:\/-]+)'
            reo = re.compile(PTN, flags=re.I)
            songlinks = reo.finditer(textRes)
            
            global title_links

            for i,link in enumerate(songlinks, 1):
                title = ' '.join( link.groups()[0].split('/')[5].split('-') ).title()                
                if playlist:
                    artist = ' '.join( link.groups()[0].split('/')[4].split('-') ).title()
                title_links[str(i)] = (title, link.groups()[0], artist)

        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)

    except Exception as e:
        raise Exception(Fore.RED+'Check Your Internet Connection'+Fore.RESET)


# Display artist's songs and perform downloads
def artist_action(artist_url):
    
    artist = ' '.join(artist_url.split('/')[4].split('-')).title()

    try:
        extract_songs_titles(artist_url)

        print(Fore.LIGHTYELLOW_EX)
        print('\n[!] Artist :', artist)
        print('[!] Available Song List')
              
        for k,v in title_links.items():
            print(f'\t{k}.{v[0]}')

        print(Fore.LIGHTYELLOW_EX+'\n[!] Enter song number that you wish to download. Enter 0 to download all')

        validate_song_no()
        
    except Exception as e:
        print('Error:',e)


def validate_song_no():
    
    try:
        print(Fore.LIGHTGREEN_EX)
        track_no = input('[+] Song Number:').strip()

        if track_no in title_links.keys():
            download(title_links[track_no][1])

        elif track_no == '0':
            for song in title_links.values():
                link = song[1]
                download(link)

        else:
            print(Fore.RED+'[!] Invalid Number\n'+Fore.RESET)
            validate_song_no()

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
            for i,link in enumerate(pl,1):
                playlist_url = link.groups()[0]
                playlist_name = ' '.join(playlist_url.split('/')[4].split('-')).title()
                no = str(i)
                playlist_links[no] = (playlist_name, playlist_url)
                print(f'\t{no}.{playlist_name}')

            validate_no()
           
        else:
            print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)
        

    except Exception as e:
        print(Fore.RED+f'[!] Something went wrong : {e}'+Fore.RESET)
        

# Display playlists's songs and perform downloads
def playlist_action(playlist_url):
    
    playlist = ' '.join(playlist_url.split('/')[4].split('-')).title()

    try:
        extract_songs_titles(playlist_url, True)

        print(Fore.LIGHTYELLOW_EX)
        print('\n[!] Playlist :', playlist)
        print('[!] Available Song List')
              
        for k,v in title_links.items():
            print(f'\t{k}.{v[0]} By {v[2]}')

        print(Fore.LIGHTYELLOW_EX+'\n[!] Enter song number that you wish to download. Enter 0 to download all')

        validate_song_no()

    except Exception as e:
        print('Error:',e)


# Validate user input when playlist selection or top artist selection
def validate_no(artist=False):
    
    check_in = top_artist_links if artist else playlist_links
    action = artist_action if artist else playlist_action
    disp = 'Artist' if artist else 'Playlist'

    try:
        print(Fore.LIGHTGREEN_EX)
        n = input(f'[!] {disp} Number : ').strip()
        
        if not n in check_in.keys():
            print(Fore.RED+'[!] Invalid Number\n'+Fore.RESET)
            validate_no()

        else:
            action(check_in[n][1])

    except KeyboardInterrupt:
        os.system('CLS')
        exit()


def top_artist():

    PTN = r'<a href="(https://sarigama\.lk/artist/[a-z0-9\-]+/[a-z0-9\-]+)" class="hidden'
    reo = re.compile(PTN, flags=re.I)

    try:
        res = r.get(HOME_URL)

        if res.status_code == 200:
            textRes = res.text
            
            global top_artist_links 

            artists = reo.finditer(textRes)

            print(Fore.LIGHTYELLOW_EX+'[!] Top Artists On Sarigama.LK')
            for i,artist in enumerate(artists, 1):
                artist_url = artist.groups()[0]
                name = ' '.join(artist_url.split('/')[4].split('-')).title()
                no = str(i)
                top_artist_links[no] = (name, artist_url)
                print(f'\t{i}.{name}')

            validate_no(True)

        else:
             print(Fore.RED+f'Error Occured while requesting given link : {res.status_code}'+Fore.RESET)
    
    except Exception as e:
        print(Fore.RED+f'[!] Something went wrong : {e}'+Fore.RESET)

        
if __name__ == '__main__':

    os.system('CLS')
    print(Fore.LIGHTMAGENTA_EX)
    tprint('Sarigama.LK',"clossal")
    print(Fore.RESET)
    
    try:
        print(Fore.LIGHTGREEN_EX)
        sarigamalk_url = input('[+] Sarigama.LK : ').strip()

        actions = {'Artist':artist_action, 'Song':download, 'Playlist':playlist_action, 'Top':lambda x: top_artist(), 'Invalid':lambda x: print(Fore.RED+'[!] Invalid URL.'+Fore.RESET), 'Trending':lambda x: playlist_action('https://sarigama.lk/playlist/trending/22adef1a-18c7-40a4-96d5-8f93ea1d7708'), 'Latest':lambda x: playlist_action('https://sarigama.lk/playlist/latest/1a08d372-f979-4654-b180-f04e5e10c336'), 'Playlists':lambda x: extract_playlists()}

        url_status = check_url(sarigamalk_url)
        actions[url_status](sarigamalk_url)

    except KeyboardInterrupt:
        os.system('CLS')
        exit()

    
        
    
    
    













