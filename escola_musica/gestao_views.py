"""
Views do Painel de Gestão de Utilizadores.
Separado de views.py para não misturar responsabilidades.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction, DatabaseError, IntegrityError

from .gestao_decorators import (
    requer_acesso_gestao,
    pode_gerir_utilizador,
    URL_LOGIN_GESTAO,
)
from .gestao_forms import (
    GestaoLoginForm,
    UtilizadorCriarForm,
    UtilizadorEditarForm,
    GruposForm,
    AssociarPerfilForm,
    PasswordForm,
)
from .models import Aluno, Professor, Matricula

audit_log = logging.getLogger('gestao_auditoria')
logger    = logging.getLogger('escola_musica')
contas_logger = logging.getLogger('contas_log')


# ─────────────────────────────────────────────────────────────
# UTILITÁRIO DE AUDITORIA
# ─────────────────────────────────────────────────────────────

def _audit(actor, accao, alvo=None, resultado='OK', detalhe=''):
    audit_log.info(
        f"[{accao}] actor={actor} | alvo={alvo or '—'} | "
        f"resultado={resultado} | detalhe={detalhe}"
    )


# ─────────────────────────────────────────────────────────────
# LOGIN / LOGOUT
# ─────────────────────────────────────────────────────────────

def gestao_login(request):
    """
    Login próprio do painel.
    Nunca redireciona para fora do painel em caso de erro.
    Mensagens genéricas — protecção account enumeration.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('gestao_lista')
        return render(request, 'gestao/login.html', {
            'form': GestaoLoginForm(),
            'erro': "Não tens permissão para aceder a esta área.",
        })

    form = GestaoLoginForm(request.POST or None)
    erro = None

    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = authenticate(request, username=email, password=password)

        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            _audit(user.username, 'LOGIN', resultado='OK')
            next_url = request.GET.get('next', '')
            if next_url and next_url.startswith('/gestaoutilizadores'):
                return redirect(next_url)
            return redirect('gestao_lista')
        else:
            # Mensagem genérica — não revela se email existe ou se é
            # problema de password vs permissões
            _audit(email, 'LOGIN', resultado='FALHOU')
            erro = "Credenciais inválidas."

    elif request.method == 'POST':
        erro = "Preenche todos os campos."

    return render(request, 'gestao/login.html', {
        'form': form,
        'erro': erro,
    })


def gestao_logout(request):
    """Logout do painel — redireciona para o login do painel."""
    if request.user.is_authenticated:
        _audit(request.user.username, 'LOGOUT')
    logout(request)
    return redirect('gestao_login')


# ─────────────────────────────────────────────────────────────
# LISTAGEM
# ─────────────────────────────────────────────────────────────

@requer_acesso_gestao
def gestao_lista(request):
    """
    Lista com pesquisa segura (ORM), filtros e paginação.
    Superuser vê todos excepto outros superusers e si próprio.
    Staff vê apenas alunos e professores.
    """
    if request.user.is_superuser:
        qs = User.objects.exclude(
            pk=request.user.pk
        ).exclude(
            is_superuser=True
        ).prefetch_related('groups')
    else:
        qs = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).prefetch_related('groups')

    # Pesquisa segura — ORM com icontains
    pesquisa = request.GET.get('q', '').strip()
    if pesquisa:
        qs = qs.filter(
            Q(username__icontains=pesquisa)   |
            Q(email__icontains=pesquisa)      |
            Q(first_name__icontains=pesquisa) |
            Q(last_name__icontains=pesquisa)
        )

    # Filtros
    filtro_estado = request.GET.get('estado', '')
    filtro_perfil = request.GET.get('perfil', '')
    filtro_grupo  = request.GET.get('grupo', '')

    if filtro_estado == 'activo':
        qs = qs.filter(is_active=True)
    elif filtro_estado == 'inactivo':
        qs = qs.filter(is_active=False)

    if filtro_perfil == 'aluno':
        qs = qs.filter(aluno__isnull=False)
    elif filtro_perfil == 'professor':
        qs = qs.filter(professor__isnull=False)
    elif filtro_perfil == 'sem_perfil':
        qs = qs.filter(aluno__isnull=True, professor__isnull=True)

    if filtro_grupo:
        qs = qs.filter(groups__name=filtro_grupo)

    # Optimização N+1
    qs = qs.select_related('aluno', 'professor').order_by('username')

    total     = qs.count()
    paginator = Paginator(qs, 15)
    pagina    = paginator.get_page(request.GET.get('pagina', 1))

    return render(request, 'gestao/lista.html', {
        'pagina':             pagina,
        'pesquisa':           pesquisa,
        'filtro_estado':      filtro_estado,
        'filtro_perfil':      filtro_perfil,
        'filtro_grupo':       filtro_grupo,
        'grupos_disponiveis': Group.objects.all(),
        'total':              total,
    })


