from dl_101soundboards.config.config import *
from getpass import getpass
import distro
import os
import platform
import requests
import zipfile

def verify_ffmpeg():
    system = platform.system()
    if system == 'Linux':
        for file_path in os.environ['PATH'].split(':'):
            if os.path.exists(file_path) and 'ffmpeg' in os.listdir(file_path):
                return True

        user_input = get_yes_or_no("\nFFmpeg not found!\nDownload FFmpeg? [Y/n]: ")
        if user_input:
            command = None
            distro_like = distro.like().split(' ')
            for like in distro_like:
                match like:
                    case 'debian':
                        command = 'sudo -S apt install ffmpeg'
                    case'fedora' | 'rhel':
                        command = 'sudo -S dnf install ffmpeg'
                    case 'arch':
                        command = 'sudo -S pacman -S ffmpeg'
                    case 'suse':
                        command = 'sudo -S zypper install ffmpeg'
                    case 'alpine':
                        command = 'sudo -S apk add ffmpeg'
                    case _:
                        continue
                break
            if command is None:
                return False
            elif os.getuid() != 0:
                pass_fail = 0
                os.system('export HISTIGNORE=\'*sudo -S*\'')
                while True:
                    exit_code = os.system(f'echo \"{getpass(f"[sudo] password for {os.path.expanduser('~')}: ")}\" | {command}')
                    if exit_code == 0:
                        print()
                        break
                    elif pass_fail > 1:
                        return False
                    else:
                        pass_fail += 1
                        print("\033[F\033[K\033[F\033[K\033[F\033[K\033[F\033[KSorry, try again.")
            else:
                os.system(command)
            return True

    elif system == 'Windows':
        for file_path in os.environ['Path'].split(';'):
            if os.path.exists(file_path) and 'ffmpeg.exe' in os.listdir(file_path):
                return True

        user_input = get_yes_or_no("\nFFmpeg not found!\nDownload FFmpeg? [Y/n]: ")
        if user_input:
            while True:
                ffmpeg_path = os.path.abspath(f"{input("Enter your preferred FFmpeg download path: ").strip()}/FFmpeg")
                if file_path_is_writable(ffmpeg_path):
                    break
            os.makedirs(ffmpeg_path, exist_ok=True)

            ffmpeg_download_path = os.path.abspath(f"{ffmpeg_path}/ffmpeg.zip")
            with requests.Session() as session:
                response = session.get(r"https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip", stream=True)
                response.raise_for_status()
                with open(ffmpeg_download_path, 'wb') as out_file:
                    print("\r\tDownloading ffmpeg....", end='')
                    out_file.write(response.content)
            print(f"\r\033[KDownloaded ffmpeg-release-essentials.zip to {ffmpeg_path}")

            with zipfile.ZipFile(ffmpeg_download_path, 'r') as ffmpeg_zip:
                print(f"\r\tExtracting {ffmpeg_download_path}....", end='')
                ffmpeg_zip.extractall(ffmpeg_path)
                ffmpeg_name = ffmpeg_zip.namelist()[0]
            ffmpeg_bin_path = os.path.abspath(f"{ffmpeg_path}/{ffmpeg_name}bin")
            print(f"\r\033[KExtracted {ffmpeg_name} to {ffmpeg_path}\n\nPlease add the following path to your system path:\n{ffmpeg_bin_path}\n")
            os.remove(ffmpeg_download_path)
    else:
        print("\nFFmpeg not found!\nVisit https://www.ffmpeg.org/download.html for a list of relevant FFmpeg mirrors\n")
    return False