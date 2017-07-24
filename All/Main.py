from bs4 import BeautifulSoup
from mutagen.easyid3 import EasyID3
import requests
import pafy
import os
import os.path
from pydub import AudioSegment
import sys


TEXT_FILE_ARTIST_NAMES = 'ArtistNames.txt'
TEXT_FILE_SONG_NAMES = 'CompletedSongs.txt'
TITLE_MATCH_ACCURACY = 0.7


def main():
    list_songs_already_downloaded = read_completed_songs_names()
    list_new_song_titles = []
    list_new_artist_names = []

    list_new_song_titles = ["WATCH ME (WHIP / NAE NAE)"]
    list_new_artist_names = ['SILENTÓ ']
    # get_947(list_new_song_titles, list_new_artist_names)

    for song_new in list_new_song_titles:   # Delete all old songs from lists
        if song_new is '':
            list_new_artist_names.pop(list_new_song_titles.index(song_new))
            list_new_song_titles.remove(song_new)
            continue

        is_old_song = False
        for song_old in list_songs_already_downloaded:
            if does_match_compare_old(song_new, song_old, TITLE_MATCH_ACCURACY):
                is_old_song = True
                break

        if is_old_song:
            print('OLD SONG: '+list_new_artist_names[list_new_song_titles.index(song_new)]+' - '+song_new)
            list_new_artist_names.pop(list_new_song_titles.index(song_new))
            list_new_song_titles.remove(song_new)
        else:
            tmp = 'NEWSONG: ' + str(list_new_artist_names[list_new_song_titles.index(song_new)]) + ' - ' + str(song_new)
            tmp = tmp.encode(sys.stdout.encoding, errors='replace')
            print(tmp.decode('utf-8'))

            # print('NEW SONG: ' + str(list_new_artist_names[list_new_song_titles.index(song_new)]) + ' - ' + str(song_new))

    print('\nSEARCHING YOUTUBE\n')
    youtube_best_result_objects = []
    youtube_next_best_result_objects = []
    for song_new in list_new_song_titles:
        youtube_result_objects = get_youtube_result_objects(
            list_new_artist_names[list_new_song_titles.index(song_new)]
            + ' - '
            + song_new
            + ' audio'
        )
        for youtube_result in youtube_result_objects:
            if not (
                does_match_compare_new(
                    list_new_artist_names[list_new_song_titles.index(song_new)] + ' ' + song_new
                    , youtube_result.title
                    , TITLE_MATCH_ACCURACY
                )
            ):
                youtube_result_objects.remove(youtube_result)

        best_youtube_result_object = get_best_youtube_result_object(youtube_result_objects)
        print(best_youtube_result_object.title)
        youtube_result_objects.remove(best_youtube_result_object)
        if len(youtube_result_objects) is 0:
            next_best_youtube_result_object = ''
        elif len(youtube_result_objects) is 1:
            next_best_youtube_result_object = youtube_result_objects[0]
        else:
            next_best_youtube_result_object = get_best_youtube_result_object(youtube_result_objects)

        youtube_best_result_objects.append(best_youtube_result_object)
        youtube_next_best_result_objects.append(next_best_youtube_result_object)

    if len(list_new_artist_names) != len(list_new_song_titles):
        raise RuntimeError('Length of new artist name <> len new song titles')

    if len(list_new_artist_names) != len(youtube_best_result_objects):
        raise RuntimeError('Length of new artist name <> len youtube best result objects')

    if len(list_new_artist_names) != len(youtube_next_best_result_objects):
        raise RuntimeError('Length of new artist name <> len youtube next best result objects')

    print('\nDOWNLOADING YOUTUBE AUDIO\n')
    list_new_songs_downloaded_names = []
    for k in range(0, len(youtube_best_result_objects)):
        video = pafy.new(youtube_best_result_objects[k].link)

        if video.length > 600:
            print('TOO LONG: '+youtube_best_result_objects[k].title)

            video = pafy.new(youtube_next_best_result_objects[k].link)
            if video.length > 600:
                print('STILL TOO LONG: '+youtube_best_result_objects[k].title)
                print('CANCELLING: '+youtube_best_result_objects[k].title)

        best_audio = video.getbestaudio(preftype="m4a")
        song_name_final = list_new_artist_names[k]+' - '+list_new_song_titles[k]
        try:
            best_audio.download(filepath=r"Songs\\" + song_name_final + '.' + best_audio.extension, quiet=False)
            list_new_songs_downloaded_names.append(song_name_final + '.' + best_audio.extension)
        except FileExistsError:
            print("File Already Exists")
            continue

        convert_to_mp3(song_name_final + '.' + best_audio.extension)    # convert to mp3

        audio = EasyID3('Songs-MP3\\' + song_name_final + '.mp3')  # update meta data

        audio["title"] = list_new_song_titles[k]  # .decode('utf-8')
        audio["artist"] = list_new_artist_names[k]  # .decode('utf-8')
        audio.save(v2_version=3)

        file_object = open('CompletedSongs.txt', 'a')
        file_object.write(list_new_song_titles[k] + '\n')
        file_object.close()

        print('\nSUCCESSFULLY COMPLETED: '+song_name_final)


def convert_to_mp3(p_file_name):
    path = os.getcwd()

    m4a_audio = AudioSegment.from_file(path + '\Songs\\' + p_file_name, format="m4a")
    m4a_audio.export(path + '\Songs-MP3\\' + '%s.mp3' % p_file_name[:-4], format='mp3')


