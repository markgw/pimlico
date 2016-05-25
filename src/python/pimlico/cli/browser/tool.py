# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool for browsing datasets, reading from the data output by pipeline modules.
"""
import sys
from importlib import import_module
from traceback import format_exc

import urwid
from pimlico.cli.browser.formatter import DefaultFormatter
from pimlico.core.modules.base import check_type, TypeCheckError
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
    if opts.formatter is not None:
        try:
            fmt_path, __, fmt_cls_name = opts.formatter.rpartition(".")
            fmt_mod = __import__(fmt_path, fromlist=[fmt_cls_name])
            fmt_cls = getattr(fmt_mod, fmt_cls_name)
        except ImportError, e:
            print "Could not load formatter %s: %s" % (opts.formatter, e)
            sys.exit(1)
        # If a formatter's given, use its attribute to determine whether we get raw input
        parse = not fmt_cls.RAW_INPUT
        # Check that the datatype provided is compatible with the formatter's datatype
        try:
            check_type(type(data), fmt_cls.DATATYPE)
        except TypeCheckError, e:
            print "formatter %s is not designed for this datatype (%s)" % (opts.formatter, type(data).__name__)
            sys.exit(1)
        # Instantiate the formatter, providing it with the dataset
        formatter = fmt_cls(data)
    else:
        parse = opts.parse
        formatter = DefaultFormatter(data, raw_data=not opts.parse)

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

    def next_document(state):
        # Get the next doc from the corpus
        try:
            state.next_document()
        except StopIteration:
            footer_text.set_text("Reached end of corpus. Exiting")
            _exit()
        doc_line.set_text("%s  ---  Doc %d / %d" % (state.current_doc_name, state.doc_num+1, state.total_docs))
        if isinstance(state.current_doc_data, InvalidDocument):
            body_text.set_text(
                "== INVALID DOCUMENT ==\nInvalid output was produced by module '%s'.\n\nFull error info from %s:\n%s" %
                (state.current_doc_data.module_name, state.current_doc_data.module_name,
                 state.current_doc_data.error_info)
            )
        else:
            doc = state.current_doc_data
            # Format the doc using the formatter
            try:
                doc = formatter.format_document(doc)
            except:
                # browser_display exists, but there was an error calling it
                doc = "Error formatting datatype %s for display:\n%s" % (type(doc).__name__, format_exc())
            body_text.set_text(doc.encode("ascii", "replace").replace("\t", "    "))

    def skip_docs(value_box, *args):
        skip = value_box.value()
        try:
            corpus_state.skip(skip)
            next_document(corpus_state)
        except StopIteration:
            footer_text.set_text("Reached end of corpus. Exiting")
            _exit()

    # Move onto the first doc to start with
    next_document(corpus_state)

    # Main layout
    main = urwid.LineBox(
        urwid.Frame(
            content_scrollbox,
            header=urwid.Pile(top_widgets),
            footer=urwid.Pile([urwid.Divider(), urwid.Columns(bottom_row)])
        )
    )
    main = SkipPopupLauncher(main, "Skip docs", callback=skip_docs)

    def _keypress(key):
        if key == "esc" or key == "q":
            _exit()
        elif key == "n" or key == "N" or key == " ":
            next_document(corpus_state)
        elif key == "s" or key == "S":
            main.open_pop_up()

    urwid.MainLoop(main, palette=PALETTE, unhandled_input=_keypress, pop_ups=True).run()


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