from django import forms

class LoginForm(forms.Form):
    matricula = forms.CharField(
        label='',
        max_length=150,
        # 2. Mudou de EmailInput para TextInput
        widget=forms.TextInput(attrs={
            'class': 'caixa-texto', 
            'placeholder': 'Introduza a sua matrícula da PUC'
        })
    )
    senha = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={
            'class': 'caixa-texto',
            'placeholder': 'Introduza a sua senha'
        })
    )


class BuscaForm(forms.Form):
    busca = forms.CharField(
        label='',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'caixa-texto',
            'placeholder': 'Buscar sala ou prédio'
        })
    )
