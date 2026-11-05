"""Formulario público de contacto."""

from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        label="Nombre completo",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    phone = forms.CharField(
        label="Teléfono",
        max_length=60,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "tel"}),
    )
    company = forms.CharField(
        label="Empresa",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "organization"}),
    )
    message = forms.CharField(
        label="Mensaje",
        min_length=10,
        max_length=5000,
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    # Campo trampa para bots. Debe permanecer vacío.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_message(self):
        return self.cleaned_data["message"].strip()
