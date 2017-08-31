"""
Script to set up a new Pimlico project, with the standard layout of directories, and fetch Pimlico itself.

Just download this Python file into a new directory where you want your Pimlico project to live and run::
   python newproject.py project_name

The Python interpreter that you use to call this script will be the one used forever more (actually wrapped
by virtualenv) when you run Pimlico.

"""
import os
import sys
import urllib2
import subprocess


RAW_URL = "https://raw.githubusercontent.com/markgw/pimlico/master/"
RELEASE_URL = "%sadmin/release.txt" % RAW_URL


def create_directory_structure(dirs, base_dir):
    for content in dirs:
        if type(content) is tuple:
            # Create a subdirectory, potentially with further subdirectories
            dir_name, subdirs = content
            os.mkdir(os.path.join(base_dir, dir_name))
            if subdirs:
                create_directory_structure(subdirs, os.path.join(base_dir, dir_name))
        else:
            # Things that aren't pairs simply create named files (equivalent to touch)
            filename = os.path.join(base_dir, content)
            with open(filename, "w") as f:
                f.write("")


def lookup_bleeding_edge():
    try:
        release_data = urllib2.urlopen(RELEASE_URL).read()
    except Exception, e:
        print "Could not fetch Pimlico release from %s: %s" % (RELEASE_URL, e)
        sys.exit(1)
    return release_data.splitlines()[-1].lstrip("v")


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    args = sys.argv[1:]

    # Allow the --git switch to pass through to bootstrap function
    if "--git" in args:
        args.remove("--git")
        git = True
    else:
        git = False

    if len(args) == 0:
        print "Specify a project name"
        print "Usage:"
        print "  python newproject.py [--git] <project_name>"
        print
        print "If you specify --checkout, Pimlico will be cloned as a Git repository, rather "
        print "than downloaded from a release. This only works on Linux and requires that Git is "
        print "installed. Most of the time, you don't want to do this: it's only for Pimlico development"
        sys.exit(1)

    project_name = args[0]
    print "Setting up new project '%s'" % project_name

    # Create basic directory structure in standard Pimlico layout
    print "Creating skeleton directory structure in %s" % base_dir
    structure = [
        ("src", [
            ("python", [
                (project_name, [
                    "__init__.py",
                    ("datatypes", ["__init__.py"]),
                    ("modules", ["__init__.py"]),
                ])
            ])
        ]),
        ("output", [])
        # `pimlico` dir will be created by bootstrap.py
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
        from bootstrap import bootstrap
    except ImportError:
        print "Got bootstrap.py, but could not import it"
        sys.exit(1)
    print "\nBootstrapping project %s to fetch Pimlico and run basic setup..." % project_name
    bootstrap(conf_filename, git=git)

    print "Bootstrapped project: Pimlico is now available in pimlico/ dir\n"
    print "Project setup complete!"

    print "\nRunning Pimlico for the first time to test setup and fetch basic dependencies"
    # Make sure that Pimlico uses the same Python interpreter that we're using now
    # This is the one that will be wrapped by virtualenv during the first run, so it will be used in later calls
    pimlico_env = os.environ.copy()
    pimlico_env["PYTHON_CMD"] = sys.executable
    try:
        # Call the status command to check the pipeline is loadable
        # We don't need to check the output of this, just check that it returns successfully
        subprocess.check_call([os.path.join(base_dir, "pimlico.sh"), conf_filename, "status"],
                              cwd=base_dir, env=pimlico_env)
    except subprocess.CalledProcessError:
        # If the status command doesn't work, there's either a problem running Pimlico at all (e.g.
        # unsatisfied basic dependencies) or it couldn't read the config file. The latter shouldn't
        # be the case, since it's our pre-defined skeleton pipeline we're loading
        print "\nError running pimlico.sh for the first time"
        print "Your project setup is complete, but you need to fix the problem above before Pimlico is ready to run"
        print "When you've done that, you can just run the Pimlico 'status' command to check that Pimlico works " \
              "and your pipeline is loadable:"
        print "  ./pimlico.sh %s status" % conf_filename
    else:
        print "\nPimlico setup is complete and Pimlico loads successfully"
        print "Edit the skeletal pipeline config in %s to start building your pipeline." % conf_filename
        print "Then you can run Pimlico on your pipeline using:"
        print "  ./pimlico.sh %s status" % conf_filename

    # Get rid of the scripts themselves used to set up the project
    def _rem(filename):
        if os.path.exists(os.path.join(base_dir, filename)):
            os.remove(os.path.join(base_dir, filename))
    _rem("bootstrap.py")
    _rem("bootstrap.pyc")
    _rem("newproject.py")


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