# ─────────────────────────────────────────────────────────────
# CRIAR UTILIZADOR
# ─────────────────────────────────────────────────────────────

@requer_acesso_gestao
def gestao_utilizador_criar(request):
    """
    Criação de utilizador.
    is_superuser NUNCA atribuível por este form.
    is_staff só para superutilizadores.
    """
    form = UtilizadorCriarForm(
        request.POST or None,
        actor=request.user
    )

    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
                _audit(
                    request.user.username, 'CRIAR_USER',
                    alvo=user.username, resultado='OK'
                )
            messages.success(
                request,
                f"Utilizador '{user.username}' criado com sucesso."
            )
            return redirect('gestao_lista')

        except IntegrityError as e:
            logger.error(
                f"IntegrityError ao criar user | "
                f"actor={request.user.username} | erro={e}"
            )
            messages.error(
                request,
                "Não foi possível criar o utilizador — email ou username duplicado."
            )
        except Exception as e:
            logger.error(
                f"Erro ao criar user | "
                f"actor={request.user.username} | erro={e}"
            )
            messages.error(request, "Erro inesperado. Tenta novamente.")

    return render(request, 'gestao/utilizador_form.html', {
        'form':   form,
        'titulo': 'Criar Utilizador',
        'acao':   'Criar',
    })


# ─────────────────────────────────────────────────────────────
# EDITAR UTILIZADOR
# ─────────────────────────────────────────────────────────────

