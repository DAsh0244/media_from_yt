#! /usr/bin/env python3
# vim:fileencoding=utf-8
# -*- coding: utf-8 -*-
"""
media_from_yt.py
converts youtube audio streams to audio files. 
uses pafy internally, thus ffmpeg or libav is required and youtube-dl is strongly reccomended.


requires:
pip install pafy
pip install pydub
ffmpeg or libav

reccomended:
pip install youtube-dl

optional:
pip install soundscrape

example usage: 
media_from_yt <youtube id> 
"""

import os
import sys
import pafy
import argparse
import logging
from glob import glob
from pydub import AudioSegment
from soundscrape import soundscrape as sc

__author__ = 'Danyal Ahsanullah'
__version_info__ = (0,6)
__version__ = '.'.join(map(str, __version_info__))

COMMENT = '##'

#todo: add in soundscrape capability -- probably rename to media_from_stream
#todo: look into pytube for maybe removing some dependencies.

class BitrateException(Exception):
    """Best detected bitrate is not within bitrate tolerance"""
    def __init__(self, *args, **kwargs):
        super(BitrateException, self).__init__("Best detected bitrate is not within bitrate tolerance")


# logger creation
# formatter = logging.Formatter('%(asctime)s - %(message)s')
formatter = logging.Formatter('%(message)s')
logger = logging.getLogger(__file__)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
logger.addHandler(ch)

parser = argparse.ArgumentParser('media_from_yt')
parser.add_argument('urls', type=str, nargs='*', help='url(s) or id(s) of youtube vids to be converted.')
parser.add_argument('--output', '-o', type=str, help='base directory to save results into.')
parser.add_argument('--extension', '--ext', '-e', type=str, default='mp3',
                    help='extension to use for file(s) to be created.'
                    )
parser.add_argument('--bitrate', '-b', type=str, default='128k', help='desired bitrate to have exported file(s) in.')

parser.add_argument('--file', '-f', action='store_true',
                    help='flag that if set, treats urls as a file with a list of urls inside it (one per line)'
                    )

loudness = parser.add_mutually_exclusive_group()
loudness.add_argument('--verbose', '-v', action='count', help='prints a more detailed output', default=0)
loudness.add_argument('--quiet', '-q', action='count', help='suppresses console output', default=0)

source = parser.add_mutually_exclusive_group()
source.add_argument('--soundcloud', '-S', action='store_true', help='treats inputs as soundcloud links')
source.add_argument('--bandcamp', '-B', action='store_true', help='treats inputs as bandcamp links')

parser.add_argument('--version', '-V', action='version', version="%(prog)s " + __version__)


def make_safe(name):
    illegal_chars = frozenset('\/|:*?<>"\'')
    return ''.join((char for char in name if char not in illegal_chars))


def get_from_yt(url, bitrate, extension, output, verbose):
    logger.info('fetching: {}'.format(url))
    best_audio = pafy.new(url).getbestaudio()
    logger.debug('fetched audiostream: {}'.format(best_audio.title, best_audio))
    if int(best_audio.bitrate[:-1]) < bitrate:
        raise BitrateException()
    if output:
        tempfile = os.path.join(output, make_safe('.'.join([best_audio.title, best_audio.extension])))
        new_file = os.path.join(output, make_safe('.'.join([best_audio.title, extension])))
    else:
        new_file = make_safe('.'.join([best_audio.title, extension]))
        tempfile = make_safe('.'.join([best_audio.title, best_audio.extension]))
    best_audio.download(filepath=tempfile, quiet=not(verbose > 1))
    logger.debug('temp file created: {}'.format(tempfile))
    logger.info('converting downloaded stream...')
    
    # todo: check on adding metadata from here
    AudioSegment.from_file(tempfile).export(new_file, format=args.extension, bitrate=args.bitrate).close()
    logger.debug('removing temp file: {}'.format(tempfile))
    os.remove(tempfile)
    return new_file

