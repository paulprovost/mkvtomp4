#!/usr/bin/python

"""Convert H.264 mkv files to mp4 files playable on the PS3."""

# @VERSION@

import os
import sys
import re
import subprocess as sp
import struct
import getopt
import pipes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class Options(object):
    def __init__(self):
        self.verbose = 0
        self.a_bitrate = '328'
        self.a_channels = '5.1'
        self.a_codec = 'libfaac'
        self.a_delay = None
        self.output = None
        self.keep_temp_files = False
        self.dry_run = False
        self.correct_prof_only = False
        self.stop_v_ex = False
        self.stop_correct = False
        self.stop_a_ex = False
        self.stop_a_conv = False
        self.stop_v_mp4 = False
        self.stop_hint_mp4 = False
        self.stop_a_mp4 = False
        self.mp4 = 'mp4creator'

def prin(*args, **kwargs):
    fobj = kwargs.pop('fobj', None)
    if fobj is None:
        fobj = sys.stdout
    sep = kwargs.pop('sep', ' ')
    end = kwargs.pop('end', '\n')
    if len(kwargs) != 0:
        warning_print('prin: unknown kwargs given: %s' % kwargs)

    if len(args) > 0:
        fobj.write(args[0])
        if len(args) > 1:
            for arg in args[1:]:
                fobj.write(sep + arg)
    fobj.write(end)

def error_print(*args, **kwargs):
    kwargs['fobj'] = sys.stderr
    prin("error:", *args, **kwargs)

def die(*args, **kwargs):
    error_print(*args, **kwargs)
    sys.exit(1)

def warning_print(*args, **kwargs):
    kwargs['fobj'] = sys.stderr
    prin("warning:", *args, **kwargs)

def usage_print(fobj=None):
    if fobj is None:
        fobj = sys.stdout
    prin('usage: mkvtomp4 [OPTIONS] [--] <mkvfile>', fobj=fobj)

def version_print(**kwargs):
    prin(__version__, **kwargs)

def verbose_print(level, *args, **kwargs):
    local = kwargs.pop('verbose', 0)
    global g_opts
    if g_opts.verbose >= level or local >= level:
        prin('verbose:', *args, **kwargs)

def __sq(one):
    squoted = pipes.quote(one)
    if squoted == '':
        return "''"
    return squoted

def sq(*args):
    return " ".join([__sq(x) for x in args])

def command(*cmd, **kwargs):
    verbose_kwargs = {}
    verboos = kwargs.pop('verbose', None)
    dry_run = kwargs.pop('dry_run', False)
    if verboos is not None:
        verbose_kwargs['verbose'] = verboos
    if len(kwargs) != 0:
        verbose_print(1, 'command: Popen kwargs: %s' % str(kwargs), **verbose_kwargs)
    if dry_run:
        prin(sq(*cmd))
    else:
        try:
            verbose_print(1, 'command: %s' % str(cmd), **verbose_kwargs)
            proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True, **kwargs)
        except OSError, e:
            die('not found: %s' % str(e))
        chout, cherr = proc.communicate()
        verbose_print(1, 'command: stdout:', chout, '\ncommand: stderr:', cherr)
        if proc.returncode != 0:
            die('failure: %s' % cherr, end='')
        return chout

def mp4_add_audio_optimize(mp4, audio, **kwargs):
    if g_opts.mp4 == 'mp4creator':
        command('mp4creator', '-c', audio, '-interleave', '-optimize', mp4
            , **kwargs)
    elif g_opts.mp4 == 'mp4box':
        delay = kwargs.pop('delay', None)
        if delay is not None:
            delay = ':delay='+delay
        else:
            delay = ''
        command('MP4Box', '-add', audio+'#audio:trackID=2'+delay, mp4, **kwargs)

def mp4_add_hint(mp4, **kwargs):
    if g_opts.mp4 == 'mp4creator':
        command('mp4creator', '-hint=1', mp4, **kwargs)
    elif g_opts.mp4 == 'mp4box':
        pass

