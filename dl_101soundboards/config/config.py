from json import JSONDecodeError
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

def get_config ():
    stdscr = unicurses.initscr()

    if not os.path.exists(config_path):
        config = _create_config(config_keys, config={}, save=True)
    else:
        with open(config_path) as file:
            try:
                config = json.load(file)
                if not 'downloads_pardir' in config:
                    _create_config(['downloads_pardir'], config=config, save=True)
                else:
                    downloads_pardir = config['downloads_pardir']
                    if not file_path_is_writable(downloads_pardir):
                        user_input = _get_yes_or_no(f"Edit 'downloads_pardir' at {config_path}? [Y/n]: ")
                        if user_input:
                            _create_config(['downloads_pardir'], config=config, save=True)
                        else:
                            yield None

            except JSONDecodeError as e:
                unicurses.addstr(f"Error parsing \"{config_path}\": {e}\n")
                user_input = _get_yes_or_no(f"Write {config_path} from scratch? [Y/n]: ")
                if user_input:
                    _create_config(config_keys, config={}, save=True)
                else:
                    yield None

            if not config is None and not 'user_agent' in config:
                _create_config(['user_agent'], config=config, save=True)

            if not 'muxers' in config:
                _create_config(['muxers'], config=config, save=True)

    muxers = get_muxers()
    unicurses.endwin()
    yield config
    yield muxers

def _create_config (keys, config={}, save=False):
    config = edit_keys(config, keys)
    if save:
        with open(config_path, 'w') as out_file:
            json.dump(config, out_file)
    return config

def edit_keys (config, keys):
    for key in keys:
        match key:
            case 'downloads_pardir':
                while True:
                    unicurses.addstr("Enter a (relative) file path for your downloads: ")
                    downloads_pardir = os.path.abspath(unicurses.getstr())
                    if file_path_is_writable(downloads_pardir):
                        config['downloads_pardir'] = downloads_pardir
                        break

            case 'user_agent':
                unicurses.addstr("Paste your user agent: ")
                config['user_agent'] = unicurses.getstr()

            case 'muxers':
                config['muxers'] = muxers_path
    return config

def get_muxers():
    try:
        with open(muxers_path, 'r') as out_file:
            valid_formats = json.load(out_file)
    except (FileNotFoundError, IOError, JSONDecodeError):
        error_statement = f"Failed to read {muxers_path}"
    else:
        if len(valid_formats) < 1:
            error_statement = f"Empty JSON at {muxers_path}"
        else:
            return valid_formats
    return get_ffmpeg_muxers(msg=error_statement)

def get_ffmpeg_muxers(msg=None):
    if not msg is None:
        unicurses.addstr(f"{msg}\n")
    unicurses.addstr("Running FFmpeg....\n")
    unicurses.refresh()
    sp_formats = subprocess.run(["ffmpeg", "-formats"], capture_output=True, text=True).stdout
    re_muxers = re.findall("\\s(?:D|)?E[\\s]+([^\\s]*)\\s", sp_formats)
    valid_formats = {}
    muxer_count = 0
    for muxer in re_muxers:
        unicurses.addstr(f"\r\tFetched {muxer_count} of {len(re_muxers)} (de)muxers")
        unicurses.refresh()
        sp_muxer = subprocess.run(['ffmpeg', '-v', '1', '-h', f'muxer={muxer}'], capture_output=True,
                                  text=True).stdout
        re_extension = re.findall('Common extensions: ([^.,]*)[.,]', sp_muxer)
        if len(re_extension) > 0:
            valid_formats[muxer] = re_extension[0]
            muxer_count += 1
        unicurses.clrtoeol()
    unicurses.addstr(f"\rRetrieved {muxer_count} muxers\n\rWriting to file....")
    unicurses.refresh()
    with open(muxers_path, 'w') as out_file:
        json.dump(valid_formats, out_file)
    unicurses.addstr(f"\r\033[KChanges saved to {muxers_path}")
    unicurses.refresh()
    return valid_formats

