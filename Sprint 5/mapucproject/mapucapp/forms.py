from django import forms
from django.core.exceptions import ValidationError

from .models import Aluno, AulaGrade

class LoginForm(forms.Form):
    matricula = forms.CharField(
        label='',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'caixa-texto',
            'placeholder': 'Introduza a sua matrícula da PUC',
            'autocomplete': 'username',
        })
    )
    senha = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'caixa-texto',
            'placeholder': 'Introduza a sua senha',
            'autocomplete': 'current-password',
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


class CadastroForm(forms.ModelForm):
    cep = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '00000-000'})
    )
    curso = forms.ChoiceField(choices=[
        ('', 'Selecione seu curso...'),
        ('Engenharia da Computação', 'Engenharia da Computação'),
        ('Engenharia de Produção', 'Engenharia de Produção'),
        ('Outro', 'Outro'),
    ])
    periodo = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'min': 1,
            'placeholder': 'Ex: 2',
        })
    )
    senha = forms.CharField(
        strip=False,
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Crie sua senha segura',
            'autocomplete': 'new-password',
        })
    )
    confirmar_senha = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Digite a senha novamente',
            'autocomplete': 'new-password',
        })
    )
    receber_noticias = forms.BooleanField(required=False)
    aceitou_privacidade = forms.BooleanField(required=True)

    class Meta:
        model = Aluno
        fields = ('nome', 'email', 'curso', 'periodo', 'matricula', 'senha')
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Ex: Mariana Silva e Souza',
                'autocomplete': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'aluno@puc.br ou seu email',
                'autocomplete': 'email',
            }),
            'matricula': forms.TextInput(attrs={
                'placeholder': 'Ex: 2024108849',
            }),
        }

    def clean_senha(self):
        senha = self.cleaned_data['senha']
        if not any(caractere.isdecimal() for caractere in senha):
            raise ValidationError('A senha deve conter pelo menos 1 número.')
        simbolos = sum(
            not caractere.isalnum() and not caractere.isspace()
            for caractere in senha
        )
        if simbolos < 2:
            raise ValidationError('A senha deve conter pelo menos 2 símbolos.')
        return senha

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')
        return cleaned_data


class AlterarDadosForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ('nome', 'curso', 'email')


class AulaGradeForm(forms.ModelForm):
    class Meta:
        model = AulaGrade
        fields = (
            'codigo_disciplina',
            'nome_disciplina',
            'dia_semana',
            'horario',
            'codigo_sala',
            'cor',
        )
        labels = {
            'codigo_disciplina': 'Código da disciplina',
            'nome_disciplina': 'Nome da disciplina',
            'dia_semana': 'Dia da semana',
            'horario': 'Horário',
            'codigo_sala': 'Sala',
            'cor': 'Cor na grade',
        }
        widgets = {
            'codigo_disciplina': forms.TextInput(attrs={'placeholder': 'Ex: INF1005'}),
            'nome_disciplina': forms.TextInput(attrs={'placeholder': 'Ex: Introdução à Computação'}),
            'codigo_sala': forms.TextInput(attrs={'placeholder': 'Ex: L318'}),
        }

    def __init__(self, *args, aluno=None, **kwargs):
        self.aluno = aluno
        kwargs.setdefault('initial', {'cor': 'verde'})
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.aluno is None:
            return cleaned_data

        dia_semana = cleaned_data.get('dia_semana')
        horario = cleaned_data.get('horario')
        if dia_semana and horario and AulaGrade.objects.filter(
            aluno=self.aluno,
            dia_semana=dia_semana,
            horario=horario,
        ).exists():
            raise ValidationError(
                'Você já cadastrou uma aula nesse dia e horário.'
            )

        return cleaned_data


from django import forms
from mapucapp.models import Aluno
import re


class RecuperarSenhaForm(forms.Form):
    matricula = forms.CharField(
        max_length=20,
        required=True
    )

    email = forms.EmailField(
        required=True
    )

    def clean(self):
        dados = super().clean()

        matricula = dados.get('matricula')
        email = dados.get('email')

        if matricula and email:
            aluno = Aluno.objects.filter(
                matricula=matricula,
                email__iexact=email
            ).first()

            if not aluno:
                raise forms.ValidationError(
                    'Matrícula ou e-mail institucional incorreto.'
                )

            dados['aluno'] = aluno

        return dados


class NovaSenhaForm(forms.Form):
    nova_senha = forms.CharField(
        required=True,
        widget=forms.PasswordInput
    )

    confirmar_senha = forms.CharField(
        required=True,
        widget=forms.PasswordInput
    )

    def clean(self):
        dados = super().clean()

        senha = dados.get('nova_senha')
        confirmar = dados.get('confirmar_senha')

        if senha:
            if len(senha) < 8:
                self.add_error(
                    'nova_senha',
                    'A senha deve ter no mínimo 8 caracteres.'
                )

            if len(re.findall(r'[^a-zA-Z0-9]', senha)) < 2:
                self.add_error(
                    'nova_senha',
                    'A senha deve possuir no mínimo 2 símbolos.'
                )

            if not re.search(r'[0-9]', senha):
                self.add_error(
                    'nova_senha',
                    'A senha deve possuir no mínimo 1 número.'
                )

        if senha and confirmar and senha != confirmar:
            self.add_error(
                'confirmar_senha',
                'As senhas não são iguais.'
            )

        return dados


from django import forms


class RecuperarSenhaForm(forms.Form):
    matricula = forms.CharField(
        max_length=20,
        required=True
    )

    email = forms.EmailField(
        required=True
    )

    def clean(self):
        dados = super().clean()

        matricula = dados.get('matricula')
        email = dados.get('email')

        if matricula and email:
            from .models import Aluno

            aluno = Aluno.objects.filter(
                matricula=matricula,
                email__iexact=email
            ).first()

            if not aluno:
                raise forms.ValidationError(
                    'Matrícula ou e-mail institucional incorreto.'
                )

            dados['aluno'] = aluno

        return dados


class NovaSenhaForm(forms.Form):
    nova_senha = forms.CharField(
        required=True,
        widget=forms.PasswordInput
    )

    confirmar_senha = forms.CharField(
        required=True,
        widget=forms.PasswordInput
    )

    def clean(self):
        dados = super().clean()

        senha = dados.get('nova_senha')
        confirmar = dados.get('confirmar_senha')

        if senha:

            if len(senha) < 8:
                self.add_error(
                    'nova_senha',
                    'A senha deve ter no mínimo 8 caracteres.'
                )


            simbolos = 0

            for caractere in senha:
                if not caractere.isalnum():
                    simbolos += 1

            if simbolos < 2:
                self.add_error(
                    'nova_senha',
                    'A senha deve possuir no mínimo 2 símbolos.'
                )


            tem_numero = False

            for caractere in senha:
                if caractere.isdigit():
                    tem_numero = True

            if not tem_numero:
                self.add_error(
                    'nova_senha',
                    'A senha deve possuir no mínimo 1 número.'
                )


        if senha and confirmar and senha != confirmar:
            self.add_error(
                'confirmar_senha',
                'As senhas não são iguais.'
            )

        return dados
