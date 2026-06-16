import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { api, listResource } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';

function asRecord(value: unknown): ApiRecord | null {
  return value && typeof value === 'object' ? (value as ApiRecord) : null;
}

/**
 * Lista relacoes do funcionario mantendo o payload bruto visivel para auditoria inicial.
 */
function RelatedList({ title, endpoint }: { title: string; endpoint: string }) {
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
            <pre
              key={index}
              className="overflow-auto rounded-md bg-panel p-3 text-xs text-slate-700 dark:bg-slate-900 dark:text-slate-200"
            >
              {JSON.stringify(record, null, 2)}
            </pre>
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
  if (profile.isError || !profile.data) return <PageState title="Não foi possível carregar o perfil" variant="error" />;

  const userAccess = asRecord(profile.data.user_access);
  const profileEntries = Object.entries(profile.data).filter(([key]) => key !== 'user_access');
  const accessFields: Array<[string, unknown]> = [
    ['ID do usuário', userAccess?.id],
    ['Usuário', userAccess?.username],
    ['E-mail', userAccess?.email],
    ['Acesso ativo', userAccess?.is_active],
    ['Administrador', userAccess?.is_staff],
    ['Último login', userAccess?.last_login],
  ];

  return (
    <section>
      <PageHeader
        title={`Funcionário ${profile.data.nome ?? id}`}
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
          <p className="text-sm text-muted dark:text-slate-400">Funcionário sem usuário de acesso vinculado.</p>
        )}
      </section>

      <div className="mb-5 grid gap-3 rounded-md border border-line bg-white p-4 md:grid-cols-3 dark:border-slate-700 dark:bg-slate-950">
        {profileEntries.map(([key, value]) => (
          <div key={key}>
            <p className="text-xs font-semibold uppercase text-muted dark:text-slate-400">{key}</p>
            <p className="mt-1 text-sm text-ink dark:text-slate-100">
              <SensitiveValue value={value} />
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <RelatedList title="Contratos" endpoint={`/funcionario/funcionarios/${id}/contratos/`} />
        <RelatedList title="Análises comportamentais" endpoint={`/funcionario/funcionarios/${id}/analises-comportamentais/`} />
        <RelatedList title="Avaliações recebidas" endpoint={`/funcionario/funcionarios/${id}/avaliacoes-recebidas/`} />
        <RelatedList title="Avaliações realizadas" endpoint={`/funcionario/funcionarios/${id}/avaliacoes-realizadas/`} />
      </div>
    </section>
  );
}
