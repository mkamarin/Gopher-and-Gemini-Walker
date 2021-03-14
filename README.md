# Gopher-and-Gemini-Walker
This is a terminal utility to navigate a folder structure containing a [Gopher](https://en.wikipedia.org/wiki/Gopher_%28protocol%29) hole or a [Gemini](https://en.wikipedia.org/wiki/Gemini_%28protocol%29) capsule.  It is useful to verify your Gopher hole or Gemini capsule before deploying them to the hosting environment.

This utility was developed to test and navigate the [Hugo-2-Gopher-and-Gemini](https://github.com/mkamarin/Hugo-2-Gopher-and-Gemini) generated Gopher holes and Gemini capsules. It is a complement to the [Test-Hugo-2-Gopher-and-Gemini](https://github.com/mkamarin/Test-Hugo-2-Gopher-and-Gemini) repository. However, it can be used stand alone to navigate any Gopher hole or Gemini capsule.

## Introduction
When creating a Gopher hole or a Gemini capsule you start by creating the files (gophermaps for Gopher or <name>.gmi for Gemini) in a local machine and then uploading them to the hosting environment. Even that gophermaps and <name>.gmi (or <name>.gemini) files are easy to create, they normally live in a folder (directory) structure and refer to other files in that structure. In addition, they may have links to other locations.

This utility `ggwalker.py` is a terminal (command line) browser like utility that allows you to browse your Gopher hole or Gemini capsule in your local machine by navigating the folder structure of the hole or capsule, without using any network communication. Similar to Gopher or Gemini browsers, if a external link or a non-textual file is found, the default OS application is invoked to process the link. Than way, this utility does not opens any network connection and only works in local files.

## Installation
There is no much to install. Just get the zip or link for this repository and unzip it or clone it in your machine. You need to have python 3 installed (normally installed by default in most Linux distributions). The executable is `src/ggwalker.py`

## Execution
You can execute `ggwalker.py` without any argument and get to the following prompt:
```
~$ src/ggwalker.py
Welcome to Gopher and Gemini walker
Type ? or help for list of commands.
walker>
```

But, most likely you want to execute it with the path to your Gopher hole or Gemini capsule, as follows:
```
~$ src/ggwalker.py  ~/sources/site
```

In this example, `~/sources/site` is the folder containing my Gopher hole (`~/sources/site/gophermap` file) or Gemini capsule, in which case there will be an `index.gmi` file (i.e. `~/sources/site/index.gmi`). 

### Typical session (example)
In this session, we will use the test directory in this repository. Let execute `ggwalker.py`, as follows:
```
src/ggwalker.py  test/toyhole
```

Let try the help:
```
walker>?
Documented commands (type help <topic>):
========================================
EOF  back  dump  help   paths  read    save  shell  urls 
add  down  exit  links  quit   remove  set   up     visit
```

Now, let `visit` the gopher hole we passed as argument (`test/toyhole`). The purpose of toyhole is to present a very small example of a Gopher hole, and to describe how you can write your own gophermap. So, let visit it, as follows:
```
walker> visit
  Gopher menu [Gopher-and-Gemini-Walker/test/toyhole/gophermap]  
                                                                      
               _____             _                 __  __             
              / ____|           | |               |  \/  |            
             | |  __  ___  _ __ | |__   ___ _ __  | \  / | __ _ _ __  
             | | |_ |/ _ \| '_ \| '_ \ / _ \ '__| | |\/| |/ _` | '_ \ 
             | |__| | (_) | |_) | | | |  __/ |    | |  | | (_| | |_) |
              \_____|\___/| .__/|_| |_|\___|_|    |_|  |_|\__,_| .__/ 
                          | |                                  | |    
                          |_|                                  |_|    
                                                                      

         A Gopher server exposes a directory structure to the network using
         the gopher protocol (RFC 1436).  In that respect, it is similar to
         FTP  (RFC 959).  The main  difference is that  Gopher  looks for a

...

        Few examples are:
 1 (TXT) A text file (relative to this gopgermap)
 2 (BIN) A pdf file (relative to the gopher site)
 3 (PIC) an image file
 4 (DIR) The stuff directory (relative to this gopgermap)
 5 (DIR) The stuff directory (relative to the gopher site)

...

walker>
```

Now, we can go to the text file that is link number 1. We do that bu just typing 1, as follows
```
walker> 1
Text file [Gopher-and-Gemini-Walker/test/toyhole/stuff/text.txt] 

This is a text file.

walker> 
```

Our text file is not very exciting, but enough to illustrate how it works. Ok, now what? There is no menu to select from, but remember that we can always use `?` to get help. In this case, it makes sense to go back to the previous page. We do that by using the `back` command, as follows:
```
walker> back
```

We now got back to the first page. We can go to any of the links in that page by typing the number of the link. But, we can also list all the raw links in the page by using the `links` command, as follows:
```
walker> links
                                List of raw links in the page                                
 1 (TXT) stuff/text.txt
 2 (BIN) /stuff/a-file.pdf
 3 (PIC) stuff/image.jpg
 4 (DIR) stuff
 5 (DIR) /stuff
 6 (DIR) gopher://sdf.org/
 7 (DIR) gopher://gopher.floodgap.com/
 8 (URL) http://sdf.org/
 9 (URL) https://www.floodgap.com/
10 (URL) gemini://myserver/
walker> 
```

Now you have enough information to navigate your own Gopher hole or Gemini capsule. You can do the same exercise using `test/toycapsule' instead. 

Note that link 10 refers to `gemini://myserver` which in this case refers to our own `test/toycapsule`. You can also have a `gopher://myserver` being listed as a link on the Gemini capsule. If you want to navigate between them, you can execute `ggwalker.py`, as follows:
```
src/ggwalker.py  -s gemini://myserver -s gopher://myserver  test/toyhole test/toycapsule
```

In here, we passed two site URLs using the `-s` option, and two paths to navigate. We can now do `visit 1` or `visit 2` to visit one of the paths. If we now go to a link that has a fully qualified url, for example `gemini://myserver/stuff/text.txt` then `ggwalker.py` will change it to `test/toycapsule/stuff/text.txt` and navigate to it.




