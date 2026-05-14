"""
Backend de autenticação por email para alunos e professores.
Reutiliza o sistema nativo do Django — sem código paralelo.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailBackend(ModelBackend):
    """
    Autentica utilizadores pelo email em vez do username.
    Compatível com admins (cujo username pode ser o email),
    alunos e professores.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        username aqui contém o email introduzido pelo utilizador.
        Procura o User cujo username == email introduzido.
        """
        if not username or not password:
            return None

        email = username.strip().lower()

        try:
            # Procura pelo username (que é o email para alunos/professores)
            # ou pelo email do campo email (para admins criados pelo admin)
            user = User.objects.filter(username=email).first()
            if not user:
                user = User.objects.filter(email=email).first()
            if not user:
                return None
        except Exception:
            return None

        # Verifica a password e se o utilizador está activo
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None