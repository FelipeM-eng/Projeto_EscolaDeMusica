from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Matricula, Pagamento
from .forms import MatriculaForm, PagamentoForm


# ─────────────────────────────────────────
# PÁGINAS PÚBLICAS
# ─────────────────────────────────────────

def mainpage(request):
    """Página principal pública."""
    return render(request, 'escola_musica/mainpage.html')


def login_view(request):
    """
    GET  → apresenta formulário de login
    POST → valida credenciais e redireciona para /matriculas/
    """
    if request.user.is_authenticated:
        return redirect('matriculas_lista')

    form = AuthenticationForm(request, data=request.POST or None)

    form.fields['username'].widget.attrs.update({
        'placeholder': 'Nome de utilizador',
        'autocomplete': 'username',
    })
    form.fields['password'].widget.attrs.update({
        'placeholder': '••••••••',
        'autocomplete': 'current-password',
    })

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('matriculas_lista')

    return render(request, 'escola_musica/login.html', {'form': form})


@require_POST
def logout_view(request):
    """Termina sessão via POST e redireciona para mainpage."""
    logout(request)
    return redirect('mainpage')


# ─────────────────────────────────────────
# ÁREA PROTEGIDA — Funcionalidade de negócio
# ─────────────────────────────────────────

@login_required
def matriculas_lista(request):
    """Lista todas as matrículas com dados relacionados."""
    matriculas = (
        Matricula.objects
        .select_related('id_aluno', 'id_curso', 'id_turma', 'id_pagamento')
        .order_by('-data_matricula')
    )
    return render(request, 'escola_musica/matriculas_lista.html', {
        'matriculas': matriculas,
    })


@login_required
def matricula_detalhe(request, pk):
    """Detalhe de uma matrícula específica."""
    matricula = get_object_or_404(
        Matricula.objects.select_related(
            'id_aluno', 'id_curso', 'id_turma', 'id_pagamento'
        ),
        pk=pk
    )
    return render(request, 'escola_musica/matricula_detalhe.html', {
        'matricula': matricula,
    })


@login_required
def matricula_nova(request):
    """
    GET  → apresenta formulário de nova matrícula + pagamento
    POST → valida, cria pagamento, cria matrícula e redireciona
    """
    form_matricula = MatriculaForm(request.POST or None)
    form_pagamento = PagamentoForm(request.POST or None)

    if request.method == 'POST':
        if form_matricula.is_valid() and form_pagamento.is_valid():
            try:
                # 1. Cria o pagamento primeiro (FK obrigatória)
                pagamento = form_pagamento.save()

                # 2. Cria a matrícula sem fazer commit ainda
                matricula = form_matricula.save(commit=False)
                matricula.id_pagamento = pagamento
                matricula.save()

                messages.success(
                    request,
                    f'Matrícula #{matricula.id_matricula} registada com sucesso!'
                )
                return redirect('matriculas_lista')

            except Exception as e:
                # Captura erros do trigger ou constraints da BD
                messages.error(
                    request,
                    f'Erro ao registar a matrícula: {e}'
                )

    return render(request, 'escola_musica/matricula_nova.html', {
        'form_matricula': form_matricula,
        'form_pagamento': form_pagamento,
    })