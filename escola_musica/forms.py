from django import forms
from .models import Matricula, Pagamento, Aluno, Curso, Turma


class PagamentoForm(forms.ModelForm):
    """Formulário para criar o pagamento associado à matrícula."""

    class Meta:
        model = Pagamento
        fields = ['data_pagamento', 'valor_pago', 'status']
        widgets = {
            'data_pagamento': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'valor_pago': forms.NumberInput(
                attrs={'step': '0.01', 'min': '0', 'placeholder': '0.00'}
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


class MatriculaForm(forms.ModelForm):
    """Formulário para registar uma nova matrícula."""

    class Meta:
        model = Matricula
        fields = ['id_aluno', 'id_curso', 'id_turma', 'data_matricula', 'ano_letivo']
        widgets = {
            'id_aluno': forms.Select(attrs={'class': 'campo-select'}),
            'id_curso': forms.Select(attrs={'class': 'campo-select'}),
            'id_turma': forms.Select(attrs={'class': 'campo-select'}),
            'data_matricula': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'ano_letivo': forms.NumberInput(
                attrs={'min': '2000', 'max': '2100', 'placeholder': '2025'}
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
        # Ordenar os dropdowns alfabeticamente
        self.fields['id_aluno'].queryset = (
            Aluno.objects.order_by('nome')
        )
        self.fields['id_curso'].queryset = (
            Curso.objects.order_by('nome')
        )
        self.fields['id_turma'].queryset = (
            Turma.objects.order_by('nome_turma')
        )
        # Placeholders nos selects
        self.fields['id_aluno'].empty_label = '— Seleciona o aluno —'
        self.fields['id_curso'].empty_label = '— Seleciona o curso —'
        self.fields['id_turma'].empty_label = '— Seleciona a turma —'