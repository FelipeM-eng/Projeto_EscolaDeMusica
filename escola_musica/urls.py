from django.urls import path
from . import views, gestao_views

urlpatterns = [
    # ── Páginas públicas ──────────────────────────────────────
    path('',                                views.mainpage,            name='mainpage'),

    # Login administrativo (admin/staff)
    path('login/',                          views.login_view,          name='login'),
    path('logout/',                         views.logout_view,         name='logout'),

    # Login de alunos
    path('aluno/login/',                    views.login_aluno,         name='login_aluno'),

    # Login de professores
    path('professor/login/',                views.login_professor,     name='login_professor'),

    # ── Dashboards ────────────────────────────────────────────
    path('aluno/dashboard/',                views.aluno_dashboard,     name='aluno_dashboard'),
    path('professor/dashboard/',            views.professor_dashboard, name='professor_dashboard'),

    # ── Área administrativa — matrículas ─────────────────────
    path('matriculas/',                     views.matriculas_lista,    name='matriculas_lista'),
    path('matriculas/nova/',                views.matricula_nova,      name='matricula_nova'),
    path('matriculas/confirmar/',           views.matricula_confirmar, name='matricula_confirmar'),
    path('matriculas/cancelar/',            views.matricula_cancelar,  name='matricula_cancelar_pendente'),
    path('matriculas/<int:pk>/',            views.matricula_detalhe,   name='matricula_detalhe'),
    path('matriculas/<int:pk>/editar/',     views.matricula_editar,    name='matricula_editar'),
    path('matriculas/<int:pk>/eliminar/',   views.matricula_eliminar,  name='matricula_eliminar'),

    # ── Painel de Gestão de Utilizadores ─────────────────────
    path('gestaoutilizadores/',                                         views.gestao_redirect,                              name='gestao_redirect'),
    path('gestaoutilizadores/login/',                                   gestao_views.gestao_login,                          name='gestao_login'),
    path('gestaoutilizadores/logout/',                                  gestao_views.gestao_logout,                         name='gestao_logout'),
    path('gestaoutilizadores/utilizadores/',                            gestao_views.gestao_lista,                          name='gestao_lista'),
    path('gestaoutilizadores/utilizadores/criar/',                      gestao_views.gestao_utilizador_criar,               name='gestao_utilizador_criar'),
    path('gestaoutilizadores/utilizadores/<int:pk>/editar/',            gestao_views.gestao_utilizador_editar,              name='gestao_utilizador_editar'),
    path('gestaoutilizadores/utilizadores/<int:pk>/grupos/',            gestao_views.gestao_utilizador_grupos,              name='gestao_utilizador_grupos'),
    path('gestaoutilizadores/utilizadores/<int:pk>/toggle/',            gestao_views.gestao_utilizador_toggle,              name='gestao_utilizador_toggle'),
    path('gestaoutilizadores/utilizadores/<int:pk>/associar/',          gestao_views.gestao_utilizador_associar,            name='gestao_utilizador_associar'),
    path('gestaoutilizadores/utilizadores/<int:pk>/remover/',           gestao_views.gestao_utilizador_remover,             name='gestao_utilizador_remover'),
    path('gestaoutilizadores/utilizadores/<int:pk>/confirmar/',         gestao_views.gestao_utilizador_confirmar,           name='gestao_utilizador_confirmar'),
    path('gestaoutilizadores/utilizadores/<int:pk>/cancelar-edicao/',   gestao_views.gestao_utilizador_cancelar_edicao,     name='gestao_utilizador_cancelar_edicao'),
]