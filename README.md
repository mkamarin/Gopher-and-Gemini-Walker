# Gopher-and-Gemini-Walker
This is a terminal utility to navigate a folder structure containing a [Gopher](https://en.wikipedia.org/wiki/Gopher_%28protocol%29) hole or a [Gemini](https://en.wikipedia.org/wiki/Gemini_%28protocol%29) capsule.  It is useful to verify your Gopher hole or Gemini capsule before deploying them to the hosting environment. This utility may be useful for people creating Gopher holes or Gemini capsules by hand in their local machines. It allows to test and inspect the Gopher hole or Gemini capsule in the file system of a local machine. This utility does not access the network.

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
In this session, we will use the test directory in this repository. The test directory has two sites, namely `test/toyhole` (a sample Gopher site), and `test/toycapsule` (a Gemini site). They serve two purposes. First, they are a minimal test suite. Second and probably most important they describe how to write a `gophermap` (`test/toyhole`) and a Gemini file (`test/toycapsule`). They follow the traditional `toybox.zip` that many of us used to learn Gopher.

For our typical session, let execute `ggwalker.py`, as follows:
```
~$ src/ggwalker.py  test/toyhole
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
10 (URL) gemini://myserver.com/
walker> 
```

Now you have enough information to navigate your own Gopher hole or Gemini capsule. You can exit this session using `exit` or `quit`, as follows:
```
walker> exit
```

You can do the same exercise using `test/toycapsule`. 

Most commands can be abbreviated to the first one or two letters. In here, we used the commands `visit`, `back`, `links` and `exit` that can be abbreviated as `v`, `b`, `l` and `e`. 

#### Few extra notes on this session 
Note that link `10` above refers to `gemini://myserver.com` which in this case refers to our own `test/toycapsule`. You can also have a `gopher://myserver.com` being listed as a link on the Gemini capsule. If you want to navigate between them, you can execute `ggwalker.py`, as follows:
```
src/ggwalker.py  -s gemini://myserver.com -s gopher://myserver.com  test/toyhole test/toycapsule
```

Note that we passed two site URLs using the `-s` option, and two paths to navigate to. We can now do `visit 1` or `visit 2` to visit one of the paths. If we go to a link that has a fully qualified url, for example `gemini://myserver.com/stuff/text.txt` then `ggwalker.py` will change it to `test/toycapsule/stuff/text.txt` and navigate to it.

### Commands
As we saw in the previous section, there is a set of commands that `ggwalker.py` will accept during an interactive session. Most of those commands can be abbreviated to one or two letters. In here we will present all the commands by type.

#### Basic commands
Basic commands that most users will need.

##### exit (`e`) / Quit (`q`) / EOF
Exit the `ggwalker.py` session. It can be abbreviated to `e`, `q`, or `<ctrl>-D`.

##### help (`?`)
Provide help about the different commands. It can be abbreviated to `?`. Detailed help for a command can be obtained using `help <command>` (same as `? <command>`)

##### shell (`!`)
Provides a way to execute shell commands. For example, `! ls`.

#### Paths and URLs
A path is the base directory of a Gopher hole or a Gemini capsule. Meaning it corresponds to `/` in your site. For example, in this repository you can find two paths, namely `Gopher-and-Gemini-Walker/test/toyhole` and `Gopher-and-Gemini-Walker/test/toycapsule`. You can pass multiple paths via command line arguments as follows:
```
src/ggwalker.py  Gopher-and-Gemini-Walker/test/toyhole  Gopher-and-Gemini-Walker/test/toycapsule
```

A site URL, in this context, corresponds to the URL the deployed Gopher hole or Gemini capsule will have. In most cases, you will not need to use them, unless you are using full URLs for all your references. For example, using our test directory, if I refer to a text file as `stuff/text.txt` the re is no need to supply the site URL, but if I use `gemini://stuff/text.txt` instead, then you need to provide the site URL, so that `ggwalker.py` can find it (otherwise, it will try to launch a gemini browser). 
You can pass multiple site URLs via command line arguments using the `-s` flag, as follows:
```
src/ggwalker.py  -s gemini://myserver.com  -s gopher://myserver.com 
```

##### add (`a`)
You can add both paths and site URLs using the add command. 
The syntax is: `a[dd] [ p[ath] <path> | u[rl] <url>]'. 
For example:
```
walker> add path Gopher-and-Gemini-Walker/test/toyhole
or
walker> a p Gopher-and-Gemini-Walker/test/toyhole
walker> add url gemini://myserver.com
or
walker> a u gemini://myserver.com
```

##### paths (`p`)
You can list all the paths with the paths command. Note that each path is assign a number that will be used for other commands that accept paths. For example:
```
walker> p
               List of Paths
  1    ~/src/Gopher-and-Gemini-Walker/test/toyhole
  2    ~/src/Gopher-and-Gemini-Walker/test/toycapsule
walker> 
```

##### urls
Similar to `paths`, `urls` list all the site URLs. This command does not have an abbreviation. 

##### remove ('re')
You can remove a path using its full name or its number. 
The syntax is: `re[move] [p[ath] <number>|<path>] [u[rl] <number>|<url>]`.

#### Configuration files
Paths and site URLs are long and cumbersome to type every time that you execute `ggwalker.py`. In addition, they are for most parts static and don't change much over time. Therefore is convenient to have a `save` and `read` commands.

 ##### save (`s`)
Saves the paths and site URLs to a json file. If no filename is given then `config.json` will be used.
The syntax is: `s[ave] [<file-name>]`

##### read (`r`)
Read a config file. If no filename is given then `config.json` will be used.
The syntax is: `r[ead] [<file-name>]`

#### Navigation
The main purpose of `ggwalker.py` is to allow you to navigate your Gopher hole and/or Gemini capsule. You start navigating by using the `visit` command.

##### visit (`v`)
You visit a path. Therefore you must provide a path name or a path number. If only one path exists, then the path number is optional.
The syntax is: `v[isit] [<path-number>|<path>]`

Visit takes you to the first page of the site at the path. Gopher sites may have a `gophermap` file under that path, otherwise the directory content is listed. Gemini sites require an `index.gmi` or `index.gemini` file under that path. In either case, that is the page that will be output.

##### <number>
Gopher and Gemini pages have links to other pages, files, directories, URLs, etc. Those links are numbered by most clients, and `ggwalker.py` do the same. You navigate to those links by inputting the link number. For example:
```
...
 1 (TXT) A text file (relative to this gopgermap)
 2 (BIN) A pdf file (relative to the gopher site)
 3 (PIC) an image file
 4 (DIR) The stuff directory (relative to this gopgermap)
 5 (DIR) The stuff directory (relative to the gopher site)
...

walker> 2
```

Entering number two above takes you to the pdf file, which will be open in the default application for pdf reading in your system.
Note that each time you navigate to a link, you are leaving the page and so the page links are not longer available. However when you get back to the page, they become available again.

##### links (`l`)
The links shown when the page is output are the human readable label for the link. You can use the `link` command to see the real link. Using the previous example:
```
walker> l
 1 (TXT) stuff/text.txt
 2 (BIN) /stuff/a-file.pdf
 3 (PIC) stuff/image.jpg
 4 (DIR) stuff
 5 (DIR) /stuff
...

walker>
```

##### back (`b`)
When you are in a page, sometimes you want to go to the previous page. You can do that using the `back` command. You can keep going back until you reach the initial page of the site. In which case, back just reload that page.

##### forward (`f`)
If you have used the `back` command, you may want to go forward to the page in which you were before. You do that using the `forward` command. If you reached the last page, then forward just reload that last page.

You can think of `back` and `forward` as the back and forward arrows in a browser.

#### Miscellaneous
These are debugging commands.

##### dump
This command just dump all the internal data structures.

## Conclusion
This utility may be useful for people creating Gopher holes or Gemini capsules by hand in their local machines. It allows to test and inspect the Gopher hole or Gemini capsule before deploying them into the hosting environment.

It was developed as a complement to he [Test-Hugo-2-Gopher-and-Gemini](https://github.com/mkamarin/Test-Hugo-2-Gopher-and-Gemini) repository. Which in turn was created to test the [Hugo-2-Gopher-and-Gemini](https://github.com/mkamarin/Hugo-2-Gopher-and-Gemini) generated Gopher holes and Gemini capsules. 
 






