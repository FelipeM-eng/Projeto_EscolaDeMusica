import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import IntegrityError, DatabaseError

from .models import Matricula, Pagamento, Aluno, Curso, Turma
from .forms import MatriculaForm, PagamentoForm, PagamentoEdicaoForm

logger = logging.getLogger('escola_musica')


# ─────────────────────────────────────────
# PÁGINAS PÚBLICAS
# ─────────────────────────────────────────

def mainpage(request):
    return render(request, 'escola_musica/mainpage.html')


def login_view(request):
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
    logout(request)
    return redirect('mainpage')



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
    GET  → formulário em branco
    POST → valida TUDO no backend;
           se válido, guarda dados em session e redireciona
           para lista com modal de confirmação.
           A BD NÃO é tocada ainda.
    """
    form_matricula = MatriculaForm(request.POST or None)
    form_pagamento = PagamentoForm(
        request.POST or None,
        utilizador=request.user      # ← passa utilizador para validação de retroactividade
    )

    if request.method == 'POST':
        mat_valida = form_matricula.is_valid()
        pag_valido = form_pagamento.is_valid()

        if mat_valida and pag_valido:
            # Recolhe os dados limpos para guardar em session
            cd_m = form_matricula.cleaned_data
            cd_p = form_pagamento.cleaned_data

            aluno = cd_m['id_aluno']
            curso = cd_m['id_curso']
            turma = cd_m['id_turma']

            # Guarda dados em session — ainda NÃO grava na BD
            request.session['matricula_pendente'] = {
                'aluno_id':       aluno.pk,
                'aluno_nome':     aluno.nome,
                'curso_id':       curso.pk,
                'curso_nome':     curso.nome,
                'turma_id':       turma.pk,
                'turma_nome':     turma.nome_turma,
                'data_matricula': cd_m['data_matricula'].isoformat()
                                  if cd_m.get('data_matricula') else None,
                'ano_letivo':     cd_m['ano_letivo'],
                'data_pagamento': cd_p['data_pagamento'].isoformat()
                                  if cd_p.get('data_pagamento') else None,
                'valor_pago':     str(cd_p['valor_pago']),
                'status':         cd_p['status'],
            }
            # Redireciona para a lista — a modal abre automaticamente
            return redirect('matriculas_lista')

    return render(request, 'escola_musica/matricula_nova.html', {
        'form_matricula': form_matricula,
        'form_pagamento': form_pagamento,
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
    Chamado quando o utilizador clica CONFIRMAR na modal.
    Lê os dados da session e grava efectivamente na BD.
    Limpa a session após uso (sucesso ou erro).
    """
    pendente = request.session.pop('matricula_pendente', None)

    if not pendente:
        messages.error(request, "Não existe matrícula pendente de confirmação.")
        return redirect('matriculas_lista')

    try:
        # Recupera os objectos da BD pelos IDs guardados em session
        aluno = Aluno.objects.get(pk=pendente['aluno_id'])
        curso = Curso.objects.get(pk=pendente['curso_id'])
        turma = Turma.objects.get(pk=pendente['turma_id'])

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
            f"IntegrityError ao confirmar matrícula | "
            f"user={request.user.username} | erro={e}"
        )
        messages.error(
            request,
            "Não foi possível registar: este aluno já está inscrito "
            "neste curso e turma."
        )

    except DatabaseError as e:
        logger.error(
            f"DatabaseError ao confirmar matrícula | "
            f"user={request.user.username} | erro={e}"
        )
        messages.error(
            request,
            "Não foi possível concluir a matrícula. "
            "Verifica se o pagamento está regularizado."
        )

    except Exception as e:
        logger.error(
            f"Erro inesperado ao confirmar matrícula | "
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
    matricula = get_object_or_404(Matricula, pk=pk)
    pagamento = matricula.id_pagamento

    form_matricula = MatriculaForm(
        request.POST or None,
        instance=matricula
    )
    form_pagamento = PagamentoEdicaoForm(
        request.POST or None,
        instance=pagamento,
        utilizador=request.user      # ← passa utilizador
    )

    if request.method == 'POST':
        mat_valida = form_matricula.is_valid()
        pag_valido = form_pagamento.is_valid()

        if mat_valida and pag_valido:
            try:
                pag_actualizado = form_pagamento.save()
                mat_actualizada = form_matricula.save(commit=False)
                mat_actualizada.id_pagamento = pag_actualizado
                mat_actualizada.save()

                messages.success(
                    request,
                    f"Matrícula #{matricula.id_matricula} actualizada com sucesso."
                )
                return redirect('matricula_detalhe', pk=matricula.pk)

            except IntegrityError as e:
                logger.error(
                    f"IntegrityError ao editar pk={pk} | "
                    f"user={request.user.username} | erro={e}"
                )
                messages.error(
                    request,
                    "Já existe uma matrícula com este aluno, curso e turma."
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
                messages.error(request, "Erro inesperado. Contacta o administrador.")

        else:
            messages.warning(request, "Corrige os erros antes de guardar.")

    return render(request, 'escola_musica/matricula_editar.html', {
        'form_matricula': form_matricula,
        'form_pagamento': form_pagamento,
        'matricula':      matricula,
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