"""Admin login form.

Django names the identifier field `username` whatever `USERNAME_FIELD` is. The
field name is kept; only its presentation is changed to an email input.
"""

from unfold.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field = self.fields["username"]
        field.label = "Email"
        field.widget.input_type = "email"
        field.widget.attrs.update(
            {
                "autocomplete": "email",
                "placeholder": "nama@kastaumuzik.com",
                "inputmode": "email",
            }
        )
