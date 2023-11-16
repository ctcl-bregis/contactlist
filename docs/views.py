# ContactList - CTCL 2023
# File: views.py
# Purpose: Integrated Documentation Views
# Created: July 31, 2023
# Modified: November 16, 2023

import csv
import io
import os
import pathlib
from datetime import datetime, timezone
import markdown
from django.db.models import CharField, Q, TextField
from django.http import (HttpResponse, HttpResponseNotFound, HttpResponseRedirect)
from django.shortcuts import render
from django.template import loader
from django.template.defaulttags import register
import contactlist.lib as lib

# String from the config file to use with strftime
strfstr = lib.getgconfig("global")["strftime"]

# Assign the config dictionary to a variable so lib.getgconfig() does not have to be called every time
docsconfig = lib.getgconfig("docs")
filepath = docsconfig["path"]

# Hardcoded documentation path
urlprefix = "/docs/"

# {{ dict|get_item:key }}
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# Function for getting info on a file, not to be used as a route
def getfiledata(path):
    # In case there is a Windows-style path
    path = path.replace('\\', '/')
    filedata = {}

    filedata["dname"] = os.path.basename(path)

    # filedata keys:
    # - dlink: Displayed/Document Link
    # - dname: Displayed/Document Name
    # - dtype: Displayed/Document Type (what is shown to the user under "Type")
    # - rtype: Render Type
    # - ftmod: File Time of Modification
    # - fsize: File Size

    if os.path.isdir(path):
        filedata["ftmod"] = datetime.fromtimestamp(os.path.getmtime(path)).strftime(strfstr)
        filedata["dlink"] = path.replace(filepath, urlprefix) + "/"
        filedata["dtype"] = "Directory"
        filedata["rtype"] = "directory"
        filedata["fsize"] = ""
    elif os.path.isfile(path):
        filedata["ftmod"] = datetime.fromtimestamp(os.path.getmtime(path)).strftime(strfstr)
        # File types supported:
        # - binary: Not readable and does not have a link
        # - markdown: Readable and is rendered with the markdown module
        # - text: Displayed as plain text in a <p></p> element
        # - source: Displayed as plain text in a <code></code> element
        # Other types that are not listed above would be treated as a binary file and would not be readable

        ext = pathlib.Path(path).suffix

        if ext in docsconfig["knowntypes"].keys():
            filedata["rtype"] = docsconfig["knowntypes"][ext]["type"]
            filedata["dtype"] = docsconfig["knowntypes"][ext]["name"]
        else:
            filedata["rtype"] = None
            filedata["dtype"] = "Unknown"

        if filedata["rtype"] in ["markdown", "source", "text"]:
            filedata["dlink"] = path.replace(filepath, urlprefix)
        else:
            filedata["dlink"] = None

        filedata["fsize"] = lib.hsize(os.path.getsize(path))

    else:
        printe(f"docs/views.py function getfiledata ERROR: {path} is not a file, not a directory or does not exist")
        return None

    return filedata

# File listing for use with the HTML table
def listfiles(path):

    if not os.path.isdir(path):
        return None

    filelist = []

    for file in os.listdir(path):
        filedata = getfiledata(path + file)
        if filedata != None:
            filelist.append(filedata)

    return filelist

# "root" page
def docs(request, path = ""):
    context = lib.mkcontext(request, "Documentation", "table")
    context["dir"] = path
    context["headers"] = docsconfig["table"]

    path = filepath + path
    if os.path.isdir(path):
        context["data"] = listfiles(path)

        return render(request, "docs_dir.html", context = context)
    elif os.path.isfile(path):
        dlink = getfiledata(path)["dlink"]
        # Make sure the file was given a link
        if dlink == None:
            return HttpResponseNotFound()

        # Remove prefix
        dlink = dlink.replace("/docs/", "/")
        context = lib.mkcontext(request, f"Documentation - {dlink}")
        filetype = getfiledata(path)["rtype"]

        # IDEA: Pre-render files and store them in memory on server start so the files are not accessed each time
        # Idea for above idea: Detect file changes during runtime and render the file again
        if filetype == "markdown":
            with open(path) as f:
                context["content"] = markdown.markdown(f.read())
        elif filetype == "text":
            with open(path) as f:
                content = f.read()
                context["content"] = f"<p>\n{content}\n</p>"
        elif filetype == "source":
            with open(path) as f:
                content = f.read()
                context["content"] = f"<code>\n{content}\n</code>"

        return render(request, "docs_page.html", context = context)

    return HttpResponseNotFound()