@requer_acesso_gestao
@pode_gerir_utilizador
def gestao_utilizador_editar(request, pk, alvo=None):
    """
    GET  → form de edição + secções de grupos, activar/desactivar,
           associar/remover perfil + botão "Mudar palavra-passe" (modal JS)
    POST → distingue a acção pelo campo hidden 'acao_secundaria'
           se 'dados'     → valida e processa edição principal
           se 'grupos'    → actualiza grupos
           se 'toggle'    → activa/desactiva conta
           se 'remover'   → remove associação de perfil
    """

    form_dados    = UtilizadorEditarForm(
        request.POST or None if request.POST.get('acao_secundaria') == 'dados'
        else None,
        instance=alvo,
        actor=request.user
    )
    form_password = PasswordForm(
        request.POST or None if request.POST.get('acao_secundaria') == 'dados'
        else None,
        user=alvo
    )
    form_grupos = GruposForm(
        request.POST or None if request.POST.get('acao_secundaria') == 'grupos'
        else None,
        initial={'grupos': alvo.groups.all()}
    )
    form_associar = AssociarPerfilForm(
        request.POST or None if request.POST.get('acao_secundaria') == 'associar'
        else None,
    )

    if request.method == 'POST':
        acao = request.POST.get('acao_secundaria', '')

        # ── Acção: guardar dados principais ──────────────────
        if acao == 'dados':
            dados_validos   = form_dados.is_valid()
            password_valida = form_password.is_valid()

            if dados_validos and password_valida:
                cd        = form_dados.cleaned_data
                cd_pass   = form_password.cleaned_data
                nova_pass = cd_pass.get('password_validada', '')

                alteracoes = _detectar_alteracoes(
                    alvo, cd, nova_pass, actor=request.user
                )

                if not alteracoes:
                    messages.info(request, "Nenhuma alteração detectada.")
                    return redirect('gestao_utilizador_editar', pk=pk)

                # Guarda dados em session — NUNCA a password em plaintext
                request.session[f'gestao_editar_{pk}'] = {
                    'pk':         pk,
                    'alteracoes': alteracoes,
                    'dados': {
                        'first_name': cd.get('first_name', ''),
                        'last_name':  cd.get('last_name', ''),
                        'email':      cd.get('email', ''),
                        'is_staff':   cd.get('is_staff', alvo.is_staff)
                                      if request.user.is_superuser
                                      else alvo.is_staff,
                    },
                    'password_alterada': bool(nova_pass),
                }

                if nova_pass:
                    from django.core import signing
                    request.session[f'gestao_pass_{pk}'] = signing.dumps(
                        nova_pass,
                        salt='gestao_password_temporaria'
                    )

                return redirect('gestao_utilizador_confirmar', pk=pk)

            else:
                messages.warning(
                    request,
                    "Corrige os erros assinalados antes de continuar."
                )

        # ── Acção: guardar grupos ─────────────────────────────
        elif acao == 'grupos':
            if form_grupos.is_valid():
                try:
                    with transaction.atomic():
                        novos_grupos = form_grupos.cleaned_data['grupos']
                        alvo.groups.set(novos_grupos)
                        _audit(
                            request.user.username, 'GERIR_GRUPOS',
                            alvo=alvo.username, resultado='OK',
                            detalhe=f"grupos={[g.name for g in novos_grupos]}"
                        )
                    messages.success(
                        request,
                        f"Grupos de '{alvo.username}' actualizados."
                    )
                    return redirect('gestao_utilizador_editar', pk=pk)
                except Exception as e:
                    logger.error(
                        f"Erro ao gerir grupos pk={pk} | "
                        f"actor={request.user.username} | erro={e}"
                    )
                    messages.error(request, "Não foi possível actualizar os grupos.")

        # ── Acção: activar / desactivar ───────────────────────
        elif acao == 'toggle':
            try:
                with transaction.atomic():
                    alvo.is_active = not alvo.is_active
                    alvo.save(update_fields=['is_active'])
                    estado = "activada" if alvo.is_active else "desactivada"
                    _audit(
                        request.user.username, 'TOGGLE_CONTA',
                        alvo=alvo.username, resultado='OK',
                        detalhe=estado
                    )
                messages.success(
                    request,
                    f"Conta de '{alvo.username}' {estado}."
                )
                return redirect('gestao_utilizador_editar', pk=pk)
            except Exception as e:
                logger.error(
                    f"Erro ao toggle pk={pk} | "
                    f"actor={request.user.username} | erro={e}"
                )
                messages.error(request, "Não foi possível alterar o estado da conta.")

        # ── Acção: remover associação de perfil ───────────────
        elif acao == 'remover':
            tipo = request.POST.get('tipo_perfil', '')
            if tipo not in ['aluno', 'professor']:
                messages.error(request, "Tipo de perfil inválido.")
            else:
                try:
                    with transaction.atomic():
                        if tipo == 'aluno':
                            perfil = Aluno.objects.select_for_update().get(
                                user_id=alvo.pk
                            )
                        else:
                            perfil = Professor.objects.select_for_update().get(
                                user_id=alvo.pk
                            )
                        nome_perfil = perfil.nome
                        perfil.user = None
                        perfil.save(update_fields=['user_id'])
                        _audit(
                            request.user.username, 'REMOVER_ASSOCIACAO',
                            alvo=alvo.username, resultado='OK',
                            detalhe=f"tipo={tipo} perfil={nome_perfil}"
                        )
                    messages.success(
                        request,
                        f"Associação com {tipo} '{nome_perfil}' removida."
                    )
                    return redirect('gestao_utilizador_editar', pk=pk)
                except (Aluno.DoesNotExist, Professor.DoesNotExist):
                    messages.error(request, "Perfil não encontrado.")
                except Exception as e:
                    logger.error(
                        f"Erro ao remover associação pk={pk} | "
                        f"actor={request.user.username} | erro={e}"
                    )
                    messages.error(request, "Não foi possível remover a associação.")

        # ── Acção: associar perfil ────────────────────────────
        elif acao == 'associar':
            if form_associar.is_valid():
                tipo      = form_associar.cleaned_data['tipo']
                perfil_id = form_associar.cleaned_data['perfil_id']
                try:
                    with transaction.atomic():
                        if tipo == 'aluno':
                            perfil = Aluno.objects.select_for_update().get(
                                pk=perfil_id
                            )
                        else:
                            perfil = Professor.objects.select_for_update().get(
                                pk=perfil_id
                            )
                        if perfil.user_id:
                            messages.error(
                                request,
                                f"Este {tipo} já tem utilizador associado."
                            )
                        else:
                            perfil.user = alvo
                            perfil.save(update_fields=['user_id'])
                            _audit(
                                request.user.username, 'ASSOCIAR_PERFIL',
                                alvo=alvo.username, resultado='OK',
                                detalhe=f"tipo={tipo} perfil={perfil.nome}"
                            )
                            messages.success(
                                request,
                                f"Utilizador associado a {tipo} '{perfil.nome}'."
                            )
                            return redirect('gestao_utilizador_editar', pk=pk)
                except (Aluno.DoesNotExist, Professor.DoesNotExist):
                    messages.error(request, "Perfil não encontrado.")
                except Exception as e:
                    logger.error(
                        f"Erro ao associar pk={pk} | "
                        f"actor={request.user.username} | erro={e}"
                    )
                    messages.error(request, "Não foi possível fazer a associação.")

    # Determina perfil actual do alvo
    try:
        perfil_aluno     = alvo.aluno
    except Exception:
        perfil_aluno     = None
    try:
        perfil_professor = alvo.professor
    except Exception:
        perfil_professor = None

    return render(request, 'gestao/utilizador_editar.html', {
        'form_dados':       form_dados,
        'form_password':    form_password,
        'form_grupos':      form_grupos,
        'form_associar':    form_associar,
        'utilizador':       alvo,
        'perfil_aluno':     perfil_aluno,
        'perfil_professor': perfil_professor,
        'grupos_actuais':   alvo.groups.all(),
    })

