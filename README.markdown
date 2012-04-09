mkvtomp4
========
Forked from Gavin Beatty <gavinbeatty@gmail.com>

mkvtomp4: Uses mpeg4ip or GPAC's MP4Box, mkvtoolnix and ffmpeg to convert
troublesome mkv files to mp4.
The conversion does not re-encode the video and only re-encodes the audio if
it doesn't use AAC codec (one can override this behaviour using
`--audio-codec`).
They will be playable on the Sony PS3.

From the manual:

    NAME
           mkvtomp4 - convert H.264 mkv files to mp4 files playable on the PS3

    SYNOPSIS
           mkvtomp4 [OPTIONS] [--] <mkvfile>

           mkvtomp4 --correct-profile-only [--] <rawh264file>

    DESCRIPTION
           Uses mpeg4ip or GPACs MP4Box, mkvtoolnix and ffmpeg to convert
           troublesome mkv files to mp4. The conversion does not re-encode the
           video and only re-encodes the audio if it doesnt use AAC codec (one
           can override this behaviour using --audio-codec). They will be playable
           on the Sony PS3.

           We depend on: mkvtoolnix, mpeg4ip or GPACs MP4Box for the conversion.
           ffmpeg is optional but required for audio transcoding.

    OPTIONS
           --use-mp4creator or --use-mp4box
               Specify which mp4 backend to use. mp4creator is the default.

           --audio-delay-ms=<delay_ms>
               When importing the audio track, delay by <delay_ms> milliseconds.
               e.g., --audio-delay-ms=1000 delays by 1 second. Not supported by
               mp4creator.

           --audio-bitrate=<bitrate>
               If/When converting audio, use the given bitrate. e.g., 128.

           --audio-channels=<channels>
               If/When converting audio, use <channels> channels in the output.
               e.g., 5.1.

           --audio-codec=<codec>
               If/When converting audio, convert to <codec>. Default is libfaac.
               This should be something supported by ffmpeg.

           -o, --output=<outfile>
               Put the completed mp4 into <outfile>.

           --keep-temp-files
               Keep all temporary files created while converting.

           -n, --dry-run
               Dont run any commands, but print them in a shellquoted format that
               can be safely copy-pasted by the user.

           --stop-before-extract-video
               Exit before extracting video from <mkvfile>.

           --stop-before-correct-profile
               Exit before correcting profile of raw H.264 stream.

           --stop-before-extract-audio
               Exit before extracting audio from <mkvfile>.

           --stop-before-convert-audio
               Exit before converting audio previously extracted. This will stop
               even if the audio does not need to be converted.

           --stop-before-video-mp4
               Exit before adding the extracted video to the mp4 container.

           --stop-before-hinting-mp4
               Exit before hinting the mp4 file with the video track.

           --stop-before-audio-mp4
               Exit before adding the extracted (and possibly converted) audio to
               the mp4 container.

           <mkvfile>
               The Matroska (.mkv) file you wish to convert.

           --correct-profile-only
               Only correct the profile

           <rawh264file>
               The raw H.264 stream file that will have its profile corrected for
               use on the PS3.

    EXIT STATUS
           0 on success and non-zero on failure.

    AUTHOR
           Gavin Beatty <gavinbeatty@gmail.com>

    RESOURCES
           Website: http://code.google.com/p/mkvtomp4/

    REPORTING BUGS
           Please report all bugs and wishes to <gavinbeatty@gmail.com>

    COPYING
           mkvtomp4 Copyright (C) 2010 Gavin Beatty, <gavinbeatty@gmail.com>

           Free use of this software is granted under the terms of the GNU General
           Public License version 3, or at your option, any later version.
           (GPLv3+)


Dependencies
------------

Tools:
* mkvtoolnix
* mpeg4ip or GPAC's MP4Box
* ffmpeg

On Linux, use your package manager to install.
On Mac OS X, use MacPorts to install.
On Windows, go to the tools' individual websites and find windows binaries.

Everything else is written using only fully cross-platform python, except:

* pipes module. This means we depend on POSIX /bin/sh for the time being.

If you want to help eliminate this dependency, help solve issue 0001.


License
-------

mkvtomp4 Copyright 2010 Gavin Beatty <gavinbeatty@gmail.com>.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You can find the GNU General Public License at:
http://www.gnu.org/licenses/


Install
-------

Use setuptools in the usual way:
    python setup.py build
    sudo python setup.py install

To install only for the current user:
    python setup.py install --user

For additional help:
    python setup.py --help


Install documentation
---------------------

Default installation prefix is `/usr/local`:
    sudo make install-docs

Install to your own prefix:
    make install-docs prefix=~/.local


Website
-------
http://code.google.com/p/mkvtomp4/


