from dl_101soundboards.config.config import *
from mutagen.flac import FLAC
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError, CouldntEncodeError
import argparse
import json
import os
import re
import requests
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--edit-config', action='store_true',
                        help='Enables user to edit config from command line')
    a2 = parser.add_argument('--no-delete', action='store_true',
                             help='Disables default behaviour of deleting original downloads')
    a3 = parser.add_argument('--no-trim', action='store_true',
                             help='Disables default behaviour of producing trimmed files')
    a4 = parser.add_argument('-f', '--format', nargs='+', action='append', type=str.lower,
                             help='Produces trimmed files in the specified format')

    group1 = parser.add_mutually_exclusive_group()
    group1._group_actions.append(a2)
    group1._group_actions.append(a3)

    group2 = parser.add_mutually_exclusive_group()
    group2._group_actions.append(a3)
    group2._group_actions.append(a4)

    args, unknown = parser.parse_known_args()

    get_config_gen = get_config()
    config = next(get_config_gen)
    if config is None:
        exit(1)
    else:
        valid_formats = next(get_config_gen)
    if args.edit_config:
        print("Opening config editor....")
        edit_config_gen = edit_config(config, valid_formats)
        config = next(edit_config_gen)
        valid_formats = next(edit_config_gen)
    downloads_pardir = f"{config['downloads_pardir']}"
    user_agent = config['user_agent']
    formats = []
    unknown_formats = []
    if not args.format is None:
        user_formats = args.format[0]
        format_count = 0
        while len(formats) < len(valid_formats) and format_count < len(user_formats):
            format = user_formats[format_count]
            if format in valid_formats:
                if format not in formats:
                    formats.append(format)
            else:
                unknown_formats.append(format)
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

    with requests.Session() as session:
        session.headers['User-Agent'] = user_agent
        for url in urls:
            url = f"https://www.{url}?show_all_sounds=yes"
            print(f"Fetching \"{url}\"....")

            response = session.get(url)
            response.raise_for_status()
            response_content = response.content.decode(
                json.detect_encoding(response.content))
            board_data_inline = json.loads(
                re.findall(r"board_data_inline =(.*?)}};", response_content, re.DOTALL)[0] + "}}")

            board_title = board_data_inline["board_title"]
            sounds_count = board_data_inline['sounds_count']
            sounds_tense = 's' if sounds_count != 1 else ''
            print(f"Fetching \"{board_title}\" ({sounds_count} sound{sounds_tense})....")
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

                try:
                    response = session.get(url, stream=True)
                    response.raise_for_status()
                    with open(download_path, 'wb') as out_file:
                        out_file.write(response.content)
                except IOError:
                    continue

            print(f"\r\033[KDownloaded {current_sound} sound{sounds_tense} to \"{untrimmed_sounds_dir}\"")

            if not args.no_trim:
                trimmed_sounds_dir = os.path.abspath(f"{downloads_dir}/trimmed")
                current_sound = 0
                print(f"Trimming sound file{sounds_tense}....")
                for sound in board_data_inline["sounds"]:
                    current_sound += 1
                    print(
                        f"\r\tTrimming {current_sound} of {sounds_count} sound{sounds_tense}....",
                        end='')
                    sound_id = str(sound["id"])
                    try:
                        audio = AudioSegment.from_mp3(f"{untrimmed_sounds_dir}/{sound_id}.mp3")
                        if sound["sound_rendered"]:
                            trim_samples = 8820 * int(sound_id[-1]) if sound_id[-1] != '0' else 88200
                            trim_samples = trim_samples * 2 if audio.channels == 2 else trim_samples
                            audio = audio._spawn(audio.get_array_of_samples()[trim_samples:])
                        for format in formats:
                            export_dir = os.path.abspath(f"{trimmed_sounds_dir}/{format}")
                            os.makedirs(export_dir, exist_ok=True)
                            trimmed_sound_export_name = os.path.abspath(f"{export_dir}/{sound_id}.{valid_formats[format]}")
                            audio.export(trimmed_sound_export_name, format=format)
                    except (CouldntDecodeError, CouldntEncodeError, IOError):
                        continue
                for format in formats:
                    print(
                        f"\r\033[KExported {current_sound} .{valid_formats[format].upper()} file{sounds_tense} to \"{os.path.abspath(f"{trimmed_sounds_dir}/{format}")}\"")

                if 'flac' in formats:
                    print(f"Adding metadata to export{sounds_tense}....")
                    current_sound = 0
                    for sound in board_data_inline['sounds']:
                        current_sound += 1
                        print(
                            f"\r\tTagging {current_sound} of {sounds_count} sound{sounds_tense}....", end='')
                        try:
                            file = FLAC(os.path.abspath(f"{trimmed_sounds_dir}/flac/{sound["id"]}.flac"))
                            metadata = {
                                "TITLE": sound['sound_transcript'],
                                "DESCRIPTION": f"Sound ID: {sound['id']}",
                                "ARTIST": 'www.101soundboards.com',
                                "ALBUM": board_data_inline['board_title'],
                                "YEAR": board_data_inline['created_at'][:4],
                                "DATE": sound['updated_at'],
                                "TRACKNUMBER": str(sound['sound_order']),
                                "GENRE": 'Soundboard',
                                "ORGANIZATION": "www.101soundboards.com",
                                "COPYRIGHT": "www.101soundboards.com",
                            }
                            for key, value in metadata.items():
                                file[key] = value
                            file.save()
                        except Exception:
                            continue

                    print(f"\r\033[KTagged {current_sound} FLAC file{sounds_tense}")

                if not args.no_delete:
                    print("Removing original downloads....")
                    shutil.rmtree(untrimmed_sounds_dir)
                    print(f"Removed \"{untrimmed_sounds_dir}\"")


if __name__ == "__main__":
    main()