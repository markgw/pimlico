from __future__ import print_function
from builtins import range

import warnings

try:
    import urwid
except ImportError:
    print("Urwid is not installed: installing now")
    from pimlico.core.dependencies.python import urwid_dependency
    urwid_dependency.install({})

    try:
        import urwid
    except ImportError:
        print("Tried to install Urwid, but still not available")
        raise

PALETTE = [
    ('reversed', 'standout', ''),
    ('body', 'white', 'dark blue', 'standout'),
    ('border', 'black', 'dark blue'),
    ('shadow', 'white', 'black'),
    ('selectable', 'black', 'dark cyan'),
    ('focus', 'white', 'dark blue', 'bold'),
    ('focustext', 'light gray', 'dark blue'),
    ('popbg', 'white', 'dark blue'),
]


def browse_files(reader):
    """
    Browser tool for NamedFileCollections.

    """
    # Top of the screen
    top_widgets = [
        urwid.Text("Reading files from: {}".format(reader.data_dir)),
        urwid.Divider(),
    ]

    def menu_item(caption, callback):
        button = urwid.Button(caption)
        urwid.connect_signal(button, 'click', callback)
        return urwid.AttrMap(button, None, focus_map='reversed')

    def selected(name):
        def _selected(button):
            show_file(name)
        return _selected

    def _file_view_keypress(key):
        if key == "esc":
            # Go back to the main menu
            main_loop.widget = main
            main_loop._unhandled_input = _keypress

    def show_file(filename):
        if filename == "Quit":
            _exit()
        path = reader.get_absolute_path(filename)
        # Try reading some of the file to see if it's text
        if is_binary_file(path):
            # TODO Check whether to show the file
            warnings.warn("{} seems to be a binary file: showing anyway for now".format(filename))
        # Read in the file
        # If the datatype overrides the reading behaviour, use that
        data = reader.datatype.browse_file(reader, filename)
        new_box = urwid.LineBox(urwid.Frame(urwid.ListBox(urwid.SimpleListWalker([
            urwid.Text(data)
        ])), header=urwid.Pile([
            urwid.Columns([
                urwid.Text("File: {}".format(filename)),
                urwid.Text("Esc: return to menu"),
            ]),
            urwid.Divider(),
        ])))
        main_loop.widget = new_box
        main_loop._unhandled_input = _file_view_keypress

    # Middle: content
    # Get the list of filenames that this collection includes
    filenames = reader.filenames + ["Quit"]
    items = [menu_item(filename, selected(filename)) for filename in filenames]
    content_scrollbox = urwid.ListBox(urwid.SimpleFocusListWalker(items))

    #content_scrollbox = yesno_dialog(content_scrollbox,
    #                                  "This appears to be a binary file. Are you sure you want to try displaying it?")

    # Main layout
    main = urwid.LineBox(
        urwid.Frame(
            content_scrollbox,
            header=urwid.Pile(top_widgets),
        )
    )

    def _keypress(key):
        if key == "esc" or key == "q":
            _exit()

    main_loop = urwid.MainLoop(main, palette=PALETTE, unhandled_input=_keypress)
    content_scrollbox.set_focus(0)
    main_loop.run()


def _exit(*args):
    raise urwid.ExitMainLoop()


textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})


def is_binary_string(bytes):
    return bool(bytes.translate(None, textchars))


def is_binary_file(path):
    """ Try reading a bit of a file to work out whether it's a binary file or text """
    with open(path, "rb") as f:
        return is_binary_string(f.read(1024))

