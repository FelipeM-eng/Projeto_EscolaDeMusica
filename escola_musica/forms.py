from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

from .models import Matricula, Pagamento, Aluno, Curso, Turma

DATA_MINIMA  = datetime.date(1900, 1, 1)
ANO_ATUAL    = timezone.now().year

# Limite de retroactividade para datas de pagamento (utilizador normal)
DIAS_RETROATIVOS_NORMAL = 60

# Limite futuro para data de matrícula: 2 meses a partir de hoje
def _data_maxima_matricula():
    hoje = timezone.now().date()
    mes  = hoje.month + 2
    ano  = hoje.year + (mes - 1) // 12
    mes  = ((mes - 1) % 12) + 1
    try:
        return hoje.replace(year=ano, month=mes)
    except ValueError:
        # Ajusta para o último dia do mês (ex: 31 jan + 2 meses)
        import calendar
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        return hoje.replace(year=ano, month=mes, day=ultimo_dia)


# ─────────────────────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────────────────────

def _validar_data_minima(valor, nome):
    if valor and valor < DATA_MINIMA:
        raise ValidationError(
            f"'{nome}' não pode ser anterior a 01/01/1900."
        )

def _validar_nao_passada(valor, nome):
    if valor and valor < timezone.now().date():
        raise ValidationError(
            f"'{nome}' não pode ser anterior a hoje "
            f"({timezone.now().date().strftime('%d/%m/%Y')})."
        )

def _aplicar_atributos(fields):
    """Aplica classe CSS e atributo required a todos os campos."""
    for field in fields.values():
        attrs = field.widget.attrs
        if 'class' not in attrs:
            attrs['class'] = 'campo-input'
        if field.required:
            attrs['required'] = True


# ─────────────────────────────────────────────────────────────
# OPÇÕES DE ESTADO
# ─────────────────────────────────────────────────────────────

OPCOES_STATUS_NOVA = [
    ('',         '— Seleciona o estado —'),
    ('Pendente', 'Pendente'),
    ('Pago',     'Pago'),
]

OPCOES_STATUS_EDICAO = [
    ('',          '— Seleciona o estado —'),
    ('Pendente',  'Pendente'),
    ('Pago',      'Pago'),
    ('Cancelado', 'Cancelado'),
]


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE PAGAMENTO — criação
# ─────────────────────────────────────────────────────────────

