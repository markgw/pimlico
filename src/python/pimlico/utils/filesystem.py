# This file is part of Pimlico
# Copyright (C) 2020 Mark Granroth-Wilding
# Licensed under the GNU LGPL v3.0 - https://www.gnu.org/licenses/lgpl-3.0.en.html

from __future__ import print_function
from builtins import input
from past.builtins import basestring

from io import open
import os
import shutil
import tarfile
import threading
from zipfile import ZipFile

from pimlico.utils.progress import get_progress_bar


def dirsize(path):
    """
    Recursively compute the size of the contents of a directory.

    :param path:
    :return: size in bytes
    """
    return sum(
        os.path.getsize(os.path.join(dirpath,filename))
        for dirpath, dirnames, filenames in os.walk(os.path.abspath(path))
        for filename in filenames
    )


def format_file_size(bytes):
    if bytes >= 1e9:
        return "%.2fGb" % (float(bytes) / 1e9)
    elif bytes >= 1e6:
        return "%.2fMb" % (float(bytes) / 1e6)
    elif bytes >= 1e3:
        return "%.2fKb" % (float(bytes) / 1e3)
    else:
        return "%db" % bytes


def copy_dir_with_progress(source_dir, target_dir, move=False):
    """
    Utility for moving/copying a large directory and displaying a progress bar showing how much is copied.

    Note that the directory is first copied, then the old directory is removed, if move=True.

    :param source_dir:
    :param target_dir:
    :return:
    """
    if not os.path.exists(source_dir):
        raise IOError("cannot copy %s: directory doesn't exist" % source_dir)
    # Check that the parent dir of the target exists
    target_parent = os.path.abspath(os.path.join(target_dir, os.pardir))
    if not os.path.exists(target_parent):
        os.makedirs(target_parent)
    # Make sure the target itself doesn't exist
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    source_size = dirsize(source_dir)
    print("%s %s from %s to %s" % ("Moving" if move else "Copying",
                                   format_file_size(source_size), source_dir, target_dir))

    # Do the copying in a thread
    copy_thread = threading.Thread(target=shutil.copytree, args=(source_dir, target_dir))
    copy_thread.start()
    # Monitor the filesize of the target while it's copying
    pbar = get_progress_bar(source_size, title="Copying")
    # TODO Don't loop as fast as possible: wait a bit after each measurement
    while copy_thread.is_alive():
        # Measure the target size
        if os.path.exists(target_dir):
            target_size = dirsize(target_dir)
            if target_size <= source_size:
                pbar.update(target_size)
    pbar.finish()
    if move:
        # Remove from source
        shutil.rmtree(source_dir)


def move_dir_with_progress(source_dir, target_dir):
    copy_dir_with_progress(source_dir, target_dir, move=True)


def new_filename(directory, initial_filename="tmp_file"):
    """
    Generate a filename that doesn't already exist.

    """
    # If the file doesn't exist already, we're done
    if not os.path.exists(os.path.join(directory, initial_filename)):
        return initial_filename
    else:
        # Split off extension, so we can vary filename
        # Special case for splitting off .tar.gz extensions
        if initial_filename.endswith(".tar.gz"):
            base_filename = initial_filename[:-7]
            ext = initial_filename[-7:]
        else:
            base_filename, ext = os.path.splitext(initial_filename)
        # Keep increasing this index until we get a filename that doesn't exist
        index = 1
        while True:
            filename = "%s-%d.%s" % (base_filename, index, ext)
            if not os.path.exists(os.path.join(directory, filename)):
                return filename
            index += 1


def retry_open(filename, errnos=[13], retry_schedule=[2, 10, 30, 120, 300], **kwargs):
    """
    Try opening a file, using the builtin open() function (Py3, or io.open on Py2).
    If an IOError is raised and its `errno` is in the given
    list, wait a moment then retry. Keeps doing this, waiting a bit longer each time, hoping that the problem will
    go away.

    Once too many attempts have been made, outputs a message and waits for user input. This means the
    user can fix the problem (e.g. renew credentials) and pick up where execution left off. If they choose not to,
    the original error will be raised

    Default list of errnos is just `[13]` -- permission denied.

    Use `retry_schedule` to customize the lengths of time waited between retries. Default: 2s, 10s, 30s, 2m, 5m,
    then give up.

    Additional kwargs are pass on to `open()`.

    """
    import warnings
    import time

    while True:
        for retry_wait in retry_schedule + [None]:
            try:
                return open(filename, **kwargs)
            except IOError as e:
                if e.errno not in errnos:
                    # Caught an error, but not one we should retry on
                    raise
                # Any other errors just get raised
                if retry_wait is None:
                    # If we've used our last retry: time to give up and ask user what to do
                    # Ran out of retries: ask the user what to do
                    warnings.warn("Error opening file: %s. Not making any more attempts. If possible, fix the problem "
                                  "and we can try again" % e)
                    answer = input("Try opening %s again? [Y/n] " % filename)
                    if answer.lower() == "n":
                        # Don't try again, give up and raise the error
                        raise
                    else:
                        # Go round again, starting the schedule over
                        continue
                else:
                    # If IOErrro had a suitable errno, we wait a bit and try again
                    warnings.warn("open file failed with error: %s. Waiting %d secs and trying again" % (e, retry_wait))
                    time.sleep(retry_wait)


def extract_from_archive(archive_filename, members, target_dir, preserve_dirs=True):
    """
    Extract a file or files from an archive, which may be a tarball or a zip file (determined by the file extension).

    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if isinstance(members, basestring):
        members = [members]

    if archive_filename.endswith(".tar.gz"):
        # Tarball
        with tarfile.open(archive_filename, "r") as tarball:
            for member in members:
                tar_member = tarball.getmember(member)
                if not preserve_dirs:
                    # Replace member name with filename without directories, so we extract flat
                    tar_member.name = os.path.basename(tar_member.name)
                tarball.extract(tar_member, target_dir)
    elif archive_filename.endswith(".zip"):
        with ZipFile(archive_filename) as zip_file:
            for member in members:
                if preserve_dirs:
                    # Simple extract preserves directory structure
                    zip_file.extract(member, target_dir)
                else:
                    # Extract flat
                    zip_member = zip_file.getinfo(member)
                    member_filename = os.path.basename(zip_member.filename)
                    source = zip_file.open(zip_member)
                    target = open(os.path.join(target_dir, member_filename), "w")
                    with source, target:
                        shutil.copyfileobj(source, target)
    else:
        raise ValueError("could not determine archive type from filename %s. Expect a filename with extension .tar.gz "
                         "or .zip" % archive_filename)


def extract_archive(archive_filename, target_dir, preserve_dirs=True):
    """
    Extract all files from an archive, which may be a tarball or a zip file (determined by the file extension).

    """
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if archive_filename.endswith(".tar.gz"):
        # Tarball
        with tarfile.open(archive_filename, "r") as tarball:
            tarball.extractall(target_dir)
    elif archive_filename.endswith(".zip"):
        with ZipFile(archive_filename) as zip_file:
            zip_file.extractall(target_dir)
    else:
        raise ValueError("could not determine archive type from filename %s. Expect a filename with extension .tar.gz "
                         "or .zip" % archive_filename)
