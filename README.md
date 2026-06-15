# Escola de Música

Sistema de gestão para uma escola de música desenvolvido com Django 5.1.1.

## Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL 12 ou superior
- pip (gestor de pacotes Python)
- Virtual environment (venv)

## Instalação

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd ProjetoPW
```

### 2. Criar e ativar o ambiente virtual

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
venv\Scripts\activate

# Ativar ambiente virtual (Linux/Mac)
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

## Configuração

### 1. Configurar base de dados PostgreSQL

Crie uma base de dados PostgreSQL:

```sql
CREATE DATABASE escola_musica;
CREATE USER escola_user WITH PASSWORD 'sua_password_segura';
GRANT ALL PRIVILEGES ON DATABASE escola_musica TO escola_user;
```

### 2. Configurar variáveis de ambiente

Crie um ficheiro `.env` na raiz do projeto com as seguintes variáveis:

```env
SECRET_KEY=your-secret-key-here-generate-with-python
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Configuração da Base de Dados
DB_NAME=escola_musica
DB_USER=escola_user
DB_PASSWORD=sua_password_segura
DB_HOST=localhost
DB_PORT=5432
```

**Para gerar uma SECRET_KEY segura:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Criar diretórios de logs

```bash
mkdir logs
```

### 4. Executar migrações da base de dados

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Criar superutilizador (opcional)

```bash
python manage.py createsuperuser
```

## Execução

### Iniciar o servidor de desenvolvimento

```bash
python manage.py runserver
```

A aplicação estará disponível em: `http://localhost:8000`

### Aceder ao painel de administração

Após criar o superutilizador, aceda a: `http://localhost:8000/admin/`

## Estrutura do Projeto

- `escola_musica/` - Aplicação principal com modelos, views e formulários
- `escola_musica_project/` - Configurações do projeto Django
- `templates/` - Ficheiros de templates HTML
- `static/` - Ficheiros estáticos (CSS, JS, imagens)
- `logs/` - Ficheiros de log da aplicação
- `manage.py` - Script de gestão Django

## Segurança

O projeto inclui várias medidas de segurança:

- **Django Axes**: Proteção contra ataques de força bruta (bloqueia após 5 tentativas falhadas)
- **Validação de passwords**: Validação robusta de passwords
- **Headers de segurança**: XSS, Clickjacking, e proteção de conteúdo
- **CSRF**: Proteção contra ataques CSRF ativa
- **Logging**: Registo de erros e auditoria de ações

## Tecnologias Utilizadas

- **Django 5.1.1** - Framework web
- **PostgreSQL** - Base de dados
- **Django REST Framework** - API REST
- **django-decouple** - Gestão de configurações
- **django-axes** - Proteção contra força bruta
- **drf-spectacular** - Documentação OpenAPI/Swagger
- **django-cors-headers** - Suporte CORS

## Notas Importantes

- Em produção, altere `DEBUG=False` no ficheiro `.env`
- Configure `ALLOWED_HOSTS` com os domínios de produção
- Em produção, descomente as linhas de SSL/HTTPS no `settings.py`
- Os ficheiros de log são armazenados no diretório `logs/`
- O projeto está configurado para português (pt-pt) e fuso horário de Lisboa

## Resolução de Problemas

### Erro de conexão à base de dados
- Verifique se o PostgreSQL está a correr
- Confirme as credenciais no ficheiro `.env`
- Certifique-se de que a base de dados existe

### Erro de migração
- Execute `python manage.py makemigrations` antes de `migrate`
- Verifique se não há conflitos de migração

### Problemas com permissões
- Certifique-se de que o utilizador da base de dados tem as permissões necessárias
- Verifique as permissões dos diretórios `logs/` e `static/`