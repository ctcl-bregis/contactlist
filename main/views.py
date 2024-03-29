# ContactList - CTCL 2023-2024
# File: views.py
# Purpose: Global app settings
# Created: June 9, 2023
# Modified: February 19, 2024

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.template.defaulttags import register
from django.db.models import CharField, TextField, Q
from datetime import datetime
from app import lib
from app.lib import printe
import csv, io
import pytz

try:
    from .models import ContactItem
except ModuleNotFoundError:
    pass

try:
    from .fields import ContactForm, SearchForm
except ModuleNotFoundError:
    pass
    
try:
    from .choices import Choices
except ModuleNotFoundError:
    pass

# {{ dict|get_item:key }}
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='zip')
def zip_lists(a, b):
  return zip(a, b)
    
# "Main" page that currently lists everything
def index(request):
    template = loader.get_template("main.html")
    headers = lib.getconfig("headers")
    
    # htmltable in the config should not contain titles, so add them from headers
    columns = []
    for i in lib.getconfig("htmltable"):
        if i["type"] == "info" or i["type"] == "infotime":
            i["title"] = headers[i["col"]]
        elif i["type"] == "button":
            i["title"] = ""
            
        columns.append(i)
    
    allitems = [i.todict() for i in ContactItem.objects.all()]
    
    tmplst = []
    for i in allitems:
        i["tcrd"] = lib.dt2fmt(i["tcrd"])
        i["tmod"] = lib.dt2fmt(i["tmod"])
        tmplst.append(i)
    allitems = tmplst
    
    context = lib.mkcontext(request, "ContactList - List", "table")
    context["headers"] = columns
    context["data"] = allitems
    return HttpResponse(template.render(context, request))

def view(request, inid):
    template = loader.get_template("view.html")
    dbitem = ContactItem.objects.get(pk=inid)
    data = dbitem.todict()
    cfgdata = ContactItem.cfgdata()
    context = lib.mkcontext(request, "ContactList - View")

    context["id"] = data["inid"]

    # Remove database ID
    data.pop("inid")
    headers = lib.getconfig("headers")

    context["headers"] = headers
    context["data"] = data
    context["groups"] = lib.getconfig("tablecats")
    context["groupnames"] = lib.getconfig("tablecats").keys()
    
    tableconfig = lib.getconfig("table")
    context["groupednames"] = {}
    for x in tableconfig.keys():
        context["groupednames"][x] = [i["col"] for i in tableconfig[x]]

    allchoices = Choices.choicedict

    # Remove tcrd and tmod froim the "data" dictionary to prevent errors; tcrd and tmod have already been put into the context
    data.pop("tcrd")
    data.pop("tmod")
    for field in data.keys():
        if cfgdata[field]["datatype"] == "select":
            getchoices = allchoices[cfgdata[field]["ddfile"]]
            for k, v in getchoices.items():
                if data[field] == k:
                    data[field] = v
 
    return HttpResponse(template.render(context, request))

def new(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            newentry = ContactItem()
            cld = form.cleaned_data
            for k, v in cld.items():
                setattr(newentry, k, v)
            
            dt = datetime.utcnow().replace(tzinfo=pytz.utc)
            setattr(newentry, "tcrd", dt)
            setattr(newentry, "tmod", dt)
            newentry.save()
            
            return HttpResponseRedirect("/")
        else:
            return HttpResponseRedirect("/")
    else:    
        form = ContactForm()
        
        tableconfig = lib.getconfig("table")
        
        context = lib.mkcontext(request, "ContactList - New", "form")
        context["form"] = form
        context["groups"] = lib.getconfig("tablecats")
        context["groupnames"] = lib.getconfig("tablecats").keys()
        
        context["groupednames"] = {}
        for x in tableconfig.keys():
            context["groupednames"][x] = [i["col"] for i in tableconfig[x]]
    
        return render(request, "new.html", context)

def edit(request, inid):
    if request.method == "POST":
        data = ContactItem.objects.get(pk=inid)
        form = ContactForm(request.POST, instance=data)
        if form.is_valid():
            form.save()
            data = ContactItem.objects.get(pk=inid)
            data.tmod = datetime.utcnow().replace(tzinfo=pytz.utc)
            data.save()
            return HttpResponseRedirect("/")
        else:
            return HttpResponseRedirect("/")
    else:
        data = ContactItem.objects.get(pk=inid)
        form = ContactForm(initial = data.todict())
        
        tableconfig = lib.getconfig("table")
        
        context = lib.mkcontext(request, "ContactList - Edit", "form")
        context["form"] = form
        context["groups"] = lib.getconfig("tablecats")
        context["groupnames"] = lib.getconfig("tablecats").keys()
        context["inid"] = inid
        
        context["groupednames"] = {}
        for x in tableconfig.keys():
            context["groupednames"][x] = [i["col"] for i in tableconfig[x]]
        
        return render(request, "edit.html", context)

def delete(request, inid):
    # The button for continuing with deletion would be a form that does not include data
    # This also allows for the deletion of an item by sending a POST request
    if request.method == "POST":
        dbitem = ContactItem.objects.get(inid=inid)
        dbitem.delete()
        return HttpResponseRedirect("/")
    else:
        return render(request, "delconfirm.html", lib.mkcontext(request, "ContactList - Delete Item"))
    
def search(request):
    if request.method == "POST":
        form = SearchForm(request.POST)
        if form.is_valid():
            context = lib.mkcontext(request, "ContactList - Search", "table")
            searchquery = form.cleaned_data["query"]
            
            # Quick hack until Haystack or something is implemented
            fields = [f for f in ContactItem._meta.fields if isinstance(f, CharField) or isinstance(f, TextField)]
            # "icontains" may not function correctly with SQLite3, see Django documentation for details
            queries = [Q(**{f.name + "__icontains": searchquery}) for f in fields]
            qs = Q()
            for query in queries:
                qs = qs | query
            
            allitems = [i.todict() for i in ContactItem.objects.filter(qs)]
            
            headers = lib.getconfig("headers")
            columns = []
            for i in lib.getconfig("htmltable"):
                if i["type"] == "info":
                    i["title"] = headers[i["col"]]
                elif i["type"] == "button":
                    i["title"] = ""
            
                columns.append(i)
            
            tmplst = []
            for i in allitems:
                i["tcrd"] = lib.dt2fmt(i["tcrd"])
                i["tmod"] = lib.dt2fmt(i["tmod"])
                tmplst.append(i)
            allitems = tmplst
    
            context = lib.mkcontext(request, "ContactList - List", "table")
            context["headers"] = columns
            context["data"] = allitems
            
            return render(request, "results.html", context)
        else:
            return HttpResponseRedirect("/")
    else:
        context = lib.mkcontext(request, "ContactList - Search")
        context["form"] = SearchForm()
        
        return render(request, "search.html", context)
    
def settings(request):    
    context = lib.mkcontext(request, "ContactList - Settings")
    return render(request, "settings.html", context)
        
def exportcsv(request):
    allitems = [i.todict() for i in ContactItem.objects.all()]
    fields = ContactItem.fieldnames()
    
    for item in allitems:
        for field in fields:
            # Format any datetime objects as they would be shown on the HTML table
            if isinstance(item[field], datetime):
                item[field] = lib.dt2fmt(item[field])
    
    # Create "file" in memory for DictWriter to minimize disk read/writes
    memcsv = io.StringIO()
    writer = csv.DictWriter(memcsv, fieldnames = fields, delimiter = ",", quoting = csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(allitems)
    
    response = HttpResponse()
    response['Content-Disposition'] = "attachment;filename=export.csv"
    response.write(memcsv.getvalue())
    
    return response