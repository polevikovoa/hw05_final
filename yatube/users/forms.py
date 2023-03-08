from django.contrib.auth.forms import UserCreationForm

from django import forms


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ('first_name', 'last_name', 'username', 'email')


class EmailForm(forms.Form):
    recipient = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
