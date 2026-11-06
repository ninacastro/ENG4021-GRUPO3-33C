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
    coordenadas_field = 'coordenadas'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.coordenadas_field].widget = CoordenadasMapWidget()
        self.fields[self.coordenadas_field].help_text = (
            'Clique no mapa para escolher a localização ou arraste o marcador. '
            'Também é possível informar latitude e longitude em graus decimais.'
        )

    def clean(self):
        cleaned_data = super().clean()
        coordenadas = cleaned_data.get(self.coordenadas_field)
        if coordenadas is not None:
            try:
                parsear_coordenadas(coordenadas)
            except ValueError as erro:
                self.add_error(self.coordenadas_field, str(erro))
        return cleaned_data


class BibliotecaAdminForm(CoordenadasMapFormMixin, forms.ModelForm):
    class Meta:
        model = Biblioteca
        fields = '__all__'


class RestauranteAdminForm(CoordenadasMapFormMixin, forms.ModelForm):
    class Meta:
        model = Restaurante
        fields = '__all__'


class PredioAdminForm(CoordenadasMapFormMixin, forms.ModelForm):
    coordenadas_field = 'coordenadas_entradas'

    class Meta:
        model = Predio
        fields = '__all__'


class SalaAdminForm(CoordenadasMapFormMixin, forms.ModelForm):
    class Meta:
        model = Sala
        fields = '__all__'


@admin.register(Biblioteca)
class BibliotecaAdmin(admin.ModelAdmin):
    form = BibliotecaAdminForm
    list_display = ('nome', 'predio', 'andar', 'horario_funcionamento')


@admin.register(Restaurante)
class RestauranteAdmin(admin.ModelAdmin):
    form = RestauranteAdminForm
    list_display = ('nome', 'predio', 'telefone')


@admin.register(Predio)
class PredioAdmin(admin.ModelAdmin):
    form = PredioAdminForm
    list_display = ('nome', 'sigla_codigo', 'quantidade_andares', 'horario_funcionamento')


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    form = SalaAdminForm
    list_display = ('codigo_sala', 'nome_exibicao', 'predio', 'andar', 'tipo_sala')


admin.site.register(Professor)
admin.site.register(Disciplina)
admin.site.register(Aluno)
admin.site.register(Turma)
admin.site.register(Andar)
admin.site.register(Departamento)
admin.site.register(Notificacao)