class PagamentoForm(forms.ModelForm):

    status = forms.ChoiceField(
        choices=OPCOES_STATUS_NOVA,
        label='Estado do pagamento',
        error_messages={
            'required':       'Seleciona o estado do pagamento.',
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
                    # Não pode ser futura — máximo = hoje
                    'max':      timezone.now().date().isoformat(),
                    # Mínimo = 60 dias atrás (utilizador normal)
                    'min':      (
                        timezone.now().date() -
                        datetime.timedelta(days=DIAS_RETROATIVOS_NORMAL)
                    ).isoformat(),
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

    def __init__(self, *args, utilizador=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Guarda o utilizador para usar na validação de retroactividade
        self.utilizador = utilizador
        for field in self.fields.values():
            field.required = True
        _aplicar_atributos(self.fields)

    def clean_data_pagamento(self):
        data  = self.cleaned_data.get('data_pagamento')
        hoje  = timezone.now().date()

        if not data:
            raise ValidationError("A data de pagamento é obrigatória.")

        _validar_data_minima(data, "Data de pagamento")

        # Regra 1: não pode ser futura
        if data > hoje:
            raise ValidationError(
                "A data de pagamento não pode ser uma data futura. "
                f"A data máxima permitida é {hoje.strftime('%d/%m/%Y')}."
            )

        # Regra 2: retroactividade limitada para utilizadores normais
        is_admin = (
            self.utilizador and
            (self.utilizador.is_superuser or self.utilizador.is_staff)
        )
        if not is_admin:
            data_minima_retro = hoje - datetime.timedelta(
                days=DIAS_RETROATIVOS_NORMAL
            )
            if data < data_minima_retro:
                raise ValidationError(
                    f"Não é possível registar pagamentos com mais de "
                    f"{DIAS_RETROATIVOS_NORMAL} dias de retroactividade "
                    f"(mínimo permitido: "
                    f"{data_minima_retro.strftime('%d/%m/%Y')}). "
                    "Contacta um administrador para lançamentos anteriores."
                )

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
# FORMULÁRIO DE PAGAMENTO — edição
# ─────────────────────────────────────────────────────────────

class PagamentoEdicaoForm(PagamentoForm):
    """Permite Cancelado e aplica as mesmas regras de datas."""

    status = forms.ChoiceField(
        choices=OPCOES_STATUS_EDICAO,
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
        opcoes = ['Pendente', 'Pago', 'Cancelado']
        if status not in opcoes:
            raise ValidationError(
                f"Estado inválido. Escolhe entre: {', '.join(opcoes)}."
            )
        return status


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE MATRÍCULA
# ─────────────────────────────────────────────────────────────

class MatriculaForm(forms.ModelForm):

    class Meta:
        model  = Matricula
        fields = [
            'id_aluno', 'id_curso', 'id_turma',
            'data_matricula', 'ano_letivo',
        ]
        widgets = {
            'id_aluno': forms.Select(attrs={'class': 'campo-input'}),
            'id_curso': forms.Select(attrs={'class': 'campo-input'}),
            'id_turma': forms.Select(attrs={'class': 'campo-input'}),
            'data_matricula': forms.DateInput(
                attrs={
                    'type':     'date',
                    'min':      timezone.now().date().isoformat(),
                    'max':      _data_maxima_matricula().isoformat(),
                    'class':    'campo-input',
                    'required': True,
                    # ID usado pelo JS para preencher o ano letivo
                    'id':       'id_data_matricula',
                },
                format='%Y-%m-%d'
            ),
            'ano_letivo': forms.NumberInput(
                attrs={
                    'min':         '1900',
                    'max':         '2100',
                    'placeholder': str(ANO_ATUAL),
                    'step':        '1',
                    'class':       'campo-input',
                    'required':    True,
                    # ID usado pelo JS para preenchimento automático
                    'id':          'id_ano_letivo',
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
        self.fields['id_aluno'].queryset    = Aluno.objects.order_by('nome')
        self.fields['id_curso'].queryset    = Curso.objects.order_by('nome')
        self.fields['id_turma'].queryset    = Turma.objects.order_by('nome_turma')
        self.fields['id_aluno'].empty_label = '— Seleciona o aluno —'
        self.fields['id_curso'].empty_label = '— Seleciona o curso —'
        self.fields['id_turma'].empty_label = '— Seleciona a turma —'
        for field in self.fields.values():
            field.required = True
        _aplicar_atributos(self.fields)

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
        data  = self.cleaned_data.get('data_matricula')
        hoje  = timezone.now().date()
        maxima = _data_maxima_matricula()

        if not data:
            raise ValidationError("A data de matrícula é obrigatória.")

        _validar_data_minima(data, "Data de matrícula")

        # Não pode ser anterior a hoje
        if data < hoje:
            raise ValidationError(
                "A data de matrícula não pode ser anterior a hoje "
                f"({hoje.strftime('%d/%m/%Y')})."
            )

        # Máximo 2 meses no futuro
        if data > maxima:
            raise ValidationError(
                "A data de matrícula não pode ser superior a 2 meses "
                f"a partir de hoje (máximo: {maxima.strftime('%d/%m/%Y')})."
            )

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

    def clean(self):
        """Validações cruzadas entre campos."""
        cleaned = super().clean()
        aluno   = cleaned.get('id_aluno')
        curso   = cleaned.get('id_curso')
        turma   = cleaned.get('id_turma')
        data    = cleaned.get('data_matricula')

        # Regra: data de matrícula >= data de nascimento do aluno
        if aluno and data and aluno.data_nascimento:
            if data < aluno.data_nascimento:
                self.add_error(
                    'data_matricula',
                    f"A data de matrícula ({data.strftime('%d/%m/%Y')}) "
                    f"não pode ser anterior à data de nascimento do aluno "
                    f"({aluno.data_nascimento.strftime('%d/%m/%Y')})."
                )

        # Regra: sem matrículas duplicadas
        if aluno and curso and turma:
            qs = Matricula.objects.filter(
                id_aluno=aluno,
                id_curso=curso,
                id_turma=turma,
            )
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f"O aluno '{aluno.nome}' já está matriculado "
                    f"no curso '{curso.nome}' / turma '{turma.nome_turma}'. "
                    "Não é possível criar uma matrícula duplicada."
                )

        return cleaned