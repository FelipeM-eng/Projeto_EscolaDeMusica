from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import IntegrityError, DatabaseError   # ← estes dois são novos

from .models import Matricula, Pagamento
from .forms import MatriculaForm, PagamentoForm

import logging
logger = logging.getLogger('escola_musica')


# ─────────────────────────────────────────
# PÁGINAS PÚBLICAS
# ─────────────────────────────────────────

def mainpage(request):
    """Página principal pública."""
    return render(request, 'escola_musica/mainpage.html')


def login_view(request):
    """
    GET  → apresenta formulário de login
    POST → valida credenciais; em caso de falha dá feedback claro
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

    if request.method == 'POST':
        if form.is_valid():
            login(request, form.get_user())
            messages.success(
                request,
                f"Bem-vindo, {form.get_user().username}!"
            )
            return redirect('matriculas_lista')
        else:
            # Mensagem de erro clara sem revelar qual campo está errado
            messages.error(
                request,
                "Credenciais inválidas. Verifica o utilizador e a palavra-passe."
            )

    return render(request, 'escola_musica/login.html', {'form': form})


@require_POST
def logout_view(request):
    """
    Termina sessão via POST (protegido por CSRF).
    Limpa a sessão completamente antes de redirecionar.
    """
    username = request.user.username
    logout(request)
    messages.info(request, f"Sessão de '{username}' terminada com sucesso.")
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
    """Detalhe completo de uma matrícula específica."""
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
    GET  → formulário em branco
    POST → valida, cria pagamento e matrícula com tratamento
           de excepções estruturado por tipo.
           Nenhuma mensagem técnica da BD é exposta ao utilizador.
    """
    form_matricula = MatriculaForm(request.POST or None)
    form_pagamento = PagamentoForm(request.POST or None)

    if request.method == 'POST':
        matricula_valida = form_matricula.is_valid()
        pagamento_valido = form_pagamento.is_valid()

        if matricula_valida and pagamento_valido:
            pagamento = None
            try:
                # ── Passo 1: guardar o pagamento ──────────────────────────
                pagamento = form_pagamento.save()

                # ── Passo 2: associar e guardar a matrícula ───────────────
                matricula = form_matricula.save(commit=False)
                matricula.id_pagamento = pagamento
                matricula.save()

                # ── Sucesso ───────────────────────────────────────────────
                messages.success(
                    request,
                    f"Matrícula #{matricula.id_matricula} registada com sucesso!"
                )
                return redirect('matriculas_lista')

            except IntegrityError as e:
                # Log interno com detalhe técnico completo
                logger.error(
                    "IntegrityError ao criar matrícula | "
                    f"user={request.user.username} | erro={e}"
                )
                _limpar_pagamento_orfao(pagamento)
                # Mensagem sanitizada para o utilizador
                messages.error(
                    request,
                    "Não foi possível registar a matrícula: "
                    "este aluno já pode estar inscrito neste curso e turma."
                )

            except DatabaseError as e:
                # Captura erros de triggers PL/pgSQL — regista internamente
                logger.error(
                    "DatabaseError ao criar matrícula | "
                    f"user={request.user.username} | erro={e}"
                )
                _limpar_pagamento_orfao(pagamento)
                messages.error(
                    request,
                    "Não foi possível concluir a matrícula. "
                    "Verifica se o pagamento está regularizado e tenta novamente."
                )

            except Exception as e:
                logger.error(
                    "Erro inesperado ao criar matrícula | "
                    f"user={request.user.username} | erro={e}"
                )
                _limpar_pagamento_orfao(pagamento)
                messages.error(
                    request,
                    "Ocorreu um erro inesperado. "
                    "Se o problema persistir, contacta o administrador."
                )

        else:
            messages.warning(
                request,
                "Corrige os erros assinalados antes de submeter."
            )

    return render(request, 'escola_musica/matricula_nova.html', {
        'form_matricula': form_matricula,
        'form_pagamento': form_pagamento,
    })


def _limpar_pagamento_orfao(pagamento):
    """
    Função auxiliar — remove o pagamento criado se a matrícula falhar.
    Evita registos de pagamento órfãos na BD em caso de erro a meio.
    Não propaga excepções — é chamada dentro de um bloco except.
    """
    if pagamento and pagamento.pk:
        try:
            pagamento.delete()
        except Exception as e:
            logger.error(f"Falha ao limpar pagamento órfão pk={pagamento.pk} | erro={e}")