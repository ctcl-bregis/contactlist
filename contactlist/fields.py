# ContactList - CTCL 2023
# Generated: June 16, 2023
# Purpose: Django form data
# THIS FILE IS AUTOMATICALLY GENERATED

from django import forms
from . import choices
from .models import ContactItem

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactItem
        fields = ['name', 'irln', 'loca', 'dtmt', 'appe', 'smp1', 'smu1', 'smp2', 'smu2', 'smp3', 'smu3', 'smp4', 'smu4', 'note']
        labels = {'name': 'Name', 'irln': 'Full Name', 'loca': 'Location', 'dtmt': 'Date Met', 'appe': 'Appearance', 'smp1': 'Social Platform 1', 'smu1': 'Social Username 1', 'smp2': 'Social Platform 2', 'smu2': 'Social Username 2', 'smp3': 'Social Platform 3', 'smu3': 'Social Username 3', 'smp4': 'Social Platform 4', 'smu4': 'Social Username 4', 'note': 'Notes'}

