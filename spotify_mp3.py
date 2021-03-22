import spotipy
from spotipy.oauth2 import SpotifyOAuth
from youtube_search import YoutubeSearch
import youtube_dl
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import eyed3
import urllib.request
import shutil
import googleapiclient.discovery


def spotify_txt():
    search_title = []
    other_info = []
    # user choice time
    toggle = int(input("Do you want your favorite songs saved (1), do you have a link to a playlist (2),"
                       " or do you have a link to an album (3)?\n"))
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="1bfd06968a4d44ff8ffb937ab7301f06",
                                                   client_secret="95e85447f3a444f5b1fd64843d58f8a9",
                                                   redirect_uri="http://localhost:8888/callback",
                                                   scope="user-library-read"))
    # favorite songs list
    if toggle == 1:
        n = 0
        title = {'name': 'Liked Songs'} # sets playlist title to "Liked Songs"
        while n > -1:
            results = sp.current_user_saved_tracks(limit=50, offset=50*n) # gets the list of tracks from spotify 50 at a time (maximum allowed by the spotify API)
            for idx, item in enumerate(results['items']):
                track = item['track'] # saves the information about the track to search_title and other_info arrays
                search_title.append(track['artists'][0]['name'] + " – " + track['name'] + ' audio')
                other_info.append({'name': track['name'], 'artist': track['artists'][0]['name'],
                                   'album': track['album']['name'], 'track_number': track['track_number'],
                                   'image_location': track['album']['images'][0]['url']})
            n += 1
            if len(results['items']) < 50: # stops sending requests to the API once a set of songs less than 50 has been recieved, meaning the end of the playlist has been reached
                break
    # playlist w/ identifier code
    elif toggle == 2:
        n = 0
        uri = input("Please input the playlist identifier code (i.e. 78pJV5u1zBe6vCrbNcx7Ic)\n")
        title = sp.playlist(uri, fields='name') # sets the playlist name to whatever name it has on spotify
        while n > -1:
            results = sp.playlist_items(playlist_id=uri,
                                        fields='items(track(name,artists(name),album(name,images),track_number))',
                                        limit=100, offset=100*n) # gets the information shown by "fields" 100 songs at a time
            for idx, item in enumerate(results['items']):
                track = item['track']
                search_title.append(track['artists'][0]['name'] + ' ' + track['name'] + ' audio')
                other_info.append({'name': track['name'], 'artist': track['artists'][0]['name'],
                                   'album': track['album']['name'], 'track_number': track['track_number'],
                                   'image_location': track['album']['images'][0]['url']})
            if len(results['items']) < 100:
                break
            n += 1
    # album w/ identifier code
    # functionally almost identical to the playlist finder, just taking an album URI instead of a playlist URI
    elif toggle == 3:
        uri = input("Please input the album identifier code (i.e. 1kwAv74rVTTGMpawGsXtiE)\n")
        title = sp.album(uri) 
        results = sp.album_tracks(album_id=uri, limit=50)
        for idx, item in enumerate(results['items']):
            search_title.append(item['artists'][0]['name'] + ' ' + item['name'] + ' audio')
            other_info.append({'name': item['name'], 'artist': item['artists'][0]['name'],
                               'album': title['name'], 'track_number': item['track_number'],
                               'image_location': title['images'][0]['url']})
    return search_title, toggle, title, other_info


def youtube_search(search_list):
    url_list = []
    x = 1
    for terms in search_list:
        try: # uses the web scraper version of Youtube search to try and find each of the things in the search list, which is just the search_title array from spotify_txt
            results = YoutubeSearch(terms.lower(), max_results=1).to_dict()
            print(str(x) + ' ' + results[0]['title'])
            url_list.append("https://www.youtube.com" + results[0]['url_suffix'])
            x += 1
        except: # if the web scraper version fails, as it sometimes does, it then goes to the official Google Youtube API (however, this version has a limit to the number of requests you can send in a day, so it doesn't work for massive amounts of songs)
            api_service_name = "youtube"
            api_version = "v3"
            DEVELOPER_KEY = "AIzaSyCGo4DdnZwC9PgJLQyozcI7spNEkMwQYj8"

            youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

            request = youtube.search().list(
                part="snippet",
                maxResults=1,
                q=terms,
                type="video"
            )
            response = request.execute()
            print("https://www.youtube.com/watch?v=" + response['items'][0]['id']['videoId'])
            url_list.append("https://www.youtube.com/watch?v=" + response['items'][0]['id']['videoId'])
    return url_list


