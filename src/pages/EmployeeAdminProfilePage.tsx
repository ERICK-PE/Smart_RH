import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { api, listResource } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';

type DisplayField = {
  key: string;
  label: string;
};

type FieldLayout = 'default' | 'profile';

const profileFields: DisplayField[] = [
  { key: 'nome', label: 'Nome' },
  { key: 'cpf', label: 'CPF' },
  { key: 'email', label: 'E-mail' },
  { key: 'telefone', label: 'Telefone' },
  { key: 'data_admissao', label: 'Data de admissao' },
  { key: 'status', label: 'Status' },
  { key: 'fk_id_setor', label: 'Setor' },
  { key: 'fk_id_cargo', label: 'Cargo' },
];

const contractFields: DisplayField[] = [
  { key: 'tipo_contrato', label: 'Tipo' },
  { key: 'salario', label: 'Salario' },
  { key: 'data_inicio', label: 'Data inicio' },
  { key: 'data_fim', label: 'Data fim' },
  { key: 'arquivo', label: 'Arquivo' },
];

const behaviorFields: DisplayField[] = [
  { key: 'resultado', label: 'Resultado' },
  { key: 'data_analise', label: 'Data analise' },
];

const reviewFields: DisplayField[] = [
  { key: 'fk_id_funcionario', label: 'Funcionario' },
  { key: 'fk_id_avaliador', label: 'Avaliador' },
  { key: 'categoria', label: 'Categoria' },
  { key: 'nota', label: 'Nota' },
  { key: 'comentario', label: 'Comentario' },
  { key: 'data_avaliacao', label: 'Data avaliacao' },
];

function asRecord(value: unknown): ApiRecord | null {
  return value && typeof value === 'object' ? (value as ApiRecord) : null;
}

function gridClass(layout: FieldLayout) {
  if (layout === 'profile') return 'grid gap-x-8 gap-y-4 md:grid-cols-2';
  return 'grid gap-3 md:grid-cols-2 xl:grid-cols-3';
}

function FieldGrid({
  record,
  fields,
  layout = 'default',
}: {
  record: ApiRecord;
  fields: DisplayField[];
  layout?: FieldLayout;
}) {
  return (
    <div className={gridClass(layout)}>
      {fields.map((field) => (
        <div key={field.key}>
          <p className="text-xs font-semibold uppercase text-muted dark:text-slate-400">{field.label}</p>
          <p className="mt-1 text-sm text-ink dark:text-slate-100">
            <SensitiveValue value={record[field.key]} />
          </p>
        </div>
      ))}
    </div>
  );
}

/**
 * Lista relacoes do funcionario com campos permitidos para RH/admin.
 */
function RelatedList({ title, endpoint, fields }: { title: string; endpoint: string; fields: DisplayField[] }) {
  const query = useQuery({
    queryKey: ['related', endpoint],
    queryFn: () => listResource<ApiRecord>(endpoint, { page_size: 10 }),
  });

  return (
    <section className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
      <h2 className="mb-3 font-semibold text-ink dark:text-slate-100">{title}</h2>
      {query.isLoading ? (
        <p className="text-sm text-muted dark:text-slate-400">Carregando...</p>
      ) : query.data?.results.length ? (
        <div className="space-y-2">
          {query.data.results.map((record, index) => (
            <article
              key={String(record.id_contrato ?? record.id_analise ?? record.id_avaliacao ?? index)}
              className="rounded-md border border-line bg-panel p-3 dark:border-slate-700 dark:bg-slate-900"
            >
              <FieldGrid record={record} fields={fields} />
            </article>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted dark:text-slate-400">Nenhum registro encontrado.</p>
      )}
    </section>
  );
}

/**
 * Perfil administrativo de funcionario com dados funcionais e acesso integrado.
 */
export function EmployeeAdminProfilePage() {
  const { id } = useParams();
  const profile = useQuery({
    queryKey: ['employee-profile', id],
    queryFn: async () => {
      const response = await api.get<ApiRecord>(`/funcionario/funcionarios/${id}/rh/perfil/`);
      return response.data;
    },
    enabled: Boolean(id),
  });

  if (profile.isLoading) return <PageState title="Carregando perfil" />;
  if (profile.isError || !profile.data) return <PageState title="Nao foi possivel carregar o perfil" variant="error" />;

  const userAccess = asRecord(profile.data.user_access);
  const accessFields: Array<[string, unknown]> = [
    ['E-mail', userAccess?.email],
    ['Ultimo login', userAccess?.last_login],
  ];

  return (
    <section>
      <PageHeader
        title={`Funcionario ${profile.data.nome ?? id}`}
        description="Perfil administrativo com dados funcionais, acesso e relacionamentos."
        action={
          <Link to="/rh/funcionarios">
            <Button variant="secondary">Voltar</Button>
          </Link>
        }
      />

      <section className="mb-5 rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
        <h2 className="mb-3 font-semibold text-ink dark:text-slate-100">Acesso ao sistema</h2>
        {userAccess ? (
          <div className="grid gap-3 md:grid-cols-3">
            {accessFields.map(([label, value]) => (
              <div key={label}>
                <p className="text-xs font-semibold uppercase text-muted dark:text-slate-400">{label}</p>
                <p className="mt-1 text-sm text-ink dark:text-slate-100">
                  <SensitiveValue value={value} />
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted dark:text-slate-400">Funcionario sem usuario de acesso vinculado.</p>
        )}
      </section>

      <section className="mb-5 rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
        <h2 className="mb-3 font-semibold text-ink dark:text-slate-100">Dados funcionais</h2>
        <FieldGrid record={profile.data} fields={profileFields} layout="profile" />
      </section>

      <div className="grid gap-4 xl:grid-cols-2">
        <RelatedList title="Contratos" endpoint={`/funcionario/funcionarios/${id}/contratos/`} fields={contractFields} />
        <RelatedList title="Analises comportamentais" endpoint={`/funcionario/funcionarios/${id}/analises-comportamentais/`} fields={behaviorFields} />
        <RelatedList title="Avaliacoes recebidas" endpoint={`/funcionario/funcionarios/${id}/avaliacoes-recebidas/`} fields={reviewFields} />
        <RelatedList title="Avaliacoes realizadas" endpoint={`/funcionario/funcionarios/${id}/avaliacoes-realizadas/`} fields={reviewFields} />
      </div>
    </section>
  );
}
