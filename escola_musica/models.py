from django.db import models
from django.contrib.auth.models import User


class Professor(models.Model):
    id_professor    = models.AutoField(primary_key=True)
    nome            = models.CharField(max_length=100)
    email           = models.CharField(max_length=120, null=True, blank=True)
    telefone        = models.CharField(max_length=20, null=True, blank=True)
    data_contratacao = models.DateField(null=True, blank=True)
    # Liga ao utilizador Django — adicionado via SQL (managed=False)
    user            = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='user_id',
        related_name='professor',
    )

    class Meta:
        managed  = False
        db_table = 'professor'

    def __str__(self):
        return self.nome


class Especialidade(models.Model):
    id_especialidade = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'especialidade'

    def __str__(self):
        return self.nome


class EspecialidadesDoProfessor(models.Model):
    id_professor = models.ForeignKey(
        Professor,
        on_delete=models.DO_NOTHING,
        db_column='id_professor'
    )
    id_especialidade = models.ForeignKey(
        Especialidade,
        on_delete=models.DO_NOTHING,
        db_column='id_especialidade'
    )
    nivel_competencia = models.CharField(max_length=50, null=True, blank=True)
    anos_experiencia = models.IntegerField(null=True, blank=True)
    certificado = models.BooleanField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'especialidades_do_professor'
        unique_together = (('id_professor', 'id_especialidade'),)


class Sala(models.Model):
    id_sala = models.AutoField(primary_key=True)
    capacidademax = models.IntegerField(null=True, blank=True, db_column='capacidademax')
    nome = models.CharField(max_length=50, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'sala'

    def __str__(self):
        return self.nome or str(self.id_sala)


class TipoAula(models.Model):
    id_tipoaula = models.AutoField(primary_key=True, db_column='id_tipoaula')
    nome = models.CharField(max_length=80, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tipoaula'

    def __str__(self):
        return self.nome or str(self.id_tipoaula)


class TipoInstrumento(models.Model):
    id_tipoinstrumento = models.AutoField(primary_key=True, db_column='id_tipoinstrumento')
    nome = models.CharField(max_length=80, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tipoinstrumento'

    def __str__(self):
        return self.nome or str(self.id_tipoinstrumento)


class Instrumento(models.Model):
    id_instrumento = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=80, null=True, blank=True)
    quantidade = models.IntegerField(null=True, blank=True)
    id_tipoinstrumento = models.ForeignKey(
        TipoInstrumento,
        on_delete=models.DO_NOTHING,
        db_column='id_tipoinstrumento',
        null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = 'instrumento'

    def __str__(self):
        return self.nome or str(self.id_instrumento)


class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True)
    id_instrumento = models.ForeignKey(
        Instrumento,
        on_delete=models.DO_NOTHING,
        db_column='id_instrumento',
        null=True, blank=True
    )
    nome = models.CharField(max_length=80, null=True, blank=True)
    descricao = models.TextField(null=True, blank=True)
    duracao = models.CharField(max_length=50, null=True, blank=True)
    nivel = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cursos'

    def __str__(self):
        return self.nome or str(self.id_curso)


class Turma(models.Model):
    id_turma = models.AutoField(primary_key=True)
    id_curso = models.ForeignKey(
        Curso,
        on_delete=models.DO_NOTHING,
        db_column='id_curso',
        null=True, blank=True
    )
    nome_turma = models.CharField(max_length=50, null=True, blank=True)
    ano_letivo = models.IntegerField(null=True, blank=True)
    horario = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'turmas'

    def __str__(self):
        return self.nome_turma or str(self.id_turma)


class Aluno(models.Model):
    id_aluno        = models.AutoField(primary_key=True)
    nome            = models.CharField(max_length=100, null=True, blank=True)
    email           = models.CharField(max_length=120, null=True, blank=True)
    telefone        = models.CharField(max_length=20, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    # Liga ao utilizador Django — adicionado via SQL (managed=False)
    user            = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='user_id',
        related_name='aluno',
    )

    class Meta:
        managed  = False
        db_table = 'alunos'

    def __str__(self):
        return self.nome or str(self.id_aluno)


class Pagamento(models.Model):
    id_pagamento = models.AutoField(primary_key=True)
    data_pagamento = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'pagamentos'

    def __str__(self):
        return f"Pagamento {self.id_pagamento}"


class Matricula(models.Model):
    id_matricula = models.AutoField(primary_key=True)

    id_aluno = models.ForeignKey(
        Aluno,
        models.DO_NOTHING,
        db_column='id_aluno'
    )

    id_curso = models.ForeignKey(
        Curso,
        models.DO_NOTHING,
        db_column='id_curso'
    )

    id_turma = models.ForeignKey(
        Turma,
        models.DO_NOTHING,
        db_column='id_turma'
    )

    id_pagamento = models.ForeignKey(
        Pagamento,
        models.DO_NOTHING,
        db_column='id_pagamento',
        blank=True,
        null=True
    )

    data_matricula = models.DateField(blank=True, null=True)
    ano_letivo = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'matricula'
        unique_together = [('id_aluno', 'id_curso', 'id_turma')]

    def __str__(self):
        return f"Matrícula #{self.id_matricula}"
    

class Aula(models.Model):
    id_aula = models.AutoField(primary_key=True)
    id_professor = models.ForeignKey(
        Professor,
        on_delete=models.DO_NOTHING,
        db_column='id_professor',
        null=True, blank=True
    )
    id_turma = models.ForeignKey(
        Turma,
        on_delete=models.DO_NOTHING,
        db_column='id_turma',
        null=True, blank=True
    )
    id_curso = models.ForeignKey(
        Curso,
        on_delete=models.DO_NOTHING,
        db_column='id_curso',
        null=True, blank=True
    )
    id_instrumento = models.ForeignKey(
        Instrumento,
        on_delete=models.DO_NOTHING,
        db_column='id_instrumento',
        null=True, blank=True
    )
    id_sala = models.ForeignKey(
        Sala,
        on_delete=models.DO_NOTHING,
        db_column='id_sala',
        null=True, blank=True
    )
    id_tipoaula = models.ForeignKey(
        TipoAula,
        on_delete=models.DO_NOTHING,
        db_column='id_tipoaula',
        null=True, blank=True
    )
    conteudo = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'aulas'

    def __str__(self):
        return f"Aula {self.id_aula}"


class AulaDoAluno(models.Model):
    id_aluno = models.ForeignKey(
        Aluno,
        on_delete=models.DO_NOTHING,
        db_column='id_aluno', 
    )
    id_aula = models.ForeignKey(
        Aula,
        on_delete=models.DO_NOTHING,
        db_column='id_aula'
    )

    data_inicio = models.DateTimeField(null=True, blank=True)
    data_final = models.DateTimeField(null=True, blank=True)
    presenca = models.BooleanField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'aula_do_aluno'
        unique_together = (('id_aluno', 'id_aula'),)