def youtube_download(song_list, playlist, urls):
    n = 0
    filepaths = []
    for links in urls:
        ydl_opts = {
            'format': 'mp4',
            'outtmpl': "C:\\Users\\" + os.getlogin() + "\\Desktop\\" + playlist + "\\" + song_list[n] + '.mp4' # uses song information to create a unique filepath to download the .mp4 files to
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([links]) # uses the youtube downloader to download each of the urls that were found using the youtube_search function as an .mp4 file
        filepaths.append("C:\\Users\\" + os.getlogin() + "\\Desktop\\" + playlist + "\\" + song_list[n] + '.mp4') # attaches the file path to the .mp4 file to the array, so that future steps can find the file again
        n += 1
    return filepaths


def music_convert(filepath): # this function just takes in a list of .mp4 files, opens them into the python program, finds the audio track, and saves the audio track as a .mp3 file with 256kbps bitrate
    for mp4_file in filepath:
        video_clip = VideoFileClip(mp4_file)
        audio_clip = video_clip.audio
        mp3_result = mp4_file.replace('.mp4', '.mp3')
        audio_clip.write_audiofile(filename=mp3_result, bitrate='256k')
        audio_clip.close()
        video_clip.close()
        os.remove(mp4_file)


def album_art(url, folder, song_title): # this function downloads the album art, found using the spotify album art URLs, and saves the files to a temporary folder that is deleted at the end of the program
    file_name = "C:\\Users\\" + os.getlogin() + "\\Desktop\\" + folder + "\\album_art\\"
    song_title = song_title.replace('.mp3', '')
    if not os.path.isdir(file_name):
        os.makedirs(file_name)
    file_name = file_name + song_title + ".jpg"
    urllib.request.urlretrieve(url, file_name)
    return file_name


def add_mp3_tags(tags, collection): # this function adds MP3 tags to all of the songs, allowing Itunes or other music platforms to properly display cover art, song titles, album titles, artist names, and track numbers

    audiofile = eyed3.load('C:\\Users\\' + os.getlogin() + '\\Desktop\\' + collection + '\\' + tags['mp3_title'])
    if audiofile.tag is None:
        audiofile.initTag()
    audiofile.tag.artist = tags['artist']
    audiofile.tag.album = tags['album']
    audiofile.tag.title = tags['name']
    audiofile.tag.track_num = tags['track_number']
    audiofile.tag.images.set(0, open(tags['image_location'], 'rb').read(), 'image/jpeg')
    audiofile.tag.save(version=eyed3.id3.ID3_V2_3)


save = spotify_txt()  # return value from spotify_txt function
sanitize = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']  # cleans the file names of bad characters
saved_or_other = save[1]  # toggle value from spotify_txt
collection_name = save[2]['name']  # playlist name from spotify_txt
mp3_tags = save[3]  # tags from spotify_txt
songs = []  # holds sanitized file names

iterate = 0  # iterator
for media in save[0]: # cleans up the search_title array by removing any characters that Windows has trouble using in a filename
    for value in sanitize:
        media = media.replace(value, '')
    songs.append(media)
    mp3_tags[iterate].update({'mp3_title': media + '.mp3'})
    iterate += 1

for value in sanitize: # cleans up the playlist title to do the same thing as above
    collection_name = collection_name.replace(value, '')

files = youtube_download(songs, collection_name, youtube_search(songs)) # downloads the files and then converts them to mp3 
music_convert(files)

iterate = 0  # counts through the items in the mp3_tags array
for items in mp3_tags:
    mp3_tags[iterate].update({'image_location': album_art(items['image_location'], collection_name,
                                                          items['mp3_title'])}) # replaces the 'image_location' url with a filepath to the temporary cover art file
    iterate += 1

for i in mp3_tags: # adds the mp3 tags to each item in the array
    add_mp3_tags(i, collection_name)

shutil.rmtree('C:\\Users\\' + os.getlogin() + '\\Desktop\\' + collection_name + '\\album_art') # deletes the temporary cover art folder
