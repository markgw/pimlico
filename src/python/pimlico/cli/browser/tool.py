# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool for browsing datasets, reading from the data output by pipeline modules.
"""

import sys
from traceback import format_exc

try:
    import urwid
except ImportError:
    print "Urwid is not installed: installing now"
    from pimlico.core.dependencies.python import PythonPackageOnPip
    urwid_dep = PythonPackageOnPip("urwid")
    urwid_dep.install()

    try:
        import urwid
    except ImportError:
        print "Tried to install Urwid, but still not available"
        raise

from pimlico.cli.browser.formatter import load_formatter
from pimlico.datatypes.base import InvalidDocument

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


def browse_cmd(pipeline, opts):
    """
    Command for main Pimlico CLI

    """
    from pimlico.datatypes.base import IterableCorpus

    module_name = opts.module_name
    output_name = opts.output_name
    print "Loading %s of module '%s'" % \
          ("default output" if output_name is None else "output '%s'" % output_name, module_name)
    data = pipeline[module_name].get_output(output_name)
    print "Datatype: %s" % data.datatype_name

    # We can only browse tarred corpora document by document
    if not isinstance(data, IterableCorpus):
        print "%s is not a sub-type of iteratable corpus, so can't be browsed (datatype class is %s)" % \
              (data.datatype_name, type(data).__name__)
        sys.exit(1)

    # Check we've got urwid installed
    try:
        import urwid
    except ImportError:
        print "You need Urwid to run the browser: install by running 'make urwid' in the Python lib dir"
        sys.exit(1)

    # Load the formatter if one was requested
    try:
        formatter = load_formatter(data, opts.formatter, parse=not opts.raw)
    except TypeError, e:
        print >>sys.stderr, "Error loading formatter"
        print >>sys.stderr, e
        sys.exit(1)

    if opts.formatter is not None:
        # If a formatter's given, use its attribute to determine whether we get raw input
        parse = not formatter.RAW_INPUT
    else:
        # Otherwise (default formatter), use the cmd-line option
        parse = not opts.raw

    browse_data(data, formatter, parse=parse)


def browse_data(data, formatter, parse=False):
    if not parse:
        data.raw_data = True
    if not data.data_ready():
        print "Data not available from module output: perhaps it hasn't been run? (base dir: %s)" % data.base_dir
        sys.exit(1)

    # Top of the screen
    doc_line = urwid.Text("")
    top_widgets = [
        urwid.Text("Documents in %s" % data.base_dir),
        doc_line,
        urwid.Divider(),
    ]

    # Middle: content
    body_text = urwid.Text("")
    #body = [body_text, urwid.Divider()]
    content_scrollbox = urwid.ListBox(urwid.SimpleListWalker([body_text]))

    # Bottom: footer
    footer_text = urwid.Text("", align='right')
    bottom_row = [urwid.Text("Navigation: up, down = scroll | n/space = next doc | s = skip docs | esc/q = exit"), footer_text]

    # Management of current document, navigation
    corpus_state = CorpusState(data)

    def skip_docs(value_box, *args):
        skip = value_box.value()
        try:
            corpus_state.skip(skip)
            next_document(corpus_state)
        except StopIteration:
            footer_text.set_text("Reached end of corpus. Exiting")
            _exit()

    # Main layout
    main = urwid.LineBox(
        urwid.Frame(
            content_scrollbox,
            header=urwid.Pile(top_widgets),
            footer=urwid.Pile([urwid.Divider(), urwid.Columns(bottom_row)])
        )
    )
    skip_launcher = SkipPopupLauncher(main, "Skip docs", callback=skip_docs)

    def next_document(state):
        doc_data = None
        # Skip over docs until we get one that's not rejected by the formatter
        while doc_data is None:
            # Get the next doc from the corpus
            try:
                state.next_document()
            except StopIteration:
                footer_text.set_text("Reached end of corpus. Exiting")
                _exit()
            doc_line.set_text("%s  ---  Doc %d / %d" % (state.current_doc_name, state.doc_num+1, state.total_docs))
            if main_loop.screen.started:
                main_loop.draw_screen()
            doc_data = formatter.filter_document(state.current_doc_data)

        if isinstance(doc_data, InvalidDocument):
            body_text.set_text(
                "== INVALID DOCUMENT ==\nInvalid output was produced by module '%s'.\n\nFull error info from %s:\n%s" %
                (doc_data.module_name, doc_data.module_name,
                 doc_data.error_info)
            )
        else:
            # Format the doc using the formatter
            try:
                doc = formatter.format_document(doc_data)
            except:
                doc = "Error formatting datatype %s for display:\n%s" % (type(doc_data).__name__, format_exc())
            body_text.set_text(doc.encode("ascii", "replace").replace("\t", "    "))

    def _keypress(key):
        if key == "esc" or key == "q":
            _exit()
        elif key == "n" or key == "N" or key == " ":
            next_document(corpus_state)
        elif key == "s" or key == "S":
            skip_launcher.open_pop_up()

    main_loop = urwid.MainLoop(skip_launcher, palette=PALETTE, unhandled_input=_keypress, pop_ups=True)

    # Move onto the first doc to start with
    next_document(corpus_state)

    main_loop.run()


class CorpusState(object):
    """
    Keep track of which document we're on.
    """
    def __init__(self, corpus):
        self.corpus = corpus
        self.doc_num = -1
        self.total_docs = len(corpus)
        self.current_doc_name = None
        self.current_doc_data = None
        self.doc_iter = iter(corpus)

    def next_document(self):
        self.current_doc_name, self.current_doc_data = self.doc_iter.next()
        self.doc_num += 1
        return self.current_doc_name, self.current_doc_data

    def skip(self, n):
        for i in range(n):
            self.next_document()


def _exit(*args):
    raise urwid.ExitMainLoop()


class SkipDialog(urwid.WidgetWrap):
    """A dialog that appears with an int input """
    signals = ["close", "cancel"]

    def __init__(self, text, default=None):
        close_button = urwid.Button("OK", lambda button: self._emit("close"))
        cancel_button = urwid.Button("Cancel", lambda button: self._emit("cancel"))
        buttons = [close_button, cancel_button]

        self.value_box = urwid.IntEdit(default=default)
        w = urwid.Pile([
            urwid.Text(text),
            self.value_box,
            urwid.Divider(),
            urwid.Columns([urwid.AttrWrap(b, "selectable") for b in buttons])
        ])
        w = urwid.LineBox(urwid.Filler(w))

        super(SkipDialog, self).__init__(urwid.AttrWrap(w, 'popbg'))

    def keypress(self, size, k):
        if k == "enter":
            # Pass enter to the "ok" button
            self._emit("close")
            return
        elif k == "esc":
            self._emit("cancel")
            return
        super(SkipDialog, self).keypress(size, k)


class MessageDialog(urwid.WidgetWrap):
    """A dialog that appears with a message """
    def __init__(self, text, default=None):
        w = urwid.Text(text)
        w = urwid.LineBox(urwid.Filler(w))
        super(MessageDialog, self).__init__(urwid.AttrWrap(w, 'popbg'))


class SkipPopupLauncher(urwid.PopUpLauncher):
    def __init__(self, original_widget, text, default=None, callback=None):
        super(SkipPopupLauncher, self).__init__(original_widget)
        self.callback = callback
        self.text = text
        self.default = default

    def create_pop_up(self):
        pop_up = SkipDialog(self.text, default=self.default)
        if self.callback is not None:
            urwid.connect_signal(pop_up, "close", self.callback, user_args=[pop_up.value_box])
        urwid.connect_signal(pop_up, "close", lambda button: self.close_pop_up())
        urwid.connect_signal(pop_up, "cancel", lambda button: self.close_pop_up())
        return pop_up

    def get_pop_up_parameters(self):
        lines = self.text.splitlines()
        height = len(lines) + 6
        width = max(25, max(len(l) for l in lines) + 4)
        return {'left': 5, 'top': 5, 'overlay_width': width, 'overlay_height': height}


class MessagePopupLauncher(urwid.PopUpLauncher):
    def __init__(self, original_widget, text):
        super(MessagePopupLauncher, self).__init__(original_widget)
        self.text = text

    def create_pop_up(self):
        return MessageDialog(self.text)

    def get_pop_up_parameters(self):
        lines = self.text.splitlines()
        height = len(lines) + 6
        width = max(25, max(len(l) for l in lines) + 4)
        return {'left': 5, 'top': 5, 'overlay_width': width, 'overlay_height': height}