def _detectar_alteracoes(alvo, cd, nova_pass, actor):
    """
    Compara os dados submetidos com o estado actual do utilizador.
    Retorna lista de dicts com 'campo', 'antes', 'depois'.
    Lista vazia = nenhuma alteração.
    """
    alteracoes = []

    mapeamento = {
        'first_name': ('Primeiro nome', alvo.first_name),
        'last_name':  ('Apelido',       alvo.last_name),
        'email':      ('Email',         alvo.email),
    }

    for campo, (label, valor_actual) in mapeamento.items():
        novo = cd.get(campo, valor_actual)
        # Normaliza strings para comparação
        if isinstance(valor_actual, str):
            valor_actual = valor_actual.strip().lower() \
                if campo == 'email' else valor_actual.strip()
        if isinstance(novo, str):
            novo = novo.strip().lower() \
                if campo == 'email' else novo.strip()

        if novo != valor_actual:
            alteracoes.append({
                'campo':  label,
                'antes':  _formatar_valor(campo, valor_actual),
                'depois': _formatar_valor(campo, novo),
            })

    # is_staff — só relevante para superutilizadores
    if actor and actor.is_superuser:
        novo_staff = cd.get('is_staff', alvo.is_staff)
        if novo_staff != alvo.is_staff:
            alteracoes.append({
                'campo':  'Acesso staff',
                'antes':  'Sim' if alvo.is_staff else 'Não',
                'depois': 'Sim' if novo_staff else 'Não',
            })

    # Password
    if nova_pass:
        alteracoes.append({
            'campo':  'Palavra-passe',
            'antes':  '••••••••',
            'depois': '→ será alterada',
        })

    return alteracoes


def _formatar_valor(campo, valor):
    """Formata valores para apresentação na confirmação."""
    if isinstance(valor, bool):
        return 'Sim' if valor else 'Não'
    return str(valor) if valor else '—'


