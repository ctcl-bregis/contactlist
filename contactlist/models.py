# ContactList - CTCL 2023
# Generated: June 15, 2023
# Purpose: Database model metadata
# THIS FILE IS AUTOMATICALLY GENERATED

from django.utils import timezone
from django.db import models
from . import choices

class ContactItem(models.Model):
    inid = models.AutoField(primary_key = True)
    name = models.TextField(blank = True)
    irln = models.TextField(blank = True)
    loca = models.TextField(blank = True)
    smp1 = models.CharField(max_length = 128, choices = choices.choices_smp1)
    smu1 = models.TextField(blank = True)
    smp2 = models.CharField(max_length = 128, choices = choices.choices_smp2)
    smu2 = models.TextField(blank = True)
    smp3 = models.CharField(max_length = 128, choices = choices.choices_smp3)
    smu3 = models.TextField(blank = True)
    smp4 = models.CharField(max_length = 128, choices = choices.choices_smp4)
    smu4 = models.TextField(blank = True)
    nte = models.TextField(blank = True)
    dmt = models.TextField(blank = True)
    crd = models.DateTimeField(null = True)
    mod = models.DateTimeField(null = True)

    class Meta:
        verbose_name_plural = "Contact Entries"

    def todict(self):
        return {"inid": self.inid, "name": self.name, "irln": self.irln, "loca": self.loca, "smp1": self.smp1, "smu1": self.smu1, "smp2": self.smp2, "smu2": self.smu2, "smp3": self.smp3, "smu3": self.smu3, "smp4": self.smp4, "smu4": self.smu4, "nte": self.nte, "dmt": self.dmt, "crd": self.crd, "mod": self.mod, }
        
    def __str__(self):
        return self.name