def get_best_youtube_result_object(p_objects):
    max_view_index = 0
    for p_k in range(0, len(p_objects)):
        if 'audio' in p_objects[p_k].title.lower():
            return p_objects[max_view_index]

        if p_objects[p_k].views > p_objects[max_view_index].views:
            max_view_index = p_k

    return p_objects[max_view_index]


def get_youtube_result_objects(p_song_name):
    result_objects = []
    song_url = 'https://www.youtube.com/results?search_query='+p_song_name.replace(' ', '+')+'+audio'
    result_page = requests.get(song_url)
    browser = BeautifulSoup(result_page.text, "html.parser")

    failed_counter = 0
    soup_title_result = browser.find_all('h3', class_="yt-lockup-title")
    soup_views_result = browser.find_all(class_="yt-lockup-meta-info")
    while len(result_objects) < 3:

        if len(result_objects)+failed_counter > 15:
            continue

        link = str(soup_title_result[len(result_objects)+failed_counter])
        if (link.find('/watch') < 0) or (link.find(' - Playlist') > -1):
            failed_counter += 1
            continue

        link = link[link.find("/watch") + 9:]
        link = link[:link.find("\"")]
        link = 'https://www.youtube.com/watch?v=' + link

        new_result_obj = YoutubeResultObject(link)

        title = str(soup_title_result[len(result_objects)+failed_counter])
        title = title[title.find('title="')+7:]
        title = title[:title.find('"')]
        new_result_obj.title = title

        views = str(soup_views_result[len(result_objects)+failed_counter])

        if views.find('</li><li>') < 0:
            failed_counter += 1
            continue

        views = views[views.find('</li><li>')+9:]
        views = views[:views.find(' views')]
        views = views.replace(',', '')
        try:
            new_result_obj.views = int(views)
        except ValueError:
            new_result_obj.views = 0

        result_objects.append(new_result_obj)

    return result_objects


def does_match_compare_old(p_new_song, p_old_song, accuracy):
    p_counter = 0
    p_old_song_split = p_old_song.split()
    for k in p_old_song_split:
        p_old_song_split[p_old_song_split.index(k)] = k.lower()

    p_new_song_split = p_new_song.split()
    for k in p_new_song_split:
        p_new_song_split[p_new_song_split.index(k)] = k.lower()

    for p_original_word in p_old_song_split:
        if p_original_word.lower() in p_new_song_split:
            p_counter += 1

    return p_counter / len(p_old_song_split) >= accuracy


def does_match_compare_new(p_new_song, p_old_song, accuracy):
    p_counter = 0
    p_old_song_split = p_old_song.split()
    for k in p_old_song_split:
        p_old_song_split[p_old_song_split.index(k)] = k.lower()

    p_new_song_split = p_new_song.split()
    for k in p_new_song_split:
        p_new_song_split[p_new_song_split.index(k)] = k.lower()

    for p_new_song_word in p_new_song_split:
        if p_new_song_word in p_old_song_split:
            p_counter += 1

    if len(p_new_song_split) is 0:
        raise ValueError('No new song')

    return p_counter / len(p_new_song_split) >= accuracy


def read_completed_songs_names():
        f = open(TEXT_FILE_SONG_NAMES, 'r')

        completed_song_names = []
        for line in f:
            completed_song_names.append(line.replace('\n', ''))
        f.close()

        return completed_song_names


def get_947(p_list_new_song_titles, p_list_new_artist_names):
    print('\nSEARCHING 947.co.za\n')
    html_page_source = requests.get('http://www.947.co.za/')
    html_page_source_soup = BeautifulSoup(html_page_source.text, 'html.parser')

    html_recently_played = html_page_source_soup.find(class_='songs-list')
    html_recently_played_soup = BeautifulSoup(str(html_recently_played), 'html.parser')

    html_song_list = html_recently_played_soup.find_all(class_='play-item')

    for k in range(0, 10):
        new_song_name_full = str(html_song_list[k])
        new_song_name_full = new_song_name_full[new_song_name_full.index('data-track-title=')+len('data-track-title="'):]
        new_song_name_full = new_song_name_full[:new_song_name_full.index('" src=')]

        new_artist_name = new_song_name_full[:new_song_name_full.index(' - ')]
        new_song_title = new_song_name_full[new_song_name_full.index(' - ')+3:]

        new_song_title = new_song_title.replace('&amp;', '&')
        new_song_title = new_song_title.replace('&lt;', '<')
        new_song_title = new_song_title.replace('&gt;', '>')
        new_song_title = new_song_title.replace('&quote;', '"')
        new_song_title = new_song_title.replace('\\', '&')
        new_song_title = new_song_title.replace('/', '&')

        new_artist_name = new_artist_name.replace('&amp;', '&')
        new_artist_name = new_artist_name.replace('&lt;', '<')
        new_artist_name = new_artist_name.replace('&gt;', '>')
        new_artist_name = new_artist_name.replace('&quote;', '"')
        new_artist_name = new_artist_name.replace('\\', '&')
        new_artist_name = new_artist_name.replace('/', '&')

        p_list_new_song_titles.append(new_song_title)
        p_list_new_artist_names.append(new_artist_name)


class YoutubeResultObject:

    def __init__(self, video_link):
        self.link = video_link
        self.views = ''
        self.title = ''


if __name__ == '__main__':
    main()
