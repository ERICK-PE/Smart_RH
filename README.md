# Smart-RH

Projeto de conclusao de faculdade de ADS.

## Estrutura atual

Backend Django/DRF com apps:

- `setor`
- `funcionario`
- `candidato_vaga`
- `avaliacao`

Entrada principal da API:

- `/api/`
- `/api/auth/token/`
- `/api/auth/token/refresh/`
- `/admin/`

## Requisitos de sistema

Validado localmente com:

- Python 3.14.2
- PostgreSQL
- pip
- virtualenv/venv

Banco esperado:

- PostgreSQL acessivel pela maquina local ou rede.
- Usuario e banco criados antes de rodar `migrate`.
- Driver Python usado: `psycopg2-binary`.

## Dependencias Python

Runtime:

- Django
- Django REST Framework
- django-filter
- django-cors-headers
- djangorestframework-simplejwt
- drf-spectacular
- psycopg2-binary
- pypdf
- openai

Desenvolvimento/testes:

- pytest
- pytest-django

Instalacao recomendada:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Para instalar apenas runtime:

```powershell
python -m pip install -r requirements.txt
```

## Variaveis de ambiente

O projeto carrega `.env` na raiz, mas esse arquivo nao deve ser versionado.

Variaveis obrigatorias:

```env
DJANGO_SECRET_KEY=troque-este-valor
DB_ENGINE=django.db.backends.postgresql
DB_NAME=smart_rh
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

Variaveis opcionais:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
CORS_ALLOW_CREDENTIALS=True
JWT_ACCESS_TOKEN_MINUTES=30
JWT_REFRESH_TOKEN_DAYS=1
OPEN_API_KEY=sua_chave_openai
OPENAI_AGENT_MODEL=gpt-4o-mini
```

## Preparar outra maquina

1. Instalar Python e PostgreSQL.
2. Clonar repositorio.
3. Criar e ativar ambiente virtual.
4. Instalar dependencias com `python -m pip install -r requirements-dev.txt`.
5. Criar banco PostgreSQL.
6. Criar `.env` local com as variaveis acima.
7. Rodar validacoes.

Comandos:

```powershell
python manage.py check
python manage.py migrate
python manage.py test
python -m pytest
```

Servidor local:

```powershell
python manage.py runserver
```

## Testes e validacoes

Comandos usados para validar o estado atual:

```powershell
python -m pip check
python -m compileall Smart_RH apps
python manage.py check
python manage.py test
python -m pytest --collect-only -q
python manage.py spectacular --validate --file NUL
```

Observacao:

- `pytest.ini` limita descoberta para arquivos reais de teste.
- Arquivos `apps/*/api/test_views.py` sao views locais de teste/debug, nao testes pytest.
- `sitecustomize.py` cria fallback local `.tmp/` apenas quando Python nao encontra nenhum diretorio temporario utilizavel no ambiente.

## Agente interno de RH

O backend possui endpoint para perguntas dos integrantes internos da empresa com base em documentos importantes enviados pelo RH:

- RH/admin gerencia documentos em `/api/funcionario/agente/`.
- Funcionario comum, lideranca, RH e admin autenticados perguntam em `POST /api/funcionario/agente/perguntar/`.
- Documentos aceitos: `.pdf`, `.docx`, `.doc`.
- Uploads ficam em `imp_doc/` com o nome base original do arquivo.
- Resposta usa a API da OpenAI com contexto extraido de todos os documentos legiveis em `imp_doc/`.
- A chave deve vir do ambiente em `OPEN_API_KEY`; `.env` nunca deve ser versionado.

## Seguranca

- Nunca versionar `.env`.
- Nunca commitar senhas, tokens, chaves JWT, credenciais ou dumps do banco.
- HTTPS nao e dependencia Python. Em producao, usar proxy/servidor com certificado TLS e revisar `DEBUG`, `ALLOWED_HOSTS`, cookies seguros e origem CORS.

## Documentacao da API

Quando `drf-spectacular` estiver instalado:

- `/api/schema/`
- `/api/docs/`
- `/api/redoc/`

Validacao atual do schema OpenAPI retorna `Errors: 0`. Warnings conhecidos seguem ligados a serializers aninhados com `depth`, `CompositePrimaryKey` e parametros customizados de actions.
