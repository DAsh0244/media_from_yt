#! /usr/bin/env python3
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import youtube_dl
from pydub import AudioSegment
from mutagen.mp3 import EasyMP3 as MP3
import re
import sys
import os.path as osp
import os

OUTPUTDIR = 'output'

class MyLogger(object):
    # def __init__(self, level='debug', stderr=sys.stderr, stdout=sys.stdout):
        # self.level = level
        # self.stderr = stderr
        # self.stdout = stdout    
    def debug(self, msg):
        pass
    warning = error = debug
    # def debug(self, msg):
        # print('[debug]',msg)
    # def warning(self, msg):
        # print('[warning]',msg)
    # def error(self, msg):
        # print('[error]',msg)

def my_hook(d):
    """
    d will have keys:
    
    [downloading]
    'status'
    'downloaded_bytes'
    'total_bytes'
    'tmpfilename'
    'filename'
    'eta'
    'speed'
    'elapsed'
    '_eta_str'
    '_percent_str'
    '_speed_str'
    '_total_bytes_str'
    
    [finished]
    'filename'
    'status'
    'total_bytes'
    '_total_bytes_str'
    """
    if d['status'] == 'finished':
        print('\nDone downloading, now converting ...')
    else:
        # print(d.keys())
        print('\r{}:{} -- ({})'.format(d['filename'],round(d['downloaded_bytes']/d['total_bytes']*100,2), round(d['elapsed'],3)),end='')


ydl_opts = {
    'format': 'bestaudio/best',
    # 'verbose': 'True',
    # 'verbose': 'False',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '2',
        # 'preferredquality': '128k',
    }],
    # 'logger': MyLogger(),
    # 'progress_hooks': [my_hook],
}


# regex for parsing track titles -- todo: look into 'chapters' meta data
# 
# listings = [ 
# '01 – Culture Shock 0:00\n'\
# '02 – Light 4:42\n'\
# '03 – Florence 8:32\n'\
# '04 – Nightmare 11:43\n'\
# '05 – Storm 15:48\n'\
# '06 – Bittersweet 19:18\n'\
# '07 – Symmetry 23:12\n'\
# '08 – Ivory 25:09\n'\
# '09 – Paradise 28:15\n'\
# '10 – Amour 32:32\n'\
# '11 – Crush 36:13\n'\
# '12 – Euphoria 40:14',
#
# '00:00 - Centred and One\n'\
# '05:09 - Outspoken\n'\
# '10:23 - To Surive\n'\
# '15:45 - Zero\n'\
# '20:53 - Flower of Life',
# 
# '1. Everything's Fine (00:00)\n'\
# '2. Where is Now? (3:11)\n'\
# '3. Smile (10:43)\n'\
# '4. Nostalgia (20:17)\n'\
# '5. Wrinkle Maze (27:40)\n'\
# '6. Daydreamers (32:38),
# 
# '1. Intro 00:00\n'\
# '2. Incredible 00:51\n'\
# '3. Crossroads 04:23\n'\
# '4. Leave 08:10\n'\
# '5. Emotions 11:39\n'\
# '6. Made For Love 16:54',
# 
# '00:00 Pillars of Creation\n'\
# '01:11 Orion\n'\
# '06:08 Cassini\n'\
# '09:41 Messier Object\n'\
# '13:02 Double Helix\n'\
# '18:29 Dirac Sea\n'\
# '24:03 Multiverse Part I: Origin\n'\
# '29:25 Multiverse Part II: Divergence\n'\
# '34:29 Multiverse Part III: Alternate Realities\n'\
# '39:35 And Here's to Many More',
# 
# '1. 0:00\n'\
# '2. 1:28\n'\
# '3. 6:30\n'\
# '4. 10:17\n'\
# '5. 16:36\n'\
# '6. 22:16\n'\
# '7. 23:55\n'\
# '8. 30:05\n'\
# '9. 36:54\n'\
# '10.41:34',
# ]
# 
# pull_num = re.compile(r'^(\d*)\.?\s*\W*(.*[a-zA-z0-9]\)?)\s*(\(\))?')
track_exp = re.compile(r'^(?P<num>\d*)\.?\s*\W*(?P<title>.*[a-zA-z0-9]\)?)\s*(\(\))?')

# regex to parse title and artist from title
# 
# albums = [
# r'(FULL ALBUM) Polyphia - Renaissance',
# r'Sithu Aye - Invent The Universe - (Full Album)',
# r'Sithu Aye - Cassini (5th Anniversary Remaster) || Full Album Stream',
# r'Dorje - Centred and One [FULL EP]',
# r'DJELMASH | CROSSROADS | FULL EP', 
# r'David Maxim Micic | ECO | FULL ALBUM STREAMING',
# r'David Maxim Micic - BILO 3.0 | FULL ALBUM STREAMING',
# r'David Maxim Micic / Who Bit the Moon / FULL ALBUM 2017',
# r'Jakub Zytecki : Wishful Lotus Proof [Full Album]',
# r"Destiny Potato - 'LUN' | FULL ALBUM 2014",
# ]
# 
# desired = [
# ('Polyphia','Renaissance'),
# ('Sithu Aye','Invent The Universe'),
# ('Sithu Aye', 'Cassini', '5th Anniversary Remaster'),
# ('Dorje','Centred and One'),
# ('DJELMASH', 'CROSSROADS'),
# ('David Maxim Micic', 'ECO'),
# ('David Maxim Micic', 'BILO 3.0'),
# ('David Maxim Micic','Who Bit the Moon', '2017'),
# ('Jakub Zytecki','Wishful Lotus Proof'),
# ('Destiny Potato', 'LUN', '2014'),
# ]
# album_exp = re.compile(r'(?:\s\-\s|\s*[\[\]\|]\s*)+|full\s*album\s*stream[ing]?|full\s*ep\s*stream[ing]?|\(*full\s*album\)*\s*|full\s*ep', re.IGNORECASE)
album_exp = re.compile(r'(?:(?:\s*[\(|\[]\s*)?full\s*(?:album|ep)(?:[\)|\]]\s*)?(?:\s*stream(?:ing)?)?)\s*|(?:\s*[\!-\-\/\|\:]\s*)', re.IGNORECASE)
# parsed = [tuple(filter(None, album_exp.split(album))) for album in albums]

