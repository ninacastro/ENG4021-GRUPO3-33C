from django.shortcuts import redirect, render
from django.db.models import Q
from .models import *
from .forms import BuscaForm, LoginForm

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
    aluno = Aluno.objects.first()
    turmas = None
    if aluno:
        turmas = aluno.turmas.all()

    context = {
        'aluno': aluno,
        'turmas': turmas,
    }
    return render(request, "telaperfilmelhorado.html", context)


def login(request):
    form_login = LoginForm()
    
    context = {
        'form': form_login
    }
    return render(request, "loginmelhorado.html",context)


def grade(request):
    aluno_atual = Aluno.objects.first()
    turmas_do_aluno = None
    if aluno_atual:
        turmas_do_aluno = aluno_atual.turmas.all()

    context = {
        'aluno': aluno_atual,
        'turmas': turmas_do_aluno,
    }
    return render(request, "telaaulas.html", context)


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
    aluno = Aluno.objects.first()
    iniciais = ""
    if aluno:
        partes = aluno.nome.split()
        iniciais = (partes[0][0] + partes[-1][0]).upper()

    context = {
        'aluno': aluno,
        'iniciais': iniciais,
    }
    return render(request, "deslogar.html", context)

def dados(request):
    perfil = get_object_or_404(Perfil, matricula='2110482')

    if request.method == 'POST':
        perfil.nome = request.POST.get('nome')
        perfil.curso = request.POST.get('curso')
        perfil.email = request.POST.get('email')
        perfil.save()

        messages.success(request, 'Dados atualizados com sucesso!')
        return redirect(request.path)

    return render(request, 'dados.html', {
        'perfil': perfil
    })


def notificacoes(request):
    aluno_atual = Aluno.objects.first()

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
    aluno_atual = Aluno.objects.first()
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
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        curso = request.POST.get('curso')
        periodo = request.POST.get('periodo') or None
        matricula = request.POST.get('matricula')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if senha != confirmar_senha:
            return render(request, 'cadastro.html', {'erro': 'As senhas não coincidem.'})

        if Aluno.objects.filter(email=email).exists() or Aluno.objects.filter(matricula=matricula).exists():
            return render(request, 'cadastro.html', {'erro': 'E-mail ou matrícula já cadastrados.'})

        Aluno.objects.create(
            nome=nome,
            email=email,
            curso=curso,
            periodo=periodo,
            matricula=matricula,
            senha=make_password(senha)
        )

        return redirect('login')

    return render(request, 'cadastro.html')

def restaurantes(request):
    return render(request, 'restaurantes.html')

def privacidade(request):
    return render(request, "privacidade.html")
