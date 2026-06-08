"""
Management command: limpar_contas_inativas
Elimina contas de utilizadores que estão inativas há mais de 1 ano.
Lê o ficheiro logs/contas.log para determinar a data de desativação.
Só elimina contas de alunos — nunca staff ou superutilizadores.

Uso:
    python manage.py limpar_contas_inativas
    python manage.py limpar_contas_inativas --simulacao   (dry run)
"""

import logging
import re
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import os

logger       = logging.getLogger('escola_musica')
contas_logger = logging.getLogger('contas_log')


class Command(BaseCommand):
    help = 'Elimina contas de alunos inativas há mais de 1 ano.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--simulacao',
            action='store_true',
            help='Mostra o que seria eliminado sem executar.',
        )

    def handle(self, *args, **options):
        simulacao = options['simulacao']
        agora     = timezone.now()
        limite    = agora - timedelta(days=365)

        self.stdout.write(
            self.style.WARNING(
                f"{'[SIMULAÇÃO] ' if simulacao else ''}"
                f"A verificar contas inativas antes de {limite.strftime('%d/%m/%Y')}..."
            )
        )

        # ── Lê datas de desativação do contas.log ────────────────
        datas_desativacao = self._ler_datas_desativacao()

        eliminadas  = 0
        ignoradas   = 0
        erros       = 0

        # ── Processa utilizadores inativos ───────────────────────
        # Nunca toca em staff ou superutilizadores
        usuarios_inativos = (
            User.objects
            .filter(
                is_active=False,
                is_staff=False,
                is_superuser=False,
            )
        )

        for user in usuarios_inativos:

            # Determina a data de desativação
            data_desativ = datas_desativacao.get(user.username)

            # Fallback: usa last_login ou date_joined se não há registo no log
            if not data_desativ:
                data_desativ = user.last_login or user.date_joined

            # Só elimina se inativo há mais de 1 ano
            if not data_desativ or data_desativ > limite:
                ignoradas += 1
                continue

            # Confirma que é um aluno (nunca elimina staff/professores)
            eh_aluno = hasattr(user, 'aluno')
            if not eh_aluno:
                self.stdout.write(
                    f"  IGNORADO (não é aluno): {user.username}"
                )
                ignoradas += 1
                continue

            # Confirma que não tem matrículas activas
            from escola_musica.models import Matricula
            tem_matriculas = False
            try:
                tem_matriculas = Matricula.objects.filter(
                    id_aluno=user.aluno
                ).exists()
            except Exception:
                pass

            if tem_matriculas:
                self.stdout.write(
                    f"  IGNORADO (tem matrículas): {user.username}"
                )
                ignoradas += 1
                continue

            # ── Elimina ───────────────────────────────────────────
            if simulacao:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [SIMULAÇÃO] Seria eliminado: {user.username} "
                        f"(inativo desde {data_desativ.strftime('%d/%m/%Y')})"
                    )
                )
                eliminadas += 1
                continue

            try:
                with transaction.atomic():
                    username_log = user.username
                    user.delete()

                    contas_logger.info(
                        f"[ELIMINAR] "
                        f"actor=sistema | "
                        f"alvo={username_log} | "
                        f"motivo=inativo_ha_mais_de_1_ano | "
                        f"data_desativacao={data_desativ.strftime('%Y-%m-%d')}"
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ELIMINADO: {username_log} "
                            f"(inativo desde "
                            f"{data_desativ.strftime('%d/%m/%Y')})"
                        )
                    )
                    eliminadas += 1

            except Exception as e:
                logger.error(
                    f"Erro ao eliminar conta {user.username}: {e}"
                )
                self.stdout.write(
                    self.style.ERROR(f"  ERRO: {user.username} — {e}")
                )
                erros += 1

        # ── Resumo ────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f"{'[SIMULAÇÃO] ' if simulacao else ''}"
                f"Concluído — "
                f"{'a eliminar' if simulacao else 'eliminadas'}: {eliminadas} | "
                f"ignoradas: {ignoradas} | "
                f"erros: {erros}"
            )
        )

    def _ler_datas_desativacao(self):
        """
        Lê o ficheiro contas.log e extrai a data mais recente
        de desativação para cada username.
        Formato esperado:
        [INFO] 2025-06-01 10:30:00,000 gestao_views: [DESATIVAR] ... alvo=username ...
        """
        datas = {}
        log_path = os.path.join(settings.BASE_DIR, 'logs', 'contas.log')

        if not os.path.exists(log_path):
            return datas

        # Regex para extrair timestamp e username do log
        padrao = re.compile(
            r'\[INFO\]\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
            r'.*?\[DESATIVAR\].*?alvo=([^\s|]+)'
        )

        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                for linha in f:
                    m = padrao.search(linha)
                    if not m:
                        continue
                    try:
                        from datetime import datetime
                        data_str = m.group(1)
                        username = m.group(2)
                        data_dt  = datetime.strptime(
                            data_str, '%Y-%m-%d %H:%M:%S'
                        )
                        # Guarda a data mais recente de desativação
                        data_dt_aware = timezone.make_aware(data_dt)
                        if username not in datas or \
                                data_dt_aware > datas[username]:
                            datas[username] = data_dt_aware
                    except (ValueError, IndexError):
                        continue
        except OSError as e:
            logger.error(f"Erro ao ler contas.log: {e}")

        return datas