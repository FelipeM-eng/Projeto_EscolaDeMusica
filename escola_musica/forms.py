from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Matricula, Pagamento, Aluno, Curso, Turma

# Data mínima aceitável globalmente
DATA_MINIMA = timezone.datetime(1900, 1, 1).date()


# ─────────────────────────────────────────────────────────────
# UTILITÁRIOS DE VALIDAÇÃO
# ─────────────────────────────────────────────────────────────

def validar_data_nao_futura(valor, nome_campo="Data"):
    """
    Rejeita datas futuras.
    Usado em campos onde a data já deve ter ocorrido
    (ex: data de pagamento, data de matrícula passada).
    """
    if valor and valor > timezone.now().date():
        raise ValidationError(
            f"{nome_campo} não pode ser uma data futura."
        )


def validar_data_minima(valor, nome_campo="Data"):
    """Rejeita datas anteriores a 1900."""
    if valor and valor < DATA_MINIMA:
        raise ValidationError(
            f"{nome_campo} não pode ser anterior a 1900."
        )


def validar_data_nao_passada(valor, nome_campo="Data"):
    """
    Rejeita datas anteriores a hoje.
    Usado em campos onde a data deve ser presente ou futura
    (ex: data de matrícula nova).
    """
    if valor and valor < timezone.now().date():
        raise ValidationError(
            f"{nome_campo} não pode ser uma data anterior a hoje."
        )


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE PAGAMENTO
# ─────────────────────────────────────────────────────────────

class PagamentoForm(forms.ModelForm):

    class Meta:
        model = Pagamento
        fields = ['data_pagamento', 'valor_pago', 'status']
        widgets = {
            'data_pagamento': forms.DateInput(
                attrs={
                    'type': 'date',
                    # Impede seleção de datas anteriores a hoje no datepicker
                    'min': timezone.now().date().isoformat(),
                },
                format='%Y-%m-%d'
            ),
            'valor_pago': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0.01',
                    'placeholder': '0.00'
                }
            ),
            'status': forms.Select(
                choices=[
                    ('', '— Seleciona o estado —'),
                    ('Pendente', 'Pendente'),
                    ('Pago', 'Pago'),
                    ('Cancelado', 'Cancelado'),
                ]
            ),
        }
        labels = {
            'data_pagamento': 'Data de pagamento',
            'valor_pago': 'Valor pago (€)',
            'status': 'Estado do pagamento',
        }

    def clean_data_pagamento(self):
        """Validação backend da data de pagamento."""
        data = self.cleaned_data.get('data_pagamento')
        if data:
            validar_data_minima(data, "Data de pagamento")
        return data

    def clean_valor_pago(self):
        """Impede valores negativos ou zero."""
        valor = self.cleaned_data.get('valor_pago')
        if valor is not None and valor <= 0:
            raise ValidationError("O valor pago tem de ser superior a zero.")
        return valor

    def clean_status(self):
        """
        Garante que o estado foi selecionado e que não é 'Cancelado'.
        Um pagamento cancelado não pode ser associado a uma matrícula nova.
        Esta validação antecipa a regra do trigger trg_verifica_pagamento
        da BD, dando feedback claro antes de qualquer escrita.
        """
        status = self.cleaned_data.get('status')

        if not status:
            raise ValidationError("Seleciona o estado do pagamento.")

        if status == 'Cancelado':
            raise ValidationError(
                "Não é possível registar uma matrícula com pagamento cancelado. "
                "Seleciona 'Pendente' ou 'Pago'."
            )

        return status


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE MATRÍCULA
# ─────────────────────────────────────────────────────────────

class MatriculaForm(forms.ModelForm):

    class Meta:
        model = Matricula
        fields = ['id_aluno', 'id_curso', 'id_turma', 'data_matricula', 'ano_letivo']
        widgets = {
            'id_aluno': forms.Select(),
            'id_curso': forms.Select(),
            'id_turma': forms.Select(),
            'data_matricula': forms.DateInput(
                attrs={
                    'type': 'date',
                    # Datepicker começa no dia de hoje como mínimo
                    'min': timezone.now().date().isoformat(),
                },
                format='%Y-%m-%d'
            ),
            'ano_letivo': forms.NumberInput(
                attrs={
                    'min': '1900',
                    'max': '2100',
                    'placeholder': str(timezone.now().year)
                }
            ),
        }
        labels = {
            'id_aluno': 'Aluno',
            'id_curso': 'Curso',
            'id_turma': 'Turma',
            'data_matricula': 'Data de matrícula',
            'ano_letivo': 'Ano letivo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_aluno'].queryset = Aluno.objects.order_by('nome')
        self.fields['id_curso'].queryset = Curso.objects.order_by('nome')
        self.fields['id_turma'].queryset = Turma.objects.order_by('nome_turma')
        self.fields['id_aluno'].empty_label = '— Seleciona o aluno —'
        self.fields['id_curso'].empty_label = '— Seleciona o curso —'
        self.fields['id_turma'].empty_label = '— Seleciona a turma —'

    def clean_data_matricula(self):
        """
        Validação backend da data de matrícula.
        Aceita datas de hoje em diante; rejeita datas absurdas.
        """
        data = self.cleaned_data.get('data_matricula')
        if data:
            validar_data_minima(data, "Data de matrícula")
            validar_data_nao_passada(data, "Data de matrícula")
        return data

    def clean_ano_letivo(self):
        """Ano letivo tem de estar num intervalo razoável."""
        ano = self.cleaned_data.get('ano_letivo')
        if ano is not None:
            if ano < 1900:
                raise ValidationError("O ano letivo não pode ser anterior a 1900.")
            if ano > 2100:
                raise ValidationError("O ano letivo introduzido não é válido.")
        return ano

    def clean(self):
        """
        Validação cruzada — regra de negócio:
        Impede matrícula duplicada (mesmo aluno + curso + turma).
        Esta validação ocorre no backend independentemente do frontend.
        A constraint UNIQUE da BD é a salvaguarda final,
        mas validamos aqui para dar feedback claro ao utilizador.
        """
        cleaned = super().clean()
        aluno  = cleaned.get('id_aluno')
        curso  = cleaned.get('id_curso')
        turma  = cleaned.get('id_turma')

        if aluno and curso and turma:
            duplicado = Matricula.objects.filter(
                id_aluno=aluno,
                id_curso=curso,
                id_turma=turma
            ).exists()
            if duplicado:
                raise ValidationError(
                    f"O aluno '{aluno.nome}' já está matriculado "
                    f"no curso '{curso.nome}' / turma '{turma.nome_turma}'."
                )
        return cleaned