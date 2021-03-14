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

#mport io
#mport random
#mport urllib
#mport datetime

verbose = False

def vbprint(*args, **kwargs):
    if verbose:
        print(*args, **kwargs)


def error(*args, **kwargs):
    if verbose:
        print("ERROR [",os.path.basename(sys.argv[0]),":",inspect.currentframe().f_back.f_lineno,"]: ",
                *args, **kwargs, sep="", file = sys.stderr)
    else:
        print("ERROR: ", *args, **kwargs, sep="", file = sys.stderr)


def warn(*args, **kwargs):
    if verbose:
        print("WARNING [",os.path.basename(sys.argv[0]),":",inspect.currentframe().f_back.f_lineno,"]: ",
                *args, **kwargs, sep="", file = sys.stderr)
    else:
        print("WARNING: ", *args, **kwargs, sep="", file = sys.stderr)

###############|123456789|
# Example      |12 (TXT) |
gopherFiller = '         '
gopherItems  = ['0','1','2','3','4','5','6','7','8','9','+','T','g','I','h','s','i','s']

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
    elif item == 'h':     # HTML file (may be a URL -- indicated with 'URL:')
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
        if name.endswith('gophermap'):
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

    ## Terminal size in number of columns and lines (updated often)
    lines  = 0
    columns= 0

    paging = False # check: https://www.geeksforgeeks.org/print-colors-python-terminal/

    ## Paths are the list of folders containing Gopher or Gemini sites.
    ## Corresponds to <path> in the command line invocation of this program
    ## Paths can be updated by using 'add path' (do_add) or 'remove path' (do_remove)
    ## Paths can be listed by using paths (do_paths)
    ## They can be persisted in a config by using save (do_save) or read (do_read)
    paths  = []

    ## Site URLs are used to process fully qualified links (by replacing them with a correct path)
    ## Site URLs can be updated by using 'add url' (do_add) or 'remove url' (do_remove)
    ## They can be listed by using urls (do_urls)
    ## They can be persisted in a config by using save (do_save) or read (do_read)
    site_urls = []

    ## Base is the path (from paths above) to the current Gopher or Gemini site being walked
    ## It can only be changed by visit (do_visit)
    ## IMPORTANT MUST never end in '/' (os.sep), we .rstrip(os.sep) when setting it.
    base   = ''

    ## Links are the list of raw links in the current page being processed.
    ## Links can be listed using links (do_links)
    ## A page can be a gophermap file, a gemini file (like index.gmi), or a directory
    ## In gopher:
    ##    - a directory without a gophermap file becomes a page listing the content of it
    ##    - a link that starts with '/' is relative to the base (unless it has host & port)
    ##    - otherwise relative to current directory (unless it has host & port or is a URL)
    links  = []

    ## Stack of visited links. Used for back (do_back)
    stack  = []

    ## Type of processing being done (either gopher or gemini)
    processing = ''

    def update_stack(self, place):
        self.stack.append(place)
        self.links = []

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
            title = 'Gopher menu [' + name + ']' 
            print('\x1b[44m' + title.center(self.columns) + '\x1b[0m')
            self.update_stack(name)

            while True:
                line = flSrc.readline()
                if not line:
                    break
                part = line.rstrip('\r\n').split('\t')
                numParts = len(part)
                item = '' if not part[0] else part[0][0]
                if not item:
                    print()
                elif item == 'i':
                    print(gopherFiller + part[0][1:])
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
            title = 'Gemini page [' + name + ']' 
            print('\x1b[44m' + title.center(self.columns) + '\x1b[0m')
            self.update_stack(name)
            lineWidth = self.columns - len(geminiFiller) -2

            while True:
                line = flSrc.readline()
                if not line:
                    break
                line = line.rstrip('\r\n')
                
                ## From: https://gemini.circumlunar.space/docs/specification.html
                ## Note that I relaxed the start of the line to allow spaces (as it is not clear in the spec)
                if re.search(r"^\s*```",line): # Section 5.4.3 Preformatting toggle lines
                    isFenced = not isFenced
                    continue
                if isFenced:                   # Section 5.4.4 Preformated text lines
                    print(geminiFiller + line)
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
                        print(geminiFiller + '\x1b[4m' + line + '\x1b[0m')
                    elif line.startswith('##'):
                        line  = line[2:].strip('\t ')
                        print(geminiFiller + '\x1b[1m' + line + '\x1b[0m')
                    else:
                        line  = line[1:].strip('\t ')
                        print(geminiFiller + '\x1b[1m\x1b[4m' + line + '\x1b[0m')
                    continue
                if re.search(r'^\s*\* ',line): # Section 5.5.2 Unordered list items
                    lines = textwrap.wrap(line.strip('\t ')[2:],
                            initial_indent='*  ', subsequent_indent='   ', width = lineWidth)
                    for l in lines:
                        print(geminiFiller + l)
                    continue
                if re.search(r'^\s*>',line):   # Section 5.5.3 Quote lines
                    lines = textwrap.wrap(line.strip('\t ')[1:],
                            initial_indent=geminiFiller, subsequent_indent=geminiFiller, 
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

    def process_text_file(self, name):
        try:
            flSrc = open(name, 'rt')
            title = 'Text file [' + name + ']' 
            print('\x1b[44m' + title.center(self.columns) + '\x1b[0m')
            self.update_stack(name)

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
            title = 'Gopher directory [' + name + ']' 
            print('\x1b[44m' + title.center(self.columns) + '\x1b[0m')
            self.update_stack(name)

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
        title = 'URL [' + url + ']' 
        print('\x1b[44m' + title.center(self.columns) + '\x1b[0m')
        self.update_stack(url)
        webbrowser.open(url)

    def print_list(self, lst, padding=' ', marker=0):
        count = 1
        for l in lst:
            print('{:2d} {} \x1b[38;5;119m{}\x1b[0m'.format(count, '  ' if marker != count else '=>', l))
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
            try:
                subprocess.run(['xdg-open', name])
            except OSError as e:
                error(e, " while processin file: [", name,"]")

    def rebase_link(link):
        for url in self.site_urls:
            if link.startswith(url):
                for l in self.links:
                    new = link.replace(url,l,1)
                    if os.path.exists(new):
                        return new
        return ''

    def visit_link(self, id):
        try:
            link = self.links[id]
            item = link[0]
            rest = link[1:]
            local, kind = link_type(item, rest)
            localLink = ''
            if not local and (kind.startswith('gopher://') or kind.startswith('gemini://')):
                localLink = rebase_link(kind)
            if localLink:
                local = True
            else:
                localLink = os.path.join(self.base,rest.strip(os.sep))
            if local and (kind == 'dir'):
                self.visit(localLink)
            elif local and (kind == 'file'):
                if rest.endswith('gophermap'):
                    self.process_gopher_map(localLink)
                else:
                    self.visit_file(localLink)
            elif not local:
                self.process_url(rest)
            else:
                print("Not supported [",rest,"]")

        except IndexError:
            print('Invalid link id')

    def visit(self, place):
        '''Place must be a fully qualified path'''

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
        print('\x1b[44m' + 'List of raw links in the page'.center(self.columns) + '\x1b[0m')
        count = 1
        for link in self.links:
            item = link[0]
            rest = link[1:] if not link[1:].startswith('URL:') else link[5:]
            print(gopher_link_line(count, item, rest))
            count += 1


    def do_visit(self, line):
        '''Visit a path to a Gopher hole or Gemini capsule (shortcut 'v')\nv[isit] [<number>|<path>]'''
        path = line.strip()
        old = self.base
        self.base = ''
        if path:
            if path.isdigit():
                if int(path) <= len(self.paths):
                    self.base = self.paths[int(path)-1]
                else:
                    error("invalid index")
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
        '''Set the following:\n    p[aging] = [true|false] (default false)'''
        line = line.strip()
        if line:
            opt = line.split('=')
            lside = opt[0]
            rside = '' if len(opt) <= 1 else opt[1]
            if lside in ['p', 'paging']:
                self.paging = True if (not rside) or (rside.lower() == 'true') else False
                return
        print("Invalid set option ",line)

    def do_up(self, line):
        '''Move one page up (shortcuts: 'u', 'k')'''
        print(self.stack)
        print("TODO")

    def do_down(self, line):
        '''Move one page down (shortcuts: 'd', 'j')'''
        print("TODO")

    ### This section deal with configuration files ###
    def do_save(self, line):
        '''Save configuration to <file> (shortcut 's')\ns[ave] [<file>] (default to config.json)'''
        name = line.strip()
        name = name if name else 'config.json'
        config = { 'paths' : self.paths, 'site_urls' : self.site_urls }
        with open(name, 'w') as fl:
            json.dump(config, fl)
        print("saved to",name)

    def do_read(self, line):
        '''Read configuration from <file> (shortcut 'r')\nr[ead] [<file>] (default to config.json)'''
        name = line.strip()
        name = name if name else 'config.json'
        with open(name, 'r') as fl:
            config = json.load(fl)
        self.paths     = config['paths']
        self.site_urls = config['site_urls']
        print("read from",name)

    ### This section deal with list of paths commands ###
    def do_add(self, line):
        '''Add <path> to bookmarks of paths (shortcut 'a')\na[dd] [ p[ath] <path> | u[rl] <url>]'''
        what = line.strip().split(' ',1)
        if len(what) != 2:
            error("Missing component should be 'a[dd] [p[ath] <path> | u[rl] <url>]'") 
            return

        if what[0].strip().lower() in ['p', 'path']:
            path = what[1].strip()
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
        '''Remove a <path> from bookmarks of paths (shortcut 're')\nre[move] [p[ath] <number>|<path>] [u[rl] <number>|<url>]'''

        what = line.strip().split(' ',1)
        if len(what) != 2:
            error("Missing component should be 're[move] [p[ath] <number>|<path>] [u[rl] <number>|<url>]'") 
            return

        if what[0].strip().lower() in ['p', 'path']:
            path = what[1].strip()
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
            url = line.strip()
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

    def do_back(self, line):
        '''Back to previous page in the site (shortcut 'b')'''
        if self.stack:
            # Need to pop twice as the top is the current page
            self.stack.pop()
        if not self.stack:
            self.visit(self.base)
            return
        place = self.stack.pop()
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
            error("Unknown place [".place,"]")

    def do_paths(self, line):
        '''List of paths to visit (shortcut 'p')\np[aths]'''
        print('\x1b[44m' + 'List of Paths'.center(self.columns) + '\x1b[0m')
        self.print_list(self.paths)

    def do_urls(self, line):
        '''List of site URLs'''
        print('\x1b[44m' + 'List of URLs'.center(self.columns) + '\x1b[0m')
        self.print_list(self.site_urls)

    def do_dump(self, line):
        '''Dump internal structures'''
        print('\x1b[44m' + 'Dump of internal structures'.center(self.columns) + '\x1b[0m')
        print("Terminal:\n    Lines:   ",self.lines,"\n    Columns: ",self.columns,
                "\nProcessing:",self.processing,"\nBase:",self.base,
                "\nPaths:", sep='')
        self.print_list(self.paths,'    ')
        print("\nSite URLs:")
        self.print_list(self.site_urls,'    ')
        print("\nLinks:")
        self.print_list(self.links,'    ')
        print("\nStack:")
        self.print_list(self.stack,'    ')


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
        elif CMD == 're':
            return self.do_remove(line)
        elif CMD == 'r':
            return self.do_read(line)
        elif CMD == 's':
            return self.do_save(line)
        elif CMD == 'b':
            return self.do_back(line)
        elif CMD == 'v':
            return self.do_visit(line)
        elif CMD.isdigit() and (0 < int(CMD) <= len(self.links)):
            return self.visit_link(int(CMD) -1)
        else:
            error("Invalid command")

    do_EOF    = do_exit
    help_EOF  = help_exit
    do_quit   = do_exit
    help_quit = help_exit


def arguments() :
    print("Usage:\n ",os.path.basename(sys.argv[0])," [flags] [<path> ... <path>]\n\nFlags:")
    print("   -s, --site-url  <url>  Site url for the sites being processed")
    print("                          (e.g gopher://my.site or gemini://host.name.com)")
    print("                          replacing site-url with <path> in a link should")
    print("                          generate a valid path (this flag can repeat)")
    print("   -h, --help             Prints this help")
    print("   -v, --verbose          Produces extra verbose output")
    sys.exit(2)


def main(argv):

   try:
       opts, args = getopt.getopt(argv,"hvs:",
               ["help","verbose","site-url="])
   except getopt.GetoptError as e:
      error(e)
      arguments()

   walk = walker()

   for opt, arg in opts:
      if (opt in ("-h","--help")) or (len(sys.argv) == 1):
         arguments()
      elif opt in ("-v", "--verbose"):
          global verbose
          verbose = True
      elif opt in ("-s", "--site-url"):
         arSiteUrl = arg.strip()
         if(not arSiteUrl.startswith('gopher://')) and (not arSiteUrl.startswith('gemini://')): 
             error("Invalid site-url argument (must start with either gopher:// or gemini://)")
             arguments()
         walk.site_urls.append(arSiteUrl)
      elif opt == "": 
          error("Invalid argument")
          arguments()

   if args:
       for arg in args:
           walk.paths.append(arg.rstrip(os.sep))

   walk.cmdloop()
   print("done")

if __name__ == "__main__":
   main(sys.argv[1:])
