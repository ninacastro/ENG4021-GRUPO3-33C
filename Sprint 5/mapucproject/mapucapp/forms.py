from django import forms

class LoginForm(forms.Form):
    matricula = forms.EmailField(
        label='',
        max_length=150,
        widget=forms.EmailInput(attrs={
            'class': 'caixa-texto', 
            'placeholder': 'Introduza o seu matrícula da PUC'
        })
    )
    senha = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={
            'class': 'caixa-texto',
            'placeholder': 'Introduza a sua senha'
        })
    )