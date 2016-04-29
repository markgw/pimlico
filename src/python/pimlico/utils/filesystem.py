import os
import shutil
import threading
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


def copy_dir_with_progress(source_dir, target_dir):
    """
    Utility for copying a large directory and displaying a progress bar showing how much is copied.

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
    print "Moving %s from %s to %s" % (format_file_size(source_size), source_dir, target_dir)

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
    # Remove from source
    shutil.rmtree(source_dir)
