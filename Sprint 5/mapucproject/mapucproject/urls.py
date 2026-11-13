from django.contrib import admin
from django.urls import path
from mapucapp.views import *

urlpatterns = [
    path('', login, name='login'),
    path('admin/', admin.site.urls),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('inicio/', inicio, name='inicio'),
    path('mapa/', mapa, name='mapa'),
    path('bibliotecas/', bibliotecas, name='bibliotecas'),
    path('restaurantes/', restaurantes, name='restaurantes'),
    path('perfil/', perfil, name='perfil'),
    path('grade/', grade, name='grade'),
    path('feriados/', feriados, name='feriados'),
    path('detalhes-aula/', aula, name='aula'),
    path('deslogar/', deslogar, name='deslogar'),
    path('dados/', dados, name='dados'),
    path('avisos/', notificacoes, name='avisos'),
    path('notificacoes/', notificacoes, name='notificacoes'),
    path('cadastro/', cadastro, name='cadastro'),
    path('privacidade/', privacidade, name='privacidade'),
    path('cadastrar-grade/', cadastrar_grade, name='cadastrar_grade'),
    path('aulas/<int:aula_id>/excluir/', excluir_aula, name='excluir_aula'),
    path('historico/', historico, name='historico'),
    path('favoritar/<int:sala_id>/', favoritar_sala, name='favoritar_sala'),
    path('recuperar/', recuperar, name='recuperar'),

]
