# ContactList - CTCL 2023
# Date: June 9, 2023 - July 18, 2023
# Purpose: Management command for generating database models, form data and other files

# Valid data types
# - date: datetime.date object, editable via Django DateField form class
# - select: Value chosen by a dropdown menu
# - string: Text input with a text length limit
# - text: Text input that is displayed using a textarea

from django.core.management.base import BaseCommand, CommandError
import os, json, shutil
from datetime import datetime, timezone
from csscompressor import compress

def configchoices(jsonconfig, themes):
    choicedict = jsonconfig["dropdown"]
    
    themechoices = {}
    for k, v in themes.items():
        themechoices[k] = v["disp_name"]
            
    choicedict["themes"] = themechoices
    
    d = datetime.now(timezone.utc)
    choicespy = """# ContactList - CTCL 2023
# Generated: {date}
# Purpose: Dropdown choices
# THIS FILE IS AUTOMATICALLY GENERATED

class Choices:
    choicedict = {choicedict}

    def totuplelist(ddfile):
        return list(Choices.choicedict[ddfile].items())

""".format(date = d.strftime("%B %e, %Y"), choicedict = choicedict)

    return choicespy

def configmodels(jsonconfig):
    dbconfig = []
    table = ""
    cfgdata = {}
    for x in jsonconfig["table"].keys():
        dbconfig = jsonconfig["table"][x]
        for y in dbconfig:
            dt = y["datatype"]
            
            cfgdata[y["col"]] = y
        
            if dt in "select":
                table += f"    {y['col']} = models.CharField(blank = True, max_length = 128, choices = Choices.totuplelist(\"{y['ddfile']}\"))\n    {y['col']}.group = \"{x}\"\n" 
            elif dt == "string":
                table += f"    {y['col']} = models.CharField(blank = True, max_length = {y['max']})\n    {y['col']}.group = \"{x}\"\n"
            elif dt == "text":
                table += f"    {y['col']} = models.TextField(blank = True, null = True)\n    {y['col']}.group = \"{x}\"\n"
            elif dt == "date":
                table += f"    {y['col']} = models.DateField(null = True)\n    {y['col']}.group = \"{x}\"\n"
            else:
                print(f"WARNING: Unknown datatype \"{dt}\", skipping")
    
    groups = ""
    for i in jsonconfig["table"].keys():
        groups += """
    def group_{i}(self):
        return filter(lambda x: x.group == "{i}", self.fields.values())
""".format(i = i)
        
    colnames = []
    for x in jsonconfig["table"].keys():
        for y in jsonconfig["table"][x]:
            colnames.append(y["col"])
    
    colnames = ["inid"] + colnames
    colnames.append("tcrd")
    colnames.append("tmod")
    todict = ""
    for i in colnames:
        todict += f"\"{i}\": self.{i}, "
    todict = "{" + todict + "}"
    
    d = datetime.now(timezone.utc)
    modelspy = """# ContactList - CTCL 2023
# Generated: {date}
# Purpose: Database model metadata
# THIS FILE IS AUTOMATICALLY GENERATED

from django.utils import timezone
from django.db import models
from .choices import Choices

class ContactItem(models.Model):
    # inid, tcrd, tmod are not defined by the configuration file
    inid = models.AutoField(primary_key = True)
    tcrd = models.DateTimeField(null = True)
    tmod = models.DateTimeField(null = True)

{table}
    class Meta:
        verbose_name_plural = "Contact Entries"

    def todict(self):
        return {todict}
        
    def cfgdata():
        return {cfgdata}
        
    def fieldnames():
        return {colnames}
        
    def __str__(self):
        return self.name
""".format(date = d.strftime("%B %e, %Y"), table = table, groups = groups, todict = todict, cfgdata = cfgdata, colnames = colnames)
    
    return modelspy
    
def configfields(jsonconfig):
    allfields = []
    for i in jsonconfig["table"].keys():
        allfields += jsonconfig["table"][i]
    hconfig = jsonconfig["headers"]
    fields = []
    labels = {}
    for i in allfields:
        dt = i["datatype"]
        col = i["col"]
        
        if dt in ["date", "select", "string", "text"]:
            fields.append(col)
            labels[col] = hconfig[col]
        else:
            pass
            
    d = datetime.now(timezone.utc)
    fieldspy = """# ContactList - CTCL 2023
# Generated: {date}
# Purpose: Django form data
# THIS FILE IS AUTOMATICALLY GENERATED

from django import forms
from .choices import Choices
from .models import ContactItem

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactItem
        fields = {fields}
        labels = {labels}

class SettingsForm(forms.Form):
    theme = forms.CharField(label = "Theme Selection", widget = forms.Select(choices = Choices.totuplelist("themes")))

class SearchForm(forms.Form):
    query = forms.CharField(label = "Search", max_length = 128)

""".format(date = d.strftime("%B %e, %Y"), fields = fields, labels = labels)

    return fieldspy

class Command(BaseCommand):
    help = "Generates a model.py for the application using config files under config/database/"
    
    def handle(self, *args, **options):
        # Create a backup of the database since migrations may wipe the data
        if os.path.exists("db.sqlite3"):
            if os.path.exists("db_backup.sqlite3"):
                os.remove("db_backup.sqlite3")
                
            shutil.copyfile("db.sqlite3", "db_backup.sqlite3")
        
        # Current working directory should be the project root
        try:
            with open("config/config.json") as f:
                jsonconfig = json.loads(f.read())["config"]
        except FileNotFoundError:
            cwd = os.getcwd()
            print(f"genmodels.py ERROR: config/config.json does not exist. Current working directory is \"{cwd}\".")
            return
        except (json.JSONDecodeError, json.decoder.JSONDecodeError) as e:
            print(f"genmodels.py ERROR: Exception \"{e}\" raised by JSON library")
            return
            
        themedir = [f for f in os.listdir("config/themes") if os.path.isdir(os.path.join("config/themes", f))]
        themeindices = []
        for i in themedir:
            try:
                with open(f"config/themes/{i}/index.json") as f:
                    themedata = dict(json.load(f))["theme"]
            except FileNotFoundError:
                print(f"genmodels.py WARNING: Theme \"{i}\" does not have a index.json, the theme would not be available")
            except (json.JSONDecodeError, json.decoder.JSONDecodeError) as e:
                print(f"genmodels.py WARNING: Exception \"{e}\" raised by JSON library, the theme would not be available")
                
            themeindices.append(themedata)
        
        with open(jsonconfig["misc"]["basecss"]) as f:
            basecss = f.read()
        
        themes = {}
        for theme in themeindices:
            themedir = os.path.join("config/themes", theme["int_name"])
            themeind = os.path.join(themedir, "index.json")
            
            if os.path.exists(themeind):
                with open(theme["css"]) as f:
                    theme["css"] = compress(basecss + f.read())
                
                themes[theme["int_name"]] = theme
            else:
                print(f"themecfg.py WARNING: Theme directory \"{themedir}\" does not have an index.json. The theme would not be available.")
        
        with open("themecfg.json", "w") as f:
            f.write(json.dumps(themes))
        
        with open("contactlist/choices.py", "w") as f:
            f.write(configchoices(jsonconfig, themes))
        
        with open("contactlist/models.py", "w") as f:
            f.write(configmodels(jsonconfig))
            
        with open("contactlist/fields.py", "w") as f:
            f.write(configfields(jsonconfig))