# album_exp = re.compile(r'(.*)', re.IGNORECASE)
bad_exps = {'full album', 'full ep', 'streaming'  '-', ' ', '\t', '\n', '\r', '\x0b', '\x0c'}

def make_safe(name):
    illegal_chars = frozenset('\/|:*?<>"\'')
    return ''.join((char for char in name if char not in illegal_chars)).strip()

def filter_list(full_list, excludes=(None, '')):
    return (x for x in full_list if x not in set(excludes))

def parse_track(track_dict, num):    
    # track_dict.update(track_exp.match(track_dict['title']).groupdict())
    # if not track_dict['num']:
    track_dict['num'] = num

def parse_album(info_dict):
    base_set = re.split('\w|/-\s+', info_dict['title'])
    parsed_res = tuple(filter(None, album_exp.split(info_dict['title'])))
    return parsed_res

def fill_metadata(media_file,tag_dict):
    accepted_keys = {"album",
                     "bpm",
                     "compilation",  # iTunes extension
                     "composer",
                     "copyright",
                     "encodedby",
                     "lyricist",
                     "length",
                     "media",
                     "mood",
                     "title",
                     "version",
                     "artist",
                     "albumartist",
                     "conductor",
                     "arranger",
                     "discnumber",
                     "organization",
                     "tracknumber",
                     "author",
                     "albumartistsort",  # iTunes extension
                     "albumsort",
                     "composersort",  # iTunes extension
                     "artistsort",
                     "titlesort",
                     "isrc",
                     "discsubtitle",
                     "language",
                     }
    audio = MP3(media_file)
    safe_dict = {key:val for key,val in tag_dict.items() if key in accepted_keys}
    try:
        safe_dict['tracknumber'] = str(tag_dict['num'])
    except KeyError:
        pass
    # print(safe_dict)
    audio.update(safe_dict)
    audio.save()
    
def slice_chapters(origin_media,track_dict,quality='2'):
    base,ext = osp.splitext(origin_media)
    base = osp.dirname(base)
    print('loading origin media...')
    origin = AudioSegment.from_file(origin_media,ext[1:])
    for chapter in track_dict.values():
        # print(chapter)
        path = osp.join(base,OUTPUTDIR,chapter['album'])
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        track = '{0:02d}-{1}'.format(chapter['num'],chapter['title'])
        try:
            print('slicing:',track)
        except UnicodeEncodeError:
            print('slicing:', chapter['num'])
        track_name = make_safe(track)
        file_name = osp.join(path,track_name+ext)
        time_frame = [chapter[val]*1000 for val in ['start_time','end_time']]
        segment = origin[time_frame[0]:time_frame[1]]
        try:
            print('saving as {}'.format(file_name))
        except UnicodeEncodeError:
            print('saving file to {}'.format(path))
        segment.export(file_name,format=ext[1:],parameters=["-q:a", quality])
        print('populating metadata')
        fill_metadata(file_name,chapter)
        print('Done!\n')
    
if __name__ == '__main__':
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(sys.argv[1], download=False)
        # print(info['extractor_key'])
        print('')
        # print(info.keys())
        # print('')
        print('title', info.get('title','N/A'),sep=':')
        print('creator', info.get('uploader',info.get('id','N/A')),sep=':') 
        print('bit_rate', info.get('abr','N/A'),sep=':')
        print('format', info.get('ext','N/A'),sep=':')
        try:
            track_dict = {}
            num = 0
            album_info = parse_album(info)
            if len(album_info) == 1:
                album = album_info[0]
            else:
                album = album_info[1]
            key = 'chapters' if info.get('chapters', None) is not None else 'entries'
            print(key,':', sep='', end='\n\n')
            for dict in info.get(key, []):
                num += 1
                dict['album'] = album
                try:
                    dict['artist'] = info['uploader']
                except KeyError:
                    pass
                parse_track(dict,num)
                # for item in dict:
                    # print(item, dict[item] if item not in ['url','http_headers','formats'] else 'LEN', sep=': ')
                # print('')
                try:
                    print('\n\tnum:{num}\n\ttitle:{title}\n\tstart:{start_time}\n\tstop:{end_time}'.format(**dict))
                except:
                    pass
                track_dict[dict['title']] = dict
        except (TypeError, KeyError):
            print('no timestamp info')
        out_info = info
        try:
            out_info['ext'] = ydl_opts['postprocessors'][0]['preferredcodec']
        except KeyError:
            pass
        outfile = ydl.prepare_filename(out_info)
        print('starting dowload...')
        ydl.download([sys.argv[1]])
        print('Done!')
        
        # from pprint import pprint
        # pprint(track_dict)
        
        print('slicing chapters from origin...')
        # begin pydub chapter slicing:
        slice_chapters(outfile,track_dict,ydl_opts['postprocessors'][0]['preferredquality'])
        