def mp4_add_video(mp4, video, fps, **kwargs):
    if g_opts.mp4 == 'mp4creator':
        command('mp4creator', '-c', video, '-rate', fps, mp4, **kwargs)
    elif g_opts.mp4 == 'mp4box':
        command('MP4Box', '-add', video+'#video:trackID=1', '-hint', '-fps', fps, mp4, **kwargs)

def ffmpeg_convert_audio(old, new, **kwargs):
    bitrate = kwargs.pop('bitrate', '128')
    channels = kwargs.pop('channels', '2')
    codec = kwargs.pop('codec', 'libfaac')
    verboos = kwargs.get('verbose', 0)
    if channels == '5.1':
        channels = '6'

    if verboos > 1:
        cmdlist = ['ffmpeg', '-v', str(verboos - 1)]
    else:
        cmdlist = ['ffmpeg']
    cmdlist.extend(['-i', old, '-ac', channels, '-acodec', codec
        , '-ab', bitrate+'k', new])
    cmd = sq(*cmdlist)
    dry_run = kwargs.pop('dry_run', False)
    verbose_kwargs = {}
    verbose_kwargs['verbose'] = kwargs.pop('verbose', 0)
    verbose_print(1, 'command:', str(cmdlist), **verbose_kwargs)
    if not dry_run:
        os.system(cmd)
    else:
        prin(cmd)

def convert_audio(old, new, **kwargs):
    fixaudio = kwargs.pop('fixaudio', False)
    keep_temp = kwargs.pop('keep_temp', False)

    if fixaudio:
        try:
            codec = kwargs.pop('codec')
            ffmpeg_convert_audio(old, new+'.wav', codec='wav', **kwargs)
            kwargs['codec'] = codec
            ffmpeg_convert_audio(new+'.wav', new, **kwargs)
        finally:
            if not keep_temp:
                try:
                    os.remove(new+'.wav')
                except OSError:
                    pass
    else:
        ffmpeg_convert_audio(old, new, **kwargs)

def correct_profile(video, **kwargs):
    if kwargs.get('dry_run', False):
        prin(" ".join([sq(x) for x in (kwargs['argv0'], '--correct-profile-only', video)]))
    else:
        level_string = struct.pack('b', int('29', 16))
        fobj = open(video, 'r+b')
        try:
            fobj.seek(7)
            verbose_print(1, 'correcting profile:', video)
            fobj.write(level_string)
        finally:
            fobj.close()

def mkv_extract_track(mkv, out, track, **kwargs):
    verboos = kwargs.get('verbose', 0)
    cmd = ['mkvextract', 'tracks', mkv]
    if verboos > 0:
        cmd.extend(['-v'])
    cmd.extend(["%s:%s" % (str(track), out)])
    command(*cmd, **kwargs)

