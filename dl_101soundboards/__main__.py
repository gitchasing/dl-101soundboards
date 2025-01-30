from dl_101soundboards.config.config import *
from mutagen.flac import FLAC
from pydub import AudioSegment
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
  a4 = parser.add_argument('-f ', '--format', choices=['flac', 'wav'], type=str.lower, default='flac',
                         help='Produces trimmed files in the specified format')

  group1 = parser.add_mutually_exclusive_group()
  group1._group_actions.append(a2)
  group1._group_actions.append(a3)

  group2 = parser.add_mutually_exclusive_group()
  group2._group_actions.append(a3)
  group2._group_actions.append(a4)

  args, unknown = parser.parse_known_args()

  config = verify_config()
  if config is None:
      exit(1)
  if args.edit_config:
      config = edit_config(config)
  downloads_pardir = f"{config['downloads_pardir']}"
  user_agent = config['user_agent']

  urls = []
  for arg in unknown:
      urls += re.findall("(101soundboards.com/boards/[0-9]+)(?=101soundboards.com/boards/[0-9]+|$|\D)", arg)

  with requests.Session() as session:
      session.headers['User-Agent'] = user_agent
      for url in urls:
          url = f"https://www.{url}?show_all_sounds=yes"
          print(f"\nFetching \"{url}\"....")

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

          sounds_count_digits = len(str(sounds_count))
          current_sound = 0
          for sound in board_data_inline["sounds"]:
              current_sound += 1
              print(
                  f"\r\tDownloading {current_sound} of {sounds_count} sound{sounds_tense}....",
                  end=' ')
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
              except Exception:
                  continue

          print(f"\r\033[K\rDownloaded {current_sound} sound{sounds_tense} to \"{untrimmed_sounds_dir}\"")

          if not args.no_trim:
            trimmed_sounds_dir = os.path.abspath(f"{downloads_dir}/trimmed")
            os.makedirs(trimmed_sounds_dir, exist_ok=True)
            standard = args.format
            current_sound = 0
            print(f"Trimming sound file{sounds_tense}....")
            for sound in board_data_inline["sounds"]:
                current_sound += 1
                print(
                    f"\r\tTrimming {current_sound} of {sounds_count} sound{sounds_tense}....",
                    end=' ')
                sound_id = str(sound["id"])
                trimmed_sound_export_name = os.path.abspath(f"{trimmed_sounds_dir}/{sound_id}.{standard}")
                try:
                    audio = AudioSegment.from_mp3(f"{untrimmed_sounds_dir}/{sound_id}.mp3")
                    audio_length = len(audio)
                    if not sound["sound_duration"] > audio_length:
                        trim_samples = 8820 * int(sound_id[-1]) if sound_id[-1] != '0' else 88200
                        trim_samples = trim_samples * 2 if audio.channels == 2 else trim_samples
                        audio_trimmed = audio._spawn(audio.get_array_of_samples()[trim_samples:])
                        audio_trimmed.export(trimmed_sound_export_name, format=standard)
                    else:
                        audio.export(trimmed_sound_export_name, format=standard)
                except Exception:
                    continue

            print(f"\r\033[K\rExported {current_sound} {standard.upper()} file{sounds_tense} to \"{trimmed_sounds_dir}\"")

            if args.format == 'flac':
                print(f"Adding metadata to export{sounds_tense}....")
                current_sound = 0
                for sound in board_data_inline['sounds']:
                    current_sound += 1
                    print(
                        f"\r\tTagging {current_sound} of {sounds_count} sound{sounds_tense}....", end='')
                    try:
                        file = FLAC(os.path.abspath(f"{trimmed_sounds_dir}/{sound["id"]}.flac"))
                        metadata = {
                            "TITLE": str(sound['id']),
                            "DESCRIPTION": sound['sound_transcript'],
                            "ARTIST": 'www.101soundboards.com',
                            "ALBUM": board_data_inline["board_title"],
                            "YEAR": board_data_inline['created_at'][:4],
                            "DATE": sound['updated_at'],
                            "TRACKNUMBER": str(sound['sound_order']),
                            "GENRE": "www.101soundboards.com",
                            "ORGANIZATION": "www.101soundboards.com",
                            "COPYRIGHT": "www.101soundboards.com",
                        }
                        for key, value in metadata.items():
                            file[key] = value
                        file.save()
                    except Exception:
                        continue

                print(f"\r\033[K\rTagged {current_sound} {standard.upper()} file{sounds_tense}")

            if not args.no_delete:
                print("Removing original downloads....")
                shutil.rmtree(untrimmed_sounds_dir)
                print(f"Removed \"{untrimmed_sounds_dir}\"")


if __name__ == "__main__":
  main()