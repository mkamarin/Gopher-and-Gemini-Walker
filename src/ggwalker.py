#!/usr/bin/python3

""" Gopher and Gemini walker (ggwalker.py)

    Terminal utility to navigate a folder structure containing a Gopher 
    hole or a Gemini capsule.  Useful to verify  your Gopher hole or 
    Gemini capsule before deploying them to the hosting environment.

    Copyright (C) 2021 Mike Marin -- All Rights Reserved

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

    You can contact me at mmarin <at> acm <dot> org
"""

import os
import re
import sys
import cmd
import json
import getopt
import inspect
import textwrap
import mimetypes
import webbrowser
import subprocess

verbose = False

def vbprint(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def error(*args, **kwargs):
    if verbose:
        print("ERROR [",os.path.basename(sys.argv[0]),":",
                inspect.currentframe().f_back.f_lineno,"]: ",
                *args, **kwargs, sep="", file = sys.stderr)
    else:
        print("ERROR: ", *args, **kwargs, sep="", file = sys.stderr)


def warn(*args, **kwargs):
    if verbose:
        print("WARNING [",os.path.basename(sys.argv[0]),":",
                inspect.currentframe().f_back.f_lineno,"]: ",
                *args, **kwargs, sep="", file = sys.stderr)
    else:
        print("WARNING: ", *args, **kwargs, sep="", file = sys.stderr)

###############|123456789|
# Example      |12 (TXT) |
gopherFiller = '         '
gopherItems  = ['0','1','2','3','4','5','6','7','8','9','+','T','g',
        'I','h','s','i','s']

def gopher_link_line(index, item, text):
    label = '  (?)'
    if   item == '0':     # File
        label  = '(TXT)'
    elif item == '1':     # Directory
        label  = '(DIR)'
    elif item == '9':     # Binary file
        label  = '(BIN)'
    elif item == 'g':     # GIf graphic file
        label  = '(GIF)'
    elif item == 'I':     # Image file (other than GIF)
        label  = '(PIC)'
    elif item == 'h':     # HTML file (may be a URL - indicated with 'URL:')
        label  = '(URL)'
    elif item == 's':     # Sound file
        label  = '(WAV)'
    elif item == '>':     # Non typed item (used for gemini)
        label  = '     '
    return '{:2d} {} \x1b[38;5;119m{}\x1b[0m'.format(index, label, text)

###############|12345|
# Example      |12 > |
geminiFiller = '     '

def gemini_link_line(index, text):
    return '{:2d} > \x1b[38;5;119m{}\x1b[0m'.format(index, text)

def heading_one(line):
    return '\x1b[1m\x1b[4m' + line + '\x1b[0m'

def heading_two(line):
    return '\x1b[1m' + line + '\x1b[0m'

def heading_three(line):
    return '\x1b[4m' + line + '\x1b[0m'

def fenced_line(line, width):
    #return '\x1b[40m' + line.ljust(self.columns) + '\x1b[0m'
    return '\x1b[48;5;239m' + line.ljust(width) + '\x1b[0m'

def separation_line(title, width):
    print('\x1b[1A\x1b[44m' + title.center(width) + '\x1b[0m')

def gopher_real_link(item, parts):
    numParts = len(parts)
    assert numParts > 1
    schema = 'gopher://'
    selector = parts[1]
    host = '' if numParts < 3 else parts[2].strip()
    port = '' if numParts < 4 else parts[3].strip()

    if (item == 'h') and selector.startswith('URL:'):
        selector = selector[4:].strip()
        if re.search(r'^[a-zA-Z]+://',selector):
            return selector  # a fully qualified URL
    if selector[0] != '/':
        return selector # A local file or directory
    if host and port:
        port = '' if port == '70' else ':' + port
        return schema + host + port + selector # remote file or directory
    return selector # if everything fails

def gopher_file_item(name):
    mime = mimetypes.MimeTypes().guess_type(name)[0]
    if not mime:
        if (name.endswith('gophermap') or name.endswith('.gmi') 
                or name.endswith('.gemini')):
            return '0'
        else:
            return '1' # Assume directory
    mm = mime.split('/')
    if mime == 'image/gif':
        item = 'g' # GIF graphic
    elif mime == 'text/html':
        item = 'h' # HTML file
    elif mm[0] == 'text':
        item = '0' # Plain text
    elif (mm[0] == 'application') or (mm[0] == 'video'):
        item = '9' # Binary (including pdf)
    elif mm[0] == 'image':
        item = 'I' # grafic files other than GIF
    elif mm[0] == 'audio':
        item = 's' # Sound file
    else:
        item = '9' # default to Binary
    return item

def link_type(item, text):
    local = False if re.search(r'^[a-zA-Z]+://', text) else True
    if item == '>': ## This is a gemini link, so need mime:
        item = gopher_file_item(text)

    if item in ['0','4','5','6','9','g','I','h','s']:
        return local, 'file' # all kind of files
    elif item == '1':
        return local, 'dir' # Directory
    elif item == 'i':
        return  True, 'txt' # Informational message (should not get here)
    elif item == '3':
        return local, 'err' # an Error
    elif item == '+':
        return local, 'svr' # a redundant server
    elif item in ['8','9']:
        return local, 'session' # text base session (telnet, tn3270)
    elif item in ['2','7']:
        return local, 'search' # search sessions
    return local, 'unk'


class walker(cmd.Cmd):
    prompt = 'walker> '
    intro  = "Welcome to Gopher and Gemini walker\nType ? or help for list of commands."

    def __init__(self):
        cmd.Cmd.__init__(self)
        ## Terminal size in number of columns and lines (updated often)
        self.lines    = 0
        self.columns  = 0
        self.minWidth = 80

        self.paging = False # check: https://www.geeksforgeeks.org/print-colors-python-terminal/

        ## Type of processing being done (either gopher or gemini)
        self.processing = ''

        ## Last command to be used in self.default (where self.lastcmd == current command)
        ## Therefore we need to keep our own and set it on self.precmd
        self.last_cmd = ''

        ## Paths are the list of folders containing Gopher or Gemini sites.
        ## Corresponds to <path> in the command line invocation of this program
        ## Paths can be updated by using 'add path' (do_add) or 'remove path' (do_remove)
        ## Paths can be listed by using paths (do_paths)
        ## They can be persisted in a config by using save (do_save) or read (do_read)
        self.paths  = []

        ## Site URLs are used to process fully qualified links (by replacing them with a correct path)
        ## Site URLs can be updated by using 'add url' (do_add) or 'remove url' (do_remove)
        ## They can be listed by using urls (do_urls)
        ## They can be persisted in a config by using save (do_save) or read (do_read)
        self.site_urls = []

        ## Base is the path (from paths above) to the current Gopher or Gemini site being walked
        ## It can only be changed by visit (do_visit)
        ## IMPORTANT MUST never end in '/' (os.sep), we .rstrip(os.sep) when setting it.
        self.base   = ''

        ## Links are the list of raw links in the current page being processed.
        ## Links can be listed using links (do_links)
        ## A page can be a gophermap file, a gemini file (like index.gmi), or a directory
        ## In gopher:
        ##    - a directory without a gophermap file becomes a page listing the content of it
        ##    - a link that starts with '/' is relative to the base (unless it has host & port)
        ##    - otherwise relative to current directory (unless it has host & port or is a URL)
        ## In gemini:
        ##    - a directory without a index.gmi is a problem
        ##    - a link that starts with '/' is relative to the base
        ##    - otherwise relative to current directory
        self.links  = []

        ## Stack of visited links. Used to navigate using back (do_back) and forward (do_forward)
        self.stack  = []
        self.pStack = -1

    def update_stack(self, place):
        self.links = []
        if self.stack and (self.stack[self.pStack] == place):
            return
        if self.pStack != (len(self.stack) -1):
            self.stack = self.stack[:self.pStack+1]
        self.stack.append(place)
        self.pStack += 1

    def back_stack(self):
        if 0 <= (self.pStack -1) < len(self.stack):
            self.pStack -= 1
            return self.stack[self.pStack]
        else:
            return self.base

    def forward_stack(self):
        if 0 <= (self.pStack +1) < len(self.stack):
            self.pStack += 1
            return self.stack[self.pStack]
        elif self.stack and (self.pStack == (len(self.stack) -1)):
            return self.stack[self.pStack]
        else:
            return self.base

    def current_stack(self):
        if 0 <= self.pStack < len(self.stack):
            return self.stack[self.pStack]
        else:
            return self.base

    def clear_stack(self):
        self.stack  = []
        self.pStack = -1

    def remove_base(self, place):
        return place.replace(self.base, '', 1)

    def new_page(self, place, title):
        separation_line(title, self.columns)
        self.update_stack(place)

    def best_width(self):
        return self.minWidth if self.minWidth <= self.columns else self.columns

    ##################################################################
    ###                    Processing section                      ###
    ### This section do the real work of generating the output     ###
    ###        Composed of various process_* functions             ###
    ##################################################################
    def process_gopher_map(self, name):
        if not os.path.isfile(name):
            error('File does not exist [',name,']')
            return
        self.processing = 'gopher'
        count = 1
        try:
            flSrc = open(name, 'rt')
            self.new_page(name, 'Gopher menu [' + 
                    self.remove_base(name) + ']')

            while True:
                line = flSrc.readline()
                if not line:
                    break
                part = line.rstrip('\r\n').split('\t')
                numParts = len(part)
                item = '' if not part[0] else part[0][0]
                if not item:
                    print()
                elif (item == 'i') and (numParts > 1):
                    print(gopherFiller + fenced_line(part[0][1:],self.best_width()))
                elif (numParts > 1) and (item in gopherItems):
                    part[0] = part[0][1:]
                    self.links.append(item + gopher_real_link(item, part))
                    print(gopher_link_line(count, item, part[0]))
                    count += 1
                else:
                    print(gopherFiller + part[0])

        except OSError as e:
            error(e, " while processing", name)

        flSrc.close()

    def process_gemini_map(self, name):
        if not os.path.isfile(name):
            error('File does not exist [',name,']')
            return
        self.processing = 'gemini'
        count = 1
        isFenced = False
        try:
            flSrc = open(name, 'rt')
            self.new_page(name, 'Gemini page [' + 
                    self.remove_base(name) + ']')
            lineWidth = self.minWidth

            while True:
                line = flSrc.readline()
                if not line:
                    break
                line = line.rstrip('\r\n')
                
                ## From: https://gemini.circumlunar.space/docs/specification.html
                ## Note that I relaxed the start of the line to allow spaces 
                ##      (as it is not clear in the spec)
                if re.search(r"^\s*```",line): # Section 5.4.3 Preformatting toggle lines
                    isFenced = not isFenced
                    continue
                if isFenced:                   # Section 5.4.4 Preformated text lines
                    print(geminiFiller + fenced_line(line,self.best_width()))
                    continue
                if not line.strip('\t '):
                    print()
                if re.search(r'^\s*=>',line):  # Section 5.4.2 Link lines
                    line  = line.strip()[2:].strip()
                    parts = re.split(r'\s+',line, 1)
                    label = parts[0] if len(parts) == 1 else parts[1]
                    self.links.append('>' + parts[0].strip())
                    print(gemini_link_line(count, label))
                    count += 1
                    continue
                if re.search(r'^\s*#+',line):  # Section 5.5.1 Heading lines
                    line  = line.strip('\t ')
                    if line.startswith('###'):
                        line  = line[3:].strip('\t ')
                        print(geminiFiller + heading_three(line))
                    elif line.startswith('##'):
                        line  = line[2:].strip('\t ')
                        print(geminiFiller + heading_two(line))
                    else:
                        line  = line[1:].strip('\t ')
                        print(geminiFiller + heading_one(line))
                    continue
                if re.search(r'^\s*\* ',line): # Section 5.5.2 Unordered list items
                    lines = textwrap.wrap(line.strip('\t ')[2:],
                            initial_indent='*  ', subsequent_indent='   ',
                            width = lineWidth)
                    for l in lines:
                        print(geminiFiller + l)
                    continue
                if re.search(r'^\s*>',line):   # Section 5.5.3 Quote lines
                    lines = textwrap.wrap(line.strip('\t ')[1:],
                            initial_indent=geminiFiller, 
                            subsequent_indent=geminiFiller, 
                            width = lineWidth - len(geminiFiller))
                    for l in lines:
                        print(geminiFiller + l)
                    continue
                                               # Section 5.4.1 Text lines
                lines = textwrap.wrap(line, width = lineWidth)
                for l in lines:
                    print(geminiFiller + l)

        except OSError as e:
            error(e, " while processing", name)

        flSrc.close()

    def process_external_app(self, name):
        try:
            self.new_page(name, 'Invoke app [' + 
                    self.remove_base(name) + ']') 

            subprocess.run(['xdg-open', name])
        except OSError as e:
            error(e, " while processin file: [", name,"]")

    def process_text_file(self, name):
        try:
            flSrc = open(name, 'rt')
            self.new_page(name, 'Text file [' + 
                    self.remove_base(name) + ']')

            while True:
                line = flSrc.readline()
                if not line:
                    break
                print(line)

        except OSError as e:
            error(e, " while processing", name)

        flSrc.close()

    def process_gopher_dir(self, name):
        self.processing = 'gopher'
        count = 1
        try:
            files = os.listdir(name)
            self.new_page(name, 'Gopher directory [' + 
                    self.remove_base(name) + ']')

            print('\nContent:\n')
            for filename in files:
                path = os.path.join(name,filename)
                item = '1' if os.path.isdir(path) else gopher_file_item(filename)
                # Path must be relative to base
                self.links.append(item + (path.replace(self.base, '', 1)))
                print(gopher_link_line(count, item, filename))
                count += 1
            print()

        except OSError as e:
            error(e, " while processing", name)

    def process_url(self, url):
        self.new_page(url, 'URL [' + url + ']')
        webbrowser.open(url)

    def print_list(self, lst, padding=' ', marker=0):
        count = 1
        for l in lst:
            print('{}{:2d} {} \x1b[38;5;119m{}\x1b[0m'.format(padding, 
                count, '  ' if marker != count else '=>', l))
            count += 1

    ##################################################################
    ###                    Navigation section                      ###
    ### This section deals with finding the right content to print ###
    ### But, it does not print the content. Mostly visit_* defs    ###
    ##################################################################

    def visit_file(self, name):
        if not os.path.isfile(name):
            error('Must be a valid file [',name,']')
            return
        mime = mimetypes.MimeTypes().guess_type(name)[0]
        if not mime:
            error('Unknown file type [',name,']')
            return
        mm = mime.split('/')
        if mm[0] == 'text':
            self.process_text_file(name)
        else:
            self.process_external_app(name)

    def rebase_link(self, link):
        for url in self.site_urls:
            if link.startswith(url):
                ## First try our current base
                new = link.replace(url,self.base,1)
                if os.path.exists(new):
                    return new
                ## Now try other paths
                for p in self.paths:
                    new = link.replace(url,p,1)
                    if os.path.exists(new):
                        self.base = p
                        self.clear_stack()
                        return new
        return ''

    def base_link(self, link):
        ## Link relative to the base
        if (not link) or (link[0] == '/'):
            return self.base
        ## Link relative to the current place on the stack
        stk = self.current_stack()
        if os.path.isdir(stk):
            return stk
        else:
            return os.path.dirname(stk)

    def visit_link(self, id):
        try:
            link = self.links[id]
            item = link[0]
            rest = link[1:]
            local, kind = link_type(item, rest)
            localLink = ''
            if (not local and (rest.startswith('gopher://') or 
                    rest.startswith('gemini://'))):
                localLink = self.rebase_link(rest)
            if localLink:
                local = True
            else:
                localLink = os.path.join(self.base_link(rest),rest.strip(os.sep))
            if local and (kind == 'dir'):
                self.visit(localLink)
            elif local and (kind == 'file'):
                if rest.endswith('gophermap'):
                    self.process_gopher_map(localLink)
                elif rest.endswith('.gmi') or rest.endswith('.gemini'):
                    self.process_gemini_map(localLink)
                else:
                    self.visit_file(localLink)
            elif not local:
                self.process_url(rest)
            else:
                print("Not supported [",rest,"]")

        except IndexError:
            print('Invalid link id')

    def visit_stack(self, place):
        if re.search(r'^[a-zA-Z]+://',place):
            self.process_url(place)
        elif os.path.isdir(place):
            self.visit(place)
        elif os.path.isfile(place):
            if place.endswith('.gmi') or place.endswith('.gemini'):
                self.process_gemini_map(place)
            elif place.endswith('gophermap'):
                self.process_gopher_map(place)
            else:
                self.visit_file(place)
        else:
            error("Unknown place [",place,"]")

    def visit(self, place):
        '''Place must be a fully qualified directory path'''

        if not os.path.isdir(place):
            error('Place must be a valid directory [',place,']')
            return
        name = place.rstrip(os.sep) + os.sep + 'gophermap'
        if os.path.isfile(name):
            self.process_gopher_map(name)
            return
        name = place.rstrip(os.sep) + os.sep + 'index.gmi'
        if os.path.isfile(name):
            self.process_gemini_map(name)
            return
        name = place.rstrip(os.sep) + os.sep + 'index.gemini'
        if os.path.isfile(name):
            self.process_gemini_map(name)
            return
        if self.processing and (self.processing == 'gopher'):
            self.process_gopher_dir(place)
        elif self.processing and (self.processing == 'gemini'):
            error("Not a Gemini file '", place,"'")
        else:
            error("Unable to find the site at '", place,"'")


    #################################################################
    ###                      Command section                      ###
    ###  This section deals with the cmd.Cmd stuff (do_*, etc.)   ###
    #################################################################
    def precmd(self, line):
        sx = os.get_terminal_size()
        # set the terminal configuration:
        self.lines, self.columns  = sx.lines, sx.columns
        self.last_cmd = self.lastcmd
        if self.columns < self.minWidth:
            warn("Terminal too narrow at ",self.columns," (min ",self.minWidth,")\n")
        return line

    def do_exit(self, line):
        return True

    def do_shell(self, line):
        '''Run a shell command (shortcut: '!')'''
        print("line:",line)
        out = os.popen(line).read()
        print(out)
        self.last_output = out

    def help_exit(self):
        print("Exit execution (shortcuts: 'q', 'e' and '<Ctrl>-D')")

    def do_links(self, line):
        '''List the raw links in the current page (shorcut 'l')'''
        if not self.links:
            print("No links currently availables")
            return
        separation_line('List of raw links in [' + 
                self.remove_base(self.current_stack()) + ']', self.columns)
        count = 1
        for link in self.links:
            item = link[0]
            rest = link[1:] if not link[1:].startswith('URL:') else link[5:]
            print(gopher_link_line(count, item, rest))
            count += 1

    def do_visit(self, line):
        '''Visit a path to a Gopher hole or Gemini capsule (shortcut 'v')\nv[isit] [<path-number>|<path>]'''
        path = line.strip("'\"\t ")
        old = self.base
        self.base = ''
        self.clear_stack()
        if path:
            if path.isdigit():
                if 0 < int(path) <= len(self.paths):
                    self.base = self.paths[int(path)-1]
                else:
                    error("invalid path index")
            else:
                if not (path in self.paths):
                    self.base = path.rstrip(os.sep)
            self.visit(self.base)
        else:
            if old:
                self.base = old
                self.visit(self.base)
            elif len(self.paths) == 1:
                self.base = self.paths[0]
                self.visit(self.base)
            else:
                error("missing path or index")

    def do_set(self, line):
        '''Set the following:\n    p[aging] = [true|false] (default false)\n    w[idth] = <number> (must be greater than 80)'''
        line = line.strip()
        if line:
            opt = line.split('=')
            lside = opt[0].strip()
            rside = '' if len(opt) <= 1 else opt[1].strip()
            if lside in ['p', 'paging']:
                self.paging = True if (not rside) or (rside.lower() == 'true') else False
                return
            elif lside in ['w', 'width']:
                if rside.isdigit():
                    w = int(rside)
                    self.minWidth = w if w >= 80 else 80
                    return
        print("Invalid set option ",line)


    ### This section deal with configuration files ###
    def do_save(self, line):
        '''Save configuration to <file> (shortcut 's')\ns[ave] [<file>] (default to config.json)'''
        name = line.strip("'\"\t ")
        name = name if name else 'config.json'
        config = { 'paths' : self.paths, 'site_urls' : self.site_urls }
        with open(name, 'w') as fl:
            json.dump(config, fl)
        print("saved to",name)

    def do_read(self, line):
        '''Read configuration from <file> (shortcut 'r')\nre[ad] [<file>] (default to config.json)'''
        name = line.strip("'\"\t ")
        name = name if name else 'config.json'
        with open(name, 'r') as fl:
            config = json.load(fl)
        self.paths     = list(filter(None, config['paths']))
        self.site_urls = list(filter(None, config['site_urls']))
        print("read from",name)

    ### This section deal with list of paths commands ###
    def do_add(self, line):
        '''Add <path> to bookmarks of paths (shortcut 'a')\na[dd] [ p[ath] <path> | u[rl] <url>]'''
        what = line.strip().split(' ',1)
        if len(what) != 2:
            error("Missing component should be 'a[dd] [p[ath] <path> | u[rl] <url>]'") 
            return

        if what[0].strip().lower() in ['p', 'path']:
            path = what[1].strip("'\"\t ")
            if path:
                if not (path in self.paths):
                    self.paths.append(path.rstrip(os.sep))
        elif what[0].strip().lower() in ['u', 'url']:
            url = what[1].strip()
            if url:
                if not (url in self.site_urls):
                    self.site_urls.append(url.rstrip(os.sep))
        else:
            error("Invalid type 'a[dd] [p[ath] <path> | u[rl] <url>]'") 
            return

    def do_remove(self, line):
        '''Remove a <path> from paths (shortcut 're')\nr[emove] [p[ath] <number>|<path>] [u[rl] <number>|<url>]'''
        what = line.strip().split(' ',1)
        if len(what) != 2:
            error("Missing component should be 're[move] [p[ath] <number>|<path>] [u[rl] <number>|<url>]'") 
            return

        if what[0].strip().lower() in ['p', 'path']:
            path = what[1].strip("'\"\t ")
            if path:
                if path.isdigit():
                    if int(path) < len(self.paths):
                        del self.paths[int(path)]
                    else:
                        error("invalid index")
                else:
                    if path in self.paths:
                        self.paths.remove(path)
                    else:
                        error("path not in list")
        elif what[0].strip().lower() in ['u', 'url']:
            url = line.strip("'\"\t ")
            if url:
                if url.isdigit():
                    if int(url) < len(self.site_urls):
                        del self.site_urls[int(url)]
                    else:
                        error("invalid index")
                else:
                    if url in self.site_urls:
                        self.site_urls.remove(url)
                    else:
                        error("url not in list")
        else:
            error("Invalid type 're[move] [p[ath] <number>|<path>] [u[rl] <number>|<url>]'") 
            return

    def do_forward(self, line):
        '''Forward to next page in the site stack (shortcut 'f')'''
        self.visit_stack(self.forward_stack())

    def do_back(self, line):
        '''Back to previous page in the site stack (shortcut 'b')'''
        self.visit_stack(self.back_stack())

    def do_paths(self, line):
        '''List of paths to visit (shortcut 'p')\np[aths]'''
        separation_line('List of Paths', self.columns)
        self.print_list(self.paths)

    def do_urls(self, line):
        '''List of site URLs'''
        separation_line('List of URLs', self.columns)
        self.print_list(self.site_urls)

    def do_dump(self, line):
        '''Dump internal structures'''
        separation_line('Dump of internal structures', self.columns)
        print("Terminal:\n    Lines:     ",self.lines,
                "\n    Columns:   ",self.columns,
                "\n    min width: ",self.minWidth,
                "\nProcessing:",self.processing,
                "\nBase: \x1b[38;5;119m ",self.base,
                "\x1b[0m\nPaths:", sep='')
        self.print_list(self.paths,'    ')
        print("\nSite URLs:")
        self.print_list(self.site_urls,'    ')
        print("\nLinks:")
        self.print_list(self.links,'    ')
        print("\nStack(",self.pStack+1,"):", sep='')
        self.print_list(self.stack,'    ',self.pStack+1)


    def default(self, line):
        ln = line.split(' ',1)
        line = '' if len(ln) <= 1 else ln[1]
        CMD = ln[0].strip()
        if CMD in ['q','e']:
            return self.do_exit(line)
        elif CMD == 'p':
            return self.do_paths(line)
        elif CMD == 'l':
            return self.do_links(line)
        elif CMD == 'a':
            return self.do_add(line)
        elif CMD == 'r':
            return self.do_remove(line)
        elif CMD == 're':
            return self.do_read(line)
        elif CMD == 's':
            return self.do_save(line)
        elif CMD == 'b':
            return self.do_back(line)
        elif CMD == 'f':
            return self.do_forward(line)
        elif CMD == 'v':
            return self.do_visit(line)
        elif CMD.isdigit():
            if (self.last_cmd in ['p', 'paths'] 
                    and (0 < int(CMD) <= len(self.paths))):
                return self.do_visit(CMD)
            elif (0 < int(CMD) <= len(self.links)):
                return self.visit_link(int(CMD) -1)
            else:
                error("Index out of range in current context")
        else:
            error("Invalid command")

    do_EOF    = do_exit
    help_EOF  = help_exit
    do_quit   = do_exit
    help_quit = help_exit


def offline_walk(w):

    def gopher_hole(path): # input path is a file name
        # path is a fully qualified file name
        files = set()

        def extract_links(item,base,local, name): 
            # item is the gopher line item (first charcter of the line)
            # base is site base (directory of initial index.gmi)
            # local is the local directory 
            # name is the file name to extract links from
            links = set()
            listFiles = []
            nonlocal files
            # We set the fileName to open depending of the original name that is 
            # indicated by the first char of the name
            # a '/' indicates relatibe to the base, otherwise relative to the file was being analyzed
            fileName = base + name if name and name[0] == os.sep else local + os.sep + name
            if os.path.isdir(fileName):
                if fileName[-1] == os.sep:
                    name = fileName + "gophermap"
                else:
                    name = fileName + os.sep + "gophermap"
                if os.path.isfile(name):
                    fileName = name
            #print("Extracting:[",fileName,"[",base,"]",local,"[",name,"]",sep='')
            if not os.path.isfile(fileName) and not os.path.isdir(fileName):
                print("ERROR: path not present [",fileName,"]",sep='')
                print("ALL:",item,"[",base,"]",local,"[",name,"]",sep='')
                return
            elif os.path.isdir(fileName):
                # Note that in gopher a directory without a gophermap mean that all files should be listed in the client
                listFiles = os.listdir(fileName) 
            if fileName in files:
                return
            if listFiles:
                files.update(listFiles)
            else:
                files.add(fileName)
            if not fileName.endswith("gophermap"):
                return
            print("Processing:",fileName)
            with open(fileName,'r') as hole:
                for line in hole:
                    line = line.rstrip(' \r\n')
                    if not line:
                        continue
                    item = line[0]
                    if not item in ['0','1','4','5','6','9','g','I','h','s']:
                        continue
                    linePart = line.split('\t')
                    if len(linePart) == 1: # Gopher lines without tabs are just text
                        continue
                    if len(linePart) < 2:
                        print("ERROR invalid link: [",line,"]",sep='')
                        continue
                    url = linePart[1]
                    if len(url) > 0:
                        links.add(item + url)

            new_local = os.path.dirname(fileName)
            for l in links:
                if re.match(r'^hURL:',l):
                    print("Ignoring external link:",l[1:])
                else:
                    extract_links(l[0],base, new_local, l[1:])
            return


        base = path[:-1*len(os.sep + "gophermap")]
        print("Gopher hole:",path)
        extract_links('1',base, base, os.sep + "gophermap")
        return files

    def gemini_capsule(path): 
        # path is a fully qualified file name
        files = set()

        def extract_links(base,local, name): 
            # base is site base (directory of initial index.gmi)
            # local is the local directory 
            # name is the file name to extract links from
            links = set()
            nonlocal files
            # We set the fileName to open depending of the original name that is 
            # indicated by the first char of the name
            # a '/' indicates relatibe to the base, otherwise relative to the file was being analyzed
            fileName = base + name if name and name[0] == os.sep else local + os.sep + name
            #print("Extracting:[",fileName,"[",base,"]",local,"[",name,"]",sep='')
            if not os.path.isfile(fileName):
                print("ERROR: File not present [",fileName,"]",sep='')
                print("ALL:[",base,"]",local,"[",name,"]",sep='')
                return 
            if fileName in files:
                return
            files.add(fileName)
            if not fileName.endswith(".gmi"):
                return
            with open(fileName,'r') as capsule:
                for line in capsule:
                    if not line.startswith("=>"):
                        continue
                    url = re.split(r'[ \t]+',line[2:].lstrip(" \t"))[0]
                    if len(url) > 0:
                        links.add(url)

            new_local = os.path.dirname(fileName)
            for l in links:
                if re.match(r'^[a-z]*:',l):
                    print("Ignoring external link:",l)
                else:
                    extract_links(base, new_local, l)
            return 

        base = path[:-1*len(os.sep + "index.gmi")]
        print("Gemini capsule: [",path,"] in ",base,sep='')
        extract_links(base, base, os.sep + "index.gmi")
        return files

    visited_files = set()
    visited_sites = set()
    for path in w.paths:
        print("\nProcessing:",path)
        if os.path.isdir(path):
            if os.path.isfile(path + os.sep + "gophermap"):
                visited_files |= gopher_hole(path + os.sep + "gophermap")
                visited_sites.add(path)
            elif os.path.isfile(path + os.sep + "index.gmi"):
                visited_files |= gemini_capsule(path + os.sep + "index.gmi")
                visited_sites.add(path)
            else:
                print("Invalid path:",path,"[Missing either gophermap or index.gmi]")
        elif os.path.isfile(path) and path.endswith("gophermap"):
            visited_files |= gopher_hole(path)
            visited_sites.add(path[:-1*len(os.sep + "gophermap")])
        elif os.path.isfile(path) and path.endswith("index.gmi"):
            visited_files |= gemini_capsule(path)
            visited_sites.add(path[:-1*len(os.sep + "index.gmi")])
        else:
            print("Invalid path:",path,"[Not a directory, a gophermap, or a index.gmi]")

    # This is what we have collected
    print("Visited sites:")
    for s in visited_sites:
        print("Site:",s)
    print("Visited files:")
    for f in visited_files:
        print("File:",f)

    # Now we need to files that were not linked (meaning not in the visited_file set)
    # For that we need to navigate the whole directory structure provided as the input
    print("Orphan files:")
    for path in w.paths:
        for root, dirs, files in os.walk(path):
            for name in files:
                #print(os.path.join(root,name)," [",root,"]",name,sep='')
                fullName = os.path.join(root,name)
                if not fullName in visited_files:
                    print("Orphan:",fullName)


def arguments() :
    print("Usage:\n ",os.path.basename(sys.argv[0])," [online | online] [flags] [<path> ... <path>]\n\nFlags:")
    print("   online                 Indicated intereactive mode (default)")
    print("   offline                Walk the indicated path in offline mode")
    print("                          checking that all links are correct")
    print("   -s, --site-url  <url>  Site url for the sites being processed")
    print("                          (e.g gopher://my.site or gemini://host.name.com)")
    print("                          replacing site-url with <path> in a link should")
    print("                          generate a valid path (this flag can repeat)")
    print("   -w, --width  <number>  Min line width (minimum and default is 80)")
    print("   -c, --config <file>    Read the config file")
    print("   -h, --help             Prints this help")
    print("   -v, --verbose          Produces extra verbose output")
    sys.exit(2)


if __name__ == "__main__":

   arg_values = []
   mode = "online"
   if len(sys.argv) > 1 and sys.argv[1] in ("offline","online"):
       mode = "offline" if sys.argv[1] == "offline" else "online"
       arg_values = sys.argv[2:]
   else:
       arg_values = sys.argv[1:]

   try:
       opts, args = getopt.getopt(arg_values,"hvs:c:w:",
               ["help","verbose","site-url=","config=","width="])
   except getopt.GetoptError as e:
      error(e)
      arguments()

   walk = walker()

   for opt, arg in opts:
      if (opt in ("-h","--help")) or (len(sys.argv) == 1):
         arguments()
      elif opt in ("-v", "--verbose"):
          verbose = True
      elif opt in ("-s", "--site-url"):
         arSiteUrl = arg.strip()
         if(not arSiteUrl.startswith('gopher://')) and (not arSiteUrl.startswith('gemini://')): 
             error("Invalid site-url argument (must start with either gopher:// or gemini://)")
             arguments()
         walk.site_urls.append(arSiteUrl)
      elif opt in ("-c", "--config"):
         walk.do_read(arg)
      elif opt in ("-w", "--width"):
         walk.do_set("width = " + arg)
      elif opt == "": 
          error("Invalid argument")
          arguments()

   if args:
       for arg in args:
           walk.paths.append(arg.rstrip(os.sep))

   if mode == "online":
       walk.cmdloop()
   else:
       offline_walk(walk)

   print("done")


