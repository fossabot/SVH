from django.conf import settings
import os
from svh.models import VideoSource, VideoFile, VIDEO_FORMATS, VideoFolder
from imohash import hashfile
from svh.utils import Protocol
from twisted.internet import reactor, defer
from crochet import wait_for
import yaml

VIDEO_EXTENSIONS = ['webm', 'mkv', 'flv', 'vob', 'ogv', 'drc', 'gifv', 'mng', 'avi', 'mov', 'wmv', 'yuv', 'rm', 'mp4', 'm4p',
                    'mpg', 'mpeg', 'mp2', 'mpv', 'mpe', 'm4v', '3gp', 'mts']


def update_library():
    folder_traverser()
    scan_new_videos()
    check_deleted_videosources()
    update_video_sizes()


def scan_new_videos():
    paths = [os.path.join(dp, f) for dp, dn, filenames in os.walk(settings.SOURCE_VIDEOS_PATH)
              for f in filenames if
              os.path.splitext(f)[1] in ['.%s' % ex for ex in VIDEO_EXTENSIONS + [ext.upper() for ext in VIDEO_EXTENSIONS]]]
    for path in paths:
        hash = hashfile(path, hexdigest=True)
        try:
            obj = VideoSource.objects.get(hash=hash)
            obj.path = path
            obj.save()
        except VideoSource.DoesNotExist:
            vs = VideoSource(path=path, hash=hash)
            vs.save()
        print(path, hash)

    return len(paths)


def folder_traverser():
    folders = []
    for path, dirs, files in os.walk(settings.SOURCE_VIDEOS_PATH):
        folders.append(path)
        vf = VideoFolder.objects.filter(path=path).first()
        if not vf:
            vf = VideoFolder(path=path)
            parent_path = os.path.abspath(os.path.join(path, os.pardir))
            vf.parent = VideoFolder.objects.filter(path=parent_path).first()  # Get parent object or none

        if 'desc.yaml' in files:
            root_yaml = yaml.load(open(os.path.join(path, 'desc.yaml')))
            vf.type = root_yaml['type']
            vf.description = root_yaml.get('description')
            vf.preview_path = root_yaml.get('preview_path')

        vf.save()

    paths = [os.path.join(dp, f) for dp, dn, filenames in os.walk(settings.SOURCE_VIDEOS_PATH)
             for f in filenames if
             os.path.splitext(f)[1] == ".yaml"]
    for root_path in paths:
        root_yaml = yaml.load(open(root_path))
        root = Root(path=root_path, type=root_yaml['type'])
        root.description = root_yaml.get('description')
        root.preview_path = root_yaml.get('preview_path')


def check_deleted_videosources():
    for vs in VideoSource.objects.filter(deleted=False):
        if not os.path.isfile(vs.path):
            vs.deleted=True
            print(vs.path,' was deleted.')
            vs.save()

def update_video_sizes():
    for vs in VideoSource.objects.all():
        vs.sizeBytes = os.stat(vs.path).st_size
        vs.save()

    for vf in VideoFile.objects.all():
        vf.sizeBytes = os.stat(vf.path).st_size
        vf.save()


def convert_video_in_format(input_path, output_path, format='default'):
    cmd = "ffmpeg"
    if os.name == 'nt':
        cmd = "C:\\\\Windows\\ffmpeg.exe" #todo magic path
    args = [cmd, "-i", input_path, VIDEO_FORMATS[format], "-y", output_path]
    pp = Protocol()
    reactor.spawnProcess(pp, cmd, args, {})
    return pp.deferred


@wait_for(timeout=3600)
def convert_videos(format='default'):
    deferreds = []
    for source in VideoSource.objects.filter(deleted=False):
        if not source.videofile_set.filter(format=format).exists():
            target_path = os.path.join(settings.MEDIA_ROOT, '%s.mp4' % source.hash)
            deferred = convert_video_in_format(source.path, target_path, format)

            def save_videofile(result, _source, _path):
                if result.get('code') == 0:
                    vf = VideoFile(path = _path, format=format, source=_source)
                    vf.save()
                else:
                    print("Some shit happens in conversion! %s" % result.get('logs'))

            deferred.addCallback(save_videofile, _source=source, _path=target_path)
            deferreds.append(deferred)

    return defer.DeferredList(deferreds)