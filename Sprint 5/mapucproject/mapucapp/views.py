from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import *
from .forms import AlterarDadosForm, BuscaForm, CadastroForm, LoginForm

ALUNO_SESSION_KEY = 'aluno_id'


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

    context = {
        'form_busca': form_busca,
        'busca': busca,
        'predios': predios,
        'salas': salas,
    }
    return render(request, "telainiciomelhorada.html", context)


def bibliotecas(request):
    bibliotecas = Sala.objects.filter(tipo_sala__icontains="Biblioteca")

    context = {
        'bibliotecas': bibliotecas,
    }
    return render(request, "bibliotecas.html", context)


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
    return render(request, "feriadoAPI.html")


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
    }
    return render(request, 'notificacoesmelhorado.html', context)



def rota(request):
    destino = 'F402'
    local_atual = 'Você está aqui'

    return render(request, 'telarota.html', {
        'destino': destino,
        'local_atual': local_atual
    })


def caminho_frings(request):
    predios = Predio.objects.all()
    aluno_atual = obter_aluno_logado(request)
    notificacoes_nao_lidas = 0
    if aluno_atual:
        notificacoes_nao_lidas = Notificacao.objects.filter(
            aluno=aluno_atual,
            lida=False,
        ).count()

    context = {
        'predios': predios,
        'notificacoes_nao_lidas': notificacoes_nao_lidas,
    }

    return render(request, 'caminhofrings.html', context)



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

def restaurantes(request):
    return render(request, 'restaurantes.html')

def privacidade(request):
    return render(request, "privacidade.html")
