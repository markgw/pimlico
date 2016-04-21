"""
Tool for browsing datasets, reading from the data output by pipeline modules.
"""
import sys

import urwid
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


def browse_data(data):
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
    body = [body_text, urwid.Divider()]

    # Bottom: footer
    footer_text = urwid.Text("", align='right')
    bottom_row = [urwid.Text("Navigation: up, down = scroll | n = next doc | s = skip docs | esc/q = exit"), footer_text]

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
            body_text.set_text(unicode(state.current_doc_data).encode("ascii", "replace").replace("\t", "    "))

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
            urwid.ListBox(urwid.SimpleFocusListWalker(body)),
            header=urwid.Pile(top_widgets),
            footer=urwid.Pile([urwid.Divider(), urwid.Columns(bottom_row)])
        )
    )
    main = SkipPopupLauncher(main, "Skip docs", default=1, callback=skip_docs)

    def _keypress(key):
        if key == "esc" or key == "q":
            _exit()
        elif key == "n" or key == "N":
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

    def __init__(self, text, default=0):
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
    def __init__(self, original_widget, text, default=0, callback=None):
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