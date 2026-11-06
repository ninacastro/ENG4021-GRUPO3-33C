from django.contrib import admin
from django import forms
from django.forms.widgets import TextInput
from .models import *
from .mapa_utils import parsear_coordenadas


class CoordenadasMapWidget(TextInput):
    template_name = 'mapucapp/widgets/coordenadas_map.html'

    class Media:
        css = {
            'all': (
                'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
                'css/coordenadas-admin.css',
            ),
        }
        js = (
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
            'js/coordenadas-admin-v2.js',
        )


class CoordenadasMapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['coordenadas'].widget = CoordenadasMapWidget()
        self.fields['coordenadas'].help_text = (
            'Clique no mapa para escolher a localização ou arraste o marcador. '
            'Também é possível informar latitude e longitude em graus decimais.'
        )

    def clean_coordenadas(self):
        coordenadas = self.cleaned_data['coordenadas']
        try:
            parsear_coordenadas(coordenadas)
        except ValueError as erro:
            raise forms.ValidationError(str(erro)) from erro
        return coordenadas


class BibliotecaAdminForm(CoordenadasMapFormMixin, forms.ModelForm):
    class Meta:
        model = Biblioteca
        fields = '__all__'


class RestauranteAdminForm(CoordenadasMapFormMixin, forms.ModelForm):
    class Meta:
        model = Restaurante
        fields = '__all__'


@admin.register(Biblioteca)
class BibliotecaAdmin(admin.ModelAdmin):
    form = BibliotecaAdminForm
    list_display = ('nome', 'predio', 'andar', 'horario_funcionamento')


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    form = RestauranteAdminForm
    list_display = ('nome', 'predio', 'telefone')

admin.site.register(Professor)
admin.site.register(Disciplina)
admin.site.register(Aluno)
admin.site.register(Turma)
admin.site.register(Predio)
admin.site.register(Andar)
admin.site.register(Sala)
admin.site.register(Departamento)
admin.site.register(Notificacao)