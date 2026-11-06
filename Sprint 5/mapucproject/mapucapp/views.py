from functools import wraps
import logging

from django.contrib import messages
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import *
from .forms import AlterarDadosForm, BuscaForm, CadastroForm, LoginForm
from .feriados_service import criar_avisos_de_feriados, obter_feriados_proximos
from .mapa_utils import parsear_coordenadas

ALUNO_SESSION_KEY = 'aluno_id'
logger = logging.getLogger(__name__)

def obter_aluno_logado(request):
    aluno_id = request.session.get(ALUNO_SESSION_KEY)
    if aluno_id is None:
        return None

    try:
        return Aluno.objects.get(pk=aluno_id)
    except Aluno.DoesNotExist:
        request.session.pop(ALUNO_SESSION_KEY, None)
        return None


def requer_aluno(view):
    @wraps(view)
    def view_protegida(request, *args, **kwargs):
        if obter_aluno_logado(request) is None:
            return redirect('login')
        return view(request, *args, **kwargs)

    return view_protegida



def inicio(request):
    form_busca = BuscaForm(request.GET or None)
    busca = ''

    if form_busca.is_valid():
        busca = form_busca.cleaned_data['busca'].strip()

    predios = Predio.objects.none()
    salas = Sala.objects.none()

    if busca:
        predios = Predio.objects.filter(
            Q(nome__icontains=busca) |
            Q(sigla_codigo__icontains=busca)
        )

        salas = Sala.objects.select_related('predio', 'andar').filter(
            Q(codigo_sala__icontains=busca) |
            Q(nome_exibicao__icontains=busca) |
            Q(predio__nome__icontains=busca) |
            Q(predio__sigla_codigo__icontains=busca)
        )

        aluno = obter_aluno_logado(request)

        if aluno:
            HistoricoBusca.objects.create(
                aluno=aluno,
                termo=busca
            )

    context = {
        'form_busca': form_busca,
        'busca': busca,
        'predios': predios,
        'salas': salas,
    }

    return render(request, "telainiciomelhorada.html", context)

def historico(request):
    aluno = obter_aluno_logado(request)

    buscas = HistoricoBusca.objects.filter(
        aluno=aluno
    ).order_by('-data')

    context = {
        'buscas': buscas
    }

    return render(request, 'historico.html', context)


def mapa(request):
    return render_mapa(request)


def render_mapa(request, categoria=None):
    marcadores = []
    coordenadas_invalidas = []
    local_selecionado = None

    tipo_local = request.GET.get('local')
    id_local = request.GET.get('id')

    if tipo_local == 'predio' and id_local:
        local = Predio.objects.filter(pk=id_local).first()
        if local:
            nome_local = local.nome
            coordenadas_local = local.coordenadas_entradas
        else:
            coordenadas_local = None
    elif tipo_local == 'sala' and id_local:
        local = Sala.objects.filter(pk=id_local).first()
        if local:
            nome_local = local.nome_exibicao
            coordenadas_local = local.coordenadas
        else:
            coordenadas_local = None
    else:
        local = None
        coordenadas_local = None

    if local and coordenadas_local:
        try:
            latitude, longitude = parsear_coordenadas(coordenadas_local)
        except ValueError:
            coordenadas_invalidas.append(nome_local)
        else:
            local_selecionado = {
                'latitude': latitude,
                'longitude': longitude,
                'nome': nome_local,
            }

    if categoria == 'bibliotecas':
        locais = Biblioteca.objects.select_related('predio', 'andar')
        for biblioteca in locais:
            try:
                latitude, longitude = parsear_coordenadas(biblioteca.coordenadas)
            except ValueError:
                coordenadas_invalidas.append(biblioteca.nome)
                continue

            marcadores.append({
                'latitude': latitude,
                'longitude': longitude,
                'nome': biblioteca.nome,
                'detalhes': (
                    f'{biblioteca.predio.nome} · {biblioteca.andar.nome_exibicao} · '
                    f'{biblioteca.horario_funcionamento}'
                ),
            })
    elif categoria == 'restaurantes':
        locais = Restaurante.objects.select_related('predio')
        for restaurante in locais:
            try:
                latitude, longitude = parsear_coordenadas(restaurante.coordenadas)
            except ValueError:
                coordenadas_invalidas.append(restaurante.nome)
                continue

            detalhes = restaurante.predio.nome
            if restaurante.telefone:
                detalhes = f'{detalhes} · {restaurante.telefone}'
            marcadores.append({
                'latitude': latitude,
                'longitude': longitude,
                'nome': restaurante.nome,
                'detalhes': detalhes,
            })

    titulos = {
        'bibliotecas': 'Bibliotecas',
        'restaurantes': 'Alimentação',
    }
    return render(request, 'mapa.html', {
        'marcadores': marcadores,
        'coordenadas_invalidas': coordenadas_invalidas,
        'titulo_mapa': titulos.get(categoria),
        'local_selecionado': local_selecionado,
    })


def bibliotecas(request):
    return render_mapa(request, categoria='bibliotecas')


def restaurantes(request):
    return render_mapa(request, categoria='restaurantes')


