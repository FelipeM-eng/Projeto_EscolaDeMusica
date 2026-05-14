from django.urls import path
from . import views

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
]