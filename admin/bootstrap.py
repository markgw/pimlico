"""
Bootstrapping script that create a basic Pimlico setup, either for an existing config file, or for a new project.

Distribute this with your Pimlico project code. You don't need to distribute Pimlico itself
with your project, since it can be downloaded later. Just distribute a directory tree containing your config files,
your own code and this Python script, which will fetch everything else it needs.

Another use is to get a whole new project up and running. Simply download this script, place it in your project
directory, and call `python bootstrap.py`.

"""
import sys
import os
import tarfile
import urllib2


REPOSITORY_URL = "https://gitlab.com/markgw/pimlico/"
RAW_URL = "%s/raw/master/" % REPOSITORY_URL


def lookup_pimlico_versions():
    release_list_url = "%sadmin/releases.txt" % RAW_URL
    try:
        release_data = urllib2.urlopen(release_list_url).read()
    except Exception, e:
        print "Could not fetch Pimlico init code from %s: %s" % (release_list_url, e)
        sys.exit(1)
    return [line for line in release_data.splitlines() if not line.startswith("#")]


def lookup_bleeding_edge():
    return lookup_pimlico_versions()[-1]


def find_config_value(config_path, key, start_in_pipeline=False):
    with open(config_path, "r") as f:
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
            elif line.startswith("%% INCLUDE"):
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


def bootstrap(config_file):
    # Check the config file to find the version of Pimlico we need
    version = find_config_value(config_file, "release")
    major_version = int(version.partition(".")[0])
    print "Config file requires Pimlico version %s" % version

    available_releases = lookup_pimlico_versions()
    bleeding_edge = available_releases[-1]
    tags = available_releases[:-1]

    # If the bleeding edge version is compatible (same major version) just use that
    if int(bleeding_edge.lstrip("v").partition(".")[0]) == major_version:
        print "Bleeding edge (%s) is compatible" % bleeding_edge
        fetch_release = "master"
    else:
        # Find the latest release that has the same major version
        compatible_tags = [t for t in tags if int(t.lstrip("v").partition(".")[0]) == major_version]
        fetch_release = compatible_tags[-1]
        print "Fetching latest release of major version %s, which is %s" % (major_version, fetch_release)

    archive_url = "%srepository/archive.tar.gz?ref=%s" % (REPOSITORY_URL, fetch_release)
    print "Downloading Pimlico source code from %s" % archive_url
    tar_download_path = os.path.join(current_dir, "archive.tar.gz")
    with open(tar_download_path, "wb") as archive_file:
        archive_file.write(urllib2.urlopen(archive_url).read())

    print "Extracting source code"
    extracted_dirname = tar_dirname(tar_download_path)
    extract(tar_download_path)
    # Extracted source code: remove the archive
    os.remove(tar_download_path)

    os.rename(os.path.join(current_dir, extracted_dirname), os.path.join(current_dir, "pimlico"))
    print "Pimlico source (%s) is now available in directory pimlico/" % fetch_release


if __name__ == "__main__":
    args = sys.argv[1:]
    current_dir = os.path.abspath(os.path.dirname(__file__))

    if os.path.exists(os.path.join(current_dir, "pimlico")):
        print "Pimlico source directory already exists: delete it if you want to fetch again"
        sys.exit(1)

    if len(args) == 0:
        print "Specify a Pimlico config file to set up Pimlico for"
        print "If you want to start a new project, with an empty config file, use the newproject.py script"
        sys.exit(1)
    else:
        config_file = os.path.abspath(args[0])
        bootstrap(config_file)