def edit_config (config, muxers):
    new_config = config.copy()
    config_changes = 0
    stdscr = unicurses.initscr()
    while True:
        unicurses.clear()
        if config_changes < 1:
            unicurses.addstr("'q' to quit\n\n{")
        else:
            unicurses.addstr("'s' to save and quit\n'q' to quit without saving\n\n{")
        key_count = 0
        for key in new_config:
            key_count += 1
            unicurses.addstr(f"\n\t{key_count} - \"{key}\": {new_config[key]},")
        key_range = f"1-{key_count}" if key_count > 1 else '1'
        unicurses.addstr(f"\n}}\n\nSelect a key to edit [{key_range}]: ")

        user_selection = _verify_input(new_config, unicurses.getstr())

        while True:
            if user_selection.isnumeric() and int(user_selection) > 0:
                user_selection = int(user_selection) - 1
                key = list(new_config.keys())[user_selection]
                previous_value = new_config[key]
                new_config = _create_config([key], config=new_config, save=False)
                if config[key] != new_config[key] and previous_value == config[key]:
                    config_changes += 1
                elif config[key] == new_config[key] and previous_value != config[key]:
                    config_changes -= 1

                if key == 'muxers':
                    muxers = get_ffmpeg_muxers()
                break
            elif user_selection == 'Q':
                unicurses.endwin()
                if config_changes > 0:
                    print("Changes discarded")
            elif user_selection == 'S' and config_changes > 0:
                config = _create_config({}, config=new_config, save=True)
                unicurses.endwin()
                print("Changes saved")
            else:
                unicurses.addstr(f"Bad input\nPlease enter [1-{key_count}]: ")
                user_selection = _verify_input(config, unicurses.getstr())
                continue
            yield config
            yield muxers

def _verify_input (config, user_selection):
    key_count = len(config)
    while True:
        regex = re.compile("^(\d+|Q|S|q|s)")
        search_result = regex.search(user_selection)
        if not search_result is None:
            user_selection = search_result.group(0)
        try:
            if search_result is None or (int(user_selection) < 1 or int(user_selection) > key_count):
                unicurses.addstr(f"Bad input\nPlease enter [1-{key_count}]: ")
                user_selection = unicurses.getstr()
                continue
        except ValueError:
            user_selection = user_selection[0].upper()
        return user_selection
    config = _create_config([list(config.keys())[user_selection]], config=config, save=False)

def _get_yes_or_no (input_message):
    unicurses.addstr(input_message)
    user_input = unicurses.getstr()
    while not type(user_input) == str or (len(user_input) > 0 or (not user_input[0].upper() == 'Y' and not user_input[0].upper() == 'N')):
        unicurses.addstr("Bad input\nPlease enter [Y/n]: ")
        user_input = unicurses.getstr()
    user_input = False if user_input[0].upper() == 'N' else True
    return user_input

def file_path_is_writable (downloads_pardir):
    try:
        os.makedirs(downloads_pardir, exist_ok=True)
    except PermissionError as e:
        error_message = f"\"{os.path.abspath(e.filename)}\" does not have writing access"
    except FileNotFoundError as e:
        error_message = f"\"{e.filename}\" does not exist"
    except FileExistsError as e:
        error_message = f"\"{downloads_pardir}\" contains a file path: \'{os.path.abspath(e.filename)}\'"
    except OSError as e:
        error_message =  f"Error validating {downloads_pardir}: {str(e)}"
    else:
        while True:
            dummy = ''.join(random.choices(string.ascii_letters, k=5))
            dummy_path = f"{downloads_pardir}/{dummy}"
            try:
                os.makedirs(dummy_path)
            except PermissionError as e:
                error_message = f"\"{os.path.abspath(e.filename)}\" does not have writing access"
            except FileExistsError:
                continue
            else:
                os.rmdir(dummy_path)
                return True
    unicurses.addstr(error_message)
    return False