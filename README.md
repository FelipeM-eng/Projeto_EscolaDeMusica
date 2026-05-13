# Escola de Música - Aplicação Web

Projeto desenvolvido em Django para a unidade curricular de Programação Web.

Esta aplicação permite gerir administrativamente uma escola de música, incluindo matrículas de alunos, autenticação e permissões por tipo de utilizador.

## Descrição

O sistema foi desenvolvido para permitir a gestão de matrículas de alunos em cursos e turmas.

A aplicação possui autenticação e diferentes níveis de acesso através de grupos de utilizadores. Apenas utilizadores autorizados conseguem aceder às funcionalidades protegidas.

---

## Tecnologias Utilizadas

- Django 6+
- PostgreSQL
- psycopg2-binary
- python-decouple
- HTML5
- CSS3
- JavaScript (vanilla)

---

## Requisitos

Antes de executar o projeto é necessário ter:

- Python 3.10 ou superior
- PostgreSQL 13 ou superior
- pip

---

## Instalação

### 1. Ir para a pasta do projeto

```bash
cd caminho/para/o/projeto
```

### 2. Criar ambiente virtual

```bash
python -m venv venv
```

Ativar o ambiente virtual:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## Configuração

### 1. Criar ficheiro `.env`

Na raiz do projeto (onde está o `manage.py`) criar um ficheiro `.env` com o seguinte conteúdo:

```env
SECRET_KEY=substitui-por-uma-chave-segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=escola_de_musica
DB_USER=Servidor_Emusica
DB_PASSWORD=escolademusicasegura
DB_HOST=localhost
DB_PORT=5432
```

Para gerar uma `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2. Configurar a base de dados

A aplicação utiliza PostgreSQL.

É necessário garantir que a base de dados `escola_de_musica` já existe e que as credenciais definidas no `.env` estão corretas.

### 3. Executar migrações

As migrações criam apenas as tabelas internas do Django (sessões, autenticação, etc.). As tabelas da base de dados principal não são alteradas porque os modelos usam `managed = False`.

```bash
python manage.py migrate
```

### 4. Criar superutilizador

```bash
python manage.py createsuperuser
```

Depois seguir os passos indicados no terminal.

---

## Executar o Projeto

Iniciar servidor:

```bash
python manage.py runserver
```

Abrir no browser:

- Página principal: `http://127.0.0.1:8000/`
- Login: `http://127.0.0.1:8000/login/`
- Matrículas: `http://127.0.0.1:8000/matriculas/`
- Admin Django: `http://127.0.0.1:8000/admin/`

---

## Estrutura do Projeto

```txt
projeto/
│── .env
│── .gitignore
│── requirements.txt
│── manage.py
│── README.md
│
├── escola_musica_project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── escola_musica/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── utils.py
│   ├── urls.py
│   └── admin.py
│
├── templates/
│
├── static/
│
└── logs/
    └── erros.log
```

### Organização MVC (MTV no Django)

O projeto segue o padrão MVC através do modelo MTV do Django:

- **Model** → `models.py`
- **Controller** → `views.py`, `forms.py`, `utils.py`
- **View** → templates HTML

---

## Configuração de Utilizadores e Grupos

Depois de executar as migrações e criar o superutilizador, é necessário configurar os acessos.

### 1. Aceder ao painel admin

```txt
http://127.0.0.1:8000/admin/
```

Entrar com o superutilizador criado anteriormente.

### 2. Criar grupo `Recepcao`

No painel admin:

**Autenticação e Autorização → Grupos → Adicionar grupo**

Nome do grupo:

```txt
Recepcao
```

Permissões a adicionar:

- Can add matricula
- Can change matricula
- Can view matricula

Não adicionar:

- `Can delete matricula`

### 3. Criar utilizadores

Ir a:

**Autenticação e Autorização → Utilizadores → Adicionar utilizador**

Criar username e password.

Configuração recomendada:

#### Superutilizador
- Active → Sim
- Staff status → Sim
- Superuser status → Sim

#### Recepção
- Active → Sim
- Staff status → Não
- Superuser status → Não
- Grupo → `Recepcao`

### 4. Permissões dos perfis

**Superutilizador**
- Pode listar matrículas
- Pode ver detalhes
- Pode criar
- Pode editar sem restrições
- Pode eliminar

**Recepção**
- Pode listar matrículas
- Pode ver detalhes
- Pode criar
- Pode editar com restrições
- Não pode eliminar

Restrições do grupo `Recepcao`:

- O campo `valor_pago` não pode ser alterado
- Se o pagamento estiver marcado como `Pago`, os campos financeiros ficam bloqueados
- Não existe acesso ao botão de eliminar
- Tentativas de acesso direto ao URL de eliminação são bloqueadas

### Persistência

Os grupos e utilizadores ficam guardados nas tabelas do PostgreSQL:

- `auth_group`
- `auth_group_permissions`
- `auth_user`
- `auth_user_groups`

Se a base de dados for limpa, é necessário recriar tudo manualmente.

---

## Funcionalidades

### Autenticação

- Login com username e password
- Sessão termina ao fechar o browser
- Timeout de 8 horas de inatividade
- Logout manual com confirmação

### Gestão de Matrículas

A aplicação tem uma funcionalidade principal: gestão de matrículas.

O utilizador autenticado pode:

- Listar matrículas
- Ver detalhes
- Criar nova matrícula
- Editar matrícula
- Eliminar (apenas administrador)

Existe confirmação antes de gravar nova matrícula.

---

## Validações Implementadas

### Data de matrícula

- Obrigatória
- Não pode ser anterior ao dia atual
- Máximo de 2 meses no futuro
- Não pode ser anterior à data de nascimento do aluno

### Data de pagamento

- Obrigatória
- Não pode ser futura
- Utilizadores normais só podem inserir até 60 dias para trás
- Administradores não têm limite

### Ano letivo

- Preenchido automaticamente
- Pode ser alterado manualmente
- Intervalo entre 1900 e 2100

### Matrículas duplicadas

O backend impede matrículas repetidas do mesmo aluno na mesma turma e curso.

---

## Segurança

Foram implementadas algumas medidas de segurança:

- `@login_required` nas páginas protegidas
- Proteção CSRF do Django
- Proteção XSS automática nos templates
- ORM do Django para evitar SQL Injection
- Variáveis sensíveis guardadas no `.env`
- `SESSION_COOKIE_HTTPONLY = True`
- `X_FRAME_OPTIONS = 'DENY'`
- Logging interno de erros em `logs/erros.log`
- Apenas administradores podem eliminar matrículas
- Validações feitas no backend independentemente do frontend

---

## Decisões Técnicas

Algumas decisões tomadas durante o desenvolvimento:

- Uso de `managed = False` para não alterar a base de dados original
- Modelos gerados com `inspectdb` e ajustados manualmente
- Sistema de confirmação antes de gravar nova matrícula
- CSS e JavaScript separados por página
- Sistema de grupos do Django para permissões
- Registo interno de erros sem mostrar detalhes técnicos ao utilizador

---

## Notas para Entrega

O ficheiro `.env` não deve ser enviado para o repositório.

O ficheiro `logs/erros.log` também não deve ser enviado.

Ambos já estão definidos no `.gitignore`.

Se forem adicionadas novas dependências, atualizar o `requirements.txt`:

```bash
pip freeze > requirements.txt
```

Numa instalação nova, é necessário recriar os grupos e utilizadores seguindo os passos indicados acima.