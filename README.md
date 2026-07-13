# Smart-RH

Sistema web para gestao de RH, funcionarios, candidatos, vagas, avaliacoes, documentos e indicadores.

## Tecnologias utilizadas

### Back-end

- Python
- Django
- Django REST Framework
- django-filter
- django-cors-headers
- djangorestframework-simplejwt
- drf-spectacular
- pypdf
- OpenAI SDK

### Front-end

- React
- TypeScript
- Vite
- Tailwind CSS
- Axios
- React Router
- TanStack React Query
- React Hook Form
- Zod
- Lucide React

### Banco de dados

- PostgreSQL
- psycopg2-binary

### APIs REST para comunicacao

- Django REST Framework
- Axios
- JWT Bearer Token
- CORS
- OpenAPI

## Funcionalidades

- Autenticacao por perfil.
- Painel RH/admin.
- Cadastro e gestao de funcionarios.
- Setores e cargos.
- Contratos e folhas de pagamento com upload de arquivo.
- Plano de carreira.
- Avaliacoes de desempenho.
- Analises comportamentais.
- Cadastro de candidatos.
- Vagas e candidaturas.
- Triagem automatica de curriculos.
- Dashboard de indicadores.
- Agente interno de RH com OpenAI.
- Documentacao da API via Swagger/ReDoc.

## Como rodar localmente

### Requisitos

- Python
- Node.js
- PostgreSQL
- pip
- npm

### Back-end

Crie ambiente virtual e instale dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Crie arquivo `.env` na raiz:

```env
DJANGO_SECRET_KEY=sua_chave_local
DB_ENGINE=django.db.backends.postgresql
DB_NAME=smart_rh
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CORS_ALLOW_CREDENTIALS=True
JWT_ACCESS_TOKEN_MINUTES=30
JWT_REFRESH_TOKEN_DAYS=1
OPEN_API_KEY=sua_chave_openai
OPENAI_AGENT_MODEL=gpt-4o-mini
```

Prepare banco e rode servidor:

```powershell
python manage.py check
python manage.py migrate
python manage.py runserver
```

API local:

```txt
http://127.0.0.1:8000/api/
```

Admin Django:

```txt
http://127.0.0.1:8000/admin/
```

### Front-end

Instale dependencias e rode Vite:

```powershell
npm install
npm run dev
```

Front local:

```txt
http://127.0.0.1:5173/
```

Build:

```powershell
npm run build
```

## Rotas uteis

- `/api/`
- `/api/auth/token/`
- `/api/auth/token/refresh/`
- `/api/auth/me/`
- `/api/docs/`
- `/api/redoc/`
- `/admin/`

## Observacoes

- `.env` nao deve ser versionado.
- Arquivos enviados ficam em `media/` e `imp_doc/`.
- Vite e usado para desenvolvimento/build do front-end.
- Django continua sendo back-end e API principal.