def perfil(request):
    aluno = obter_aluno_logado(request)
    if aluno is None:
        return redirect('login')
    turmas = None
    if aluno:
        turmas = aluno.turmas.all()

    context = {
        'aluno': aluno,
        'turmas': turmas,
    }
    return render(request, "telaperfilmelhorado.html", context)


def login(request):
    if obter_aluno_logado(request) is not None:
        return redirect('inicio')

    form = LoginForm(
        request.POST if request.method == 'POST' else None
    )
    if request.method == 'POST' and form.is_valid():
        try:
            aluno = Aluno.objects.get(matricula=form.cleaned_data['matricula'])
        except Aluno.DoesNotExist:
            aluno = None

        senha_digitada = form.cleaned_data['senha']
        senha_valida = False
        senha_legada = False
        if aluno is not None:
            try:
                identify_hasher(aluno.senha)
            except ValueError:
                senha_legada = True
                senha_valida = constant_time_compare(senha_digitada, aluno.senha)
            else:
                senha_valida = check_password(senha_digitada, aluno.senha)

        if aluno is not None and senha_valida:
            if senha_legada:
                aluno.senha = make_password(senha_digitada)
                aluno.save(update_fields=['senha'])
            request.session.cycle_key()
            request.session[ALUNO_SESSION_KEY] = aluno.pk
            messages.success(request, 'Login realizado com sucesso.')
            return redirect('inicio')

        form.add_error(None, 'Matrícula ou senha inválida.')

    return render(request, "loginmelhorado.html", {'form': form})


@require_POST
def logout(request):
    request.session.flush()
    messages.success(request, 'Você saiu da sua conta.')
    return redirect('login')


def grade(request):
    aluno_atual = obter_aluno_logado(request)
    turmas_do_aluno = None
    if aluno_atual:
        turmas_do_aluno = aluno_atual.turmas.all()

    context = {
        'aluno': aluno_atual,
        'turmas': turmas_do_aluno,
    }
    return render(request, "telaaulas.html", context)



def feriados(request):
    try:
        feriados_proximos = obter_feriados_proximos()
        erro_feriados = None
    except (OSError, ValueError):
        logger.exception("Não foi possível carregar os próximos feriados.")
        feriados_proximos = []
        erro_feriados = (
            "Não foi possível carregar os feriados agora. Tente novamente mais tarde."
        )

    return render(request, "feriadoAPI.html", {
        'feriados': feriados_proximos,
        'erro_feriados': erro_feriados,
    })


def aula(request):
    turma_especifica = Turma.objects.first()
    salas_da_turma = None
    if turma_especifica:
        salas_da_turma = turma_especifica.salas.all()

    context = {
        'turma': turma_especifica,
        'salas': salas_da_turma,
    }
    return render(request, "aula.html", context)


def deslogar(request):
    aluno = obter_aluno_logado(request)
    if aluno is None:
        return redirect('login')
    iniciais = ""
    if aluno:
        partes = aluno.nome.split()
        iniciais = (partes[0][0] + partes[-1][0]).upper()

    context = {
        'aluno': aluno,
        'iniciais': iniciais,
    }
    return render(request, "deslogar.html", context)

@requer_aluno
def dados(request):
    perfil = obter_aluno_logado(request)
    if perfil is None:
        raise Http404("Nenhum aluno está cadastrado.")

    form = AlterarDadosForm(
        request.POST if request.method == 'POST' else None,
        instance=perfil,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()

        messages.success(request, 'Dados atualizados com sucesso!')
        return redirect(request.path)

    return render(request, 'dados.html', {'perfil': perfil, 'form': form})


def notificacoes(request):
    erro_feriados = None
    try:
        criar_avisos_de_feriados()
    except (OSError, ValueError):
        logger.exception("Não foi possível sincronizar avisos de feriados.")
        erro_feriados = (
            "Não foi possível atualizar os avisos de feriados agora. "
            "Tente novamente mais tarde."
        )

    aluno_atual = obter_aluno_logado(request)

    if aluno_atual:
        avisos_do_aluno = Notificacao.objects.filter(aluno=aluno_atual)

        if request.method == 'POST' and request.POST.get('acao') == 'marcar_todas_lidas':
            avisos_do_aluno.filter(lida=False).update(lida=True)
            return redirect('avisos')

        avisos_do_aluno = avisos_do_aluno.order_by('-data_criacao')
        notificacoes_nao_lidas = avisos_do_aluno.filter(lida=False).exists()
    else:
        avisos_do_aluno = Notificacao.objects.none()
        notificacoes_nao_lidas = False

    context = {
        'notificacoes': avisos_do_aluno,
        'notificacoes_nao_lidas': notificacoes_nao_lidas,
        'aluno': aluno_atual,
        'erro_feriados': erro_feriados,
    }
    return render(request, 'notificacoesmelhorado.html', context)



def cadastro(request):
    form = CadastroForm(
        request.POST if request.method == 'POST' else None
    )
    if request.method == 'POST' and form.is_valid():
        aluno = form.save(commit=False)
        aluno.senha = make_password(form.cleaned_data['senha'])
        aluno.save()
        messages.success(request, 'Cadastro realizado. Entre com sua matrícula e senha.')
        return redirect('login')

    return render(request, 'cadastro.html', {'form': form})

def privacidade(request):
    return render(request, "privacidade.html")
    
def cadastrar_grade(request):
    return render(request, 'cadastrograde.html')
