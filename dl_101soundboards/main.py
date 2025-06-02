from dl_101soundboards.config.config import *
from dl_101soundboards.config.get_iso639_xxx import get_iso639_xxx

from mutagen.aiff import AIFF
from mutagen.flac import FLAC
from mutagen.id3 import TIT2, COMM, TALB, TPE1, TDOR, TDRC, TRCK, TCON, TPUB, TCOP
from mutagen.trueaudio import TrueAudio
from mutagen.wave import WAVE
from mutagen.wavpack import WavPack

from pydub import AudioSegment

import argparse
import json
import os
import re
import requests
import shutil

MAX_SOUNDS = 750

def main ():

    config = get_config()
    if config is None:
        return 0
    else:
        valid_formats = config.muxers

    parser = argparse.ArgumentParser()

    a1 = parser.add_argument('-t', '--token', help=
        "Adds a cf_clearance token to the request. "
        "This will be necessary to bypass Cloudflare."
    )

    a2 = parser.add_argument('-o', '--output', help=
        "Defines the subdirectory to which sounds are stored. "
        "This will be necessary when the board title raises an OSError."
    )

    a3 = parser.add_argument('-e', '--edit-config', action='store_true',
        help="Enables user to edit config from command line."
    )

    a4 = parser.add_argument('--no-delete', action='store_true',
        help="Disables default behaviour of deleting original downloads."
    )

    a5 = parser.add_argument('--no-trim', action='store_true',
        help="Disables default behaviour of producing trimmed files."
    )

    a6 = parser.add_argument('-f', '--format', nargs='+', action='append',
        type=str.lower, help="Produces trimmed files in the specified format."
    )

    a7 = parser.add_argument('-wd', '--working-directory',
        action='store_true', help="Download to the working directory instead of "
            "the downloads path specified in the config file."
    )

    group1 = parser.add_mutually_exclusive_group()
    group1._group_actions.append(a4)
    group1._group_actions.append(a5)

    group2 = parser.add_mutually_exclusive_group()
    group2._group_actions.append(a5)
    group2._group_actions.append(a6)

    args, unknown = parser.parse_known_args()

    if args.edit_config:
        print("Opening config editor....")
        config = edit_config(config)
        valid_formats = config.muxers
    downloads_pardir = config.json['downloads_pardir']
    if args.working_directory:
        cwd = os.getcwd()
        if file_path_is_writable(cwd):
            downloads_pardir = cwd
    user_agent = config.json['user_agent']
    formats = []
    unknown_formats = []
    if not args.format is None:
        user_formats = args.format[0]
        format_count = 0

        def match_unknown_format (format):
            match (format):
                case 'aif':
                    format = 'aiff'
                case 'trueaudio':
                    format = 'tta'
                case 'wave':
                    format = 'wav'
                case 'wavpack':
                    format = 'wv'
                case _:
                    unknown_formats.append(format)
                    return
            if format not in formats:
                formats.append(format)

        while len(formats) < len(valid_formats) and format_count < len(user_formats):
            format = user_formats[format_count]
            if format in valid_formats:
                if format not in formats:
                    formats.append(format)
            else:
                match_unknown_format(format)
            format_count += 1
        unknown += unknown_formats + user_formats[format_count:]

    if len(formats) < 1:
        formats.append('flac')

    urls = []
    for arg in unknown:
        re_urls = re.findall("(101soundboards.com/boards/[0-9]+)(?=101soundboards.com/boards/[0-9]+|$|\D)", arg)
        for url in re_urls:
            if url not in urls:
                urls.append(url)

    def get_board_info(board_url, session):
        print(f"Fetching \"{board_url}\"....")
        response = session.get(board_url)
        response.raise_for_status()
        response_content = response.content.decode(
            json.detect_encoding(response.content))
        return {
            'board_data_inline': json.loads(
                re.findall(r"board_data_inline = (.*?)};", response_content, re.DOTALL)[0] + "}"
            ),
            'response_content': response_content
        }

    session_headers = {'User-Agent': user_agent}
    session_cookies = {'cf_clearance': args.token} if args.token else {}

    for url in urls:
        with requests.Session() as session:
            session.headers = session_headers
            session.cookies.update(session_cookies)
            url = f"https://www.{url}"
            board_info = get_board_info(url, session)
            board_data_inline = board_info['board_data_inline']
            loaded_sounds_count = len(board_data_inline['sounds'])
            complete_sounds_count = board_data_inline['sounds_count']
            if loaded_sounds_count <= MAX_SOUNDS < complete_sounds_count:
                load_all_sounds_url = re.findall(f'<a href=\"({url}.*) \">',
                                                 board_info['response_content'], re.DOTALL)[0]
                if load_all_sounds_url is None:
                    if not ask_yes_no(f"Failed to retrieve all {complete_sounds_count} sounds!"
                    f"\nDownload {loaded_sounds_count} sound{p_or_s(loaded_sounds_count)}?"):
                        continue
                else:
                    board_data_inline = get_board_info(load_all_sounds_url, session)['board_data_inline']
            board_title = args.output if not args.output is None else board_data_inline["board_title"]
            sounds_count = board_data_inline['sounds_count']
            sounds_tense = p_or_s(sounds_count)
            print(f"Fetching \"{board_data_inline['board_title']}\" ({sounds_count} sound{sounds_tense})....")
            board_title = board_title.translate({ord(x): '' for x in "\\/:*?\"<>|"})

            downloads_dir = os.path.abspath(f"{downloads_pardir}/{board_title}/{board_data_inline['id']}")
            untrimmed_sounds_dir = os.path.abspath(f"{downloads_dir}/untrimmed")

            os.makedirs(untrimmed_sounds_dir, exist_ok=True)

            current_sound = 0
            for sound in board_data_inline["sounds"]:
                current_sound += 1
                print(
                    f"\r\tDownloading {current_sound} of {sounds_count} sound{sounds_tense}....",
                    end='')
                sound_file_url = sound['sound_file_url']
                if sound_file_url.startswith('https'):
                    url = sound_file_url
                else:
                    url = f"https://www.101soundboards.com/{sound_file_url}"
                sound_id = str(sound['id'])

                download_path = os.path.abspath(f"{untrimmed_sounds_dir}/{sound_id}.mp3")
                headers = {
                    "Host": "101soundboards.com"
                }
                response = session.get(url, stream=True)
                response.raise_for_status()
                with open(download_path, 'wb') as out_file:
                    out_file.write(response.content)

            print(f"\r\033[KDownloaded {current_sound} sound{sounds_tense} to \"{untrimmed_sounds_dir}\"")

            if not args.no_trim:
                current_sound = 0
                print(f"Trimming sound file{sounds_tense}....")
                for sound in board_data_inline["sounds"]:
                    current_sound += 1
                    print(
                        f"\r\tTrimming {current_sound} of {sounds_count} sound{sounds_tense}....",
                        end='')
                    sound_id = str(sound["id"])
                    audio = AudioSegment.from_mp3(f"{untrimmed_sounds_dir}/{sound_id}.mp3")
                    if sound["sound_rendered"]:
                        trim_samples = 8820 * int(sound_id[-1]) if sound_id[-1] != '0' else 88200
                        trim_samples = trim_samples * 2 if audio.channels == 2 else trim_samples
                        audio = audio._spawn(audio.get_array_of_samples()[trim_samples:])
                    for format in formats:
                        export_dir = os.path.abspath(f"{downloads_dir}/{format}")
                        os.makedirs(export_dir, exist_ok=True)
                        trimmed_sound_export_name = os.path.abspath(f"{export_dir}/{sound_id}.{valid_formats[format]}")
                        audio.export(trimmed_sound_export_name, format=format)
                for format in formats:
                    print(
                        f"\r\033[KExported {current_sound} {format.upper()} file{sounds_tense} to \"{os.path.abspath(f"{downloads_dir}/{format}")}\"")

                def tag_id3 (format, format_class):
                    sounds_path = os.path.abspath(f"{downloads_dir}/{format}")
                    print(f"Adding metadata to {os.path.abspath(f"{sounds_path}/*.{valid_formats[format]}")}....")
                    current_sound = 0
                    if format == 'flac':
                        for sound in board_data_inline['sounds']:
                            current_sound += 1
                            sound_path = os.path.abspath(f"{sounds_path}/{sound["id"]}.{valid_formats[format]}")
                            file = format_class(sound_path)
                            print(
                                f"\r\tTagging {current_sound} of {sounds_count} sound{sounds_tense}....", end='')
                            metadata = {
                                "TITLE": sound['sound_transcript'],
                                "DESCRIPTION": f"Sound ID: {sound['id']}",
                                "ARTIST": 'www.101soundboards.com',
                                "ALBUM": board_data_inline['board_title'],
                                "YEAR": board_data_inline['created_at'][:4],
                                "DATE": sound['updated_at'],
                                "TRACKNUMBER": f"{sound['sound_order']}/{board_data_inline['sounds_count']}",
                                "GENRE": 'Soundboard',
                                "ORGANIZATION": 'www.101soundboards.com',
                                "COPYRIGHT": 'www.101soundboards.com',
                            }
                            for key, value in metadata.items():
                                file[key] = value
                            file.save()
                    elif format == 'wv':
                        for sound in board_data_inline['sounds']:
                            current_sound += 1
                            print(
                                f"\r\tTagging {current_sound} of {sounds_count} sound{sounds_tense}....", end='')
                            metadata = {
                                "TITLE": sound['sound_transcript'],
                                "COMMENT": f"Sound ID: {sound['id']}",
                                "ARTIST": 'www.101soundboards.com',
                                "ALBUM": board_data_inline['board_title'],
                                "YEAR": board_data_inline['created_at'][:4],
                                "DATE": sound['updated_at'],
                                "TRACK": f"{sound['sound_order']}/{board_data_inline['sounds_count']}",
                                "GENRE": 'Soundboard',
                                "PUBLISHER": 'www.101soundboards.com',
                                "COPYRIGHT": 'www.101soundboards.com',
                            }
                            for key, value in metadata.items():
                                file[key] = value
                            file.save()
                    else:
                        lang = get_iso639_xxx()
                        for sound in board_data_inline['sounds']:
                            current_sound += 1
                            print(
                                f"\r\tTagging {current_sound} of {sounds_count} sound{sounds_tense}....", end='')
                            sound_path = os.path.abspath(f"{sounds_path}/{sound["id"]}.{valid_formats[format]}")
                            file = format_class(sound_path)
                            try:
                                file.add_tags()
                            except:
                                pass
                            metadata = (
                                TIT2(encoding=3, text=sound['sound_transcript']),
                                COMM(encoding=3, lang=get_iso639_xxx(), text=f"Sound ID: {sound['id']}"),
                                TPE1(encoding=3, text='www.101soundboards.com'),
                                TALB(encoding=3, text=board_data_inline['board_title']),
                                TDOR(encoding=3, text=board_data_inline['created_at'][:4]),
                                TDRC(encoding=3, text=sound['updated_at']),
                                TRCK(encoding=3, text=f"{sound['sound_order']}/{board_data_inline['sounds_count']}"),
                                TCON(encoding=3, text='Soundboard'),
                                TPUB(encoding=3, text='www.101soundboards.com'),
                                TCOP(encoding=3, text='www.101soundboards.com'),
                            )
                            for tag in metadata:
                                file.tags.add(tag)
                            file.tags.save(sound_path)

                    print(f"\r\033[KTagged {current_sound} {format.upper()} file{sounds_tense}")

                if 'aiff' in formats:
                    tag_id3('aiff', AIFF)
                if 'flac' in formats:
                    tag_id3('flac', FLAC)
                if 'tta' in formats:
                    tag_id3('tta', TrueAudio)
                if 'wav' in formats:
                    tag_id3('wav', WAVE)
                if 'wv' in formats:
                    tag_id3('wv', WavPack)

                if not args.no_delete:
                    print("Removing original downloads....")
                    shutil.rmtree(untrimmed_sounds_dir)
                    print(f"Removed \"{untrimmed_sounds_dir}\"")

def ask_yes_no (prompt):
    while True:
        response = input(f"{prompt} [Y/n] ").strip().lower()
        if len(response) > 0:
            if response[0] == 'y':
                return True
            elif response[0] == 'n':
                return False
        print("Please enter yes or no [Y/n] ")

def p_or_s (len):
    return '' if len == 1 else 's'

if __name__ == "__main__":
    main()