@requer_acesso_gestao
@pode_gerir_utilizador
def gestao_utilizador_confirmar(request, pk, alvo=None):
    """
    GET  → página de confirmação com lista de alterações reais.
           Password aparece como 'será alterada' — nunca em plaintext.
    POST → revalida password (signing.loads) + transaction.atomic()
           Password nunca esteve em plaintext na session.
           Invalida sessões activas do alvo se password foi alterada.
    """
    from django.core import signing

    chave_session      = f'gestao_editar_{pk}'
    chave_session_pass = f'gestao_pass_{pk}'
    pendente           = request.session.get(chave_session)

    if not pendente or pendente.get('pk') != pk:
        messages.error(
            request,
            "Não existe edição pendente para este utilizador."
        )
        return redirect('gestao_utilizador_editar', pk=pk)

    if request.method == 'POST':
        acao = request.POST.get('acao', '')

        if acao == 'cancelar':
            request.session.pop(chave_session, None)
            request.session.pop(chave_session_pass, None)
            messages.info(request, "Edição cancelada.")
            return redirect('gestao_utilizador_editar', pk=pk)

        if acao == 'confirmar':
            try:
                with transaction.atomic():
                    dados             = pendente['dados']
                    password_alterada = pendente.get('password_alterada', False)
                    nova_password     = None

                    # Recupera e revalida a password via signing
                    # Nunca foi guardada em plaintext na session
                    if password_alterada:
                        token = request.session.get(chave_session_pass)
                        if not token:
                            raise ValueError(
                                "Token de password em falta ou expirado."
                            )
                        try:
                            # max_age=300 — token expira em 5 minutos
                            nova_password = signing.loads(
                                token,
                                salt='gestao_password_temporaria',
                                max_age=300
                            )
                        except signing.SignatureExpired:
                            raise ValueError(
                                "O tempo para confirmar expirou. "
                                "Repete a edição."
                            )
                        except signing.BadSignature:
                            raise ValueError(
                                "Token de password inválido."
                            )

                        # Revalida no backend antes de set_password()
                        try:
                            from django.contrib.auth.password_validation import \
                                validate_password
                            validate_password(nova_password, user=alvo)
                        except Exception as e:
                            raise ValueError(
                                f"Password inválida: {e}"
                            )

                    # Aplica alterações de dados
                    alvo.first_name = dados['first_name']
                    alvo.last_name  = dados['last_name']
                    alvo.email      = dados['email']
                

                    # is_staff só para superutilizadores
                    if request.user.is_superuser:
                        alvo.is_staff = dados.get('is_staff', alvo.is_staff)

                    # is_superuser NUNCA alterado
                    alvo.is_superuser = User.objects.get(
                        pk=pk
                    ).is_superuser

                    # Password — set_password() + nunca plaintext
                    if nova_password:
                        alvo.set_password(nova_password)

                    alvo.save()

                    # Invalida sessões activas do alvo após mudança de password
                    if password_alterada and nova_password:
                        from django.contrib.sessions.models import Session
                        from django.utils import timezone as tz
                        sessoes = Session.objects.filter(
                            expire_date__gte=tz.now()
                        )
                        for s in sessoes:
                            try:
                                dados_sessao = s.get_decoded()
                                if dados_sessao.get(
                                    '_auth_user_id'
                                ) == str(alvo.pk):
                                    s.delete()
                            except Exception:
                                pass  # sessão corrompida — ignorar

                    # Limpa session após gravação bem sucedida
                    request.session.pop(chave_session, None)
                    request.session.pop(chave_session_pass, None)

                    _audit(
                        request.user.username,
                        'EDITAR_USER',
                        alvo=alvo.username,
                        resultado='OK',
                        detalhe=(
                            f"campos={[a['campo'] for a in pendente['alteracoes']]} "
                            f"password_alterada={password_alterada}"
                        )
                    )

                messages.success(
                    request,
                    f"Utilizador '{alvo.username}' actualizado com sucesso."
                )
                return redirect('gestao_lista')

            except ValueError as e:
                # Erros de token/password — mensagem clara ao utilizador
                logger.error(
                    f"Erro de validação ao confirmar pk={pk} | "
                    f"actor={request.user.username} | erro={e}"
                )
                # Limpa session — força resubmissão do form
                request.session.pop(chave_session, None)
                request.session.pop(chave_session_pass, None)
                messages.error(request, str(e))
                return redirect('gestao_utilizador_editar', pk=pk)

            except Exception as e:
                logger.error(
                    f"Erro ao confirmar edição pk={pk} | "
                    f"actor={request.user.username} | erro={e}"
                )
                messages.error(
                    request,
                    "Não foi possível guardar as alterações. Tenta novamente."
                )
                return redirect('gestao_utilizador_editar', pk=pk)

    # GET → página de confirmação
    return render(request, 'gestao/utilizador_confirmar.html', {
        'utilizador': alvo,
        'alteracoes': pendente['alteracoes'],
        'pk':         pk,
    })


@requer_acesso_gestao
@pode_gerir_utilizador
def gestao_utilizador_cancelar_edicao(request, pk, alvo=None):
    """Cancela edição pendente e limpa session."""
    request.session.pop(f'gestao_editar_{pk}', None)
    request.session.pop(f'gestao_pass_{pk}', None)
    return redirect('gestao_lista')


# ─────────────────────────────────────────────────────────────
# GERIR GRUPOS
# ─────────────────────────────────────────────────────────────

