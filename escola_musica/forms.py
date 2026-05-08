from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Matricula, Pagamento, Aluno, Curso, Turma

DATA_MINIMA = timezone.datetime(1900, 1, 1).date()
ANO_ATUAL   = timezone.now().year


# ─────────────────────────────────────────────────────────────
# UTILITÁRIOS DE VALIDAÇÃO REUTILIZÁVEIS
# ─────────────────────────────────────────────────────────────

def _validar_data_minima(valor, nome):
    if valor and valor < DATA_MINIMA:
        raise ValidationError(
            f"'{nome}' não pode ser anterior a 01/01/1900."
        )

def _validar_nao_passada(valor, nome):
    if valor and valor < timezone.now().date():
        raise ValidationError(
            f"'{nome}' não pode ser uma data anterior a hoje "
            f"({timezone.now().date().strftime('%d/%m/%Y')})."
        )


# ─────────────────────────────────────────────────────────────
# WIDGET PERSONALIZADO — aplica classes CSS a todos os inputs
# ─────────────────────────────────────────────────────────────

def _aplicar_atributos(fields):
    """
    Aplica atributos HTML5 de validação e classe CSS
    a todos os campos do formulário.
    """
    for nome, field in fields.items():
        widget = field.widget

        # Classe CSS base para todos os inputs
        attrs = widget.attrs
        if 'class' not in attrs:
            attrs['class'] = 'campo-input'

        # required no HTML5 (reforço visual imediato)
        if field.required:
            attrs['required'] = True

        # Placeholder específico por tipo
        if isinstance(widget, forms.Select):
            pass  # empty_label trata o placeholder

        elif isinstance(widget, forms.NumberInput):
            if 'placeholder' not in attrs:
                attrs['placeholder'] = 'Introduz um número'

        elif isinstance(widget, forms.DateInput):
            attrs['type'] = 'date'
            if 'min' not in attrs:
                attrs['min'] = timezone.now().date().isoformat()


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE PAGAMENTO — criação
# ─────────────────────────────────────────────────────────────

# Opções partilhadas — definidas uma vez, usadas em ambos os formulários
OPCOES_STATUS = [
    ('',          '— Seleciona o estado —'),
    ('Pendente',  'Pendente'),
    ('Pago',      'Pago'),
    ('Cancelado', 'Cancelado'),
]

OPCOES_STATUS_NOVA = [
    ('',         '— Seleciona o estado —'),
    ('Pendente', 'Pendente'),
    ('Pago',     'Pago'),
    # Cancelado não aparece na criação
]


