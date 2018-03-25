#! /usr/bin/env python3
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import os
import sys
import logging
import argparse
import youtube_dl
import os.path as osp

"""
media_from_yt.py
converts youtube audio streams to audio files. 
uses youtube-dl internally, thus ffmpeg or libav is required and youtube-dl is strongly recommended.


requires:
ffmpeg or libav
youtube-dl

optional: 
pydub  -- audio slicing

mutagen --  metadata tagging (may be removed with youtube-dl / pydub capabilities)

example usage: 
media_from_yt <youtube id> 
"""

try: 
    from pydub import AudioSegment
    # from mutagen.mp3 import EasyMP3 as MP3
    PYDUB = True
except ImportError:
    # dont like this... fix it
    import warnings
    warnings.warn('Unable to Find pydub in PYTHONPATH, slicing of audio segments is not supported without it.')
    del warnings
    PYDUB = False
    
__author__ = 'Danyal Ahsanullah'
__version_info__ = (1,0)
__version__ = '.'.join(map(str, __version_info__))

COMMENT = '##'
OUTPUTDIR = 'output'


# logger creation
# formatter = logging.Formatter('%(asctime)s - %(message)s')
formatter = logging.Formatter('%(message)s')
logger = logging.getLogger(__file__)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
logger.addHandler(ch)

# cli parser definition
parser = argparse.ArgumentParser('media_from_yt')
parser.add_argument('urls', type=str, nargs='+', help='url(s) or id(s) of media to be converted')
parser.add_argument('--output', '-o', type=str, metavar='PATH', help='base directory to save results into')
parser.add_argument('--extension', '-e', type=str, metavar='EXT',default='mp3',
                                    help='extension to use for file(s) to be created')
parser.add_argument('--file', '-f', action='store_true',
                                    help='flag that if set, treats urls as a file with a list of urls inside it'
                                             '(one per line, comments start with "{}")'.format(COMMENT))
parser.add_argument('--no-metadata', action='store_true', help='if passed, prevents metadata from being added')

parser_quality = parser.add_mutually_exclusive_group()        
parser_quality.add_argument('--bitrate', '-br', type=str, metavar='BR',default='', 
                                                help='desired bitrate to have exported file(s) in')
parser_quality.add_argument('--quality', '-qa', type=str, metavar='QA',default='2', 
                                                help='desired vbr quality to have exported file(s) in')

parser_loudness = parser.add_mutually_exclusive_group()
parser_loudness.add_argument('--verbose', '-v', action='count', help='prints a more detailed output', default=0)
parser_loudness.add_argument('--quiet', '-q', action='count', help='suppresses console output', default=0)

# source = parser.add_mutually_exclusive_group()
# source.add_argument('--soundcloud', '-S', action='store_true', help='treats inputs as soundcloud links')
# source.add_argument('--bandcamp', '-B', action='store_true', help='treats inputs as bandcamp links')

parser.add_argument('--version', '-V', action='version', version="%(prog)s " + __version__)



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
        logger.warning('done downloading %s, applying any post-processing', d['filename'])
    # else:
        # # print(d.keys())
        # print('\r{}:{} -- ({})'.format(d['filename'],round(d['downloaded_bytes']/d['total_bytes']*100,2), round(d['elapsed'],3)),end='')


ydl_opts = {
    'format': 'bestaudio/best',
    # 'verbose': 'True',
    # 'verbose': 'False',
    'quiet':'True',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '2',
        # 'preferredquality': '128k',
    }],
    # 'logger': MyLogger(),
    'progress_hooks': [my_hook],
}


# regex for parsing track titles -- see ref/regex_text.txt
track_exp = re.compile(r'^((?P<track>(\d*(?!\d*\:\d*)))|(?:\d*\W*\d*)|)'
                                     r'\s*\W*\s*(?P<title>.*?(?=\(?\d+\:\d*\)?)|(.*))',re.I)

# regex to parse title and artist from title -- see ref/regex_test.txt
album_exp = re.compile(r'(?:(?:\s*[\(|\[]\s*)?full\s*(?:album|ep)(?:[\)|\]]\s*)?(?:\s*stream(?:ing)?)?)\s*'
                                       r'|(?:\s*[\!-\-\/\|\:]\s*)'
                                       r'|(?:\s\s+)', re.I)

# parsed = [tuple(filter(None, album_exp.split(album))) for album in albums]

bad_exps = {'full album', 'full ep', 'streaming'  '-', ' ', '\t', '\n', '\r', '\x0b', '\x0c'}

def make_safe(name):
    illegal_chars = frozenset(r'\'\/:*?"<>|')
    illegal_names = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 
                                'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
    f_name = ''.join((char for char in name if char not in illegal_chars)).strip()
    for bad_name in illegal_names:
        if f_name.lower()  == bad_name:
            f_name = '{}_safe'.format(f_name)
    return f_name

def filter_list(full_list, excludes=(None, '')):
    return (x for x in full_list if x not in set(excludes))

def parse_track(track_dict, num): 
    parsed_title_dict = track_exp.match(track_dict['title']).groupdict()
    if parsed_title_dict['track'] is None:
        parsed_title_dict['track'] = num
    if parsed_title_dict['title'] is None:
        parsed_title_dict['title'] = '{}: Track {}'.format(track_dict['title'],num)
    track_dict.update(parsed_title_dict)

def parse_album(info_dict):
    base_set = re.split(album_exp, info_dict['title'])
    parsed_res = tuple(filter(None, album_exp.split(info_dict['title'])))
    return parsed_res