@requer_acesso_gestao
@pode_gerir_utilizador
def gestao_utilizador_grupos(request, pk, alvo=None):
    """
    Atribuição/remoção de grupos.
    Só grupos existentes — sem criação de novos.
    Protecção self-lockout: staff não remove os próprios grupos críticos.
    """
    form = GruposForm(
        request.POST or None,
        initial={'grupos': alvo.groups.all()}
    )

    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                novos_grupos = form.cleaned_data['grupos']
                alvo.groups.set(novos_grupos)
                _audit(
                    request.user.username, 'GERIR_GRUPOS',
                    alvo=alvo.username,
                    resultado='OK',
                    detalhe=f"grupos={[g.name for g in novos_grupos]}"
                )
            messages.success(
                request,
                f"Grupos de '{alvo.username}' actualizados."
            )
            return redirect('gestao_lista')

        except Exception as e:
            logger.error(
                f"Erro ao gerir grupos pk={pk} | "
                f"actor={request.user.username} | erro={e}"
            )
            messages.error(request, "Não foi possível actualizar os grupos.")

    return render(request, 'gestao/utilizador_grupos.html', {
        'form':            form,
        'utilizador':      alvo,
        'grupos_actuais':  alvo.groups.all(),
    })


# ─────────────────────────────────────────────────────────────
# ACTIVAR / DESACTIVAR
# ─────────────────────────────────────────────────────────────

@requer_acesso_gestao
@pode_gerir_utilizador
@require_POST
def gestao_utilizador_toggle(request, pk, alvo=None):
    """
    Ativa/desativa conta.

    Regras:
    - Não permite alterar a própria conta.
    - Não permite alterar superutilizadores.
    - Ao activar aluno, exige que exista pelo menos uma matrícula.
    - Professores/staff sem perfil de aluno não são bloqueados por esta regra.
    """

    try:
        with transaction.atomic():

            # Se a conta está inativa, a operação actual é ATIVAR.
            if not alvo.is_active:
                try:
                    aluno = alvo.aluno
                except Aluno.DoesNotExist:
                    aluno = None
                except AttributeError:
                    aluno = None

                if aluno:
                    tem_matricula = Matricula.objects.filter(
                        id_aluno=aluno
                    ).exists()

                    if not tem_matricula:
                        _audit(
                            request.user.username,
                            'TOGGLE_CONTA',
                            alvo=alvo.username,
                            resultado='BLOQUEADO',
                            detalhe='aluno_sem_matricula'
                        )

                        contas_logger.warning(
                            f"[BLOQUEAR_ATIVACAO] "
                            f"actor={request.user.username} | "
                            f"alvo={alvo.username} | "
                            f"alvo_id={alvo.pk} | "
                            f"motivo=aluno_sem_matricula"
                        )

                        messages.error(
                            request,
                            f"Não é possível ativar a conta de '{alvo.username}': "
                            f"o aluno não possui nenhuma matrícula activa. "
                            f"Cria uma matrícula primeiro."
                        )
                        return redirect('gestao_lista')

            alvo.is_active = not alvo.is_active
            alvo.save(update_fields=['is_active'])

            estado = "ativada" if alvo.is_active else "desativada"

            _audit(
                request.user.username,
                'TOGGLE_CONTA',
                alvo=alvo.username,
                resultado='OK',
                detalhe=estado
            )

            contas_logger.info(
                f"[{'ATIVAR' if alvo.is_active else 'DESATIVAR'}] "
                f"actor={request.user.username} | "
                f"alvo={alvo.username} | "
                f"alvo_id={alvo.pk} | "
                f"estado={estado}"
            )

        messages.success(
            request,
            f"Conta de '{alvo.username}' {estado}."
        )

    except Exception as e:
        logger.error(
            f"Erro ao toggle pk={pk} | "
            f"actor={request.user.username} | erro={e}"
        )
        messages.error(request, "Não foi possível alterar o estado da conta.")

    return redirect('gestao_lista')


# ─────────────────────────────────────────────────────────────
# ASSOCIAR PERFIL (User ↔ Aluno ou Professor)
# ─────────────────────────────────────────────────────────────

