import json
import os
import random
import re
import string
import subprocess
import unicurses

config_dirname = os.path.dirname(__file__)
config_keys = ['downloads_pardir', 'user_agent', 'muxers']
config_path = os.path.abspath(f"{config_dirname}/config.json")

muxers_path = os.path.abspath(f"{config_dirname}/muxers.json")

class _Config:
    def __init__(self, json_object, muxers=None):
        self.json = json_object
        self.muxers = muxers

def get_config ():
    stdscr = unicurses.initscr()
    try:
        with open(config_path) as file:
            config = _Config(json.load(file))
    except FileNotFoundError:
        config = _create_config(config_keys)
    else:
        missing_keys = []
        for key in config_keys:
            if key not in config.json:
                missing_keys.append(key)
        if len(missing_keys) > 0:
            _create_config(missing_keys, config=config)
        if not file_path_is_writable(config.json['downloads_pardir']):
            user_input = _get_yes_or_no(f"Edit 'downloads_pardir' at {config_path}? [Y/n]: ")
            if user_input:
                _create_config(['downloads_pardir'], config=config)
            else:
                return None

    try:
        config.muxers = json.load(open(muxers_path, 'r'))
    except Exception:
        pass
    finally:
        if config.muxers is None or len(config.muxers) < 1:
            config.muxers = get_ffmpeg_muxers()
            with open(muxers_path, 'w') as out_file:
                json.dump(config.muxers, out_file)
            unicurses.addstr(f"\r\033[KChanges saved to {muxers_path}")
    unicurses.endwin()
    return config

def _create_config (keys, config=_Config({})):
    for key in keys:
        match key:
            case 'downloads_pardir':
                while True:
                    unicurses.addstr("Enter a (relative) file path for your downloads: ")
                    downloads_pardir = os.path.abspath(unicurses.getstr())
                    if file_path_is_writable(downloads_pardir):
                        config.json['downloads_pardir'] = downloads_pardir
                        break

            case 'user_agent':
                unicurses.addstr("Paste your user agent: ")
                config.json['user_agent'] = unicurses.getstr()

            case 'muxers':
                config.json['muxers'] = muxers_path
    with open(config_path, 'w') as out_file:
        json.dump(config.json, out_file)
    return config

def get_ffmpeg_muxers(msg=None):
    if not msg is None:
        unicurses.addstr(f"{msg}\n")
    unicurses.addstr("Running FFmpeg....\n")
    sp_formats = subprocess.run(["ffmpeg", "-formats"], capture_output=True, text=True).stdout
    re_muxers = re.findall("\\s(?:D|)?E[\\s]+([^\\s]*)\\s", sp_formats)
    valid_formats = {}
    muxer_count = 0
    for muxer in re_muxers:
        unicurses.addstr(f"\r\tFetching {muxer_count} of {len(re_muxers)} (de)muxers")
        unicurses.refresh()
        sp_muxer = subprocess.run(['ffmpeg', '-v', '1', '-h', f'muxer={muxer}'], capture_output=True,
                                  text=True).stdout
        re_extension = re.findall('Common extensions: ([^.,]*)[.,]', sp_muxer)
        if len(re_extension) > 0:
            valid_formats[muxer] = re_extension[0]
            muxer_count += 1
        unicurses.clrtoeol()
    unicurses.addstr(f"\rRetrieved {muxer_count} muxers\nWriting to file....")
    return valid_formats

def edit_config (config):
    stdscr = unicurses.initscr()
    while True:
        unicurses.clear()
        unicurses.addstr("'q' to quit\n\n{")
        key_count = 0
        for key in config.json.keys():
            key_count += 1
            unicurses.addstr(f"\n\t{key_count} - \"{key}\": {config.json[key]},")
        key_range = f"1-{key_count}" if key_count > 1 else '1'
        unicurses.addstr(f"\n}}\n\nSelect a key to edit [{key_range}]: ")

        while True:
            user_selection = unicurses.getstr()
            if len(user_selection) > 0:
                    if user_selection.isnumeric() and 0 < int(user_selection) <= key_count:
                        user_selection = int(user_selection) - 1
                        key = list(config.json.keys())[user_selection]
                        if key == 'muxers':
                            config.muxers = get_ffmpeg_muxers()
                        else:
                            _create_config([key], config)
                    elif user_selection[0].upper() == 'Q':
                        unicurses.endwin()
                        return config
                    else:
                        unicurses.addstr(f"Please enter [1-{key_count}]: ")
                        continue
                    break

def _get_yes_or_no (input_message):
    unicurses.addstr(input_message)
    while True:
        user_input = unicurses.getstr()
        if len(user_input) > 1:
            match (user_input[0].upper()):
                case 'Y':
                    return True
                case 'N':
                    return False
        unicurses.addstr("Please enter yes or no [Y/n]: ")

def file_path_is_writable (downloads_pardir):
    try:
        os.makedirs(downloads_pardir, exist_ok=True)
        while True:
            dummy = ''.join(random.choices(string.ascii_letters, k=5))
            dummy_path = f"{downloads_pardir}/{dummy}"
            try:
                os.makedirs(dummy_path)
            except FileExistsError:
                continue
            else:
                break
    except Exception:
        return False
    else:
        os.rmdir(dummy_path)
        return True