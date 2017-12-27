#! /usr/bin/env python3
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import youtube_dl
import re


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')
        print(d)
    else:
        print('{}:{} -- ({})'.format(d['filename'],round(d['downloaded_bytes']/d['total_bytes']*100,2), round(d['elapsed'],3)))


ydl_opts = {
    'format': 'bestaudio/best',
    'verbose': 'True',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',
    }],
    'logger': MyLogger(),
    'progress_hooks': [my_hook],
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
# '(FULL ALBUM) Polyphia - Renaissance',
# 'Sithu Aye - Invent The Universe - (Full Album)',
# 'Sithu Aye - Cassini (5th Anniversary Remaster) || Full Album Stream',
# 'Dorje - Centred and One [FULL EP]',
# 'DJELMASH | CROSSROADS | FULL EP', 
# 'David Maxim Micic | ECO | FULL ALBUM STREAMING',
# 'David Maxim Micic - BILO 3.0 | FULL ALBUM STREAMING',
# 'David Maxim Micic / Who Bit the Moon / FULL ALBUM 2017',
# 'Jakub Zytecki : Wishful Lotus Proof [Full Album]',
# 'Destiny Potato - 'LUN' | FULL ALBUM 2014',
# ]
# 
# desired = [
# ('Polyphia','Renaissance'),
# ('Sithu Aye','Invent The Universe')',
# ('Sithu Aye', 'Cassini (5th Anniversary Remaster)',
# ('Dorje','Centred and One'),
# ('DJELMASH', 'CROSSROADS'), 
# ('David Maxim Micic', 'ECO'),
# ('David Maxim Micic', 'BILO 3.0'),
# ('David Maxim Micic','Who Bit the Moon'),
# ('Jakub Zytecki','Wishful Lotus Proof'),
# ('Destiny Potato', 'LUN'),
# ]
# speshial chars | "full album stream[ing]"   | "full ep stream[ing]"   | "full album" | "full ep" 
# list(filter(None, re.split(r'[\[\]()/\|\-\s]+|full\s*album\s*stream[ing]?|full\s*ep\s*stream[ing]?|full\s*album|full\s*ep',albums[0],flags=re.IGNORECASE)))
# ['Polyphia', 'Renaissance']
album_exp = re.compile(r'(.*)', re.IGNORECASE)
bad_exps = {'full album', 'full ep', 'streaming'  '-', ' ', '\t', '\n', '\r', '\x0b', '\x0c'}

def filter_list(full_list, excludes=(None, '')):
    return (x for x in full_list if x not in set(excludes))

def parse_track(track_dict):    
    track_dict.update(track_exp.match(track_dict['title']).groupdict())
    if not track_dict['num']:
        track_dict['num'] = num

def parse_album(info_dict):
    base_set = re.split('\w|/- ', info['title'])    
    return album_exp.match(info['title']).group(1)

if __name__ == '__main__':
    import sys
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(sys.argv[1], download=False)
        ydl.download([sys.argv[1]])
        print('')
        print(info)
        print('')
        print('title', info.get('title','N/A'),sep=':')
        print('creator', info.get('uploader',info.get('id','N/A')),sep=':') 
        try:
            print('chapters:', end='')
            num = 0
            album = parse_album(info)
            for dict in info.get('chapters', info.get('entries', [])):
                num += 1
                dict['album'] = album
                # dict['num'], dict['title'] = parse_track.match(dict['title']).group(1,2)
                parse_track(dict)
                # dict.update(parse_track.match(dict['title']).groupdict())
                # if not dict['num']:
                    # dict['num'] = num
                for item in dict:
                    print(item, dict[item], sep=': ')
                print('')
                print('\n\tnum:{num}\n\ttitle:{title}\n\tstart:{start_time}\n\tstop:{end_time}'.format(**dict), end='')
        except (TypeError, KeyError):
            print('no timestamp info')
        print('')
        print('bit_rate', info.get('abr',''),sep=':')
        print('format', info['ext'],sep=':')
        print('thumbnail', info['thumbnail'],sep=':')
        print(info.keys())
        