@requer_acesso_gestao
def gestao_utilizador_associar(request, pk):
    """
    Associa um User existente a um Aluno ou Professor.
    Protecção de concorrência: select_for_update() + transaction.atomic()
    evita dupla associação simultânea por dois administradores.
    """
    alvo_user = get_object_or_404(User, pk=pk)

    # Verifica permissão de gerir este utilizador
    if alvo_user.is_superuser:
        messages.error(request, "Não é possível associar perfil a superutilizador.")
        return redirect('gestao_lista')
    if not request.user.is_superuser and alvo_user.is_staff:
        messages.error(request, "Sem permissão para gerir este utilizador.")
        return redirect('gestao_lista')

    form = AssociarPerfilForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        tipo          = form.cleaned_data['tipo']
        perfil_id     = form.cleaned_data['perfil_id']

        try:
            with transaction.atomic():
                if tipo == 'aluno':
                    # select_for_update() bloqueia a linha durante a transacção
                    # evita race condition entre dois admins simultâneos
                    perfil = (
                        Aluno.objects
                        .select_for_update()
                        .get(pk=perfil_id)
                    )
                    if perfil.user_id:
                        messages.error(
                            request,
                            f"O aluno '{perfil.nome}' já tem utilizador associado."
                        )
                        return redirect('gestao_lista')
                    perfil.user = alvo_user
                    perfil.save(update_fields=['user_id'])

                else:
                    perfil = (
                        Professor.objects
                        .select_for_update()
                        .get(pk=perfil_id)
                    )
                    if perfil.user_id:
                        messages.error(
                            request,
                            f"O professor '{perfil.nome}' já tem utilizador associado."
                        )
                        return redirect('gestao_lista')
                    perfil.user = alvo_user
                    perfil.save(update_fields=['user_id'])

                _audit(
                    request.user.username, 'ASSOCIAR_PERFIL',
                    alvo=alvo_user.username,
                    resultado='OK',
                    detalhe=f"tipo={tipo} perfil_id={perfil_id}"
                )

            messages.success(
                request,
                f"Utilizador '{alvo_user.username}' associado a "
                f"{tipo} '{perfil.nome}'."
            )
            return redirect('gestao_lista')

        except (Aluno.DoesNotExist, Professor.DoesNotExist):
            messages.error(request, "Perfil não encontrado.")
        except Exception as e:
            logger.error(
                f"Erro ao associar pk={pk} | "
                f"actor={request.user.username} | erro={e}"
            )
            messages.error(request, "Não foi possível fazer a associação.")

    return render(request, 'gestao/utilizador_associar.html', {
        'form':      form,
        'alvo_user': alvo_user,
    })


# ─────────────────────────────────────────────────────────────
# REMOVER ASSOCIAÇÃO
# ─────────────────────────────────────────────────────────────

@requer_acesso_gestao
@require_POST
def gestao_utilizador_remover(request, pk):
    """
    Remove associação User ↔ Aluno ou Professor.
    pk aqui é o id do Aluno ou Professor.
    POST obrigatório + CSRF.
    select_for_update() evita race condition.
    """
    tipo = request.POST.get('tipo', '')

    if tipo not in ['aluno', 'professor']:
        messages.error(request, "Tipo inválido.")
        return redirect('gestao_lista')

    try:
        with transaction.atomic():
            if tipo == 'aluno':
                perfil = (
                    Aluno.objects
                    .select_for_update()
                    .get(pk=pk)
                )
            else:
                perfil = (
                    Professor.objects
                    .select_for_update()
                    .get(pk=pk)
                )

            if not perfil.user_id:
                messages.warning(
                    request,
                    f"Este {tipo} não tem utilizador associado."
                )
                return redirect('gestao_lista')

            nome_user = perfil.user.username
            _audit(
                request.user.username, 'REMOVER_ASSOCIACAO',
                alvo=nome_user,
                resultado='OK',
                detalhe=f"tipo={tipo} perfil={perfil.nome}"
            )
            perfil.user = None
            perfil.save(update_fields=['user_id'])

        messages.success(
            request,
            f"Associação com '{nome_user}' removida de {tipo} '{perfil.nome}'."
        )

    except (Aluno.DoesNotExist, Professor.DoesNotExist):
        messages.error(request, "Perfil não encontrado.")
    except Exception as e:
        logger.error(
            f"Erro ao remover associação pk={pk} tipo={tipo} | "
            f"actor={request.user.username} | erro={e}"
        )
        messages.error(request, "Não foi possível remover a associação.")

    return redirect('gestao_lista')