class PagamentoForm(forms.ModelForm):

    # Declara status como ChoiceField explícito
    # Isto substitui o widget automático que não renderizava as opções
    status = forms.ChoiceField(
        choices=OPCOES_STATUS_NOVA,
        label='Estado do pagamento',
        error_messages={
            'required': 'Seleciona o estado do pagamento.',
            'invalid_choice': 'Estado inválido. Escolhe Pendente ou Pago.',
        },
        widget=forms.Select(attrs={'class': 'campo-input', 'required': True}),
    )

    class Meta:
        model  = Pagamento
        fields = ['data_pagamento', 'valor_pago', 'status']
        widgets = {
            'data_pagamento': forms.DateInput(
                attrs={
                    'type':     'date',
                    'min':      timezone.now().date().isoformat(),
                    'class':    'campo-input',
                    'required': True,
                },
                format='%Y-%m-%d'
            ),
            'valor_pago': forms.NumberInput(
                attrs={
                    'step':        '0.01',
                    'min':         '0.01',
                    'max':         '99999.99',
                    'placeholder': '0.00',
                    'class':       'campo-input',
                    'required':    True,
                }
            ),
        }
        labels = {
            'data_pagamento': 'Data de pagamento',
            'valor_pago':     'Valor pago (€)',
        }
        error_messages = {
            'data_pagamento': {
                'required': 'A data de pagamento é obrigatória.',
                'invalid':  'Formato de data inválido. Usa o selector de data.',
            },
            'valor_pago': {
                'required':           'O valor pago é obrigatório.',
                'invalid':            'Introduz um valor numérico válido (ex: 150.00).',
                'max_digits':         'O valor não pode ter mais de 10 dígitos.',
                'max_decimal_places': 'Máximo de 2 casas decimais.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

    def clean_data_pagamento(self):
        data = self.cleaned_data.get('data_pagamento')
        if not data:
            raise ValidationError("A data de pagamento é obrigatória.")
        _validar_data_minima(data, "Data de pagamento")
        return data

    def clean_valor_pago(self):
        valor = self.cleaned_data.get('valor_pago')
        if valor is None:
            raise ValidationError("O valor pago é obrigatório.")
        if valor <= 0:
            raise ValidationError(
                "O valor pago tem de ser superior a zero euros."
            )
        if valor > 99999.99:
            raise ValidationError(
                "O valor pago não pode exceder 99.999,99 €."
            )
        return valor

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if not status:
            raise ValidationError("Seleciona o estado do pagamento.")
        if status == 'Cancelado':
            raise ValidationError(
                "Não é possível registar uma matrícula com pagamento "
                "cancelado. Seleciona 'Pendente' ou 'Pago'."
            )
        return status


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE PAGAMENTO — edição (permite Cancelado)
# ─────────────────────────────────────────────────────────────

class PagamentoEdicaoForm(PagamentoForm):
    """
    Variante para edição — inclui Cancelado como opção válida.
    """

    status = forms.ChoiceField(
        choices=OPCOES_STATUS,  # inclui Cancelado
        label='Estado do pagamento',
        error_messages={
            'required':       'Seleciona o estado do pagamento.',
            'invalid_choice': 'Estado inválido.',
        },
        widget=forms.Select(attrs={'class': 'campo-input', 'required': True}),
    )

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if not status:
            raise ValidationError("Seleciona o estado do pagamento.")
        opcoes_validas = ['Pendente', 'Pago', 'Cancelado']
        if status not in opcoes_validas:
            raise ValidationError(
                f"Estado inválido. Escolhe entre: "
                f"{', '.join(opcoes_validas)}."
            )
        return status


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE MATRÍCULA — criação e edição
# ─────────────────────────────────────────────────────────────

class MatriculaForm(forms.ModelForm):

    class Meta:
        model  = Matricula
        fields = [
            'id_aluno', 'id_curso', 'id_turma',
            'data_matricula', 'ano_letivo'
        ]
        widgets = {
            'id_aluno': forms.Select(),
            'id_curso': forms.Select(),
            'id_turma': forms.Select(),
            'data_matricula': forms.DateInput(
                attrs={
                    'type': 'date',
                    'min':  timezone.now().date().isoformat(),
                },
                format='%Y-%m-%d'
            ),
            'ano_letivo': forms.NumberInput(
                attrs={
                    'min':         '1900',
                    'max':         '2100',
                    'placeholder': str(ANO_ATUAL),
                    'step':        '1',
                }
            ),
        }
        labels = {
            'id_aluno':       'Aluno',
            'id_curso':       'Curso',
            'id_turma':       'Turma',
            'data_matricula': 'Data de matrícula',
            'ano_letivo':     'Ano letivo',
        }
        error_messages = {
            'id_aluno': {
                'required': 'Seleciona o aluno a matricular.',
            },
            'id_curso': {
                'required': 'Seleciona o curso pretendido.',
            },
            'id_turma': {
                'required': 'Seleciona a turma para este curso.',
            },
            'data_matricula': {
                'required': 'A data de matrícula é obrigatória.',
                'invalid':  'Data inválida. Usa o selector de data.',
            },
            'ano_letivo': {
                'required': 'O ano letivo é obrigatório.',
                'invalid':  'Introduz um ano válido com 4 dígitos (ex: 2025).',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Querysets ordenados
        self.fields['id_aluno'].queryset = (
            Aluno.objects.order_by('nome')
        )
        self.fields['id_curso'].queryset = (
            Curso.objects.order_by('nome')
        )
        self.fields['id_turma'].queryset = (
            Turma.objects.order_by('nome_turma')
        )

        # Placeholders dos selects
        self.fields['id_aluno'].empty_label = '— Seleciona o aluno —'
        self.fields['id_curso'].empty_label = '— Seleciona o curso —'
        self.fields['id_turma'].empty_label = '— Seleciona a turma —'

        # Todos os campos obrigatórios
        for field in self.fields.values():
            field.required = True

        _aplicar_atributos(self.fields)

    # ── Validações individuais ──────────────────────────────

    def clean_id_aluno(self):
        aluno = self.cleaned_data.get('id_aluno')
        if not aluno:
            raise ValidationError("Seleciona o aluno a matricular.")
        return aluno

    def clean_id_curso(self):
        curso = self.cleaned_data.get('id_curso')
        if not curso:
            raise ValidationError("Seleciona o curso pretendido.")
        return curso

    def clean_id_turma(self):
        turma = self.cleaned_data.get('id_turma')
        if not turma:
            raise ValidationError("Seleciona a turma para este curso.")
        return turma

    def clean_data_matricula(self):
        data = self.cleaned_data.get('data_matricula')
        if not data:
            raise ValidationError("A data de matrícula é obrigatória.")
        _validar_data_minima(data, "Data de matrícula")
        _validar_nao_passada(data, "Data de matrícula")
        return data

    def clean_ano_letivo(self):
        ano = self.cleaned_data.get('ano_letivo')
        if ano is None:
            raise ValidationError("O ano letivo é obrigatório.")
        if ano < 1900:
            raise ValidationError(
                "O ano letivo não pode ser anterior a 1900."
            )
        if ano > 2100:
            raise ValidationError(
                "O ano letivo não pode ser superior a 2100."
            )
        return ano

    # ── Validação cruzada — duplicados ─────────────────────

    def clean(self):
        cleaned = super().clean()
        aluno = cleaned.get('id_aluno')
        curso = cleaned.get('id_curso')
        turma = cleaned.get('id_turma')

        if aluno and curso and turma:
            qs = Matricula.objects.filter(
                id_aluno=aluno,
                id_curso=curso,
                id_turma=turma,
            )
            # Na edição, exclui o próprio registo
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise ValidationError(
                    f"O aluno '{aluno.nome}' já está matriculado "
                    f"no curso '{curso.nome}' / turma "
                    f"'{turma.nome_turma}'. "
                    "Não é possível criar uma matrícula duplicada."
                )
        return cleaned