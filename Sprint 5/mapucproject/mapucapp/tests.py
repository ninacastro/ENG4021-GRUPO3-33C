from django.test import TestCase
from django.urls import reverse

from .models import Aluno, Notificacao


class AvisosViewTests(TestCase):
    def setUp(self):
        self.aluno = Aluno.objects.create(
            nome='Ana Silva',
            email='ana@example.com',
            senha='senha',
            matricula='12345',
            curso='Engenharia',
            periodo=3,
        )

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
