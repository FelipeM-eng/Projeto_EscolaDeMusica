import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import IntegrityError, DatabaseError, transaction

from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncMonth
import json

from django.utils import timezone

from datetime import datetime, time
import datetime as dt

from .models import (
    Aluno, Professor, Matricula, Pagamento,
    Curso, Turma, Aula, AulaDoAluno,
)
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
    requer_acesso_matriculas,
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
    """
    Dashboard do aluno.
    Segurança: todos os dados filtrados por request.user.aluno
    Nunca acessa dados de outro aluno.
    """

    # Protecção — verifica que é realmente um aluno
    if not hasattr(request.user, 'aluno'):
        messages.error(request, "Acesso restrito a alunos.")
        return redirect('login_aluno')

    aluno = request.user.aluno
    agora = timezone.now()

    # ── Matrículas com dados relacionados ────────────────────
    matriculas = (
        Matricula.objects
        .filter(id_aluno=aluno)
        .select_related(
            'id_curso',
            'id_turma',
            'id_pagamento',
        )
        .order_by('-ano_letivo')
    )

    # ── Aulas do aluno — base para todos os KPIs ─────────────
    # select_related evita N+1 queries
    aulas_qs = (
        AulaDoAluno.objects
        .filter(id_aluno=aluno)
        .select_related(
            'id_aula',
            'id_aula__id_curso',
            'id_aula__id_professor',
            'id_aula__id_sala',
            'id_aula__id_turma',
        )
        .order_by('data_inicio')
    )

    # ── KPIs de presença ─────────────────────────────────────
    # Só conta aulas com presença registada (não None)
    aulas_com_registo = aulas_qs.exclude(presenca=None)
    total_presencas   = aulas_com_registo.filter(presenca=True).count()
    total_faltas      = aulas_com_registo.filter(presenca=False).count()
    total_aulas       = aulas_com_registo.count()
    percentagem       = (
        round(total_presencas / total_aulas * 100)
        if total_aulas > 0 else 0
    )

    # ── Próxima aula ─────────────────────────────────────────
    proxima_aula = (
        aulas_qs
        .filter(data_inicio__gt=agora)
        .order_by('data_inicio')
        .first()
    )

    # ── Aulas recentes — últimas 5 passadas ──────────────────
    aulas_recentes = (
        aulas_qs
        .filter(data_inicio__lte=agora)
        .order_by('-data_inicio')[:5]
    )

    # ── Dados para o calendário (injectados no template) ─────
    # Opção B confirmada — sem AJAX
    eventos_calendario = []
    for ada in aulas_qs:
        if ada.data_inicio:
            curso_nome = ''
            if ada.id_aula and ada.id_aula.id_curso:
                curso_nome = ada.id_aula.id_curso.nome or ''

            eventos_calendario.append({
                'data':        ada.data_inicio.strftime('%Y-%m-%d'),
                'hora_inicio': ada.data_inicio.strftime('%H:%M'),
                'hora_fim':    (
                    ada.data_final.strftime('%H:%M')
                    if ada.data_final else ''
                ),
                'presenca':    ada.presenca,
                'curso':       curso_nome,
            })

    return render(request, 'escola_musica/aluno_dashboard.html', {
        'aluno':            aluno,
        'matriculas':       matriculas,
        'total_presencas':  total_presencas,
        'total_faltas':     total_faltas,
        'total_aulas':      total_aulas,
        'percentagem':      percentagem,
        'proxima_aula':     proxima_aula,
        'aulas_recentes':   aulas_recentes,
        'eventos_calendario': eventos_calendario,
    })


