from django.db import models


class Predio(models.Model):
    id_predio = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150)
    sigla_codigo = models.CharField(max_length=20, unique=True)
    coordenadas_entrada = models.CharField(max_length=255, blank=True, null=True)
    quantidade_andares = models.PositiveIntegerField(default=0)
    horario_funcionamento = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "predio"
        verbose_name = "Prédio"
        verbose_name_plural = "Prédios"

    def __str__(self):
        return f"{self.sigla_codigo} - {self.nome}"


class Andar(models.Model):
    id_andar = models.AutoField(primary_key=True)

    predio = models.ForeignKey(
        Predio,
        on_delete=models.CASCADE,
        related_name="andares"
    )

    numero_andar = models.IntegerField()
    nome_edificio = models.CharField(max_length=150, blank=True, null=True)
    possui_elevador = models.BooleanField(default=False)

    class Meta:
        db_table = "andar"
        verbose_name = "Andar"
        verbose_name_plural = "Andares"
        constraints = [
            models.UniqueConstraint(
                fields=["predio", "numero_andar"],
                name="unique_andar_por_predio"
            )
        ]

    def __str__(self):
        return f"{self.predio.sigla_codigo} - Andar {self.numero_andar}"


class Sala(models.Model):
    id_sala = models.AutoField(primary_key=True)

    codigo_sala = models.CharField(max_length=30, unique=True)
    nome_edificio = models.CharField(max_length=150, blank=True, null=True)

    predio = models.ForeignKey(
        Predio,
        on_delete=models.CASCADE,
        related_name="salas"
    )

    andar = models.ForeignKey(
        Andar,
        on_delete=models.CASCADE,
        related_name="salas"
    )

    coordenadas = models.CharField(max_length=255, blank=True, null=True)
    tipo_sala = models.CharField(max_length=50)
    capacidade = models.PositiveIntegerField()

    class Meta:
        db_table = "sala"
        verbose_name = "Sala"
        verbose_name_plural = "Salas"

    def __str__(self):
        return f"{self.codigo_sala} - {self.predio.sigla_codigo}"


class Disciplina(models.Model):
    id_disciplina = models.AutoField(primary_key=True)

    codigo_disciplina = models.CharField(
        max_length=30,
        unique=True
    )
    nome = models.CharField(max_length=150)
    creditos = models.PositiveIntegerField()
    departamento = models.CharField(max_length=100)
    tipo_disciplina = models.CharField(max_length=50)
    nivel_disciplina = models.CharField(max_length=50)

    class Meta:
        db_table = "disciplina"
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"

    def __str__(self):
        return f"{self.codigo_disciplina} - {self.nome}"


class Usuario(models.Model):
    TIPOS_USUARIO = [
        ("ALUNO", "Aluno"),
        ("PROFESSOR", "Professor"),
        ("ADMIN", "Administrador"),
    ]

    id_usuario = models.AutoField(primary_key=True)

    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=255)

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPOS_USUARIO
    )

    matricula = models.CharField(
        max_length=30,
        unique=True
    )

    curso = models.CharField(max_length=150, blank=True, null=True)
    periodo = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.nome} ({self.matricula})"


class Turma(models.Model):
    id_turma = models.AutoField(primary_key=True)

    codigo_turma = models.CharField(max_length=30)

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name="turmas"
    )

    professor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="turmas_lecionadas",
        limit_choices_to={"tipo_usuario": "PROFESSOR"}
    )

    periodo = models.CharField(max_length=30)

    quantidade_alunos = models.PositiveIntegerField(default=0)

    horario = models.CharField(max_length=100)

    salas = models.ManyToManyField(
        Sala,
        related_name="turmas",
        blank=True
    )

    alunos = models.ManyToManyField(
        Usuario,
        related_name="turmas_matriculadas",
        blank=True,
        limit_choices_to={"tipo_usuario": "ALUNO"}
    )

    class Meta:
        db_table = "turma"
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        constraints = [
            models.UniqueConstraint(
                fields=["codigo_turma", "periodo"],
                name="unique_turma_por_periodo"
            )
        ]

    def __str__(self):
        return f"{self.codigo_turma} - {self.disciplina.nome}"