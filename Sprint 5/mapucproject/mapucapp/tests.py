from io import BytesIO
from datetime import date
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache

from .models import Aluno, Notificacao
from .feriados_service import (
    criar_avisos_de_feriados,
    obter_feriados_proximos,
    buscar_feriados,
)


class MapaViewTests(TestCase):
    def test_mapa_em_tela_cheia_renderiza_mapa_e_link_de_volta(self):
        response = self.client.get(reverse('mapa'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mapa.html')
        self.assertContains(response, 'id="mapa-puc"')
        self.assertContains(response, reverse('inicio'))

    def test_inicio_exibe_link_para_mapa_em_tela_cheia(self):
        response = self.client.get(reverse('inicio'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('mapa'))
        self.assertContains(response, 'Abrir mapa em tela cheia')

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
        self.assertContains(response, reverse('privacidade'))
        self.assertContains(response, reverse('deslogar'))
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

    def test_restaurantes_tem_botao_de_volta_para_inicio(self):
        response = self.client.get(reverse('restaurantes'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('inicio'))
        self.assertContains(response, 'Voltar para a tela de início')
