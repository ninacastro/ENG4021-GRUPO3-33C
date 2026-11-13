from io import BytesIO
from datetime import date, datetime
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache

from .models import (
    Aluno,
    Andar,
    AulaGrade,
    Biblioteca,
    LocalFavorito,
    MateriaGrade,
    Notificacao,
    Predio,
    Restaurante,
    Sala,
)
from .feriados_service import (
    criar_avisos_de_feriados,
    obter_feriados_proximos,
    buscar_feriados,
)
from .mapa_utils import parsear_coordenadas
from .admin import (
    BibliotecaAdminForm,
    PredioAdminForm,
    RestauranteAdminForm,
    SalaAdminForm,
)


class RecuperacaoSenhaTests(TestCase):
    def setUp(self):
        self.aluno = Aluno.objects.create(
            nome='Ana Silva',
            email='ana@aluno.puc-rio.br',
            senha=make_password('SenhaAntiga1!'),
            matricula='2024108849',
            curso='Engenharia',
            periodo=3,
        )

    def test_fluxo_de_recuperacao_altera_a_senha(self):
        url = reverse('recuperar')

        resposta_inicial = self.client.get(url)
        self.assertEqual(resposta_inicial.status_code, 200)
        self.assertTemplateUsed(resposta_inicial, 'recuperar.html')
        self.assertEqual(resposta_inicial.context['etapa'], 'identificacao')

        resposta_identificacao = self.client.post(url, {
            'matricula': self.aluno.matricula,
            'email': self.aluno.email,
        })
        self.assertEqual(resposta_identificacao.status_code, 200)
        self.assertEqual(resposta_identificacao.context['etapa'], 'nova_senha')

        resposta_nova_senha = self.client.post(url, {
            'nova_senha': 'Nova!Senha1@',
            'confirmar_senha': 'Nova!Senha1@',
        })
        self.assertRedirects(resposta_nova_senha, reverse('login'))

        self.aluno.refresh_from_db()
        self.assertTrue(check_password('Nova!Senha1@', self.aluno.senha))


