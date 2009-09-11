from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

class FacebookUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and password.
    """
    username = forms.RegexField(label=_("Username"), max_length=30, regex=r'^\w+$',
        help_text = _("Required. 30 characters or fewer. Alphanumeric characters only (letters, digits and underscores)."),
        error_message = _("This value must contain only letters, numbers and underscores."))
    email = forms.EmailField(label=_("E-mail"), max_length=75,required=False)

    class Meta:
        model = User
        fields = ("username","email")

    def save(self, commit=True):
        user = super(FacebookUserCreationForm, self).save(commit=False)
        user.set_unusable_password()
        if commit:
            user.save()
        return user