@login_required
def professor_dashboard(request):
    """
    Dashboard do professor.
    Segurança: todos os dados filtrados por request.user.professor.
    Nunca expõe dados de outro professor.
    Nunca expõe dados pessoais sensíveis dos alunos (só nome e presença).
    """

    # ── Protecção de acesso ───────────────────────────────────
    if not hasattr(request.user, 'professor'):
        messages.error(request, "Acesso restrito a professores.")
        return redirect('login_professor')

    professor = request.user.professor
    agora     = timezone.now()
    hoje      = agora.date()

    # ── Aulas deste professor ─────────────────────────────────
    # Base queryset — todas as aulas deste professor
    # Filtra estritamente por id_professor — sem acesso cruzado
    aulas_professor = (
        Aula.objects
        .filter(id_professor=professor)
        .select_related(
            'id_turma',
            'id_curso',
            'id_sala',
            'id_tipoaula',
        )
    )

    ids_aulas = aulas_professor.values_list('id_aula', flat=True)

    # ── KPI 1: Total de alunos ativos ────────────────────────
    # Alunos matriculados nas turmas deste professor
    # Via Matricula → Turma → Aula (do professor)
    ids_turmas = aulas_professor.values_list(
        'id_turma', flat=True
    ).distinct()

    total_alunos_ativos = (
        Matricula.objects
        .filter(id_turma__in=ids_turmas)
        .values('id_aluno')
        .distinct()
        .count()
    )

    # ── KPI 2: Aulas este mês ────────────────────────────────
    mes_inicio = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if mes_inicio.month == 12:
        proximo_mes = mes_inicio.replace(year=mes_inicio.year + 1, month=1)
    else:
        proximo_mes = mes_inicio.replace(month=mes_inicio.month + 1)

    aulas_mes = (
        AulaDoAluno.objects
        .filter(
            id_aula__in=ids_aulas,
            data_inicio__gte=mes_inicio,
            data_inicio__lt=proximo_mes,
        )
        .values('id_aula', 'data_inicio')
        .distinct()
        .count()
    )
    # ── KPI 3: Taxa de assiduidade ───────────────────────────
    # Percentagem de presenças nas aulas deste professor
    registos_presenca = AulaDoAluno.objects.filter(
        id_aula__in=ids_aulas,
        presenca__isnull=False,
    )
    total_registos  = registos_presenca.count()
    total_presencas = registos_presenca.filter(presenca=True).count()
    taxa_assiduidade = (
        round(total_presencas / total_registos * 100)
        if total_registos > 0 else 0
    )

    # ── Próximas aulas ────────────────────────────────────────
    proximas_qs = (
        AulaDoAluno.objects
        .filter(
            id_aula__in=ids_aulas,
            data_inicio__gt=agora,
        )
        .select_related(
            'id_aula',
            'id_aula__id_turma',
            'id_aula__id_curso',
            'id_aula__id_sala',
            'id_aula__id_tipoaula',
        )
        .order_by('data_inicio')
    )

    proximas_aulas = []
    aulas_vistas = set()

    for aula_aluno in proximas_qs:
        chave = (aula_aluno.id_aula_id, aula_aluno.data_inicio)

        if chave in aulas_vistas:
            continue

        aulas_vistas.add(chave)
        proximas_aulas.append(aula_aluno)

        if len(proximas_aulas) == 5:
            break

    # ── Turmas com alunos ─────────────────────────────────────
    turmas_com_alunos = []
    for id_turma in ids_turmas:
        try:
            from .models import Turma
            turma = Turma.objects.select_related('id_curso').get(
                pk=id_turma
            )
            alunos = (
                Matricula.objects
                .filter(id_turma=turma)
                .select_related('id_aluno')
                # Só expõe nome — sem dados pessoais sensíveis
                .values(
                    'id_aluno__id_aluno',
                    'id_aluno__nome',
                )
            )
            # Assiduidade por turma
            aulas_turma = aulas_professor.filter(
                id_turma=turma
            ).values_list('id_aula', flat=True)

            reg_turma    = AulaDoAluno.objects.filter(
                id_aula__in=aulas_turma,
                presenca__isnull=False,
            )
            pres_turma   = reg_turma.filter(presenca=True).count()
            total_turma  = reg_turma.count()
            assiduidade_turma = (
                round(pres_turma / total_turma * 100)
                if total_turma > 0 else None
            )

            turmas_com_alunos.append({
                'turma':         turma,
                'alunos':        list(alunos),
                'total_alunos':  alunos.count(),
                'assiduidade':   assiduidade_turma,
            })
        except Exception:
            continue

    # ── Sumários (livro de sumários) ──────────────────────────
    # Últimas 10 aulas com conteudo preenchido
    sumarios = (
        aulas_professor
        .exclude(conteudo=None)
        .exclude(conteudo='')
        .order_by('-id_aula')[:10]
    )

    # ── Dados para gráficos ───────────────────────────────────
    # Ano letivo: Setembro 2025 – Julho 2026
    ano_letivo_inicio = timezone.make_aware(
        dt.datetime(2025, 9, 1, 0, 0, 0)
    )
    ano_letivo_fim = timezone.make_aware(
        dt.datetime(2026, 7, 31, 23, 59, 59)
    )

    # Aulas dadas por mês (linha)
    aulas_por_mes = (
        AulaDoAluno.objects
        .filter(
            id_aula__in=ids_aulas,
            data_inicio__gte=ano_letivo_inicio,
            data_inicio__lte=ano_letivo_fim,
            data_inicio__isnull=False,
        )
        .annotate(mes=TruncMonth('data_inicio'))
        .values('mes')
        .annotate(total=Count('pk'))
        .order_by('mes')
    )

    grafico_linha = [
        {
            'mes':   item['mes'].strftime('%b %Y') if item['mes'] else '',
            'total': item['total'],
        }
        for item in aulas_por_mes
    ]

    # Alunos por turma (barras)
    grafico_barras = [
        {
            'turma': t['turma'].nome_turma or 'Turma',
            'total': t['total_alunos'],
        }
        for t in turmas_com_alunos
    ]

    return render(request, 'escola_musica/professor_dashboard.html', {
        'professor':           professor,
        'total_alunos_ativos': total_alunos_ativos,
        'aulas_mes':           aulas_mes,
        'taxa_assiduidade':    taxa_assiduidade,
        'taxa_faltas':         100 - taxa_assiduidade,
        'proximas_aulas':      proximas_aulas,
        'turmas_com_alunos':   turmas_com_alunos,
        'sumarios':            sumarios,
        # Listas Python — json_script trata a serialização no template
        'grafico_linha':       grafico_linha,
        'grafico_barras':      grafico_barras,
    })