class MkvInfo(object):
    track_no_re = None
    track_type_re = None
    codec_re = None
    a_codec_re = None
    v_codec_re = None
    fps_re = None
    def __init__(self, mkv):
        if MkvInfo.track_no_re is None:
            MkvInfo.track_no_re = re.compile(r'^\|  \+ Track number: (\d+)$')
        if MkvInfo.track_type_re is None:
            MkvInfo.track_type_re = re.compile(r'^\|  \+ Track type: (.*)$')
        if MkvInfo.codec_re is None:
            MkvInfo.codec_re = re.compile(r'^\|  \+ Codec ID: (.*)$')
        if MkvInfo.a_codec_re is None:
            MkvInfo.a_codec_re = re.compile(r'^(A_)?(DTS|AAC|AC3)$')
        if MkvInfo.v_codec_re is None:
            MkvInfo.v_codec_re = re.compile(r'^(V_)?(MPEG4/ISO/AVC)$')
        if MkvInfo.fps_re is None:
            MkvInfo.fps_re = re.compile(r'^\|  \+ Default duration: '
                '\d+\.\d+ms \((\d+\.\d+) fps for a video track\)$')

        self.track = {'audio': None, 'video':None}
        infolines = command('mkvinfo', mkv, env={'LC_ALL':'C'}).split('\n')

        in_track_number = None
        in_track_type = None
        for line in infolines:
            match = MkvInfo.track_no_re.search(line)
            if match is not None:
                in_track_number = match.group(1)
                in_track_type = None
                verbose_print(1, 'MkvInfo: in track number: %s' % in_track_number)
                continue
            if in_track_number is not None:
                match = MkvInfo.track_type_re.search(line)
                if match is not None:
                    in_track_type = match.group(1)
                    verbose_print(1, 'MkvInfo: in track type: %s' % in_track_type)
                    self.track[in_track_type] = in_track_number
                    if in_track_type != 'audio' and in_track_type != 'video':
                        warning_print('ignoring track type: %s' % in_track_type)
            if in_track_number is not None:
                match = MkvInfo.codec_re.search(line)
                if match is not None:
                    codec = match.group(1)
                    # unrecognized track types shouldn't have codec_match := None
                    codec_match = None
                    if in_track_type == 'audio':
                        codec_match = MkvInfo.a_codec_re.search(codec)
                        if codec_match is None:
                            die('unrecognised codec: %s' % codec)
                    elif in_track_type == 'video':
                        codec_match = MkvInfo.v_codec_re.search(codec)
                        if codec_match is None:
                            die('unrecognised codec: %s' % codec)
                    if codec_match is not None:
                        key = in_track_type + '_codec'
                        self.track[key] = codec_match.group(2)
                        verbose_print(1, 'MkvInfo: found %s: %s' % (key, self.track[key]))
            if in_track_type == 'video':
                match = MkvInfo.fps_re.search(line)
                if match is not None:
                    self.track['fps'] = match.group(1)

        if self.track.get('video', None) is None:
            die('no video track found')
        if self.track.get('audio', None) is None:
            die('no audio track found')

# XXX update this old func
def mkv_split(mkv, pieces):
    if pieces != 1:
        split_size_MB = (((os.path.getsize(mkv) / pieces) + 1) / 1000) + 1
        command('mkvmerge', '-o', mkv, '--split', str(split_size_MB))

def exit_if(bbool):
    if bbool:
        sys.exit(0)

def real_main(mkv, argv0):
    mkvinfo = MkvInfo(mkv)
    try:
        video = mkv+'.h264'
        exit_if(g_opts.stop_v_ex)
        mkv_extract_track(mkv, video, mkvinfo.track['video']
            , dry_run=g_opts.dry_run, verbose=g_opts.verbose)

        exit_if(g_opts.stop_correct)
        correct_profile(video, argv0=argv0
            , dry_run=g_opts.dry_run, verbose=g_opts.verbose)

        a_codec = mkvinfo.track['audio_codec']
        audio = mkv+'.'+a_codec.lower()
        exit_if(g_opts.stop_a_ex)
        mkv_extract_track(mkv, audio, mkvinfo.track['audio']
            , dry_run=g_opts.dry_run, verbose=g_opts.verbose)
        exit_if(g_opts.stop_a_conv)
        if a_codec != 'AAC':
            audio, oldaudio = audio+'.aac', audio
            convert_audio(oldaudio, audio
                , codec=g_opts.a_codec, bitrate=g_opts.a_bitrate
                , channels=g_opts.a_channels
                , keep_temp=g_opts.keep_temp_files
                , dry_run=g_opts.dry_run
                , verbose=g_opts.verbose
            )

        if g_opts.output is None:
            g_opts.output = os.path.splitext(mkv)[0]+'.mp4'
        exit_if(g_opts.stop_v_mp4)
        mp4_add_video(g_opts.output, video, fps=mkvinfo.track['fps']
            , dry_run=g_opts.dry_run
            , verbose=g_opts.verbose
        )
        exit_if(g_opts.stop_hint_mp4)
        mp4_add_hint(g_opts.output, dry_run=g_opts.dry_run
            , verbose=g_opts.verbose)

        exit_if(g_opts.stop_a_mp4)
        mp4_add_audio_optimize(g_opts.output, audio, dry_run=g_opts.dry_run
            , delay=g_opts.a_delay
            , verbose=g_opts.verbose)

    finally:
        try:
            if not g_opts.keep_temp_files:
                try:
                    os.remove(video)
                except OSError:
                    pass
                try:
                    os.remove(audio)
                except OSError:
                    pass
        except Exception:
            pass