def make_args_dict(url, bitrate, extension, output, verbose):
    """
    shamelessly ripped from their source and converted to dict 
    """
    dict = {}
    dict['artist_url'] = url
    dict['num-tracks'] = sys.maxsize
    dict['group'] = False
    dict['bandcamp'] = False
    dict['mixcloud'] = False
    dict['audiomack'] = False
    dict['hive'] = False
    dict['likes'] = False
    dict['login'] = 'soundscrape123@mailinator.com'
    dict['downloadable'] = False
    dict['track'] = ''
    dict['folders'] = False
    dict['path'] = output
    dict['password'] = 'soundscraperocks'
    dict['open'] = False
    dict['keep'] = False
    dict['version'] = False 
    return dict
    
    
def get_from_soundcloud(url, bitrate, extension, output, verbose):
    raise NotImplementedError('Not yet implemented')
    
    logger.info('fetching: {}'.format(url))
    sc.process_soundcloud(make_args_dict(url, bitrate, extension, output, verbose))
    
    # todo: change base audio
    if int(best_audio.bitrate[:-1]) < bitrate:
        raise BitrateException()
    
    if output:
        tempfile = os.path.join(output, make_safe('.'.join([best_audio.title, best_audio.extension])))
        new_file = os.path.join(output, make_safe('.'.join([best_audio.title, extension])))
    
    else:
        new_file = make_safe('.'.join([best_audio.title, extension]))
        tempfile = make_safe('.'.join([best_audio.title, best_audio.extension]))
        
    best_audio.download(filepath=tempfile, quiet=not(verbose > 1))
    
    logger.debug('temp file created: {}'.format(tempfile))
    logger.info('converting downloaded stream...')
    # todo: check on adding metadata from here
    AudioSegment.from_file(tempfile).export(new_file, format=args.extension, bitrate=args.bitrate).close()
    logger.debug('removing temp file: {}'.format(tempfile))
    os.remove(tempfile)
    return new_file
    
def get_from_bandcamp(url, bitrate, extension, output, verbose):
    raise NotImplementedError('Not yet implemented')
    
if __name__ == '__main__':
    args,extras = parser.parse_known_args()
    try:
        extras = vars(extras)
    except TypeError:
        pass
    converted = 0
    failed = 0

    if args.verbose :
        if args.verbose > 1:
            logger.setLevel(logging.DEBUG)
            ch.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
            ch.setLevel(logging.INFO)
    elif args.quiet:
        logger.setLevel(logging.CRITICAL)
        ch.setLevel(logging.CRITICAL)
        if args.quiet > 1:
            logger.disabled = True

    if args.file:
        logger.info('reading urls from file...\n')
        urls = open(args.urls[0], 'r')
    else:
        urls = args.urls

    for url in urls:
        if not url.startswith(COMMENT):
            try:
                if not (args.soundcloud or args.bandcamp):
                    new_file = get_from_yt(url, int(args.bitrate[:-1]), args.extension, args.output, args.verbose)
                elif args.soundcloud:
                    new_file = get_from_soundcloud(url, int(args.bitrate[:-1]), args.extension, args.output, args.verbose)
                elif args.bandcamp:
                    new_file = get_from_soundcloud(url, int(args.bitrate[:-1]), args.extension, args.output, args.verbose)
                    
                converted += 1
                try:
                    logger.info('converted: {}'.format(os.path.basename(new_file)))
                except UnicodeEncodeError:
                    logger.info('converted: {}'.format(url))
                logger.debug('converted file located at: {}'.format(os.path.dirname(os.path.abspath(new_file))))
            except Exception as e:
                failed += 1
                logger.warning('failed to convert: {}'.format(url))
                logger.warning(e)

    if not (converted | failed):
        logger.warning('no identifiers found to convert')
    else:
        logger.warning('converted: {} entries'.format(converted))
        logger.warning('failed to convert: {} entries'.format(failed))
    try:
        urls.close()
    except AttributeError:
        pass
    sys.exit(0)
