from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.http import require_POST


def mainpage(request):
    """Página principal pública — ponto de entrada da aplicação."""
    return render(request, 'escola_musica/mainpage.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('matriculas_lista')

    form = AuthenticationForm(request, data=request.POST or None)

    # Aplicar atributos HTML aos campos para o CSS funcionar
    form.fields['username'].widget.attrs.update({
        'placeholder': 'Nome de utilizador',
        'autocomplete': 'username',
        'class': 'campo-input',
    })
    form.fields['password'].widget.attrs.update({
        'placeholder': '••••••••',
        'autocomplete': 'current-password',
        'class': 'campo-input',
    })

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('matriculas_lista')

    return render(request, 'escola_musica/login.html', {'form': form})

@require_POST
def logout_view(request):
    """
    Termina a sessão do utilizador.
    Apenas aceita POST para proteger contra CSRF via GET.
    Redireciona para a mainpage.
    """
    logout(request)
    return redirect('mainpage')