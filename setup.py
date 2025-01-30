# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='dl-101soundboards',
    version='1.0.6a1',
    description='Unofficial downloader for www.101soundboards.com',
    long_description=readme,
    author='gitchasing',
    url='https://github.com/gitchasing/dl-101soundboards/',
    license=license,
    packages=find_packages(),
    install_requires=[
        'mutagen~=1.47.0',
        'pydub~=0.25.1',
        'requests~=2.32.3',
    ],
data_files=[
        ("dl_101soundboards/config", ["dl_101soundboards/config/config.json"]),

    ],
    entry_points={
        "console_scripts":[
            "dl-101soundboards=dl_101soundboards:main",
        ],
    },
)