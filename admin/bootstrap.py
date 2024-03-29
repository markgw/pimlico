"""
Bootstrapping script that create a basic Pimlico setup, either for an existing config file, or for a new project.

Distribute this with your Pimlico project code. You don't need to distribute Pimlico itself
with your project, since it can be downloaded later. Just distribute a directory tree containing your config files,
your own code and this Python script, which will fetch everything else it needs.

Another use is to get a whole new project up and running. Use the `newproject.py` script for that purpose, which
calls this script.

"""
from __future__ import print_function

import os
import sys
from io import open

# Provide simply Py2-3 compatibility without requiring other libraries
PY3 = sys.version_info[0] == 3

if PY3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen

import tarfile
import json


RAW_URL = "https://raw.githubusercontent.com/markgw/pimlico/"
DOWNLOAD_URL = "https://github.com/markgw/pimlico/archive/"
GIT_URL = "https://github.com/markgw/pimlico.git"
GITHUB_API = "https://api.github.com"


def lookup_pimlico_versions():
    # Use Github API to find all tagged releases
    tag_api_url = "%s/repos/markgw/pimlico/tags" % GITHUB_API
    try:
        tag_response = urlopen(tag_api_url).read().decode("utf-8")
    except Exception as e:
        print("Could not fetch Pimlico release tags from {}: {}".format(tag_api_url, e))
        sys.exit(1)
    tag_data = json.loads(tag_response)
    return [tag["name"] for tag in reversed(tag_data)]


def lookup_bleeding_edge(branch_url):
    release_url = "{}admin/release.txt".format(branch_url)
    try:
        release_data = urlopen(release_url).read().decode("utf-8")
    except Exception as e:
        print("Could not fetch Pimlico release from {}: {}".format(release_url, e))
        sys.exit(1)
    return release_data.splitlines()[-1].lstrip("v")


def find_config_value(config_path, key, start_in_pipeline=False):
    with open(config_path, "r", encoding="utf-8") as f:
        in_pipeline = start_in_pipeline

        for line in f:
            line = line.strip("\n ")
            if in_pipeline and line:
                # Look for the required key in the pipeline section
                line_key, __, line_value = line.partition("=")
                if line_key.strip() == key:
                    return line_value.strip()
            elif line.startswith("["):
                # Section heading
                # Start looking for keys if we're in the pipeline section
                in_pipeline = line.strip("[]") == "pipeline"
            elif line.upper().startswith("%% INCLUDE"):
                # Found include directive: follow into the included file
                filename = line[10:].strip()
                # Get filename relative to current config file
                filename = os.path.join(os.path.dirname(config_path), filename)
                found_value = find_config_value(filename, key, start_in_pipeline=in_pipeline)
                if found_value is not None:
                    return found_value
    # Didn't find the key anywhere
    return


def extract(tar_path):
    extract_path = os.path.dirname(tar_path)
    with tarfile.open(tar_path, "r:gz") as tar:
        for item in tar:
            tar.extract(item, extract_path)


def tar_dirname(tar_path):
    with tarfile.open(tar_path, "r:gz") as tar:
        # Expect first member to be a directory
        member = tar.next()
        if not member.isdir():
            raise ValueError("downloaded tar file was expected to contain a directory, but didn't")
        return member.name


def symlink(source, link_name):
    """
    Symlink creator that works on Windows.

    """
    os_symlink = getattr(os, "symlink", None)
    if callable(os_symlink):
        os_symlink(source, link_name)
    else:
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        flags = 1 if os.path.isdir(source) else 0
        if csl(link_name, source, flags) == 0:
            raise ctypes.WinError()


def bootstrap(config_file, git=False):
    current_dir = os.path.abspath(os.path.dirname(__file__))
    branch_name = git if type(git) is str else "master"
    branch_url = "{}{}/".format(RAW_URL, branch_name)

    if os.path.exists(os.path.join(current_dir, "pimlico")):
        print("Pimlico source directory already exists: delete it if you want to fetch again")
        sys.exit(1)

    # Check the config file to find the version of Pimlico we need
    version = find_config_value(config_file, "release")
    if version is None:
        print("Could not find Pimlico release in config file %s" % config_file)
        sys.exit(1)
    major_version = int(version.partition(".")[0])
    print("Config file requires Pimlico version {}".format(version))

    available_releases = lookup_pimlico_versions()
    bleeding_edge = lookup_bleeding_edge(branch_url)
    tags = available_releases

    # If the bleeding edge version is compatible (same major version) just use that
    if int(bleeding_edge.lstrip("v").partition(".")[0]) == major_version:
        print("Bleeding edge ({}) is compatible".format(bleeding_edge))
        fetch_release = "master"
    else:
        if git:
            print("Error: tried to clone the Git repo instead of fetching a release, but config file is not " \
                  "compatible with latest Pimlico version")
            sys.exit(1)
        # Find the latest release that has the same major version
        compatible_tags = [t for t in tags if int(t.lstrip("v").partition(".")[0]) == major_version]
        fetch_release = compatible_tags[-1]
        print("Fetching latest release of major version {}, which is {}".format(major_version, fetch_release))

    if git:
        # Clone the latest version of the code from the Git repository
        # Allow the git kwarg to name a branch to clone
        if type(git) is str:
            args = "--branch {} ".format(git)
        else:
            args = ""
        print("Cloning git repository ({})".format("{} branch".format(git) if type(git) is str else "master"))
        import subprocess
        subprocess.check_call("git clone {}{}".format(args, GIT_URL), shell=True)
    else:
        archive_url = "%s%s.tar.gz" % (DOWNLOAD_URL, fetch_release)
        print("Downloading Pimlico source code from {}".format(archive_url))
        tar_download_path = os.path.join(current_dir, "archive.tar.gz")
        with open(tar_download_path, "wb") as archive_file:
            archive_file.write(urlopen(archive_url).read())

        print("Extracting source code")
        extracted_dirname = tar_dirname(tar_download_path)
        extract(tar_download_path)
        # Extracted source code: remove the archive
        os.remove(tar_download_path)

        os.rename(os.path.join(current_dir, extracted_dirname), os.path.join(current_dir, "pimlico"))
    print("Pimlico source (%s) is now available in directory pimlico/" % fetch_release)
    # Create symlink to pimlico.sh, so it's easier to run
    print("Creating symlink pimlico.sh for running Pimlico")
    symlink(os.path.join("pimlico", "bin", "pimlico.sh"), "pimlico.sh")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--git" in args:
        args.remove("--git")
        git = True
    else:
        git = False

    if len(args) == 0:
        print("Usage:")
        print("  python bootstrap.py [--git] <config_file>")
        print()
        print("Specify a Pimlico config file to set up Pimlico for")
        print("If you want to start a new project, with an empty config file, use the newproject.py script")
        print()
        print("If you specify --git, Pimlico will be cloned as a Git repository, rather ")
        print("than downloaded from a release. This only works on Linux and requires that Git is ")
        print("installed. Most of the time, you don't want to do this: it's only for Pimlico development")
        sys.exit(1)
    else:
        config_file = os.path.abspath(args[0])
        bootstrap(config_file, git=git)