def main(argv=None):
    if argv is None:
        argv = sys.argv
    global g_opts
    g_opts = Options()

    try:
        opts, args = getopt.gnu_getopt(argv[1:]
            , 'hvo:n'
            , ['help', 'usage', 'version', 'verbose'
                , 'use-mp4box', 'use-mp4creator'
                , 'audio-delay-ms=', 'audio-bitrate=', 'audio-channels='
                , 'audio-codec='
                , 'output=', 'keep-temp-files', 'dry-run'
                , 'correct-profile-only'
                , 'stop-before-extract-video', 'stop-before-correct-profile'
                , 'stop-before-extract-audio', 'stop-before-convert-audio'
                , 'stop-before-video-mp4', 'stop-before-hinting-mp4'
                , 'stop-before-audio-mp4'
              ])
    except getopt.GetoptError, err:
        die(str(err))

    for opt, optarg in opts:
        if opt in ('-h', '--help', '--usage'):
            usage_print()
            sys.exit(0)
        elif opt == '--version':
            version_print()
            sys.exit(0)
        elif opt in ('-v', '--verbose'):
            g_opts.verbose = g_opts.verbose + 1
        elif opt == '--use-mp4creator':
            g_opts.mp4 = 'mp4creator'
        elif opt == '--use-mp4box':
            g_opts.mp4 = 'mp4box'
        elif opt == '--audio-delay-ms':
            g_opts.a_delay = optarg
        elif opt == '--audio-bitrate':
            g_opts.a_bitrate = optarg
        elif opt == '--audio-channels':
            g_opts.a_channels = optarg
        elif opt == '--audio-codec':
            g_opts.a_codec = optarg
        elif opt in ('-o', '--output'):
            g_opts.output = optarg
        elif opt == '--keep-temp-files':
            g_opts.keep_temp_files = True
        elif opt in ('-n', '--dry-run'):
            g_opts.dry_run = True
        elif opt == '--correct-profile-only':
            g_opts.correct_prof_only = True
        elif opt == '--stop-before-extract-video':
            g_opts.stop_v_ex = True
        elif opt == '--stop-before-correct-profile':
            g_opts.stop_correct = True
        elif opt == '--stop-before-extract-audio':
            g_opts.stop_a_ex = True
        elif opt == '--stop-before-convert-audio':
            g_opts.stop_a_conv = True
        elif opt == '--stop-before-video-mp4':
            g_opts.stop_v_mp4 = True
        elif opt == '--stop-before-hinting-mp4':
            g_opts.stop_hint_mp4 = True
        elif opt == '--stop-before-audio-mp4':
            g_opts.stop_a_mp4 = True

    if len(args) == 0:
        usage_io = StringIO()
        usage_print(fobj=usage_io)
        die(usage_io.getvalue(), end='')
    elif len(args) > 1:
        usage_print(fobj=sys.stderr)
    if g_opts.a_delay is not None and g_opts.mp4 == 'mp4creator':
        die("Cannot use --audio-delay-ms with mp4creator. Try --use-mp4box")

    mkv = args[0]

    if g_opts.correct_prof_only:
        correct_profile(mkv, dry_run=g_opts.dry_run, argv0=argv[0])
    else:
        real_main(mkv, argv0=argv[0])

    return 0;

if __name__ == "__main__":
    sys.exit(main())