# ─────────────────────────────────────────
# ÁREA PROTEGIDA
# ─────────────────────────────────────────

@login_required
@requer_acesso_matriculas
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
@requer_acesso_matriculas
def matricula_nova(request):
    """
    GET -> formulário com dados do aluno, matrícula e pagamento.

    POST -> valida os formulários, valida regras cruzadas, procura/cria
    o aluno de forma segura, guarda os dados em session e redireciona.

    Regra de duplicado:
    o mesmo aluno não pode ter duas matrículas no mesmo curso.
    """

    form_aluno = AlunoForm(request.POST or None)
    form_matricula = MatriculaForm(request.POST or None)
    form_pagamento = PagamentoForm(
        request.POST or None,
        utilizador=request.user,
    )

    if request.method == "POST":
        aluno_valido = form_aluno.is_valid()
        matricula_valida = form_matricula.is_valid()
        pagamento_valido = form_pagamento.is_valid()

        if aluno_valido and matricula_valida and pagamento_valido:
            cd_a = form_aluno.cleaned_data
            cd_m = form_matricula.cleaned_data
            cd_p = form_pagamento.cleaned_data

            nome = cd_a["nome"].strip()
            email = (
                cd_a.get("email", "").strip().lower()
                if cd_a.get("email")
                else None
            )
            curso = cd_m["id_curso"]
            turma = cd_m["id_turma"]

            data_matricula = cd_m.get("data_matricula")
            data_pagamento = cd_p.get("data_pagamento")

            if data_matricula and data_pagamento and data_pagamento < data_matricula:
                form_pagamento.add_error(
                    "data_pagamento",
                    (
                        f"A data de pagamento ({data_pagamento.strftime('%d/%m/%Y')}) "
                        f"não pode ser anterior à data de matrícula "
                        f"({data_matricula.strftime('%d/%m/%Y')})."
                    ),
                )
            else:
                aluno = None
                criado = False

                if email:
                    aluno = Aluno.objects.filter(email__iexact=email).first()

                if aluno:
                    duplicado_curso = Matricula.objects.filter(
                        id_aluno=aluno,
                        id_curso=curso,
                    ).exists()

                    if duplicado_curso:
                        form_matricula.add_error(
                            None,
                            (
                                f"O aluno '{aluno.nome}' já está matriculado "
                                f"no curso '{curso.nome}'. "
                                "Não é possível criar uma segunda matrícula "
                                "no mesmo curso."
                            ),
                        )
                    else:
                        with transaction.atomic():
                            if not aluno.email and email:
                                aluno.email = email

                            aluno.nome = aluno.nome or nome

                            if not aluno.telefone and cd_a.get("telefone"):
                                aluno.telefone = cd_a.get("telefone")

                            if not aluno.data_nascimento and cd_a.get("data_nascimento"):
                                aluno.data_nascimento = cd_a.get("data_nascimento")

                            aluno.save()

                            if aluno.email:
                                associar_user_aluno(aluno)

                            request.session["matricula_pendente"] = {
                                "aluno_id": aluno.pk,
                                "aluno_nome": aluno.nome,
                                "aluno_criado": criado,
                                "aluno_email": aluno.email or "—",
                                "aluno_telefone": aluno.telefone or "—",
                                "aluno_nascimento": (
                                    aluno.data_nascimento.strftime("%d/%m/%Y")
                                    if aluno.data_nascimento else "—"
                                ),
                                "curso_id": curso.pk,
                                "curso_nome": curso.nome,
                                "turma_id": turma.pk,
                                "turma_nome": turma.nome_turma,
                                "data_matricula": (
                                    data_matricula.isoformat()
                                    if data_matricula else None
                                ),
                                "ano_letivo": cd_m["ano_letivo"],
                                "data_pagamento": (
                                    data_pagamento.isoformat()
                                    if data_pagamento else None
                                ),
                                "valor_pago": str(cd_p["valor_pago"]),
                                "status": cd_p["status"],
                            }

                        return redirect("matriculas_lista")

                else:
                    with transaction.atomic():
                        aluno = Aluno.objects.create(
                            nome=nome,
                            email=email,
                            telefone=cd_a.get("telefone"),
                            data_nascimento=cd_a.get("data_nascimento"),
                        )
                        criado = True

                        if aluno.email:
                            associar_user_aluno(aluno)

                        request.session["matricula_pendente"] = {
                            "aluno_id": aluno.pk,
                            "aluno_nome": aluno.nome,
                            "aluno_criado": criado,
                            "aluno_email": aluno.email or "—",
                            "aluno_telefone": aluno.telefone or "—",
                            "aluno_nascimento": (
                                aluno.data_nascimento.strftime("%d/%m/%Y")
                                if aluno.data_nascimento else "—"
                            ),
                            "curso_id": curso.pk,
                            "curso_nome": curso.nome,
                            "turma_id": turma.pk,
                            "turma_nome": turma.nome_turma,
                            "data_matricula": (
                                data_matricula.isoformat()
                                if data_matricula else None
                            ),
                            "ano_letivo": cd_m["ano_letivo"],
                            "data_pagamento": (
                                data_pagamento.isoformat()
                                if data_pagamento else None
                            ),
                            "valor_pago": str(cd_p["valor_pago"]),
                            "status": cd_p["status"],
                        }

                    return redirect("matriculas_lista")

        messages.warning(
            request,
            "Corrige os erros assinalados antes de submeter.",
        )

    return render(request, "escola_musica/matricula_nova.html", {
        "form_aluno": form_aluno,
        "form_matricula": form_matricula,
        "form_pagamento": form_pagamento,
        "turmas_json": Turma.objects.select_related("id_curso").order_by("nome_turma"),
    })

