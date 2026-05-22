"""
Forms do Painel de Gestão de Utilizadores.
Campos explícitos em todos os forms — protecção mass assignment.
is_superuser NUNCA incluído em nenhum form.
"""
from django import forms
from .models import Aluno, Professor
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class GestaoLoginForm(forms.Form):
    """
    Form de login do painel.
    Email + password com validação básica.
    """
    email = forms.EmailField(
        label='Email',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class':        'campo-input',
            'placeholder':  'O teu email',
            'autocomplete': 'email',
            'autofocus':    True,
        }),
        error_messages={
            'required': 'O email é obrigatório.',
            'invalid':  'Introduz um email válido.',
        },
    )

    password = forms.CharField(
        label='Palavra-passe',
        widget=forms.PasswordInput(attrs={
            'class':        'campo-input',
            'placeholder':  '••••••••',
            'autocomplete': 'current-password',
        }),
        error_messages={
            'required': 'A palavra-passe é obrigatória.',
        },
    )

    def clean_email(self):
        return self.cleaned_data.get('email', '').strip().lower()


class UtilizadorCriarForm(forms.ModelForm):
    """
    Criação de utilizador pelo painel.
    Campos explícitos — is_superuser NUNCA incluído.
    is_staff só disponível para superutilizadores.
    """
    password1 = forms.CharField(
        label='Palavra-passe',
        widget=forms.PasswordInput(attrs={'class': 'campo-input'}),
        error_messages={'required': 'A palavra-passe é obrigatória.'},
    )

    password2 = forms.CharField(
        label='Confirmar palavra-passe',
        widget=forms.PasswordInput(attrs={'class': 'campo-input'}),
        error_messages={'required': 'Confirma a palavra-passe.'},
    )

    class Meta:
        model  = User
        # is_superuser NUNCA aqui
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'campo-input'}),
            'email':      forms.EmailInput(attrs={'class': 'campo-input'}),
            'first_name': forms.TextInput(attrs={'class': 'campo-input'}),
            'last_name':  forms.TextInput(attrs={'class': 'campo-input'}),
        }
        labels = {
            'username':   'Nome de utilizador',
            'email':      'Email',
            'first_name': 'Primeiro nome',
            'last_name':  'Apelido',
        }
        error_messages = {
            'username': {'required': 'O nome de utilizador é obrigatório.'},
            'email':    {'required': 'O email é obrigatório.'},
        }

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields['email'].required = True

        # is_staff só disponível para superutilizadores
        if actor and actor.is_superuser:
            self.fields['is_staff'] = forms.BooleanField(
                label='Acesso staff (administrativo)',
                required=False,
                widget=forms.CheckboxInput(),
            )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Já existe uma conta com este email.")
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Introduz um email válido.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username=username).exists():
            raise ValidationError("Já existe um utilizador com este nome.")
        return username

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1', '')
        p2 = self.cleaned_data.get('password2', '')
        if p1 and p2 and p1 != p2:
            raise ValidationError("As palavras-passe não coincidem.")
        try:
            validate_password(p2)
        except ValidationError as e:
            raise ValidationError(list(e.messages))
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        # Garante que is_superuser nunca é definido por este form
        user.is_superuser = False
        if hasattr(self, 'cleaned_data') and 'is_staff' in self.cleaned_data:
            user.is_staff = self.cleaned_data['is_staff']
        else:
            user.is_staff = False
        if commit:
            user.save()
        return user
    

class PasswordForm(forms.Form):
    """
    Formulário de alteração de password — processado inline no form principal.
    Validado no backend mesmo que venha de hidden fields injectados por JS.
    """
    nova_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(),
        label='Nova palavra-passe',
    )
    confirmar_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(),
        label='Confirmar palavra-passe',
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user   # necessário para validate_password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('nova_password', '').strip()
        p2 = cleaned.get('confirmar_password', '').strip()

        if not p1 and not p2:
            # Ambos vazios — sem alteração de password, OK
            return cleaned

        if p1 != p2:
            raise ValidationError(
                "As palavras-passe não coincidem."
            )

        # Usa validate_password() do Django —
        # respeita AUTH_PASSWORD_VALIDATORS do settings.py
        # sem duplicar lógica
        try:
            validate_password(p1, user=self.user)
        except ValidationError as e:
            raise ValidationError(list(e.messages))

        cleaned['password_validada'] = p1
        return cleaned


