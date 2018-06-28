# This file is part of Pimlico
# Copyright (C) 2016 Mark Granroth-Wilding
# Licensed under the GNU GPL v3.0 - http://www.gnu.org/licenses/gpl-3.0.en.html

"""
Tool for browsing datasets, reading from the data output by pipeline modules.
"""
import os
import sys
from traceback import format_exc

try:
    import urwid
except ImportError:
    print "Urwid is not installed: installing now"
    from pimlico.core.dependencies.python import PythonPackageOnPip
    urwid_dep = PythonPackageOnPip("urwid")
    urwid_dep.install({})

    try:
        import urwid
    except ImportError:
        print "Tried to install Urwid, but still not available"
        raise

from pimlico.cli.browser.formatter import load_formatter
from pimlico.old_datatypes.base import InvalidDocument

urwid.set_encoding("UTF-8")

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
    from pimlico.old_datatypes.base import IterableCorpus

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

    # Catch the special formatter value 'help' that lists available standard formatters
    if opts.formatter == "help":
        standard_formatters = data.data_point_type.formatters
        if len(standard_formatters) == 0:
            print "\nDatatype does not define any standard formatters."
            print "If you don't specify one, the default formatter will be used (raw data)"
        else:
            print "\nStandard formatters for datatype: %s" % ", ".join(name for (name, cls) in standard_formatters)
            print "These can be selected by name using the --formatter option."
            print "If no formatter is selected, %s will be used" % standard_formatters[0][0]
        sys.exit(0)

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

    browse_data(data, formatter, parse=parse, skip_invalid=opts.skip_invalid)


def browse_data(data, formatter, parse=False, skip_invalid=False):
    if not parse:
        data.raw_data = True
    if not data.data_ready():
        if data.module is not None:
            if data.module.module_executable:
                print "Data not available from module output (%s): perhaps it hasn't been run? (base dir: %s)" % \
                      (data.module.module_name, data.base_dir)
            else:
                print "Data not available from non-executable module's output (%s)" % data.module.module_name
        else:
            print "Data not ready: cannot browse it"
        sys.exit(1)

    # Top of the screen
    doc_line = urwid.Text("")
    top_widgets = [
        doc_line,
        urwid.Divider(),
    ]
    if data.base_dir is not None:
        top_widgets.insert(0, urwid.Text("Documents in %s" % data.base_dir))

    # Middle: content
    body_text = urwid.Text(u"")
    #body = [body_text, urwid.Divider()]
    content_scrollbox = urwid.ListBox(urwid.SimpleListWalker([body_text]))

    # Bottom: footer
    footer_text = urwid.Text("", align='right')
    bottom_row = [urwid.Text("Navigation: up, down = scroll | n/space = next doc | s = skip docs | esc/q = exit "
                             "| w = write (save) doc"), footer_text]

    # Management of current document, navigation
    corpus_state = CorpusState(data)

    # Main layout
    main = urwid.LineBox(
        urwid.Frame(
            content_scrollbox,
            header=urwid.Pile(top_widgets),
            footer=urwid.Pile([urwid.Divider(), urwid.Columns(bottom_row)])
        )
    )

    def message(text):
        return MessagePopupLauncher(main, text).open_pop_up()

    def skip_docs(value_box, *args):
        skip = value_box.value()
        try:
            corpus_state.skip(skip)
            next_document(corpus_state)
        except StopIteration:
            footer_text.set_text("Reached end of corpus. Exiting")
            _exit()

    def save_doc(value_box, *args):
        filename = os.path.abspath(value_box.get_edit_text())
        try:
            with open(filename, "w") as f:
                f.write(formatter.format_document(corpus_state.current_doc_data).encode("utf8"))
        except IOError, e:
            message("Could not save file:\n%s" % e)
        else:
            message("Output formatted document to %s" % filename)

    skip_launcher = skip_popup_launcher(main, "Skip docs", callback=skip_docs)
    save_launcher = save_popup_launcher(skip_launcher, "Output document to file", callback=save_doc)

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

            if skip_invalid and isinstance(doc_data, InvalidDocument):
                doc_data = None
                continue

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
            body_text.set_text(unicode(doc).replace(u"\t", u"    "))

    def _keypress(key):
        if key == "esc" or key == "q":
            _exit()
        elif key == "n" or key == "N" or key == " ":
            next_document(corpus_state)
        elif key == "s" or key == "S":
            skip_launcher.open_pop_up()
        elif key == "w" or key == "W":
            save_launcher.open_pop_up()

    main_loop = urwid.MainLoop(save_launcher, palette=PALETTE, unhandled_input=_keypress, pop_ups=True)

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


class InputDialog(urwid.WidgetWrap):
    """A dialog that appears with an input """
    signals = ["close", "cancel"]

    def __init__(self, text, input_edit):
        self.value_box = input_edit
        close_button = urwid.Button("OK", lambda button: self._emit("close"))
        cancel_button = urwid.Button("Cancel", lambda button: self._emit("cancel"))
        buttons = [close_button, cancel_button]

        w = urwid.Pile([
            urwid.Text(text),
            self.value_box,
            urwid.Divider(),
            urwid.Columns([urwid.AttrWrap(b, "selectable") for b in buttons])
        ])
        w = urwid.LineBox(urwid.Filler(w))

        super(InputDialog, self).__init__(urwid.AttrWrap(w, 'popbg'))

    def keypress(self, size, k):
        if k == "enter":
            # Pass enter to the "ok" button
            self._emit("close")
            return
        elif k == "esc":
            self._emit("cancel")
            return
        super(InputDialog, self).keypress(size, k)


class MessageDialog(urwid.WidgetWrap):
    """A dialog that appears with a message """
    def __init__(self, text, default=None):
        w = urwid.Text(text)
        w = urwid.LineBox(urwid.Filler(w))
        super(MessageDialog, self).__init__(urwid.AttrWrap(w, 'popbg'))


class InputPopupLauncher(urwid.PopUpLauncher):
    def __init__(self, original_widget, text, input_edit, callback=None):
        super(InputPopupLauncher, self).__init__(original_widget)
        self.input_edit = input_edit
        self.callback = callback
        self.text = text

    def create_pop_up(self):
        pop_up = InputDialog(self.text, self.input_edit)
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


def skip_popup_launcher(original_widget, text, default=None, callback=None):
    return InputPopupLauncher(original_widget, text, urwid.IntEdit(default=default), callback=callback)


def save_popup_launcher(original_widget, text, default=None, callback=None):
    if default is None:
        default = os.path.join(os.path.expanduser("~"), "")
    return InputPopupLauncher(original_widget, text, urwid.Edit(edit_text=default), callback=callback)


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
