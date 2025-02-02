import json
import os
import random
import re
import string
from json import JSONDecodeError

config_keys = ["downloads_pardir", "user_agent"]
config_path = os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/config.json")

def verify_config ():
    if not os.path.exists(config_path):
        return _create_config(config_keys, config={}, save=True)
    else:
        with open(config_path) as file:
            try:
                config = json.load(file)
                if not 'downloads_pardir' in config:
                    _create_config(['downloads_pardir'], config=config, save=True)
                else:
                    downloads_pardir = config['downloads_pardir']
                    if not file_path_is_writable(downloads_pardir):
                        user_input = get_yes_or_no(f"Edit 'downloads_pardir' at {config_path}? [Y/n]: ")
                        if user_input:
                            _create_config(['downloads_pardir'], config=config, save=True)
                        else:
                            return None

                if not 'user_agent' in config:
                    _create_config(['user_agent'], config=config, save=True)

            except JSONDecodeError as e:
                print(f"Error parsing \"{config_path}\": ")
                user_input = get_yes_or_no(f"Write {config_path} from scratch? [Y/n]: ")
                if user_input:
                    _create_config(config_keys, config={}, save=True)
                else:
                    return None
            return config

def _create_config (keys, config={}, save=False):
    config = edit_keys(config, keys)
    if save:
        with open(config_path, "w") as outfile:
            json.dump(config, outfile)
    return config

def edit_keys (config, keys):
    for key in keys:
        match key:
            case 'downloads_pardir':
                while True:
                    downloads_pardir = os.path.abspath(input("Enter a (relative) file path for your downloads: ").strip())
                    if file_path_is_writable(downloads_pardir):
                        config['downloads_pardir'] = downloads_pardir
                        break

            case 'user_agent':
                config['user_agent'] = input("Paste your user agent: ").strip()
    return config

def edit_config (config):
    new_config = config.copy()
    config_changes = 0

    while True:
        print("\033c", end="")
        if config_changes < 1:
            print("'q' to quit\n\n{")
        else:
            print("'s' to save and quit\n'q' to quit without saving\n\n{")
        key_count = 0
        for key in new_config:
            key_count += 1
            print(f"\t{key_count} - \"{key}\": {new_config[key]},")
        print("}\n")
        key_range = f"1-{key_count}" if key_count > 1 else '1'
        user_selection = _verify_input(new_config, input(f"Select a key to edit [{key_range}]: ").strip())

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
                break
            elif user_selection == 'Q':
                print("\033c", end="")
                if config_changes > 0:
                    print("Changes discarded")
            elif user_selection == 'S' and config_changes > 0:
                config = _create_config({}, config=new_config, save=True)
                print("\033cChanges saved")
            else:
                print("Bad input")
                user_selection = _verify_input(config, input(f"Please enter [1-{key_count}]: ").strip())
                continue
            return config

def _verify_input (config, user_selection):
    key_count = len(config)
    while True:
        regex = re.compile("^(\d+|Q|S|q|s)")
        search_result = regex.search(user_selection)
        if not search_result is None:
            user_selection = search_result.group(0)
        try:
            if search_result is None or (int(user_selection) < 1 or int(user_selection) > key_count):
                print("Bad input")
                user_selection = input(f"Please enter [1-{key_count}]: ").strip()
                continue
        except ValueError:
            user_selection = user_selection[0].upper()
        return user_selection
    config = _create_config([list(config.keys())[user_selection]], config=config, save=False)

def get_yes_or_no (input_message):
    user_input = input(input_message).strip().upper()
    while not len(user_input) > 0 or (not user_input[0] == 'Y' and not user_input[0] == 'N'):
        print("Bad input")
        user_input = input("Please enter [Y/n]: ").strip().upper()
    user_input = False if user_input[0] == 'N' else True
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
    print(error_message)
    return False