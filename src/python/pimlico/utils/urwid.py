"""
Some handy Urwid utilities.

Take care only to import this where we already have a dependency on Urwid,
e.g. in the browser implementation modules.

Some of these are taken pretty exactly from Urwid examples.

.. todo::

   Not got these things working yet, but they'll be useful in the long run

"""
from __future__ import absolute_import
import urwid


class DialogExit(Exception):
    pass


class DialogDisplay(urwid.PopUpLauncher):
    palette = [
        ('body','black','light gray', 'standout'),
        ('border','black','dark blue'),
        ('shadow','white','black'),
        ('selectable','black', 'dark cyan'),
        ('focus','white','dark blue','bold'),
        ('focustext','light gray','dark blue'),
    ]

    def __init__(self, original_widget, text, height=0, width=0, body=None):
        super(DialogDisplay, self).__init__(original_widget)
        width = int(width)
        if width <= 0:
            width = ('relative', 80)
        height = int(height)
        if height <= 0:
            height = ('relative', 80)

        self.body = body
        if body is None:
            # fill space with nothing
            body = urwid.Filler(urwid.Divider(),'top')

        self.frame = urwid.Frame( body, focus_part='footer')
        if text is not None:
            self.frame.header = urwid.Pile( [urwid.Text(text),
                urwid.Divider()] )
        w = self.frame

        # pad area around listbox
        w = urwid.Padding(w, ('fixed left',2), ('fixed right',2))
        w = urwid.Filler(w, ('fixed top',1), ('fixed bottom',1))
        w = urwid.AttrWrap(w, 'body')

        # "shadow" effect
        w = urwid.Columns( [w,('fixed', 2, urwid.AttrWrap(
            urwid.Filler(urwid.Text(('border','  ')), "top")
            ,'shadow'))])
        w = urwid.Frame( w, footer =
            urwid.AttrWrap(urwid.Text(('border','  ')),'shadow'))

        # outermost border area
        w = urwid.Padding(w, 'center', width )
        w = urwid.Filler(w, 'middle', height )
        w = urwid.AttrWrap( w, 'border' )

        self.view = w

    def add_buttons(self, buttons):
        l = []
        for name, exitcode in buttons:
            b = urwid.Button( name, self.button_press )
            b.exitcode = exitcode
            b = urwid.AttrWrap( b, 'selectable','focus' )
            l.append( b )
        self.buttons = urwid.GridFlow(l, 10, 3, 1, 'center')
        self.frame.footer = urwid.Pile( [ urwid.Divider(),
            self.buttons ], focus_item = 1)

    def button_press(self, button):
        raise DialogExit(button.exitcode)

    def on_exit(self, exitcode):
        return exitcode, ""


class ListDialogDisplay(DialogDisplay):
    def __init__(self, original_widget, text, height, width, constr, items, has_default):
        j = []
        if has_default:
            k, tail = 3, ()
        else:
            k, tail = 2, ("no",)
        while items:
            j.append( items[:k] + tail )
            items = items[k:]

        l = []
        self.items = []
        for tag, item, default in j:
            w = constr( tag, default=="on" )
            self.items.append(w)
            w = urwid.Columns( [('fixed', 12, w),
                urwid.Text(item)], 2 )
            w = urwid.AttrWrap(w, 'selectable','focus')
            l.append(w)

        lb = urwid.ListBox(l)
        lb = urwid.AttrWrap( lb, "selectable" )
        DialogDisplay.__init__(self, original_widget, text, height, width, lb)

        self.frame.set_focus('body')

    def unhandled_key(self, size, k):
        if k in ('up','page up'):
            self.frame.set_focus('body')
        if k in ('down','page down'):
            self.frame.set_focus('footer')
        if k == 'enter':
            # pass enter to the "ok" button
            self.frame.set_focus('footer')
            self.buttons.set_focus(0)
            self.view.keypress( size, k )

    def on_exit(self, exitcode):
        """Print the tag of the item selected."""
        if exitcode != 0:
            return exitcode, ""
        s = ""
        for i in self.items:
            if i.get_state():
                s = i.get_label()
                break
        return exitcode, s


def msgbox(original_widget, text, height=0, width=0):
    d = DialogDisplay(original_widget, text, height, width)
    d.add_buttons([("OK", 0)])
    return d


def options_dialog(original_widget, text, options, height=0, width=0, *items):
    radiolist = []

    def constr(tag, state, radiolist=radiolist):
        return urwid.RadioButton(radiolist, tag, state)

    d = ListDialogDisplay(text, height, width, constr, items, True)
    d.add_buttons([(name, num) for (num, name) in enumerate(options)])
    return d


def yesno_dialog(original_widget, text, height=0, width=0, *items):
    return options_dialog(original_widget, text, ["Yes", "No"], height=height, width=width, *items)