class MapaViewTests(TestCase):
    @patch('mapucapp.models.timezone.localtime')
    def test_predio_informa_seu_status_de_acordo_com_horario_local(self, mock_localtime):
        predio = Predio(
            horario_funcionamento='08:00 - 20:00',
        )

        mock_localtime.return_value = datetime(2026, 11, 13, 8, 0)
        self.assertTrue(predio.esta_aberto)

        mock_localtime.return_value = datetime(2026, 11, 13, 20, 0)
        self.assertFalse(predio.esta_aberto)

    def test_predio_sem_horario_nao_informa_status(self):
        predio = Predio(horario_funcionamento='')

        self.assertIsNone(predio.esta_aberto)

    @patch('mapucapp.models.timezone.localtime')
    def test_resultado_da_busca_mostra_status_do_predio(self, mock_localtime):
        predio = Predio.objects.create(
            nome='Prédio de teste',
            sigla_codigo='PT',
            coordenadas_entradas='-22.9785, -43.2324',
            quantidade_andares=1,
            horario_funcionamento='08:00 - 20:00',
        )
        andar = Andar.objects.create(
            predio=predio,
            numero_andar=1,
            nome_exibicao='Térreo',
        )
        Sala.objects.create(
            codigo_sala='S1',
            nome_exibicao='Sala de teste',
            predio=predio,
            andar=andar,
            coordenadas='-22.9786, -43.2325',
            tipo_sala='Aula',
            capacidade=20,
        )

        for horario, status, status_do_predio in (
            (datetime(2026, 11, 13, 8, 0), 'Aberto', 'aberto'),
            (datetime(2026, 11, 13, 20, 0), 'Fechado', 'fechado'),
        ):
            with self.subTest(status=status):
                mock_localtime.return_value = horario
                resposta_predio = self.client.get(
                    reverse('inicio'),
                    {'busca': predio.nome},
                )
                resposta_sala = self.client.get(
                    reverse('inicio'),
                    {'busca': 'Sala de teste'},
                )

                self.assertContains(resposta_predio, status)
                if status == 'Fechado':
                    self.assertContains(
                        resposta_predio,
                        'class="status-local status-local--fechado"',
                    )
                classe_fechado = (
                    ' status-local--fechado'
                    if status_do_predio == 'fechado'
                    else ''
                )
                self.assertContains(
                    resposta_sala,
                    f'class="status-local{classe_fechado}">{status_do_predio}</span>',
                )

    def test_mapa_em_tela_cheia_renderiza_mapa_e_link_de_volta(self):
        response = self.client.get(reverse('mapa'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapa.html')
        self.assertContains(response, 'id="mapa-puc"')
        self.assertContains(response, 'id="botao-localizacao"')
        self.assertContains(response, 'id="botao-rota"')
        self.assertContains(response, 'Valhalla/OSM')
        self.assertContains(response, '/static/js/mapa-puc.js?v=4')
        self.assertContains(response, reverse('inicio'))
        self.assertEqual(response.context['marcadores'], [])

    def test_tela_inicial_nao_renderiza_pins(self):
        response = self.client.get(reverse('inicio'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="mapa-puc"')
        self.assertContains(response, '/static/js/mapa-puc.js?v=4')
        self.assertNotContains(response, 'mapa-marcadores')
        self.assertNotContains(response, 'Prédio Cardeal Leme')

    def test_resultado_da_busca_abre_mapa_com_pin_do_predio(self):
        predio = Predio.objects.create(
            nome='Prédio de teste',
            sigla_codigo='PT',
            coordenadas_entradas='-22.9785, -43.2324',
            quantidade_andares=1,
            horario_funcionamento='08:00-20:00',
        )

        resposta_busca = self.client.get(
            reverse('inicio'),
            {'busca': 'Prédio'},
        )

        self.assertEqual(resposta_busca.status_code, 200)
        self.assertContains(
            resposta_busca,
            f'href="{reverse("mapa")}?local=predio&id={predio.pk}"',
        )

        resposta_mapa = self.client.get(
            reverse('mapa'),
            {'local': 'predio', 'id': predio.pk},
        )
        self.assertEqual(resposta_mapa.status_code, 200)
        self.assertEqual(
            resposta_mapa.context['local_selecionado'],
            {
                'latitude': -22.9785,
                'longitude': -43.2324,
                'nome': predio.nome,
            },
        )
        self.assertContains(resposta_mapa, 'id="mapa-local-selecionado"')

    def test_resultado_da_busca_abre_mapa_com_pin_da_sala(self):
        predio = Predio.objects.create(
            nome='Prédio de teste',
            sigla_codigo='PT',
            coordenadas_entradas='-22.9785, -43.2324',
            quantidade_andares=1,
            horario_funcionamento='08:00-20:00',
        )
        andar = Andar.objects.create(
            predio=predio,
            numero_andar=1,
            nome_exibicao='Térreo',
        )
        sala = Sala.objects.create(
            codigo_sala='S1',
            nome_exibicao='Sala de teste',
            predio=predio,
            andar=andar,
            coordenadas='-22.9786, -43.2325',
            tipo_sala='Aula',
            capacidade=20,
        )

        resposta_busca = self.client.get(reverse('inicio'), {'busca': 'Sala'})
        self.assertContains(
            resposta_busca,
            f'href="{reverse("mapa")}?local=sala&id={sala.pk}"',
        )

        resposta_mapa = self.client.get(
            reverse('mapa'),
            {'local': 'sala', 'id': sala.pk},
        )
        self.assertEqual(resposta_mapa.status_code, 200)
        self.assertEqual(
            resposta_mapa.context['local_selecionado'],
            {
                'latitude': -22.9786,
                'longitude': -43.2325,
                'nome': sala.nome_exibicao,
            },
        )

    def test_mapa_de_bibliotecas_e_restaurantes_mostra_so_sua_categoria(self):
        predio = Predio.objects.create(
            nome='Prédio de teste',
            sigla_codigo='PT',
            coordenadas_entradas='-22.9785, -43.2324',
            quantidade_andares=3,
            horario_funcionamento='08:00-20:00',
        )
        andar = Andar.objects.create(
            predio=predio,
            numero_andar=1,
            nome_exibicao='1º andar',
            possui_elevador=True,
        )
        biblioteca = Biblioteca.objects.create(
            nome='Biblioteca de teste',
            predio=predio,
            andar=andar,
            coordenadas='-22.9786, -43.2325',
            horario_funcionamento='08:00-18:00',
        )
        restaurante = Restaurante.objects.create(
            nome='Restaurante de teste',
            predio=predio,
            coordenadas='-22.9787, -43.2326',
            telefone='2222-2222',
        )

        resposta_bibliotecas = self.client.get(reverse('bibliotecas'))
        self.assertEqual(resposta_bibliotecas.status_code, 200)
        self.assertEqual(resposta_bibliotecas.context['titulo_mapa'], 'Bibliotecas')
        self.assertEqual(len(resposta_bibliotecas.context['marcadores']), 1)
        self.assertEqual(
            resposta_bibliotecas.context['marcadores'][0]['nome'],
            biblioteca.nome,
        )
        self.assertContains(resposta_bibliotecas, biblioteca.nome)
        self.assertNotContains(resposta_bibliotecas, restaurante.nome)

        resposta_restaurantes = self.client.get(reverse('restaurantes'))
        self.assertEqual(resposta_restaurantes.status_code, 200)
        self.assertEqual(resposta_restaurantes.context['titulo_mapa'], 'Alimentação')
        self.assertEqual(len(resposta_restaurantes.context['marcadores']), 1)
        self.assertEqual(
            resposta_restaurantes.context['marcadores'][0]['nome'],
            restaurante.nome,
        )
        self.assertContains(resposta_restaurantes, restaurante.nome)
        self.assertNotContains(resposta_restaurantes, biblioteca.nome)

    def test_coordenadas_do_mapa_sao_validada_e_convertidas(self):
        self.assertEqual(
            parsear_coordenadas('-22.9785, -43.2324'),
            (-22.9785, -43.2324),
        )
        for coordenadas in ('sem coordenadas', '100, 200', 'nan, -43.2'):
            with self.subTest(coordenadas=coordenadas):
                with self.assertRaises(ValueError):
                    parsear_coordenadas(coordenadas)

    def test_formularios_admin_exibem_seletor_de_localizacao_no_mapa(self):
        formularios = (
            (BibliotecaAdminForm, 'coordenadas'),
            (RestauranteAdminForm, 'coordenadas'),
            (PredioAdminForm, 'coordenadas_entradas'),
            (SalaAdminForm, 'coordenadas'),
        )
        for form_class, campo_nome in formularios:
            with self.subTest(form=form_class.__name__, campo=campo_nome):
                form = form_class()
                campo = str(form[campo_nome])

                self.assertIn('coordenadas-seletor', campo)
                self.assertIn(f'data-coordenadas-input="id_{campo_nome}"', campo)
                self.assertIn('Clique no mapa', campo)
                self.assertIn('leaflet@1.9.4/dist/leaflet.js', str(form.media))
                self.assertIn('coordenadas-admin-v2.js', str(form.media))

    def test_formularios_admin_validam_coordenadas_de_predio_e_sala(self):
        predio_form = PredioAdminForm(data={
            'nome': 'Prédio inválido',
            'sigla_codigo': 'PI',
            'coordenadas_entradas': 'coordenada inválida',
            'quantidade_andares': 1,
            'horario_funcionamento': '08:00-18:00',
        })
        self.assertFalse(predio_form.is_valid())
        self.assertIn('coordenadas_entradas', predio_form.errors)

        predio = Predio.objects.create(
            nome='Prédio de teste',
            sigla_codigo='PT',
            coordenadas_entradas='-22.9785, -43.2324',
            quantidade_andares=1,
            horario_funcionamento='08:00-18:00',
        )
        andar = Andar.objects.create(
            predio=predio,
            numero_andar=1,
            nome_exibicao='Térreo',
        )
        sala_form = SalaAdminForm(data={
            'codigo_sala': 'S1',
            'nome_exibicao': 'Sala de teste',
            'predio': predio.pk,
            'andar': andar.pk,
            'coordenadas': 'coordenada inválida',
            'tipo_sala': 'Aula',
            'capacidade': 20,
        })
        self.assertFalse(sala_form.is_valid())
        self.assertIn('coordenadas', sala_form.errors)

    def test_inicio_exibe_link_para_mapa_em_tela_cheia(self):
        response = self.client.get(reverse('inicio'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('mapa'))
        self.assertContains(response, 'Abrir mapa em tela cheia')

    def test_resultado_de_sala_exibe_botao_de_favorito_e_mantem_busca_apos_clique(self):
        aluno = Aluno.objects.create(
            nome='Ana Silva',
            email='ana@example.com',
            senha=make_password('senha123'),
            matricula='12345',
            curso='Engenharia',
            periodo=3,
        )
        predio = Predio.objects.create(
            nome='Prédio de teste',
            sigla_codigo='PT',
            coordenadas_entradas='-22.9785, -43.2324',
            quantidade_andares=1,
            horario_funcionamento='08:00-20:00',
        )
        andar = Andar.objects.create(
            predio=predio,
            numero_andar=1,
            nome_exibicao='Térreo',
        )
        sala = Sala.objects.create(
            codigo_sala='S1',
            nome_exibicao='Sala de teste',
            predio=predio,
            andar=andar,
            coordenadas='-22.9786, -43.2325',
            tipo_sala='Aula',
            capacidade=20,
        )
        session = self.client.session
        session['aluno_id'] = aluno.pk
        session.save()

        resposta_busca = self.client.get(reverse('inicio'), {'busca': 'S1'})

        self.assertEqual(resposta_busca.status_code, 200)
        self.assertContains(resposta_busca, 'class="botao-favoritar"')
        self.assertContains(resposta_busca, '☆')

        resposta_favorito = self.client.post(
            reverse('favoritar_sala', args=[sala.pk]),
            {'busca': 'S1'},
        )

        self.assertRedirects(resposta_favorito, f"{reverse('inicio')}?busca=S1")
        self.assertEqual(LocalFavorito.objects.get(aluno=aluno, sala=sala).sala, sala)
        resposta_atualizada = self.client.get(resposta_favorito.url)
        self.assertContains(resposta_atualizada, '★')

    def test_atalhos_de_biblioteca_e_alimentacao_abrem_o_mapa(self):
        response_inicio = self.client.get(reverse('inicio'))

        self.assertEqual(response_inicio.status_code, 200)
        self.assertContains(response_inicio, f'href="{reverse("bibliotecas")}"')
        self.assertContains(response_inicio, f'href="{reverse("restaurantes")}"')

        for rota in ('bibliotecas', 'restaurantes'):
            with self.subTest(rota=rota):
                response = self.client.get(reverse(rota))
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'mapa.html')

    def test_link_da_tela_inicial_abre_a_grade(self):
        response_inicio = self.client.get(reverse('inicio'))

        self.assertEqual(response_inicio.status_code, 200)
        self.assertContains(
            response_inicio,
            f'<a class="botao-acao botao-g" href="{reverse("grade")}">Minha Grade de Aulas</a>',
        )

        response_grade = self.client.get(reverse('grade'))
        self.assertEqual(response_grade.status_code, 200)
        self.assertTemplateUsed(response_grade, 'telaaulas.html')


class AvisosViewTests(TestCase):
    def setUp(self):
        cache.delete('sync_feriados')
        self.aluno = Aluno.objects.create(
            nome='Ana Silva',
            email='ana@example.com',
            senha=make_password('senha123'),
            matricula='12345',
            curso='Engenharia',
            periodo=3,
        )
        session = self.client.session
        session['aluno_id'] = self.aluno.pk
        session.save()
        patcher = patch('mapucapp.views.criar_avisos_de_feriados')
        self.mock_criar_avisos = patcher.start()
        self.addCleanup(patcher.stop)

    def test_avisos_sincronizam_feriados_a_cada_acesso(self):
        self.client.get(reverse('avisos'))
        self.client.get(reverse('avisos'))

        self.assertEqual(self.mock_criar_avisos.call_count, 2)

    def test_avisos_mostram_notificacoes_do_aluno(self):
        aviso = Notificacao.objects.create(
            aluno=self.aluno,
            titulo='Mudança de sala',
            mensagem='A aula será na sala F309.',
        )

        response = self.client.get(reverse('avisos'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notificacoesmelhorado.html')
        self.assertContains(response, aviso.titulo)
        self.assertContains(response, aviso.mensagem)
        self.assertContains(response, 'Marcar tudo como lido')

    def test_avisos_tambem_estao_disponiveis_na_url_antiga(self):
        response = self.client.get(reverse('notificacoes'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'notificacoesmelhorado.html')

    def test_marcar_tudo_atualiza_apenas_notificacoes_do_aluno_atual(self):
        aviso = Notificacao.objects.create(
            aluno=self.aluno,
            titulo='Aviso do aluno atual',
            mensagem='Mensagem',
        )
        outro_aluno = Aluno.objects.create(
            nome='Bruno Souza',
            email='bruno@example.com',
            senha='senha',
            matricula='67890',
            curso='Direito',
            periodo=2,
        )
        aviso_de_outro_aluno = Notificacao.objects.create(
            aluno=outro_aluno,
            titulo='Aviso de outro aluno',
            mensagem='Mensagem',
        )

        response = self.client.post(
            reverse('avisos'),
            {'acao': 'marcar_todas_lidas'},
        )

        self.assertRedirects(response, reverse('avisos'))
        aviso.refresh_from_db()
        aviso_de_outro_aluno.refresh_from_db()
        self.assertTrue(aviso.lida)
        self.assertFalse(aviso_de_outro_aluno.lida)


class FeriadosViewTests(TestCase):
    @patch(
        'mapucapp.feriados_service.urlopen',
        return_value=BytesIO(
            b'[{"date":"2026-11-20","name":"Dia da consciencia negra"}]'
        ),
    )
    def test_busca_feriados_chama_api_com_o_ano_correto(self, mock_urlopen):
        cache_key = 'feriados_nacionais_2026'
        cache.delete(cache_key)
        self.addCleanup(cache.delete, cache_key)

        feriados = buscar_feriados(2026)

        requisicao = mock_urlopen.call_args.args[0]
        self.assertEqual(
            requisicao.full_url,
            'https://brasilapi.com.br/api/feriados/v1/2026',
        )
        self.assertEqual(
            requisicao.get_header('User-agent'),
            'Mozilla/5.0 MaPUC/1.0',
        )
        self.assertEqual(requisicao.get_header('Accept'), 'application/json')
        self.assertEqual(mock_urlopen.call_args.kwargs['timeout'], 10)
        self.assertEqual(feriados[0]['name'], 'Dia da consciencia negra')

    @patch('mapucapp.views.obter_feriados_proximos', return_value=[])
    def test_pagina_de_feriados_tem_estilo_e_link_de_volta_para_grade(self, _mock):
        response = self.client.get(reverse('feriados'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feriadoAPI.html')
        self.assertContains(response, '/static/css/feriadoAPI.css')
        self.assertContains(response, reverse('grade'))
        self.assertContains(response, 'Não há feriados nacionais em dias úteis')

    @patch(
        'mapucapp.views.obter_feriados_proximos',
        return_value=[{
            'nome': 'Feriado de teste',
            'data': date(2026, 11, 20),
            'data_formatada': '20/11/2026',
            'dia_semana': 'sexta-feira',
        }],
    )
    def test_pagina_de_feriados_mostra_apenas_feriados_proximos_uteis(self, _mock):
        response = self.client.get(reverse('feriados'))

        self.assertContains(response, 'Feriado de teste')
        self.assertContains(response, 'sexta-feira, 20/11/2026')

    def test_feriados_proximos_ignora_finais_de_semana_e_fora_do_periodo(self):
        feriados = [
            {'date': '2026-11-15', 'name': 'Antes do período'},
            {'date': '2026-11-20', 'name': 'Sexta-feira'},
            {'date': '2026-11-21', 'name': 'Sábado'},
            {'date': '2026-12-17', 'name': 'Fora do período'},
        ]

        with patch('mapucapp.feriados_service.buscar_feriados', return_value=feriados):
            proximos = obter_feriados_proximos(hoje=date(2026, 11, 16))

        self.assertEqual([feriado['nome'] for feriado in proximos], ['Sexta-feira'])

    def test_feriado_15_dias_a_frente_aparece_na_lista_de_proximos(self):
        feriados = [{'date': '2026-11-20', 'name': 'Dia da consciência negra'}]

        with patch('mapucapp.feriados_service.buscar_feriados', return_value=feriados):
            proximos = obter_feriados_proximos(hoje=date(2026, 11, 5))

        self.assertEqual(
            [feriado['nome'] for feriado in proximos],
            ['Dia da consciência negra'],
        )

    def test_avisos_de_feriados_sao_criados_apenas_para_dias_uteis_e_sem_duplicar(self):
        aluno = Aluno.objects.create(
            nome='Carla Souza',
            email='carla@example.com',
            senha='senha',
            matricula='54321',
            curso='Engenharia',
            periodo=1,
        )
        feriados = [
            {'date': '2026-11-20', 'name': 'Sexta-feira'},
            {'date': '2026-11-21', 'name': 'Sábado'},
        ]

        with patch('mapucapp.feriados_service.buscar_feriados', return_value=feriados):
            criados = criar_avisos_de_feriados(hoje=date(2026, 11, 16))
            criados_na_segunda_chamada = criar_avisos_de_feriados(
                hoje=date(2026, 11, 16),
            )

        self.assertEqual(criados, 1)
        self.assertEqual(criados_na_segunda_chamada, 0)
        avisos = Notificacao.objects.filter(aluno=aluno)
        self.assertEqual(avisos.count(), 1)
        self.assertIn('20/11/2026', avisos.get().titulo)

    def test_feriado_15_dias_a_frente_gera_notificacao(self):
        aluno = Aluno.objects.create(
            nome='Diego Souza',
            email='diego@example.com',
            senha='senha',
            matricula='54322',
            curso='Engenharia',
            periodo=1,
        )
        feriados = [{'date': '2026-11-20', 'name': 'Dia da consciência negra'}]

        with patch('mapucapp.feriados_service.buscar_feriados', return_value=feriados):
            criados = criar_avisos_de_feriados(hoje=date(2026, 11, 5))

        self.assertEqual(criados, 1)
        self.assertTrue(
            Notificacao.objects.filter(
                aluno=aluno,
                titulo__contains='20/11/2026',
            ).exists()
        )

    def test_grade_de_aulas_tem_link_para_feriados(self):
        response = self.client.get(reverse('grade'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('feriados'))
        self.assertContains(response, 'Ver feriados do ano')

    def test_grade_tem_link_para_cadastrar_grade(self):
        response = self.client.get(reverse('grade'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cadastrar_grade'))
        self.assertContains(response, 'Cadastrar grade')

    def test_cadastro_de_grade_tem_links_de_volta_para_grade(self):
        response = self.client.get(reverse('cadastrar_grade'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cadastrograde.html')
        self.assertContains(response, reverse('grade'), count=2)
        self.assertContains(response, 'Cadastrar')


class AulaGradeViewsTests(TestCase):
    def setUp(self):
        self.aluno = Aluno.objects.create(
            nome='Ana Silva',
            email='ana-grade@example.com',
            senha=make_password('senha123'),
            matricula='12345-grade',
            curso='Engenharia',
            periodo=3,
        )
        self.outro_aluno = Aluno.objects.create(
            nome='Bruno Souza',
            email='bruno-grade@example.com',
            senha=make_password('senha123'),
            matricula='67890-grade',
            curso='Engenharia',
            periodo=2,
        )
        session = self.client.session
        session['aluno_id'] = self.aluno.pk
        session.save()

    def dados_aula(self, aulas=None, **alteracoes):
        if aulas is None:
            aulas = ['segunda-feira|07:00 - 09:00']
        codigo_sala = alteracoes.pop(
            'codigo_sala',
            'SALA-QUE-NAO-EXISTE',
        )
        dados = {
            'codigo_disciplina': 'INF1005',
            'nome_disciplina': 'Introdução à Computação',
            'cor': 'azul',
            'encontros-TOTAL_FORMS': str(len(aulas)),
            'encontros-INITIAL_FORMS': '0',
            'encontros-MIN_NUM_FORMS': '1',
            'encontros-MAX_NUM_FORMS': '1000',
        }
        for indice, selecao in enumerate(aulas):
            dia_semana, horario = selecao.split('|', 1)
            dados[f'encontros-{indice}-dia_semana'] = dia_semana
            dados[f'encontros-{indice}-horario'] = horario
            dados[f'encontros-{indice}-codigo_sala'] = codigo_sala
        dados.update(alteracoes)
        return dados

    def criar_aula(self, aluno=None, **alteracoes):
        dados = self.dados_aula(**alteracoes)
        return AulaGrade.objects.create(
            aluno=aluno or self.aluno,
            codigo_disciplina=dados['codigo_disciplina'],
            nome_disciplina=dados['nome_disciplina'],
            dia_semana=dados['encontros-0-dia_semana'],
            horario=dados['encontros-0-horario'],
            codigo_sala=dados['encontros-0-codigo_sala'],
            cor=dados['cor'],
        )

    def test_formulario_comeca_com_um_encontro_e_carrega_script_dinamico(self):
        resposta = self.client.get(reverse('cadastrar_grade'))

        self.assertContains(resposta, 'id="encontros-container"')
        self.assertContains(resposta, 'id="id_encontros-0-dia_semana"')
        self.assertContains(resposta, 'Adicionar outro encontro')
        self.assertContains(resposta, '/static/js/cadastro-grade.js')
        self.assertNotContains(resposta, 'type="checkbox"')

    def test_cadastra_aula_manual_e_exibe_na_grade(self):
        resposta = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(),
        )

        self.assertRedirects(resposta, reverse('cadastrar_grade'))
        aula = AulaGrade.objects.get(aluno=self.aluno)
        self.assertEqual(aula.codigo_sala, 'SALA-QUE-NAO-EXISTE')
        self.assertEqual(aula.nome_disciplina, 'Introdução à Computação')
        self.assertEqual(aula.cor, 'azul')
        resposta_grade = self.client.get(reverse('grade'))
        self.assertContains(resposta_grade, 'Introdução à Computação')
        self.assertContains(resposta_grade, 'SALA-QUE-NAO-EXISTE')
        self.assertContains(resposta_grade, '1 disciplina')

    def test_mesma_disciplina_pode_ter_um_registro_por_dia(self):
        self.client.post(reverse('cadastrar_grade'), self.dados_aula())
        resposta = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(aulas=['quarta-feira|07:00 - 09:00']),
        )

        self.assertRedirects(resposta, reverse('cadastrar_grade'))
        self.assertEqual(AulaGrade.objects.filter(aluno=self.aluno).count(), 2)
        resposta_grade = self.client.get(reverse('grade'))
        self.assertContains(resposta_grade, '1 disciplina')

    def test_impede_duas_aulas_no_mesmo_dia_e_horario(self):
        self.client.post(reverse('cadastrar_grade'), self.dados_aula())
        resposta = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(codigo_disciplina='MAT1161'),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Você já cadastrou uma aula nesse dia e horário.')
        self.assertEqual(AulaGrade.objects.filter(aluno=self.aluno).count(), 1)

    def test_impede_repeticao_de_horario_na_mesma_disciplina(self):
        resposta = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(aulas=[
                'segunda-feira|07:00 - 09:00',
                'segunda-feira|07:00 - 09:00',
            ]),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Você já cadastrou uma aula nesse dia e horário.')
        self.assertFalse(AulaGrade.objects.filter(aluno=self.aluno).exists())
        self.assertFalse(MateriaGrade.objects.filter(aluno=self.aluno).exists())

    def test_exige_ao_menos_um_encontro(self):
        resposta = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(aulas=[]),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['formset'].non_form_errors())
        self.assertFalse(AulaGrade.objects.filter(aluno=self.aluno).exists())

    def test_campos_obrigatorios_e_horarios_fora_das_opcoes_sao_rejeitados(self):
        resposta_sem_nome = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(nome_disciplina=''),
        )
        self.assertEqual(resposta_sem_nome.status_code, 200)
        self.assertIn('nome_disciplina', resposta_sem_nome.context['form'].errors)

        resposta_horario_invalido = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(aulas=['segunda-feira|20:00 - 22:00']),
        )
        self.assertEqual(resposta_horario_invalido.status_code, 200)
        self.assertIn(
            'horario',
            resposta_horario_invalido.context['formset'].forms[0].errors,
        )
        self.assertFalse(AulaGrade.objects.filter(aluno=self.aluno).exists())

    def test_cadastra_varios_horarios_como_uma_materia_e_remove_todos_juntos(self):
        horarios = [
            'segunda-feira|07:00 - 09:00',
            'quarta-feira|07:00 - 09:00',
            'sexta-feira|09:00 - 11:00',
        ]
        dados = self.dados_aula(aulas=horarios)
        dados['encontros-1-codigo_sala'] = 'SALA-2'
        resposta = self.client.post(
            reverse('cadastrar_grade'),
            dados,
        )

        self.assertRedirects(resposta, reverse('cadastrar_grade'))
        materia = MateriaGrade.objects.get(aluno=self.aluno)
        aulas = list(AulaGrade.objects.filter(materia_grade=materia))
        self.assertEqual(len(aulas), len(horarios))
        self.assertEqual(
            AulaGrade.objects.get(
                materia_grade=materia,
                dia_semana='quarta-feira',
            ).codigo_sala,
            'SALA-2',
        )
        resposta_grade = self.client.get(reverse('grade'))
        celulas_preenchidas = [
            celula['aula']
            for linha in resposta_grade.context['grade_linhas']
            for celula in linha
            if celula['aula'] is not None
        ]
        self.assertEqual(len(celulas_preenchidas), len(horarios))

        resposta_lista = self.client.get(reverse('cadastrar_grade'))
        self.assertEqual(len(resposta_lista.context['materias']), 1)
        self.assertContains(resposta_lista, 'class="remover" type="submit"', count=1)
        self.assertContains(resposta_lista, 'Sala SALA-2')

        resposta_exclusao = self.client.post(
            reverse('excluir_aula', args=[aulas[0].pk])
        )
        self.assertRedirects(resposta_exclusao, reverse('cadastrar_grade'))
        self.assertFalse(MateriaGrade.objects.filter(pk=materia.pk).exists())
        self.assertFalse(AulaGrade.objects.filter(materia_grade=materia).exists())

    def test_nao_cadastra_materia_se_algum_dos_horarios_ja_estiver_ocupado(self):
        self.criar_aula()
        resposta = self.client.post(
            reverse('cadastrar_grade'),
            self.dados_aula(aulas=[
                'segunda-feira|07:00 - 09:00',
                'quarta-feira|09:00 - 11:00',
            ]),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Você já cadastrou uma aula nesse dia e horário.')
        self.assertEqual(AulaGrade.objects.filter(aluno=self.aluno).count(), 1)
        self.assertFalse(MateriaGrade.objects.filter(aluno=self.aluno).exists())

    def test_grade_vazia_e_isolamento_e_exclusao_por_aluno(self):
        resposta_vazia = self.client.get(reverse('grade'))
        self.assertEqual(resposta_vazia.status_code, 200)
        self.assertContains(resposta_vazia, '0 disciplinas')
        self.assertNotContains(resposta_vazia, 'INF1005')

        aula_propria = self.criar_aula(
            codigo_disciplina='AULA-DO-ALUNO',
        )
        aula_alheia = self.criar_aula(
            aluno=self.outro_aluno,
            aulas=['terça-feira|07:00 - 09:00'],
        )
        resposta_grade = self.client.get(reverse('grade'))
        self.assertContains(resposta_grade, aula_propria.nome_disciplina)
        self.assertNotContains(resposta_grade, aula_alheia.codigo_disciplina)

        resposta_exclusao = self.client.post(
            reverse('excluir_aula', args=[aula_alheia.pk])
        )
        self.assertEqual(resposta_exclusao.status_code, 404)
        self.assertTrue(AulaGrade.objects.filter(pk=aula_propria.pk).exists())
        self.assertTrue(AulaGrade.objects.filter(pk=aula_alheia.pk).exists())

        resposta_exclusao = self.client.post(
            reverse('excluir_aula', args=[aula_propria.pk])
        )
        self.assertRedirects(resposta_exclusao, reverse('cadastrar_grade'))
        self.assertFalse(AulaGrade.objects.filter(pk=aula_propria.pk).exists())


class NavegacaoTelasTests(TestCase):
    def setUp(self):
        self.aluno = Aluno.objects.create(
            nome='Ana Silva',
            email='ana@example.com',
            senha=make_password('senha123'),
            matricula='12345',
            curso='Engenharia',
            periodo=3,
        )

    def autenticar_aluno(self):
        session = self.client.session
        session['aluno_id'] = self.aluno.pk
        session.save()

    def test_botao_alimentacao_leva_para_restaurantes(self):
        response = self.client.get(reverse('inicio'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('restaurantes'))
        self.assertContains(response, 'Alimentação')

    def test_grade_tem_botao_de_volta_para_inicio(self):
        response = self.client.get(reverse('grade'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('inicio'))
        self.assertContains(response, 'Voltar para a tela de início')

    def test_perfil_abre_com_opcoes_ligadas_a_rotas_existentes(self):
        self.autenticar_aluno()
        response = self.client.get(reverse('perfil'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'telaperfilmelhorado.html')
        self.assertContains(response, reverse('dados'))
        self.assertContains(response, 'id="abrir-privacidade"')
        self.assertContains(response, 'id="modal-privacidade" hidden')
        self.assertContains(response, 'id="abrir-deslogar"')
        self.assertContains(response, 'id="modal-deslogar" hidden')
        self.assertContains(response, 'id="cancelar-deslogar"')
        self.assertContains(response, f'action="{reverse("logout")}"')
        self.assertContains(response, '/static/js/privacidade-modal.js')
        self.assertContains(response, 'Dados que usamos')
        self.assertContains(response, self.aluno.nome)

    def test_perfil_exibe_o_aluno_da_sessao_e_nao_o_primeiro_cadastrado(self):
        outro_aluno = Aluno.objects.create(
            nome='Bruno Souza',
            email='bruno@example.com',
            senha=make_password('senha456'),
            matricula='67890',
            curso='Direito',
            periodo=2,
        )
        session = self.client.session
        session['aluno_id'] = outro_aluno.pk
        session.save()

        response = self.client.get(reverse('perfil'))

        self.assertContains(response, outro_aluno.nome)
        self.assertNotContains(response, self.aluno.nome)

    def test_edicao_de_dados_do_perfil_atualiza_o_aluno(self):
        self.autenticar_aluno()
        response = self.client.post(
            reverse('dados'),
            {
                'nome': 'Ana Souza',
                'curso': 'Engenharia da Computação',
                'email': 'ana.souza@example.com',
            },
        )

        self.assertRedirects(response, reverse('dados'))
        self.aluno.refresh_from_db()
        self.assertEqual(self.aluno.nome, 'Ana Souza')
        self.assertEqual(self.aluno.curso, 'Engenharia da Computação')
        self.assertEqual(self.aluno.email, 'ana.souza@example.com')

    def test_politica_de_privacidade_volta_para_o_perfil(self):
        response = self.client.get(reverse('privacidade'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('perfil'))
        self.assertContains(response, 'Voltar para o perfil')

    def test_botao_sem_cadastro_abre_a_tela_de_cadastro(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('cadastro'))
        self.assertContains(response, 'Não tenho cadastro')

    def test_usuario_anonimo_nao_acessa_perfil_ou_edicao(self):
        response_perfil = self.client.get(reverse('perfil'))
        response_dados = self.client.get(reverse('dados'))

        self.assertRedirects(response_perfil, reverse('login'))
        self.assertRedirects(response_dados, reverse('login'))

    def test_login_valido_cria_sessao_e_abre_inicio(self):
        response = self.client.post(
            reverse('login'),
            {'matricula': self.aluno.matricula, 'senha': 'senha123'},
        )

        self.assertRedirects(response, reverse('inicio'))
        self.assertEqual(self.client.session['aluno_id'], self.aluno.pk)

    def test_login_com_senha_legada_em_texto_plano_migra_para_hash(self):
        self.aluno.senha = 'senha antiga 123'
        self.aluno.save(update_fields=['senha'])

        response = self.client.post(
            reverse('login'),
            {'matricula': self.aluno.matricula, 'senha': 'senha antiga 123'},
        )

        self.assertRedirects(response, reverse('inicio'))
        self.assertEqual(self.client.session['aluno_id'], self.aluno.pk)
        self.aluno.refresh_from_db()
        self.assertNotEqual(self.aluno.senha, 'senha antiga 123')
        self.assertTrue(check_password('senha antiga 123', self.aluno.senha))

    def test_login_invalido_mostra_erro_sem_criar_sessao(self):
        response = self.client.post(
            reverse('login'),
            {'matricula': self.aluno.matricula, 'senha': 'senha-errada'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matrícula ou senha inválida.')
        self.assertNotIn('aluno_id', self.client.session)

    def test_logout_limpa_sessao_e_volta_para_login(self):
        self.autenticar_aluno()

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('aluno_id', self.client.session)

    def test_cadastro_cria_aluno_com_senha_hash_e_volta_para_login(self):
        response = self.client.post(
            reverse('cadastro'),
            {
                'nome': 'Caio Oliveira',
                'email': 'caio@example.com',
                'curso': 'Engenharia da Computação',
                'periodo': 2,
                'matricula': '98765',
                'senha': 'senhaSegura1!!',
                'confirmar_senha': 'senhaSegura1!!',
                'aceitou_privacidade': 'on',
            },
        )

        aluno_criado = Aluno.objects.get(matricula='98765')
        self.assertRedirects(response, reverse('login'))
        self.assertNotEqual(aluno_criado.senha, 'senhaSegura1!!')
        login_response = self.client.post(
            reverse('login'),
            {'matricula': '98765', 'senha': 'senhaSegura1!!'},
        )
        self.assertRedirects(login_response, reverse('inicio'))

    def test_restaurantes_abre_mapa_com_link_de_volta_para_inicio(self):
        response = self.client.get(reverse('restaurantes'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapa.html')
        self.assertContains(response, reverse('inicio'))
        self.assertContains(response, 'Voltar ao início')