def gen_metadata(tag_dict):
    accepted_keys = { "album","composer","genre","copyright","encoded_by","title","language",
                                  "artist","album_artist","performer","disc","publisher","track","encoder","lyrics"}
    safe_dict = {key:val for key,val in tag_dict.items() if key in accepted_keys}
    try:
        safe_dict['track'] = str(tag_dict['num'])
    except KeyError:
        pass
    return safe_dict
    
def slice_chapters(origin_media,track_list,quality='2',ext=None, add_metadata=True):
    if ext is None:
        base,origin_ext = osp.splitext(origin_media)
        origin_ext = origin_ext[1:]
        ext = origin_ext
    else:
        base,origin_ext = osp.splitext(origin_media)
        origin_ext = origin_ext[1:]
    base = osp.dirname(base)
    logger.info('loading origin media %s...', origin_media)
    origin = AudioSegment.from_file(origin_media,origin_ext)
    logger.info('loaded origin media %s',origin_media)
    for chapter in track_list:
        # print(chapter)
        path = osp.join(base,OUTPUTDIR,chapter['artist'],chapter['album'])
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        track = '{0:02d}-{1}'.format(int(chapter['track']),chapter['title'])
        try:
            logger.info('slicing:%s',track)
        except UnicodeEncodeError:
            logger.info('slicing:%s', chapter['track'])
        track_name = make_safe(track)
        file_name = osp.join(path,'.'.join([track_name,ext]))
        time_frame = [chapter[val]*1000 for val in ['start_time','end_time']]
        segment = origin[time_frame[0]:time_frame[1]]
        try:
            logger.info('saving as %s', file_name)
        except UnicodeEncodeError:
            logger.info('saving file to %s', path)
        if add_metadata:
            logger.info('populating metadata')
            segment.export(file_name,format=ext,parameters=["-q:a", quality], tags=gen_metadata(chapter))
        else:
            segment.export(file_name,format=ext,parameters=["-q:a", quality])
        logger.info('Done!\n')
    

def get_info(url,ydl_opts):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # print(info.keys(),end='\n\n')
        # info['title'] = re.sub(r'\s+', ' ', info['title'])
        logger.info('title: %s', info.get('title','N/A'))
        logger.info('uploader/id: %s', info.get('uploader',info.get('id','N/A'))) 
        logger.debug('bit_rate: %s', info.get('abr','N/A'))
        logger.debug('format: %s', info.get('ext','N/A'))
        
        num = 0
        track_list = []
        try:
            album_info = parse_album(info)
            if len(album_info) == 1:
                album = album_info[0]
            else:
                album = album_info[1]
            key = 'chapters' if info.get('chapters', None) is not None else 'entries'
            logger.info('%s:',key)
            for chapter_dict in info.get(key, []):
                num += 1
                chapter_dict['album'] = album
                try:
                    chapter_dict['artist'] = info['creator']
                except KeyError:
                    logger.warning('no artist found')
                parse_track(chapter_dict,num)
                # for item in chapter_dict:
                    # print(item, chapter_dict[item] if item not in ['url','http_headers','formats'] else 'LEN', sep=': ')
                # print('')
                try:
                    logger.info('\ttrack:{track}\n\ttitle:{title}\n\tstart:{start_time}\n\tstop:{end_time}\n'.format(**chapter_dict))
                except:
                    logger.warning('failed to print info')
                track_list.append(chapter_dict)
            # else:
                # logger.debug('Finished looping through chapters')
        except (TypeError, KeyError):
            logger.warning('no timestamp info %s',url)
        return  info, track_list
    
def grab_file(url,ydl_opts,convert=True, info=None, track_list=None):
    if info is None and track_list is None:
        info, track_list = get_info(url,ydl_opts)
    if not convert:
        # info['ext'] = ydl_opts['postprocessors'][0]['preferredcodec'] 
        opts = {k:v for k,v in ydl_opts.items() if k not in {'postprocessors'}}
    else: 
        opts = ydl_opts
    
    logger.info('starting download...')
    with youtube_dl.YoutubeDL(opts) as ydl:
        # import pdb; pdb.set_trace()
        ydl.download([url])
        outfile = ydl.prepare_filename(info)
    logger.info('Done!')
    return outfile, track_list
        
if __name__ == '__main__':
    args = parser.parse_args()

    if args.verbose :
        if args.verbose > 1:
            logger.setLevel(logging.DEBUG)
            ch.setLevel(logging.DEBUG)
            ydl_opts['verbose']=  'True'
            ydl_opts.pop('quiet')
        else:
            logger.setLevel(logging.INFO)
            ch.setLevel(logging.INFO)
    elif args.quiet:
        # ydl_opts['quiet']=  'True'
        logger.setLevel(logging.CRITICAL)
        ch.setLevel(logging.CRITICAL)
        if args.quiet > 3:
            logger.disabled = True
    quality = args.quality if not args.bitrate else args.bitrate
    ydl_opts['postprocessors'][0]['preferredcodec'] = args.extension
    ydl_opts['postprocessors'][0]['preferredquality'] =  quality
    
    if args.file:
        logger.info('reading urls from file...\n')
        urls = open(args.urls[0], 'r')
    else:
        urls = args.urls

    for url in urls:
        if not url.startswith(COMMENT):
            logger.warning('processing %s', url)
            info, track_list = get_info(url,ydl_opts)
            convert = True if not track_list else False  # delay conversion until slicing happens
            logger.warning('downloading %s', info['title'])
            outfile, track_list = grab_file(url,ydl_opts,convert=convert, info=info, track_list=track_list)
            if track_list and PYDUB:
                # begin pydub chapter slicing:
                logger.info('slicing chapters from origin...')
                slice_chapters(outfile,track_list,quality=quality,ext=args.extension,add_metadata=(not args.no_metadata))
    try:
        urls.close()
    except AttributeError:
        pass
        
        