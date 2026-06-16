# Changelog

Registro objetivo das alterações realizadas no projeto Smart RH.

## 2026-06-15

### Backend

- Criado endpoint autenticado `GET /api/auth/me/` para identificar usuario logado, perfil, permissoes e vinculos.
- Criados endpoints administrativos `GET/PATCH/DELETE /api/auth/usuarios/` para listagem, edicao e exclusao de usuarios pelo RH/admin.
- Unificado o fluxo de funcionario e usuario de acesso no cadastro/edicao de funcionarios.
- Senhas permanecem ocultas e so podem ser criadas ou redefinidas.
- Inativacao e reativacao de funcionario agora sincronizam `User.is_active`.
- Exclusao de funcionario no painel foi convertida em inativacao logica para preservar historico.
- Adicionado logging basico de aplicacao em `Smart_RH/settings.py`.
- Criada compatibilidade local com SQLite em `db.sqlite3` para testes do sistema.
- Criado superusuario local de testes:
  - Usuario: `admin`
  - Senha: `Admin@12345`
- Adicionado relacionamento entre `Cargo` e `Setor`.
- Criada migration `apps/setor/migrations/0002_add_cargo_setor.py`.
- Ajustado cadastro de funcionario para derivar o setor a partir do cargo selecionado.
- Mantida compatibilidade com dados existentes, sem remocao destrutiva de tabelas.

### Frontend

- Estruturado frontend React com TypeScript, Vite, Tailwind, React Router, Axios e TanStack Query.
- Criadas rotas publicas:
  - `/login`
  - `/candidato/cadastro`
- Criadas rotas protegidas para RH/admin, lideranca, funcionario e candidato.
- Implementado cliente HTTP com JWT, refresh token e tratamento de erros.
- Implementado controle de sessao e rotas por perfil.
- Criado layout autenticado com menu lateral por perfil.
- Criado alternador de tema claro/escuro no painel principal.
- Ajustada paleta visual baseada na logo do Smart RH.
- Adicionada logo na tela de login e ajustada identidade visual.
- Corrigidos contrastes de campos e textos em tema escuro.
- Criados componentes base:
  - Cabecalho de pagina
  - Botao padrao
  - Estado de loading/erro/vazio
  - Tabela CRUD generica
  - Modal de formulario e exclusao
  - Campo de relacionamento por lista expansivel
- Ajustadas telas CRUD para evitar digitacao manual de IDs em relacionamentos.
- Mantidos IDs apenas como informacao de leitura nas tabelas.
- Criada tela administrativa de usuarios no painel RH/admin.
- Ajustada tela de cargos para selecionar setor.
- Ajustada tela de funcionarios para selecionar cargo e remover obrigatoriedade de selecionar setor manualmente.
- Ajustada tela de funcionarios para cadastrar usuario, senha inicial/nova senha e permissao administrativa no mesmo formulario.
- Ajustado perfil administrativo de funcionario para exibir dados seguros de acesso sem expor senha.
- Adicionado botao para recolher/expandir a barra lateral do painel administrativo.
- Substituidos icones repetidos do menu por icones distintos por funcionalidade.
- Aumentados icones e nomes das funcionalidades no menu lateral.
- Ajustado cabecalho para exibir o nome completo do usuario logado quando disponivel.
- Adicionado scroll interno na barra lateral para telas com menor altura.
- Reduzido botao de recolher menu para icone compacto na lateral direita.
- Ajustadas telas de contratos, planos, avaliacoes, analises e vagas para usar seletores em relacionamentos.
- Criado cadastro publico de candidato com anexos no campo curriculo.
- Adicionado upload de arquivos/imagens na aba Curriculo do candidato.
- Ajustada aba Minhas candidaturas para exibir cards legiveis em vez de JSON bruto.
- Ajustada aba Curriculo para separar texto e anexos.
- Renderizadas imagens anexadas como previa visual.
- Renderizados arquivos anexados com nome, tamanho e link de download.

### Documentacao

- Criado `AGENTS.md` com regras para agentes de IA que atuarem no projeto.
- Criado este `CHANGELOG.md` para centralizar alteracoes ja realizadas.

### Validacoes Executadas

- `python manage.py check`
- `pytest`
- `pnpm build`
- Verificacao local de frontend em `http://127.0.0.1:5173/login`
- Verificacao local de backend em `http://127.0.0.1:8000/api/`
