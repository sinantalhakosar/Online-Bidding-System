from django import forms
from .models import *


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'itemtype', 'description',
                  'bidtype', 'starting', 'minbid', 'image']
