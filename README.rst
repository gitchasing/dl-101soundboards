**NOTICE:** `yt-dlp`_ appears to support www.101soundboards.com/boards/ URLs
via generic extractors. ``yt-dlp`` is much faster than ``dl-101soundboards``, but may be less
viable with regard to file organisation and metadata-tagging.

.. _yt-dlp: https://github.com/yt-dlp/yt-dlp

=================
dl-101soundboards
=================

An unofficial downloader for ``https://www.101soundboards.com/boards/`` URLs.

Dependencies
============

* Python 3.8 or higher
* `FFmpeg`_ (add this to your system PATH)

.. _FFmpeg: https://www.ffmpeg.org/download.html

Installation
============

.. code-block:: console

    $ pip install dl-101soundboards

Usage
=====

Use the shell command ``dl-101soundboards`` with the URLs as arguments.

.. code-block:: console

    $ dl-101soundboards https://www.101soundboards.com/boards/685667-windows-95-video-game-music https://www.101soundboards.com/boards/646953-spy-vs-spy-video-game-music
    Fetching "https://www.101soundboards.com/boards/685667?show_all_sounds=yes"....
    Fetching "Windows 95 - Video Game Music" (8 sounds)....
    Downloaded 8 sounds to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\untrimmed"
    Trimming sound files....
    Exported 8 .FLAC files to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\trimmed\flac"
    Adding metadata to exports....
    Tagged 8 FLAC files
    Removing original downloads....
    Removed "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\untrimmed"
    Fetching "https://www.101soundboards.com/boards/646953?show_all_sounds=yes"....
    Fetching "Spy vs. Spy - Video Game Music" (10 sounds)....
    Downloaded 10 sounds to "C:\Users\gitchasing\Downloads\Spy vs. Spy - Video Game Music\646953\untrimmed"
    Trimming sound files....
    Exported 10 .FLAC files to "C:\Users\gitchasing\Downloads\Spy vs. Spy - Video Game Music\646953\trimmed\flac"
    Adding metadata to exports....
    Tagged 10 FLAC files
    Removing original downloads....
    Removed "C:\Users\gitchasing\Downloads\Spy vs. Spy - Video Game Music\646953\untrimmed"

By default, ``dl-101soundboards`` exports separate, trimmed files from the original downloads, then deletes said downloads.
To keep the original, unedited files with the filtered ones, simply use the ``--no-delete`` flag.

.. code-block:: console

    $ dl-101soundboards --no-delete https://www.101soundboards.com/boards/685667-windows-95-video-game-music
    Fetching "https://www.101soundboards.com/boards/685667?show_all_sounds=yes"....
    Fetching "Windows 95 - Video Game Music" (8 sounds)....
    Downloaded 8 sounds to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\untrimmed"
    Trimming sound files....
    Exported 8 .FLAC files to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\trimmed\flac"
    Adding metadata to exports....
    Tagged 8 FLAC files

Alternatively, if you wish to leave the sounds untrimmed, use the ``--no-trim`` flag.

.. code-block:: console

    $ dl-101soundboards --no-trim https://www.101soundboards.com/boards/685667-windows-95-video-game-music
    Fetching "https://www.101soundboards.com/boards/685667?show_all_sounds=yes"....
    Fetching "Windows 95 - Video Game Music" (8 sounds)....
    Downloaded 8 sounds to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\untrimmed"

Output
******

Downloads only come as MP3s, but exports support `whatever FFmpeg supports.`_

.. _whatever FFmpeg supports.: https://ffmpeg.org/ffmpeg-formats.html#Muxers

Run ``ffmpeg -formats`` to view available (de)muxers for your version of FFmpeg.

To specify the export format(s), use the ``-f`` or ``--format`` flag:

.. code-block:: console

    $ dl-101soundboards -f WAV AIFF TTA https://www.101soundboards.com/boards/685667-windows-95-video-game-music
    Fetching "https://www.101soundboards.com/boards/685667?show_all_sounds=yes"....
    Fetching "Windows 95 - Video Game Music" (8 sounds)....
    Downloaded 8 sounds to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\untrimmed"
    Trimming sound files....
    Exported 8 .WAV files to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\trimmed\wav"
    Exported 8 .AIF files to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\trimmed\aiff"
    Exported 8 .TTA files to "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\trimmed\tta"
    Removing original downloads....
    Removed "C:\Users\gitchasing\Downloads\Windows 95 - Video Game Music\685667\untrimmed"

Beware that exporting lossy formats will necessarily shed quality, due to the sample-precise trimming operations made by the program.

Further note that ``dl-101soundboards`` only supports metadata-tagging for FLAC files.
Metadata-tagging for other lossless formats will be considered in future versions.

Configuration
=============

To configure your downloads directory and user agent, use the ``-e`` or ``--edit-config`` flag.

.. code-block:: console

    $ dl-101soundboards --edit-config

You will be automatically asked to configure these settings on your first use of the program.