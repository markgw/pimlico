"""
Script to set up a new Pimlico project, with the standard layout of directories, and fetch Pimlico itself.

Just download this Python file into a new directory where you want your Pimlico project to live and run::
   python newproject.py project_name

"""
import os
import sys


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


def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    if len(sys.argv) < 2:
        print "Specify a project name"
        sys.exit(1)
    project_name = sys.argv[1]

    # Create basic directory structure in standard Pimlico layout
    structure = [
        ("src", [
            ("python", [
                (project_name, [
                    ("datatypes", []),
                    ("modules", []),
                ])
            ])
        ]),
        ("pimlico", [])
    ]
    create_directory_structure(structure, base_dir)

    # TODO Create a template pipeline config file, using latest version of Pimlico
    # TODO Fetch bootstrap.py from bleeding edge repo
    # TODO Call bootstrap.py to install Pimlico from config file
    # TODO Create symlink to pimlico.sh
    # TODO Run Pimlico for the first time to fetch basic dependencies


if __name__ == "__main__":
    main()
