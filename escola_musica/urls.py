from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.mainpage,                  name='mainpage'),
    path('login/',                        views.login_view,                name='login'),
    path('logout/',                       views.logout_view,               name='logout'),
    path('matriculas/',                   views.matriculas_lista,          name='matriculas_lista'),
    path('matriculas/nova/',              views.matricula_nova,            name='matricula_nova'),
    path('matriculas/confirmar/',         views.matricula_confirmar,       name='matricula_confirmar'),
    path('matriculas/cancelar/',          views.matricula_cancelar,        name='matricula_cancelar_pendente'),
    path('matriculas/<int:pk>/',          views.matricula_detalhe,         name='matricula_detalhe'),
    path('matriculas/<int:pk>/editar/',   views.matricula_editar,          name='matricula_editar'),
]