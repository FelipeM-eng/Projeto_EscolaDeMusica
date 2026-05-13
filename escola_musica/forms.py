from django import forms
import calendar as _calendar
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import validate_email
import datetime
import re
import unicodedata

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

def _ultimo_dia_mes_atual():
    hoje = timezone.now().date()
    ultimo = _calendar.monthrange(hoje.year, hoje.month)[1]
    return hoje.replace(day=ultimo)

def _primeiro_dia_mes_atual():
    return timezone.now().date().replace(day=1)

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
                    'min':      _primeiro_dia_mes_atual().isoformat(),
                    'max':      _ultimo_dia_mes_atual().isoformat(),
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

        # Regra: data deve estar no mês actual
        primeiro_dia = hoje.replace(day=1)
        import calendar as _cal
        ultimo_dia = hoje.replace(
            day=_cal.monthrange(hoje.year, hoje.month)[1]
        )

        if data < primeiro_dia or data > ultimo_dia:
            raise ValidationError(
                f"A data de pagamento deve ser no mês actual "
                f"({primeiro_dia.strftime('%d/%m/%Y')} a "
                f"{ultimo_dia.strftime('%d/%m/%Y')})."
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
# ── Constantes de validação do nome ──────────────────────────
# Permite letras (incluindo acentuadas), espaços, hífens e apóstrofos
# Bloqueia qualquer outro caracter — SQL, HTML, scripts, etc.
# ─────────────────────────────────────────────────────────────
# CONSTANTES DE VALIDAÇÃO
# ─────────────────────────────────────────────────────────────

REGEX_NOME_VALIDO     = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-\']+$", re.UNICODE)
REGEX_TELEFONE_VALIDO = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")
NOME_MIN_CHARS        = 2
NOME_MAX_CHARS        = 100


def _sanitizar_nome(valor):
    """Normaliza unicode, colapsa espaços, capitaliza."""
    if not valor:
        return valor
    valor = unicodedata.normalize('NFC', valor)
    valor = ' '.join(valor.split())
    valor = valor.title()
    return valor


def _sanitizar_texto(valor):
    """Remove espaços extra e normaliza unicode."""
    if not valor:
        return valor
    valor = unicodedata.normalize('NFC', valor)
    return valor.strip()


# ─────────────────────────────────────────────────────────────
# FORMULÁRIO DE DADOS PESSOAIS DO ALUNO
# ─────────────────────────────────────────────────────────────

class AlunoForm(forms.Form):
    """
    Formulário de dados pessoais do aluno.
    Usado em conjunto com MatriculaForm na criação de matrícula.
    Não é um ModelForm — a gravação é feita manualmente na view
    para controlo total da lógica de procura/criação.
    """

    nome = forms.CharField(
        label='Nome completo',
        max_length=NOME_MAX_CHARS,
        min_length=NOME_MIN_CHARS,
        required=True,
        widget=forms.TextInput(attrs={
            'class':        'campo-input',
            'placeholder':  'Ex: João Silva',
            'autocomplete': 'off',
            'maxlength':    str(NOME_MAX_CHARS),
        }),
        error_messages={
            'required':   'O nome do aluno é obrigatório.',
            'min_length': f'O nome deve ter pelo menos {NOME_MIN_CHARS} caracteres.',
            'max_length': f'O nome não pode ter mais de {NOME_MAX_CHARS} caracteres.',
        },
    )

    email = forms.CharField(
        label='Email',
        max_length=120,
        required=False,
        widget=forms.EmailInput(attrs={
            'class':        'campo-input',
            'placeholder':  'Ex: joao.silva@email.com',
            'autocomplete': 'off',
            'maxlength':    '120',
        }),
        error_messages={
            'max_length': 'O email não pode ter mais de 120 caracteres.',
        },
    )

    telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class':        'campo-input',
            'placeholder':  'Ex: +351 912 345 678',
            'autocomplete': 'off',
            'maxlength':    '20',
        }),
        error_messages={
            'max_length': 'O telefone não pode ter mais de 20 caracteres.',
        },
    )

    data_nascimento = forms.DateField(
        label='Data de nascimento',
        required=False,
        widget=forms.DateInput(
            attrs={
                'type':  'date',
                'class': 'campo-input',
                # Não pode nascer no futuro
                'max':   timezone.now().date().isoformat(),
                # Máximo 120 anos atrás
                'min':   (
                    timezone.now().date().replace(
                        year=timezone.now().year - 120
                    )
                ).isoformat(),
            },
            format='%Y-%m-%d'
        ),
        error_messages={
            'invalid':   'Data de nascimento inválida. Usa o selector de data.',
            'required':  'A data de nascimento é obrigatória.',
        },
    )

    # ── Validações individuais ──────────────────────────────

    def clean_nome(self):
        valor = self.cleaned_data.get('nome', '')

        if not valor or not valor.strip():
            raise ValidationError("O nome do aluno é obrigatório.")

        valor = _sanitizar_nome(valor)

        if len(valor) < NOME_MIN_CHARS:
            raise ValidationError(
                f"O nome deve ter pelo menos {NOME_MIN_CHARS} caracteres "
                "após remoção de espaços."
            )

        # Valida caracteres — apenas letras, espaços, hífens, apóstrofos
        if not REGEX_NOME_VALIDO.match(valor):
            raise ValidationError(
                "O nome contém caracteres inválidos. "
                "Apenas letras, espaços, hífens e apóstrofos são permitidos."
            )

        # Bloqueia padrões de injecção mesmo que passem o regex
        chars_proibidos = ['<', '>', '{', '}', ';', '=', '/', '\\',
                           '@', '#', '$', '%', '*', '|', '&', '^', '`']
        for char in chars_proibidos:
            if char in valor:
                raise ValidationError(
                    "O nome contém caracteres não permitidos."
                )

        return valor

    def clean_email(self):
        valor = self.cleaned_data.get('email', '')

        if not valor:
            return None  # campo opcional

        valor = _sanitizar_texto(valor).lower()

        # Valida formato de email com o validator do Django
        try:
            validate_email(valor)
        except ValidationError:
            raise ValidationError(
                "Introduz um endereço de email válido (ex: nome@dominio.com)."
            )

        # Bloqueia caracteres de injecção no email
        chars_proibidos = ['<', '>', '{', '}', ';', '\'', '"', '\\']
        for char in chars_proibidos:
            if char in valor:
                raise ValidationError(
                    "O email contém caracteres não permitidos."
                )

        return valor

    def clean_telefone(self):
        valor = self.cleaned_data.get('telefone', '')

        if not valor or not valor.strip():
            return None  # campo opcional

        valor = _sanitizar_texto(valor)

        # Valida formato: apenas dígitos, espaços, +, -, (, )
        if not REGEX_TELEFONE_VALIDO.match(valor):
            raise ValidationError(
                "Formato de telefone inválido. "
                "Usa apenas dígitos, espaços, +, - e parênteses "
                "(ex: +351 912 345 678)."
            )

        # Verifica número mínimo de dígitos
        apenas_digitos = re.sub(r'\D', '', valor)
        if len(apenas_digitos) < 7:
            raise ValidationError(
                "O número de telefone deve ter pelo menos 7 dígitos."
            )

        return valor

    def clean_data_nascimento(self):
        data = self.cleaned_data.get('data_nascimento')

        if not data:
            return None  # campo opcional

        hoje = timezone.now().date()

        # Não pode ser no futuro
        if data > hoje:
            raise ValidationError(
                "A data de nascimento não pode ser uma data futura."
            )

        # Não pode ser há mais de 120 anos
        data_minima = hoje.replace(year=hoje.year - 120)
        if data < data_minima:
            raise ValidationError(
                "A data de nascimento introduzida não é válida "
                "(máximo 120 anos atrás)."
            )

        # Aluno deve ter pelo menos 3 anos
        data_minima_idade = hoje.replace(year=hoje.year - 3)
        if data > data_minima_idade:
            raise ValidationError(
                "O aluno deve ter pelo menos 3 anos de idade."
            )

        return data