class UtilizadorEditarForm(forms.ModelForm):
    """
    Edição de dados do utilizador.
    Password gerida separadamente via PasswordForm.
    is_superuser NUNCA editável — preservado da BD no save().
    is_staff só para superutilizadores.
    Mass assignment: campos explícitos — sem __all__.
    """

    class Meta:
        model  = User
        # is_active removido — gerido pelo card de estado (acção toggle)
        # is_superuser NUNCA aqui
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'campo-input'}),
            'last_name':  forms.TextInput(attrs={'class': 'campo-input'}),
            'email':      forms.EmailInput(attrs={'class': 'campo-input'}),
        }
        labels = {
            'first_name': 'Primeiro nome',
            'last_name':  'Apelido',
            'email':      'Email',
        }
        error_messages = {
            'email': {'required': 'O email é obrigatório.'},
        }

    def __init__(self, *args, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor
        self.fields['email'].required = True

        # is_staff só visível e editável por superutilizadores
        if actor and actor.is_superuser:
            self.fields['is_staff'] = forms.BooleanField(
                label='Acesso staff',
                required=False,
                initial=self.instance.is_staff if self.instance else False,
                widget=forms.CheckboxInput(),
            )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError("Já existe outra conta com este email.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Protecção: is_superuser NUNCA alterado por este form
        if self.instance.pk:
            original      = User.objects.get(pk=self.instance.pk)
            user.is_superuser = original.is_superuser
            # is_active preservado — gerido exclusivamente pelo toggle
            user.is_active = original.is_active
        # is_staff só para superutilizadores
        if 'is_staff' in self.cleaned_data and self.actor \
                and self.actor.is_superuser:
            user.is_staff = self.cleaned_data['is_staff']
        if commit:
            user.save()
        return user

class GruposForm(forms.Form):
    """
    Atribuição de grupos — apenas grupos existentes.
    """
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Grupos',
    )


class AssociarPerfilForm(forms.Form):
    """
    Associa um User a um Aluno ou Professor existente.
    O utilizador (alvo_user) já está definido na URL — aqui seleccionamos
    o perfil (Aluno ou Professor) a associar.
    """
    TIPO_CHOICES = [
        ('aluno',     'Aluno'),
        ('professor', 'Professor'),
    ]

    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        label='Tipo de perfil',
        widget=forms.Select(attrs={
            'class':    'campo-input',
            'id':       'id_tipo',
        }),
        error_messages={'required': 'Seleciona o tipo de perfil.'},
    )

    perfil_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=False,
    )

    # Selects dinâmicos — preenchidos no __init__
    aluno_id = forms.ModelChoiceField(
        queryset=Aluno.objects.none(),
        label='Aluno',
        empty_label='— Seleciona o aluno —',
        required=False,
        widget=forms.Select(attrs={'class': 'campo-input', 'id': 'id_aluno_id'}),
    )

    professor_id = forms.ModelChoiceField(
        queryset=Professor.objects.none(),
        label='Professor',
        empty_label='— Seleciona o professor —',
        required=False,
        widget=forms.Select(attrs={'class': 'campo-input', 'id': 'id_professor_id'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só alunos sem user associado
        self.fields['aluno_id'].queryset = (
            Aluno.objects
            .filter(user__isnull=True)
            .order_by('nome')
        )
        # Só professores sem user associado
        self.fields['professor_id'].queryset = (
            Professor.objects
            .filter(user__isnull=True)
            .order_by('nome')
        )

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')

        if tipo == 'aluno':
            aluno = cleaned.get('aluno_id')
            if not aluno:
                raise ValidationError("Seleciona o aluno a associar.")
            cleaned['perfil_id'] = aluno.pk
        elif tipo == 'professor':
            professor = cleaned.get('professor_id')
            if not professor:
                raise ValidationError("Seleciona o professor a associar.")
            cleaned['perfil_id'] = professor.pk

        return cleaned