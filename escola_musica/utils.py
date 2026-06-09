"""
Utilitários centralizados da aplicação.
- Autorização por grupos
- Criação automática de utilizadores Django
"""
from django.contrib.auth.models import User
from decouple import config
from .models import Aluno as AlunoModel

import functools
from django.shortcuts import redirect
from django.contrib import messages

# ─────────────────────────────────────────────────────────────
# AUTORIZAÇÃO — grupos e permissões
# ─────────────────────────────────────────────────────────────

def utilizador_pode_aceder_matriculas(user):
    """
    Retorna True se o utilizador pode aceder à área de matrículas.
    Acesso permitido: superutilizadores, staff e grupo Recepção.
    Bloqueado: alunos, professores e qualquer outro perfil.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    # Grupo Recepção — tem permissões específicas de matrícula
    return user.groups.filter(name='Recepcao').exists()


def requer_acesso_matriculas(view_func):
    """
    Decorator que bloqueia alunos, professores e utilizadores
    sem permissão de aceder às views de matrículas.
    Redireciona para o dashboard correto com mensagem de erro.
    """
    

    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        if utilizador_pode_aceder_matriculas(request.user):
            return view_func(request, *args, **kwargs)

        # Utilizador autenticado mas sem permissão
        # Redireciona para o dashboard correto sem revelar conteúdo
        if hasattr(request.user, 'aluno'):
            messages.error(
                request,
                "Não tens permissão para aceder a esta área."
            )
            return redirect('aluno_dashboard')

        if hasattr(request.user, 'professor'):
            messages.error(
                request,
                "Não tens permissão para aceder a esta área."
            )
            return redirect('professor_dashboard')

        # Utilizador sem perfil conhecido
        messages.error(
            request,
            "Não tens permissão para aceder a esta área."
        )
        return redirect('mainpage')

    return wrapper

def utilizador_e_recepcao(user):
    """Retorna True se o utilizador pertence ao grupo Recepção."""
    return (
        user.is_authenticated and
        not user.is_superuser and
        not user.is_staff and
        user.groups.filter(name='Recepcao').exists()
    )


def utilizador_pode_eliminar(user):
    """Apenas superutilizadores podem eliminar matrículas."""
    return user.is_authenticated and user.is_superuser


def utilizador_pode_editar_financeiro(user):
    """Superutilizadores e staff podem editar dados financeiros."""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


def pagamento_e_protegido(pagamento):
    """
    Um pagamento está protegido quando o estado é 'Pago'.
    Recepção não pode alterar campos deste pagamento.
    """
    if not pagamento:
        return False
    return pagamento.status == 'Pago'


# ─────────────────────────────────────────────────────────────
# AUTENTICAÇÃO — criação automática de utilizadores
# ─────────────────────────────────────────────────────────────

# Password temporária padrão para alunos e professores
PASSWORD_TEMPORARIA = config('PASSWORD_TEMPORARIA')


def criar_ou_obter_user(email, nome):
    """
    Cria ou obtém um User Django para aluno/professor.
    username = email (lowercase)
    password = PASSWORD_TEMPORARIA
    Nunca duplica — verifica antes de criar.
    """
    if not email:
        return None

    email    = email.strip().lower()
    username = email

    # Procura User existente
    user = User.objects.filter(username=username).first()
    if not user:
        user = User.objects.filter(email=email).first()

    if not user:
        nome_parts = nome.strip().split() if nome else ['']
        first_name = nome_parts[0] if nome_parts else ''
        last_name  = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else ''

        user = User.objects.create_user(
            username     = username,
            email        = email,
            password     = PASSWORD_TEMPORARIA,
            first_name   = first_name,
            last_name    = last_name,
            is_active    = True,
            is_staff     = False,
            is_superuser = False,
        )

    return user


def associar_user_aluno(aluno):
    """
    Cria ou obtém User e associa ao aluno.
    Só actua se aluno tiver email.
    Protecção: nunca reassocia um User já ligado a outro aluno
    — evita IntegrityError na constraint UNIQUE user_id.
    """
    if not aluno.email:
        return None

    user = criar_ou_obter_user(aluno.email, aluno.nome or '')
    if not user:
        return None

    # Verifica se o User já está associado a outro aluno
    # Se sim, não tenta reassociar — preserva a integridade da BD
    aluno_existente = (
        AlunoModel.objects
        .filter(user=user)
        .exclude(pk=aluno.pk)
        .first()
    )
    if aluno_existente:
        # User já pertence a outro aluno — não reassocia
        return user

    if aluno.user_id != user.pk:
        aluno.user = user
        aluno.save(update_fields=['user_id'])

    return user


def associar_user_professor(professor):
    """
    Cria ou obtém User e associa ao professor.
    """
    if not professor.email:
        return None

    user = criar_ou_obter_user(professor.email, professor.nome or '')

    if user and professor.user_id != user.pk:
        professor.user = user
        professor.save(update_fields=['user_id'])

    return user