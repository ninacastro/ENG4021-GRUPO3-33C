from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import check_password, make_password

from .models import Aluno, Notificacao


class AvisosViewTests(TestCase):
    def setUp(self):
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
    def test_pagina_de_feriados_tem_estilo_e_link_de_volta_para_grade(self):
        response = self.client.get(reverse('feriados'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'feriadoAPI.html')
        self.assertContains(response, '/static/css/feriadoAPI.css')
        self.assertContains(response, reverse('grade'))

    def test_grade_de_aulas_tem_link_para_feriados(self):
        response = self.client.get(reverse('grade'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('feriados'))
        self.assertContains(response, 'Ver feriados do ano')


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
