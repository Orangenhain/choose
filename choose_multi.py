#!/usr/bin/python
#
# Urwid example similar to dialog(1) program
#    Copyright (C) 2004-2009  Ian Ward
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Urwid web site: http://excess.org/urwid/

import urwid

import sys, os
from itertools import chain
import fileinput


class DialogExit(Exception):
    pass

class DialogDisplay:
    palette = [
        ('border','black','dark blue'),
        # ('selectable','black', 'dark cyan'),   # background for (selectable) lines
        ('focus','white','dark blue','bold'),
        ('focustext','light gray','dark blue'),
        ]
        
    def __init__(self, body=None):
        self.body = body
        self.frame = urwid.Frame( body, focus_part='footer')
        
        w = self.frame
        
        self.view = w

    def main(self):
        self.loop = urwid.MainLoop(self.view, self.palette)
        try:
            self.loop.run()
        except DialogExit, e:
            return self.on_exit( e.args[0] )
        
    def on_exit(self, exitcode):
        return exitcode, ""
        

class MyCheckBox(urwid.CheckBox):
    def keypress(self, size, key):
        # f*cking Python won't let me call super here, as urwid is using old-style classes  (resulting in: "TypeError: must be type, not str")
        #   ... so we just copy the code from the source
        if self._command_map[key] != 'activate':
            return key
        
        self.toggle_state()
    
class CheckListDialogDisplay(DialogDisplay):
    def __init__(self, *items):
        j = []
        
        k, tail = 3, ()
        
        while items:
            j.append( items[:k] + tail )
            items = items[k:]
                    
        l = []
        self.items = []
        for tag, item, default in j:
            checkbox = MyCheckBox( tag, default=="on", on_state_change=self.on_checkbox_change, user_data=tag )
            self.items.append([checkbox, item])
            w = urwid.Columns( [('fixed', 12, checkbox), 
                urwid.Text(item)], 2 )
            w = urwid.AttrWrap(w, 'selectable','focus')
            l.append(w)

        lb = urwid.ListBox(l)
        # lb = urwid.AttrWrap( lb, "selectable" )   # extend background for (selectable) lines to the whole ListBox/screen
        DialogDisplay.__init__(self, lb )
        
        self.frame.set_focus('body')

    def on_exit(self, exitcode):
        if exitcode != 0:
            return exitcode, ""
        l = []
        for i in self.items:
            w = i[0]
            t = i[1]
            if w.get_state():
                l.append(t)
        return exitcode, "\n".join(l)
    
    def on_checkbox_change(self, w, state, user_data):
        # sys.exit(int(user_data))
        if w == self.items[-1][0]:
            raise DialogExit(0)
    

import select
def main():
    lines = []
    # http://repolinux.wordpress.com/2012/10/09/non-blocking-read-from-stdin-in-python/
    while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline()
        if line:
            lines.append(line.rstrip('\n'))
        else:
            # an empty line means stdin has been closed
            break
    else:
        # no input
        pass

    # lines = sys.argv[1:] if (len(sys.argv) > 1) else [line.strip() for line in fileinput.input()]
    # lines = sys.argv[1:]
    lines += sys.argv[1:]

    
    # save old stdout and in
    old_out = sys.__stdout__
    old_in  = sys.__stdin__
    old_err = sys.__stderr__
    sys.__stdout__ = sys.stdout = open('/dev/tty', 'w')
    sys.__stdin__  = sys.stdin  = open('/dev/tty')
    os.dup2(sys.stdin.fileno(), 0)
    
    
    items = list(chain.from_iterable( ("row " + str(i), lines[i], "off") for i in xrange(0,len(lines))))
    items += ["Done", "", "off"]
    
    d = CheckListDialogDisplay( *items )
    
    # Run it
    exitcode, exitstring = d.main()

    print "This won't go to the pipe!"

    sys.stdout.flush()
    sys.stderr.flush()
    sys.stdin.close()
    sys.stdout.close()
    sys.stderr.close()
    sys.__stdout__ = sys.stdout = old_out
    sys.__stdin__  = sys.stdin  = old_in
    sys.__stderr__ = sys.stderr = old_err

    
    # Exit
    if exitstring:
        print exitstring
    
    sys.exit(exitcode)
        

if __name__=="__main__": 
    main()
