from django.db import models

class Predio(models.Model):
    id_predio = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    sigla_codigo = models.CharField(max_length=20)
    coordenadas_entradas = models.CharField(max_length=255)
    quantidade_andares = models.IntegerField()
    horario_funcionamento = models.CharField(max_length=100)

class Andar(models.Model):
    id_andar = models.AutoField(primary_key=True)
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name='andares')
    numero_andar = models.IntegerField()
    nome_exibicao = models.CharField(max_length=100)
    possui_elevador = models.BooleanField(default=False)

class Sala(models.Model):
    id_sala = models.AutoField(primary_key=True)
    codigo_sala = models.CharField(max_length=50)
    nome_exibicao = models.CharField(max_length=100)
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE)
    andar = models.ForeignKey(Andar, on_delete=models.CASCADE, related_name='salas')
    coordenadas = models.CharField(max_length=255)
    tipo_sala = models.CharField(max_length=100)
    capacidade = models.IntegerField()

class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    sigla = models.CharField(max_length=20)
    nome = models.CharField(max_length=150)
    sala_secretaria = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()

class Professor(models.Model):
    id_professor = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=128)
    matricula = models.CharField(max_length=50, unique=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, related_name='professores')

class Disciplina(models.Model):
    id_disciplina = models.AutoField(primary_key=True)
    codigo_disciplina = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=150)
    creditos = models.IntegerField()
    departamento = models.ForeignKey(Departamento, on_delete=models.CASCADE, related_name='disciplinas')
    tipo_disciplina = models.CharField(max_length=100)
    nivel_disciplina = models.CharField(max_length=100)

class Aluno(models.Model):
    id_aluno = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=128)
    matricula = models.CharField(max_length=50, unique=True)
    curso = models.CharField(max_length=150)
    periodo = models.IntegerField()

class Turma(models.Model):
    id_turma = models.AutoField(primary_key=True)
    codigo_turma = models.CharField(max_length=50)
    codigo_disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='turmas')
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, related_name='turmas')
    periodo = models.CharField(max_length=50)
    quantidade_alunos = models.IntegerField()
    horario = models.CharField(max_length=100)
    salas = models.ManyToManyField(Sala, related_name='turmas')
    alunos = models.ManyToManyField(Aluno, related_name='turmas')


class Notificacao(models.Model):
    id_notificacao = models.AutoField(primary_key=True)
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='notificacoes')
    
    titulo = models.CharField(max_length=100)
    mensagem = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo} - {self.aluno.nome}"