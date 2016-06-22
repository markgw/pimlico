"""
Script to set up a new Pimlico project, with the standard layout of directories, and fetch Pimlico itself.

Just download this Python file into a new directory where you want your Pimlico project to live and run::
   python newproject.py project_name

"""
import os
import sys
import urllib2


RAW_URL = "https://gitlab.com/markgw/pimlico/raw/master/"


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


def create_directory_structure(dirs, base_dir):
    for dir_name, subdirs in dirs:
        os.mkdir(os.path.join(base_dir, dir_name))
        if subdirs:
            create_directory_structure(subdirs, os.path.join(base_dir, dir_name))


def lookup_bleeding_edge():
    release_list_url = "%sadmin/releases.txt" % RAW_URL
    try:
        release_data = urllib2.urlopen(release_list_url).read()
    except Exception, e:
        print "Could not fetch Pimlico init code from %s: %s" % (release_list_url, e)
        sys.exit(1)
    versions = [line for line in release_data.splitlines() if not line.startswith("#")]
    bleeding_edge = versions[-1]
    # Strip off the 'v' at the beginning, to get just the number
    bleeding_edge = bleeding_edge.lstrip("v")
    return bleeding_edge


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    if len(sys.argv) < 2:
        print "Specify a project name"
        sys.exit(1)
    project_name = sys.argv[1]
    print "Setting up new project '%s'" % project_name

    # Create basic directory structure in standard Pimlico layout
    print "Creating skeleton directory structure in %s" % base_dir
    structure = [
        ("src", [
            ("python", [
                (project_name, [
                    ("datatypes", []),
                    ("modules", []),
                ])
            ])
        ]),
        ("pimlico", []),
        ("output", [])
    ]
    create_directory_structure(structure, base_dir)

    # Look up the latest Pimlico version
    pimlico_version = lookup_bleeding_edge()
    print "Using latest Pimlico version, %s" % pimlico_version

    # Output a basic config file to get us started
    conf_filename = "%s.conf" % project_name
    with open(os.path.join(base_dir, conf_filename), "w") as conf_file:
        conf_file.write(TEMPLATE_CONF.format(pipeline_name=project_name, latest_release=pimlico_version))
    print "Output skeletal config file to %s" % conf_filename

    # Fetch the bootstrap script from the repository
    bootstrap_url = "%sadmin/bootstrap.py" % RAW_URL
    try:
        bootstrap_script = urllib2.urlopen(bootstrap_url).read()
    except Exception, e:
        print "Could not fetch bootstrap script from %s: %s" % (bootstrap_url, e)
        sys.exit(1)
    # Output it here, so we can run it
    with open(os.path.join(base_dir, "bootstrap.py"), "w") as bootstrap_script_file:
        bootstrap_script_file.write(bootstrap_script)
    print "Fetched bootstrap.py"

    try:
        from .bootstrap import bootstrap
    except ImportError:
        print "Got bootstrap.py, but could not import it"
        sys.exit(1)
    print "Bootstrapping project %s to fetch Pimlico and run basic setup..."
    bootstrap(conf_filename)

    # TODO Create symlink to pimlico.sh
    # TODO Run Pimlico for the first time to fetch basic dependencies


TEMPLATE_CONF = """\
[pipeline]
name={pipeline_name}
release={latest_release}
python_path=%(project_root)s/src/python

## Uncomment to create a 'vars' section, containing variable definitions to be used further down
#[vars]
# ...

## Define some Pimlico module instances here as further config sections
#[my_module_name]
#type=python.path.to.module
# ... module options

"""


if __name__ == "__main__":
    main()
