import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import IntegrityError, DatabaseError

from .models import Matricula, Pagamento, Aluno, Curso, Turma
from .forms import (
    MatriculaForm, MatriculaEdicaoForm,
    PagamentoForm, PagamentoEdicaoForm,
    AlunoForm, AlunoEdicaoForm, EmailLoginForm
)

logger = logging.getLogger('escola_musica')

# rever isto depois de implementar a autenticação por email:
from .utils import (
    utilizador_e_recepcao,
    utilizador_pode_eliminar,
    utilizador_pode_editar_financeiro,
    pagamento_e_protegido,
    associar_user_aluno,
    associar_user_professor,
)


# ─────────────────────────────────────────
# PÁGINAS PÚBLICAS
# ─────────────────────────────────────────

def mainpage(request):
    return render(request, 'escola_musica/mainpage.html')


def login_view(request):
    """
    Login administrativo — para admins e staff.
    Campo: email + password.
    Redireciona para /matriculas/ após login.
    """
    if request.user.is_authenticated:
        return _redirecionar_por_perfil(request.user)

    form = AuthenticationForm(request, data=request.POST or None)

    form.fields['username'].error_messages.update({
    'required': 'O email é obrigatório.'
    })

    form.fields['password'].error_messages.update({
        'required': 'A palavra-passe é obrigatória.'
    })

    # Altera label do campo username para Email
    form.fields['username'].label = 'Email'
    form.fields['username'].widget.attrs.update({
        'placeholder':  'Username ou email',
        'autocomplete': 'email',
        'type':         'email',
        'class':        'campo-input',
    })
    form.fields['password'].widget.attrs.update({
        'placeholder':  '••••••••',
        'autocomplete': 'current-password',
        'class':        'campo-input',
    })

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return _redirecionar_por_perfil(user)

    return render(request, 'escola_musica/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('mainpage')

# ─────────────────────────────────────────
# DASHBOARDS DE ALUNOS E PROFESSORES
# ─────────────────────────────────────────

def _redirecionar_por_perfil(user):
    """
    Redireciona o utilizador para a área correcta
    com base no seu perfil/grupo.
    """
    # Verifica se é aluno
    if hasattr(user, 'aluno'):
        return redirect('aluno_dashboard')

    # Verifica se é professor
    if hasattr(user, 'professor'):
        return redirect('professor_dashboard')

    # Admin/staff/superutilizador
    return redirect('matriculas_lista')


def login_aluno(request):
    """Login para alunos — usa EmailLoginForm (S4 cumprido)."""
    if request.user.is_authenticated:
        return _redirecionar_por_perfil(request.user)

    form = EmailLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email']
        password = form.cleaned_data['password']

        from django.contrib.auth import authenticate
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if hasattr(user, 'aluno'):
                login(request, user)
                return redirect('aluno_dashboard')
            else:
                form.add_error(None, "Dados de acesso inválidos.")
        else:
            form.add_error(None, "Email ou palavra-passe incorrectos.")

    return render(request, 'escola_musica/login_aluno.html', {'form': form})


def login_professor(request):
    """Login para professores — usa EmailLoginForm (S4 cumprido)."""
    if request.user.is_authenticated:
        return _redirecionar_por_perfil(request.user)

    form = EmailLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email    = form.cleaned_data['email']
        password = form.cleaned_data['password']

        from django.contrib.auth import authenticate
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if hasattr(user, 'professor'):
                login(request, user)
                return redirect('professor_dashboard')
            else:
                form.add_error(None, "Dados de acesso inválidos.")
        else:
            form.add_error(None, "Email ou palavra-passe incorrectos.")

    return render(request, 'escola_musica/login_professor.html', {'form': form})


@login_required
def aluno_dashboard(request):
    """Dashboard placeholder para alunos."""
    # Verifica que é realmente um aluno
    if not hasattr(request.user, 'aluno'):
        messages.error(request, "Acesso restrito a alunos.")
        return redirect('login_aluno')

    aluno = request.user.aluno
    return render(request, 'escola_musica/aluno_dashboard.html', {
        'aluno': aluno,
    })


@login_required
def professor_dashboard(request):
    """Dashboard placeholder para professores."""
    if not hasattr(request.user, 'professor'):
        messages.error(request, "Acesso restrito a professores.")
        return redirect('login_professor')

    professor = request.user.professor
    return render(request, 'escola_musica/professor_dashboard.html', {
        'professor': professor,
    })

# ─────────────────────────────────────────
# ÁREA PROTEGIDA
# ─────────────────────────────────────────

@login_required
def matriculas_lista(request):
    pendente = request.session.get('matricula_pendente', None)

    matriculas = (
        Matricula.objects
        .select_related('id_aluno', 'id_curso', 'id_turma', 'id_pagamento')
        # Ordenação alfabética pelo nome do aluno (ascendente)
        .order_by('id_aluno__nome')
    )
    return render(request, 'escola_musica/matriculas_lista.html', {
        'matriculas': matriculas,
        'pendente':   pendente,
    })


@login_required
def matricula_nova(request):
    """
    GET  → formulário com 3 secções:
           dados do aluno + dados da matrícula + dados do pagamento

    POST → valida os formulários, procura ou cria o aluno,
           guarda os dados em session e redireciona
           para confirmação na modal.

           A BD NÃO é tocada ainda
           (excepto eventual criação de Aluno).
    """

    # Formulário de dados do aluno
    form_aluno = AlunoForm(request.POST or None)

    # Formulário de dados da matrícula
    form_matricula = MatriculaForm(request.POST or None)

    # Formulário de pagamento
    # Recebe o utilizador autenticado para controlo interno
    form_pagamento = PagamentoForm(
        request.POST or None,
        utilizador=request.user
    )

    if request.method == 'POST':

        # Validação independente dos 3 formulários
        aluno_valido = form_aluno.is_valid()
        mat_valida = form_matricula.is_valid()
        pag_valido = form_pagamento.is_valid()

        # Só continua se TODOS os formulários forem válidos
        if aluno_valido and mat_valida and pag_valido:

            # Dados já limpos e sanitizados pelos forms
            cd_a = form_aluno.cleaned_data
            cd_m = form_matricula.cleaned_data
            cd_p = form_pagamento.cleaned_data

            nome = cd_a['nome']
            curso = cd_m['id_curso']
            turma = cd_m['id_turma']

            # ── Procura ou cria o aluno ───────────────────────────────
            # Usa iexact para comparação case-insensitive
            # get_or_create com ORM — nunca SQL manual (S3)
            try:
                aluno, criado = Aluno.objects.get_or_create(
                    nome__iexact=nome,
                    defaults={
                        'nome': nome,
                        'email': cd_a.get('email'),
                        'telefone': cd_a.get('telefone'),
                        'data_nascimento': cd_a.get('data_nascimento'),
                    }
                )

                # Associa User ao aluno automaticamente
                # (cria User se não existir, usando o email do aluno)
                if aluno.email:
                    associar_user_aluno(aluno)

                

            except Aluno.MultipleObjectsReturned:
                # Se existir mais do que um aluno com o mesmo nome,
                # usa o primeiro por ordem de ID
                aluno = Aluno.objects.filter(
                    nome__iexact=nome
                ).order_by('id_aluno').first()

                criado = False

            # ── Verificar duplicado de matrícula ─────────────────────
            # Impede que o mesmo aluno seja matriculado
            # no mesmo curso e turma
            duplicado = Matricula.objects.filter(
                id_aluno=aluno,
                id_curso=curso,
                id_turma=turma,
            ).exists()

            if duplicado:
                form_matricula.add_error(
                    None,
                    f"O aluno '{aluno.nome}' já está matriculado "
                    f"no curso '{curso.nome}' / turma '{turma.nome_turma}'."
                )

            else:
                # ── Validação cruzada: data de pagamento >= data de matrícula ──
                data_matricula  = cd_m.get('data_matricula')
                data_pagamento  = cd_p.get('data_pagamento')

                if data_matricula and data_pagamento:
                    if data_pagamento < data_matricula:
                        form_pagamento.add_error(
                            'data_pagamento',
                            f"A data de pagamento ({data_pagamento.strftime('%d/%m/%Y')}) "
                            f"não pode ser anterior à data de matrícula "
                            f"({data_matricula.strftime('%d/%m/%Y')})."
                        )
                        # Não avança — volta ao formulário com o erro

                    else:
                        # Tudo válido — guarda em session
                        request.session['matricula_pendente'] = {
                            'aluno_id':         aluno.pk,
                            'aluno_nome':       aluno.nome,
                            'aluno_criado':     criado,
                            'aluno_email':      cd_a.get('email') or '—',
                            'aluno_telefone':   cd_a.get('telefone') or '—',
                            'aluno_nascimento': (
                                cd_a['data_nascimento'].strftime('%d/%m/%Y')
                                if cd_a.get('data_nascimento') else '—'
                            ),
                            'curso_id':         curso.pk,
                            'curso_nome':       curso.nome,
                            'turma_id':         turma.pk,
                            'turma_nome':       turma.nome_turma,
                            'data_matricula':   (
                                cd_m['data_matricula'].isoformat()
                                if cd_m.get('data_matricula') else None
                            ),
                            'ano_letivo':       cd_m['ano_letivo'],
                            'data_pagamento':   (
                                cd_p['data_pagamento'].isoformat()
                                if cd_p.get('data_pagamento') else None
                            ),
                            'valor_pago':       str(cd_p['valor_pago']),
                            'status':           cd_p['status'],
                        }
                        return redirect('matriculas_lista')

        else:
            # Mensagem genérica caso existam erros de validação
            messages.warning(
                request,
                "Corrige os erros assinalados antes de submeter."
            )

    # Renderiza a página com os formulários
    # (vazios no GET ou preenchidos no POST com erros)
    # No return render do final da view, substitui por:
    return render(request, 'escola_musica/matricula_nova.html', {
        'form_aluno':     form_aluno,
        'form_matricula': form_matricula,
        'form_pagamento': form_pagamento,
        'turmas_json':    Turma.objects.select_related('id_curso').order_by('nome_turma'),
    })

@login_required
def matricula_cancelar(request):
    """
    Limpa os dados pendentes da session sem gravar nada na BD.
    Redireciona para o formulário de nova matrícula.
    """
    request.session.pop('matricula_pendente', None)
    messages.info(request, "Matrícula cancelada. Podes preencher novamente.")
    return redirect('matricula_nova')


@login_required
@require_POST
def matricula_confirmar(request):
    """
    Grava efectivamente na BD após confirmação na modal.
    Se o aluno já existia, actualiza os dados pessoais
    com os que foram introduzidos (email, telefone, nascimento).
    """
    pendente = request.session.pop('matricula_pendente', None)

    if not pendente:
        messages.error(request, "Não existe matrícula pendente de confirmação.")
        return redirect('matriculas_lista')

    try:
        aluno = Aluno.objects.get(pk=pendente['aluno_id'])
        curso = Curso.objects.get(pk=pendente['curso_id'])
        turma = Turma.objects.get(pk=pendente['turma_id'])

        # Actualiza dados pessoais do aluno se foram fornecidos
        # (aplica-se tanto a alunos novos como a existentes)
        campos_actualizar = []
        if pendente.get('aluno_email') and pendente['aluno_email'] != '—':
            aluno.email = pendente['aluno_email']
            campos_actualizar.append('email')
        if pendente.get('aluno_telefone') and pendente['aluno_telefone'] != '—':
            aluno.telefone = pendente['aluno_telefone']
            campos_actualizar.append('telefone')
        if pendente.get('aluno_nascimento') and pendente['aluno_nascimento'] != '—':
            from datetime import datetime
            try:
                aluno.data_nascimento = datetime.strptime(
                    pendente['aluno_nascimento'], '%d/%m/%Y'
                ).date()
                campos_actualizar.append('data_nascimento')
            except ValueError:
                pass

        if campos_actualizar:
            aluno.save(update_fields=campos_actualizar)

        # Cria o pagamento
        pagamento = Pagamento.objects.create(
            data_pagamento=pendente.get('data_pagamento'),
            valor_pago=pendente['valor_pago'],
            status=pendente['status'],
        )

        # Cria a matrícula
        matricula = Matricula.objects.create(
            id_aluno=aluno,
            id_curso=curso,
            id_turma=turma,
            id_pagamento=pagamento,
            data_matricula=pendente.get('data_matricula'),
            ano_letivo=pendente.get('ano_letivo'),
        )

        messages.success(
            request,
            f"Matrícula #{matricula.id_matricula} registada com sucesso!"
        )

    except IntegrityError as e:
        logger.error(
            f"IntegrityError ao confirmar | "
            f"user={request.user.username} | erro={e}"
        )
        messages.error(
            request,
            "Não foi possível registar: este aluno já está inscrito "
            "neste curso e turma."
        )
    except DatabaseError as e:
        logger.error(
            f"DatabaseError ao confirmar | "
            f"user={request.user.username} | erro={e}"
        )
        messages.error(
            request,
            "Não foi possível concluir a matrícula. "
            "Verifica se o pagamento está regularizado."
        )
    except Exception as e:
        logger.error(
            f"Erro inesperado ao confirmar | "
            f"user={request.user.username} | erro={e}"
        )
        messages.error(
            request,
            "Ocorreu um erro inesperado. Contacta o administrador."
        )

    return redirect('matriculas_lista')


@login_required
def matricula_detalhe(request, pk):
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
def matricula_editar(request, pk):
    """
    Edição de matrícula.
    - Mostra e permite editar dados pessoais do aluno
    - Bloqueia campos financeiros se pagamento estiver Pago
    - Valida data_pagamento >= data_matricula
    - Redireciona para lista após sucesso
    """
    matricula  = get_object_or_404(Matricula, pk=pk)
    pagamento  = matricula.id_pagamento
    aluno      = matricula.id_aluno
    pag_pago   = pagamento and pagamento.status == 'Pago'

    # Dados iniciais do aluno para pré-preencher o form
    dados_aluno_iniciais = {
        'nome':            aluno.nome            if aluno else '',
        'email':           aluno.email           if aluno else '',
        'telefone':        aluno.telefone        if aluno else '',
        'data_nascimento': aluno.data_nascimento if aluno else None,
    }

    form_aluno = AlunoEdicaoForm(
        request.POST or None,
        initial=dados_aluno_iniciais
    )
    form_matricula = MatriculaEdicaoForm(
        request.POST or None,
        instance=matricula
    )
    form_pagamento = PagamentoEdicaoForm(
        request.POST or None,
        instance=pagamento,
        utilizador=request.user
    )

    if request.method == 'POST':
        aluno_valido = form_aluno.is_valid()
        mat_valida   = form_matricula.is_valid()
        pag_valido   = form_pagamento.is_valid()

        if aluno_valido and mat_valida and pag_valido:

            # Validação cruzada: data_pagamento >= data_matricula
            data_matricula = form_matricula.cleaned_data.get('data_matricula')
            data_pagamento = form_pagamento.cleaned_data.get('data_pagamento')

            erro_datas = False
            if data_matricula and data_pagamento:
                if data_pagamento < data_matricula:
                    form_pagamento.add_error(
                        'data_pagamento',
                        f"A data de pagamento "
                        f"({data_pagamento.strftime('%d/%m/%Y')}) "
                        f"não pode ser anterior à data de matrícula "
                        f"({data_matricula.strftime('%d/%m/%Y')})."
                    )
                    erro_datas = True

            if not erro_datas:
                try:
                    # Actualiza dados pessoais do aluno
                    if aluno:
                        cd_a = form_aluno.cleaned_data
                        aluno.nome = cd_a['nome']
                        if cd_a.get('email') is not None:
                            aluno.email = cd_a['email']
                        if cd_a.get('telefone') is not None:
                            aluno.telefone = cd_a['telefone']
                        if cd_a.get('data_nascimento') is not None:
                            aluno.data_nascimento = cd_a['data_nascimento']
                        aluno.save()

                    # Guarda pagamento e matrícula
                    pag_actualizado      = form_pagamento.save()
                    mat_actualizada      = form_matricula.save(commit=False)
                    mat_actualizada.id_pagamento = pag_actualizado
                    mat_actualizada.save()

                    messages.success(
                        request,
                        f"Matrícula #{matricula.id_matricula} "
                        "actualizada com sucesso."
                    )
                    # Redireciona para a LISTA (não para o detalhe)
                    return redirect('matriculas_lista')

                except IntegrityError as e:
                    logger.error(
                        f"IntegrityError ao editar pk={pk} | "
                        f"user={request.user.username} | erro={e}"
                    )
                    messages.error(
                        request,
                        "Já existe uma matrícula com este aluno, "
                        "curso e turma."
                    )
                except DatabaseError as e:
                    logger.error(
                        f"DatabaseError ao editar pk={pk} | "
                        f"user={request.user.username} | erro={e}"
                    )
                    messages.error(
                        request,
                        "Não foi possível actualizar. Tenta novamente."
                    )
                except Exception as e:
                    logger.error(
                        f"Erro inesperado ao editar pk={pk} | "
                        f"user={request.user.username} | erro={e}"
                    )
                    messages.error(
                        request,
                        "Erro inesperado. Contacta o administrador."
                    )
        else:
            messages.warning(request, "Corrige os erros antes de guardar.")

    return render(request, 'escola_musica/matricula_editar.html', {
        'form_aluno':    form_aluno,
        'form_matricula': form_matricula,
        'form_pagamento': form_pagamento,
        'matricula':      matricula,
        'pag_pago':       pag_pago,
    })

@login_required
def matricula_eliminar(request, pk):
    """
    Apenas superutilizadores podem eliminar matrículas.
    GET  → página de confirmação com dados da matrícula
    POST → elimina matrícula e pagamento associado
    """
    # Verificação de permissão — camada da view
    if not request.user.is_superuser:
        messages.error(
            request,
            "Não tens permissão para eliminar matrículas. "
            "Esta acção está reservada a administradores."
        )
        return redirect('matriculas_lista')

    matricula = get_object_or_404(
        Matricula.objects.select_related(
            'id_aluno', 'id_curso', 'id_turma', 'id_pagamento'
        ),
        pk=pk
    )

    if request.method == 'POST':
        try:
            pagamento    = matricula.id_pagamento
            id_matricula = matricula.id_matricula
            nome_aluno   = matricula.id_aluno.nome

            # Elimina a matrícula primeiro (tem FK para pagamento)
            matricula.delete()

            # Elimina o pagamento que ficou órfão
            if pagamento:
                pagamento.delete()

            messages.success(
                request,
                f"Matrícula #{id_matricula} do aluno '{nome_aluno}' "
                "eliminada com sucesso."
            )

        except Exception as e:
            logger.error(
                f"Erro ao eliminar matrícula pk={pk} | "
                f"user={request.user.username} | erro={e}"
            )
            messages.error(
                request,
                "Não foi possível eliminar a matrícula. "
                "Tenta novamente ou contacta o administrador."
            )

        return redirect('matriculas_lista')

    # GET → página de confirmação
    return render(request, 'escola_musica/matricula_eliminar.html', {
        'matricula': matricula,
    })

# ─────────────────────────────────────────
# ENTRADA DO PAINEL DE GESTÃO
# ─────────────────────────────────────────

def gestao_redirect(request):
    """
    Ponto de entrada do painel de gestão.
    Fluxo semelhante ao /admin do Django:

    /gestaoutilizadores
      ├── autenticado + staff/superuser → painel
      └── não autenticado → login do painel
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('gestao_lista')

    return redirect('gestao_login')