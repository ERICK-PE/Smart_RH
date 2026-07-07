import type { ResourceConfig } from './types';

const setorRelation = {
  endpoint: '/setor/setores/',
  idField: 'id_setor',
  labelField: 'nome',
};

const cargoRelation = {
  endpoint: '/setor/cargos/',
  idField: 'id_cargo',
  labelField: 'nome',
};

const funcionarioRelation = {
  endpoint: '/funcionario/funcionarios/',
  idField: 'id_funcionario',
  labelField: 'nome',
  secondaryFields: ['fk_id_cargo'],
  hideIdColumn: true,
};

const vagaStatusOptions = [
  { label: 'Aberta', value: 'aberta' },
  { label: 'Andamento', value: 'andamento' },
  { label: 'Fechada', value: 'fechada' },
  { label: 'Cancelada', value: 'cancelada' },
];

export const resources = {
  setores: {
    title: 'Setores',
    description: 'Cadastro e acompanhamento dos setores da organizacao.',
    endpoint: '/setor/setores/',
    idField: 'id_setor',
    columns: [
      { key: 'id_setor', label: 'ID' },
      { key: 'nome', label: 'Nome' },
      { key: 'descricao', label: 'Descricao' },
    ],
    fields: [
      { name: 'nome', label: 'Nome', required: true },
      { name: 'descricao', label: 'Descricao', type: 'textarea' },
    ],
    filters: [
      { name: 'possui_funcionarios', label: 'Possui funcionarios', type: 'select', options: [
        { label: 'Sim', value: 'true' },
        { label: 'Nao', value: 'false' },
      ] },
      { name: 'possui_vagas', label: 'Possui vagas', type: 'select', options: [
        { label: 'Sim', value: 'true' },
        { label: 'Nao', value: 'false' },
      ] },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  cargos: {
    title: 'Cargos',
    description: 'Gestao dos cargos, descricoes e setor vinculado.',
    endpoint: '/setor/cargos/',
    idField: 'id_cargo',
    columns: [
      { key: 'id_cargo', label: 'ID' },
      { key: 'nome', label: 'Nome' },
      { key: 'fk_id_setor', label: 'Setor' },
      { key: 'descricao', label: 'Descricao' },
    ],
    fields: [
      { name: 'nome', label: 'Nome', required: true },
      { name: 'fk_id_setor', label: 'Setor', required: true, relation: setorRelation },
      { name: 'descricao', label: 'Descricao', type: 'textarea' },
    ],
    filters: [
      { name: 'setor', label: 'ID setor' },
      { name: 'setor_nome', label: 'Nome setor' },
      { name: 'possui_funcionarios', label: 'Possui funcionarios', type: 'select', options: [
        { label: 'Sim', value: 'true' },
        { label: 'Nao', value: 'false' },
      ] },
      { name: 'possui_planos_carreira', label: 'Possui planos', type: 'select', options: [
        { label: 'Sim', value: 'true' },
        { label: 'Nao', value: 'false' },
      ] },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  funcionarios: {
    title: 'Funcionarios',
    description: 'Gestao administrativa de funcionarios, acesso ao sistema, vinculos e cargos.',
    endpoint: '/funcionario/funcionarios/',
    idField: 'id_funcionario',
    columns: [
      { key: 'nome', label: 'Nome' },
      { key: 'cpf', label: 'CPF' },
      { key: 'email', label: 'E-mail' },
      { key: 'telefone', label: 'Telefone' },
      { key: 'fk_id_setor', label: 'Setor' },
      { key: 'fk_id_cargo', label: 'Cargo' },
      { key: 'status', label: 'Status' },
    ],
    fields: [
      { name: 'nome', label: 'Nome', required: true },
      { name: 'cpf', label: 'CPF', required: true },
      { name: 'email', label: 'E-mail', type: 'email' },
      { name: 'telefone', label: 'Telefone' },
      { name: 'data_admissao', label: 'Data de admissao', type: 'date', required: true },
      {
        name: 'status',
        label: 'Status',
        type: 'select',
        options: [
          { label: 'Ativo', value: 'ativo' },
          { label: 'Inativo', value: 'inativo' },
        ],
      },
      { name: 'fk_id_setor', label: 'Setor', required: true, relation: setorRelation },
      { name: 'fk_id_cargo', label: 'Cargo', required: true, relation: cargoRelation },
    ],
    filters: [
      {
        name: 'status',
        label: 'Status',
        type: 'select',
        options: [
          { label: 'Ativo', value: 'ativo' },
          { label: 'Inativo', value: 'inativo' },
        ],
      },
      { name: 'setor', label: 'Setor' },
      { name: 'cargo', label: 'Cargo' },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  contratos: {
    title: 'Contratos',
    description: 'Gestao dos contratos vinculados aos funcionarios.',
    endpoint: '/funcionario/contratos/',
    idField: 'id_contrato',
    columns: [
      { key: 'fk_id_funcionario', label: 'Funcionario' },
      { key: 'tipo_contrato', label: 'Tipo' },
      { key: 'salario', label: 'Salario' },
      { key: 'data_inicio', label: 'Inicio' },
      { key: 'data_fim', label: 'Fim' },
      { key: 'arquivo', label: 'Arquivo' },
    ],
    fields: [
      { name: 'fk_id_funcionario', label: 'Funcionario', required: true, relation: funcionarioRelation },
      { name: 'tipo_contrato', label: 'Tipo de contrato' },
      { name: 'salario', label: 'Salario', type: 'number' },
      { name: 'data_inicio', label: 'Data de inicio', type: 'date', required: true },
      { name: 'data_fim', label: 'Data de fim', type: 'date' },
      { name: 'arquivo', label: 'Arquivo PDF ou Word', type: 'file' },
    ],
    filters: [
      { name: 'funcionario', label: 'Funcionario' },
      { name: 'funcionario_nome', label: 'Nome funcionario' },
      { name: 'tipo_contrato', label: 'Tipo contrato' },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  folhasPagamento: {
    title: 'Folhas de pagamento',
    description: 'Upload e consulta de folhas de pagamento em PDF ou Word.',
    endpoint: '/funcionario/folhas-pagamento/',
    idField: 'id_folha',
    columns: [
      { key: 'fk_id_funcionario', label: 'Funcionario' },
      { key: 'competencia', label: 'Competencia' },
      { key: 'arquivo', label: 'Arquivo' },
      { key: 'criado_em', label: 'Criado em' },
    ],
    fields: [
      { name: 'fk_id_funcionario', label: 'Funcionario', required: true, relation: funcionarioRelation },
      { name: 'competencia', label: 'Competencia' },
      { name: 'arquivo', label: 'Arquivo PDF ou Word', type: 'file', required: true },
    ],
    filters: [
      { name: 'funcionario', label: 'Funcionario' },
      { name: 'funcionario_nome', label: 'Nome funcionario' },
      { name: 'competencia', label: 'Competencia' },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  planos: {
    title: 'Planos de carreira',
    description: 'Planos vinculados aos cargos e trajetorias funcionais.',
    endpoint: '/funcionario/planos-carreira/',
    idField: 'id_plano',
    columns: [
      { key: 'fk_id_cargo', label: 'Cargo' },
      { key: 'descricao', label: 'Descricao' },
      { key: 'requisitos', label: 'Requisitos' },
    ],
    fields: [
      { name: 'fk_id_cargo', label: 'Cargo', required: true, relation: cargoRelation },
      { name: 'descricao', label: 'Descricao', type: 'textarea' },
      { name: 'requisitos', label: 'Requisitos', type: 'textarea' },
    ],
    filters: [
      { name: 'cargo', label: 'ID cargo' },
      { name: 'cargo_nome', label: 'Nome cargo' },
      { name: 'texto', label: 'Descricao/requisitos' },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  avaliacoes: {
    title: 'Avaliacoes de desempenho',
    description: 'Avaliacoes, notas e comentarios conforme permissoes da API.',
    endpoint: '/avaliacao/avaliacoes-desempenho/',
    idField: 'id_avaliacao',
    columns: [
      { key: 'fk_id_funcionario', label: 'Funcionario' },
      { key: 'fk_id_avaliador', label: 'Avaliador' },
      { key: 'categoria', label: 'Categoria' },
      { key: 'nota', label: 'Nota' },
      { key: 'data_avaliacao', label: 'Data' },
    ],
    fields: [
      { name: 'fk_id_funcionario', label: 'Funcionario avaliado', required: true, relation: funcionarioRelation },
      { name: 'fk_id_avaliador', label: 'Avaliador', required: true, relation: funcionarioRelation },
      { name: 'categoria', label: 'Categoria' },
      { name: 'nota', label: 'Nota', type: 'number' },
      { name: 'comentario', label: 'Comentario', type: 'textarea' },
      { name: 'data_avaliacao', label: 'Data da avaliacao', type: 'date', required: true },
    ],
    filters: [
      { name: 'funcionario', label: 'Funcionario' },
      { name: 'avaliador', label: 'Avaliador' },
      { name: 'categoria', label: 'Categoria' },
      { name: 'nota_min', label: 'Nota minima' },
      { name: 'nota_max', label: 'Nota maxima' },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  analises: {
    title: 'Analises comportamentais',
    description: 'Gestao de analises comportamentais por funcionario.',
    endpoint: '/avaliacao/analises-comportamentais/',
    idField: 'id_analise',
    columns: [
      { key: 'fk_id_funcionario', label: 'Funcionario' },
      { key: 'resultado', label: 'Resultado' },
      { key: 'data_analise', label: 'Data' },
    ],
    fields: [
      { name: 'fk_id_funcionario', label: 'Funcionario', required: true, relation: funcionarioRelation },
      { name: 'resultado', label: 'Resultado', type: 'textarea' },
      { name: 'data_analise', label: 'Data da analise', type: 'date' },
    ],
    filters: [
      { name: 'funcionario', label: 'Funcionario' },
      { name: 'funcionario_nome', label: 'Nome funcionario' },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
  },
  vagas: {
    title: 'Vagas',
    description: 'Gestao de vagas: descricao comunica a vaga, requisitos alimentam a triagem, status controla visibilidade e fluxo.',
    endpoint: '/candidato/vagas/',
    idField: 'id_vaga',
    columns: [
      { key: 'id_vaga', label: 'ID' },
      { key: 'titulo', label: 'Titulo' },
      { key: 'status', label: 'Status' },
      { key: 'descricao', label: 'Descricao', maxLength: 80 },
      { key: 'requisitos', label: 'Requisitos', maxLength: 100 },
      { key: 'data_publicacao', label: 'Publicacao' },
      { key: 'fk_id_setor', label: 'Setor' },
    ],
    fields: [
      { name: 'titulo', label: 'Titulo da vaga', required: true },
      { name: 'descricao', label: 'Descricao publica da vaga', type: 'textarea' },
      { name: 'requisitos', label: 'Requisitos minimos para triagem', type: 'textarea' },
      {
        name: 'status',
        label: 'Status da vaga',
        type: 'select',
        required: true,
        options: vagaStatusOptions,
      },
      { name: 'data_publicacao', label: 'Data de publicacao', type: 'date' },
      { name: 'fk_id_setor', label: 'Setor', relation: setorRelation },
    ],
    filters: [
      {
        name: 'status',
        label: 'Status',
        type: 'select',
        options: vagaStatusOptions,
      },
      { name: 'setor', label: 'ID setor' },
      { name: 'setor_nome', label: 'Nome setor' },
      { name: 'texto', label: 'Titulo/descricao/requisitos' },
      { name: 'requisitos', label: 'Requisitos contem' },
    ],
    detailSections: [
      {
        title: 'Descricao - comunicacao livre',
        fields: [
          { key: 'titulo', label: 'Titulo' },
          { key: 'descricao', label: 'Texto geral da vaga' },
        ],
      },
      {
        title: 'Requisitos - base da triagem',
        fields: [
          { key: 'requisitos', label: 'Criterios reais de analise' },
        ],
      },
      {
        title: 'Status - visibilidade e fluxo',
        fields: [
          { key: 'status', label: 'Status atual' },
          { key: 'data_publicacao', label: 'Publicacao' },
          { key: 'fk_id_setor', label: 'Setor' },
        ],
      },
    ],
    allowCreate: true,
    allowEdit: true,
    allowDelete: true,
    rowLinks: [
      { label: 'Triagem/e-mail', to: (record) => `/rh/vagas/${String(record.id_vaga)}/processos` },
    ],
  },
  candidatosAdmin: {
    title: 'Candidatos',
    description: 'Consulta administrativa de candidatos e curriculos conforme permissao.',
    endpoint: '/candidato/candidatos/',
    idField: 'cpf_candidato',
    columns: [
      { key: 'cpf_candidato', label: 'CPF' },
      { key: 'nome', label: 'Nome' },
      { key: 'email', label: 'E-mail' },
      { key: 'telefone', label: 'Telefone' },
      { key: 'curriculo', label: 'Curriculo' },
    ],
    fields: [],
    filters: [
      {
        name: 'possui_curriculo',
        label: 'Possui curriculo',
        type: 'select',
        options: [
          { label: 'Sim', value: 'true' },
          { label: 'Nao', value: 'false' },
        ],
      },
    ],
    allowCreate: false,
    allowEdit: false,
    allowDelete: true,
  },
} satisfies Record<string, ResourceConfig>;
