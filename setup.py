# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

for i in ['config', 'muxers']:
    with open(f"dl_101soundboards/config/{i}.json", 'w') as f:
        f.write('{}')

setup(
    name='dl-101soundboards',
    version='1.5.2a1',
    description='Unofficial downloader for www.101soundboards.com',
    long_description=readme,
    author='gitchasing',
    url='https://github.com/gitchasing/dl-101soundboards/',
    license=license,
    packages=find_packages(),
    install_requires=[
        'uni-curses~=3.1.2',
        'mutagen~=1.47.0',
        'pydub~=0.25.1',
        'requests~=2.32.3',
    ],
    entry_points={
        "console_scripts":[
            "dl-101soundboards=dl_101soundboards:main",
        ],
    },
    include_package_data=True
)