@login_required
@requer_acesso_matriculas
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
@requer_acesso_matriculas
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
@requer_acesso_matriculas
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
@requer_acesso_matriculas
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
                        "atualizada com sucesso."
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
                        "Não foi possível atualizar. Tenta novamente."
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
@requer_acesso_matriculas
def matricula_eliminar(request, pk):
    """
    Apenas superutilizadores podem eliminar matrículas.
    GET  → página de confirmação
    POST → elimina matrícula e pagamento associado.
           Se for a última matrícula do aluno,
           desativa automaticamente a conta.
    """
    contas_logger = logging.getLogger('contas_log')

    if not request.user.is_superuser:
        messages.error(
            request,
            "Não tens permissão para eliminar matrículas. "
            "Esta ação está reservada a administradores."
        )
        return redirect('matriculas_lista')

    matricula = get_object_or_404(
        Matricula.objects.select_related(
            'id_aluno',
            'id_curso',
            'id_turma',
            'id_pagamento',
            'id_aluno__user',
        ),
        pk=pk
    )

    if request.method == 'POST':
        try:
            with transaction.atomic():
                pagamento = matricula.id_pagamento
                id_matricula = matricula.id_matricula
                aluno = matricula.id_aluno
                nome_aluno = aluno.nome if aluno else '—'

                matricula.delete()

                if pagamento:
                    pagamento_em_uso = Matricula.objects.filter(
                        id_pagamento=pagamento
                    ).exists()

                    if not pagamento_em_uso:
                        pagamento.delete()

                conta_desativada = False

                if aluno:
                    matriculas_restantes = Matricula.objects.filter(
                        id_aluno=aluno
                    ).count()

                    user_aluno = getattr(aluno, 'user', None)

                    if (
                        matriculas_restantes == 0
                        and user_aluno
                        and user_aluno.is_active
                        and not user_aluno.is_staff
                        and not user_aluno.is_superuser
                    ):
                        user_aluno.is_active = False
                        user_aluno.save(update_fields=['is_active'])

                        conta_desativada = True

                        contas_logger.info(
                            f"[DESATIVAR] "
                            f"actor={request.user.username} | "
                            f"alvo={user_aluno.username} | "
                            f"motivo=ultima_matricula_eliminada | "
                            f"matricula_id={id_matricula} | "
                            f"aluno={nome_aluno}"
                        )

            if conta_desativada:
                messages.warning(
                    request,
                    f"Matrícula #{id_matricula} eliminada. "
                    f"Era a última matrícula de '{nome_aluno}'. "
                    f"a conta de acesso foi desativada automaticamente."
                )
            else:
                messages.success(
                    request,
                    f"Matrícula #{id_matricula} do aluno "
                    f"'{nome_aluno}' eliminada com sucesso."
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