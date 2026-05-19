"""
Decorators de acesso para o painel de Gestão de Utilizadores.
Centraliza toda a lógica de permissões — evita Broken Access Control
por esquecimento humano em views futuras.

Hierarquia: superuser > staff > professor/aluno
"""
import functools
from django.shortcuts import redirect, render
from django.contrib import messages


# ── URL de login do painel (redireccionamento centralizado) ──
URL_LOGIN_GESTAO = '/gestaoutilizadores/login/'


def _acesso_negado(request, mensagem="Não tens permissão para aceder a esta área."):
    """
    Resposta padronizada para acesso negado.
    Não redireciona para fora do painel de gestão.
    """
    return render(request, 'gestao/acesso_negado.html', {
        'mensagem': mensagem,
    }, status=403)


def requer_autenticacao_gestao(view_func):
    """
    Decorator base: verifica autenticação.
    Redireciona para o login PRÓPRIO do painel — nunca para /login/ ou mainpage.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Guarda URL de destino para redirect após login
            return redirect(
                f"{URL_LOGIN_GESTAO}?next={request.path}"
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def requer_acesso_gestao(view_func):
    """
    Decorator principal: autenticado + is_staff ou is_superuser.
    Professores e alunos recebem acesso negado dentro do painel.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                f"{URL_LOGIN_GESTAO}?next={request.path}"
            )
        if not (request.user.is_staff or request.user.is_superuser):
            return _acesso_negado(
                request,
                "Acesso restrito a administradores e staff."
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def requer_superuser(view_func):
    """
    Decorator restrito: apenas superutilizadores.
    Usado para acções de gestão de staff.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                f"{URL_LOGIN_GESTAO}?next={request.path}"
            )
        if not request.user.is_superuser:
            return _acesso_negado(
                request,
                "Esta acção requer privilégios de superutilizador."
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def pode_gerir_utilizador(view_func):
    """
    Decorator de object-level permission.
    Verifica se o utilizador autenticado pode gerir o alvo (pk na URL).
    Regras:
      - Ninguém gere superutilizadores
      - Staff só gere alunos e professores
      - Superuser gere staff, alunos e professores (mas NÃO outros superusers)
    Injeta `alvo` no kwargs para a view não precisar de re-fetch.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from django.contrib.auth.models import User
        from django.shortcuts import get_object_or_404

        if not request.user.is_authenticated:
            return redirect(f"{URL_LOGIN_GESTAO}?next={request.path}")

        if not (request.user.is_staff or request.user.is_superuser):
            return _acesso_negado(request)

        pk = kwargs.get('pk')
        if pk:
            alvo = get_object_or_404(User, pk=pk)

            # Ninguém gere superutilizadores — regra absoluta
            if alvo.is_superuser:
                return _acesso_negado(
                    request,
                    "Não é possível gerir contas de superutilizador."
                )

            # Staff não gere outros staff
            if not request.user.is_superuser and alvo.is_staff:
                return _acesso_negado(
                    request,
                    "Staff não pode gerir outras contas de staff."
                )

            # Ninguém se auto-edita (protecção self-lockout)
            if alvo.pk == request.user.pk:
                return _acesso_negado(
                    request,
                    "Não podes editar a tua própria conta neste painel."
                )

            # Injeta alvo para evitar re-fetch na view
            kwargs['alvo'] = alvo

        return view_func(request, *args, **kwargs)
    return wrapper