class MatriculaForm(forms.ModelForm):
    """
    Formulário de matrícula com campo de texto livre para o aluno.
    O aluno é procurado ou criado na view após validação deste form.
    """

    class Meta:
        model  = Matricula
        # id_aluno é tratado manualmente na view — não incluir aqui
        fields = ['id_curso', 'id_turma', 'data_matricula', 'ano_letivo']
        widgets = {
            'id_curso': forms.Select(attrs={'class': 'campo-input'}),
            'id_turma': forms.Select(attrs={'class': 'campo-input'}),
            'data_matricula': forms.DateInput(
                attrs={
                    'type':     'date',
                    'min':      timezone.now().date().isoformat(),
                    'max':      _data_maxima_matricula().isoformat(),
                    'class':    'campo-input',
                    'required': True,
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
                    'class':       'campo-input campo-readonly',
                    'required':    True,
                    'id':          'id_ano_letivo',
                    'readonly':    True,   # ← não editável pelo utilizador
                    'tabindex':    '-1',   # ← não recebe foco via teclado
                    'title':       'Preenchido automaticamente com o ano da data de matrícula',
                }
            ),
        }
        labels = {
            'id_curso':       'Curso',
            'id_turma':       'Turma',
            'data_matricula': 'Data de matrícula',
            'ano_letivo':     'Ano letivo',
        }
        error_messages = {
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
        self.fields['id_curso'].queryset    = Curso.objects.order_by('nome')
        self.fields['id_turma'].queryset    = Turma.objects.order_by('nome_turma')
        self.fields['id_curso'].empty_label = '— Seleciona o curso —'
        self.fields['id_turma'].empty_label = '— Seleciona a turma —'
        for field in self.fields.values():
            field.required = True
        _aplicar_atributos(self.fields)

    # ── Validação e sanitização do nome do aluno ──────────────

    def clean_nome_aluno(self):
        """
        Validação completa do nome do aluno.
        - Sanitiza (normaliza unicode, colapsa espaços, capitaliza)
        - Valida tamanho
        - Valida caracteres permitidos (bloqueia scripts, SQL, HTML)
        - Proteção XSS: o Django templates fazem auto-escape,
          mas validamos aqui para rejeitar na entrada
        """
        valor = self.cleaned_data.get('nome_aluno', '')

        if not valor or not valor.strip():
            raise ValidationError("O nome do aluno é obrigatório.")

        # Sanitiza primeiro
        valor = _sanitizar_nome(valor)

        # Tamanho mínimo após sanitização
        if len(valor) < NOME_MIN_CHARS:
            raise ValidationError(
                f"O nome deve ter pelo menos {NOME_MIN_CHARS} caracteres."
            )

        # Valida caracteres — bloqueia HTML, SQL, scripts, etc.
        if not REGEX_NOME_VALIDO.match(valor):
            raise ValidationError(
                "O nome contém caracteres inválidos. "
                "Apenas letras, espaços, hífens e apóstrofos são permitidos."
            )

        # Bloqueia padrões típicos de injecção (camada extra de defesa)
        padroes_bloqueados = [
            '<', '>', '{', '}', '[', ']', '(', ')',
            ';', '=', '/', '\\', '@', '#', '$', '%',
            '*', '|', '&', '^', '~', '`',
        ]
        for char in padroes_bloqueados:
            if char in valor:
                raise ValidationError(
                    f"O nome contém o caracter inválido '{char}'."
                )

        return valor

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
        data   = self.cleaned_data.get('data_matricula')
        hoje   = timezone.now().date()
        maxima = _data_maxima_matricula()
        if not data:
            raise ValidationError("A data de matrícula é obrigatória.")
        _validar_data_minima(data, "Data de matrícula")
        if data < hoje:
            raise ValidationError(
                f"A data de matrícula não pode ser anterior a hoje "
                f"({hoje.strftime('%d/%m/%Y')})."
            )
        if data > maxima:
            raise ValidationError(
                f"A data de matrícula não pode ser superior a 2 meses "
                f"a partir de hoje (máximo: {maxima.strftime('%d/%m/%Y')})."
            )
        return data

    def clean_ano_letivo(self):
        """
        O ano letivo é derivado da data de matrícula.
        Ignora qualquer valor submetido pelo utilizador
        e usa sempre o ano da data_matricula (protecção server-side).
        """
        data = self.cleaned_data.get('data_matricula')
        if data:
            return data.year
        # Fallback: se data inválida, o clean_data_matricula já gerou erro
        ano = self.cleaned_data.get('ano_letivo')
        if ano is None:
            raise ValidationError("O ano letivo é obrigatório.")
        return ano

    def clean(self):
        """
        Validação cruzada de duplicados.
        Nota: id_aluno não está aqui — é resolvido na view.
        A verificação de duplicado com o aluno real é feita na view
        após procurar/criar o aluno.
        """
        cleaned = super().clean()
        curso = cleaned.get('id_curso')
        turma = cleaned.get('id_turma')

        # Valida que a turma pertence ao curso seleccionado
        if curso and turma:
            if turma.id_curso and turma.id_curso != curso:
                self.add_error(
                    'id_turma',
                    f"A turma '{turma.nome_turma}' não pertence "
                    f"ao curso '{curso.nome}'."
                )
        return cleaned