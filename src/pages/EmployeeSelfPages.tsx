import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { listResource, api } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { PageHeader, SensitiveValue } from '../components/ui';

/**
 * Renderiza listas do autoatendimento de funcionario.
 */
function SelfListPage({
  title,
  description,
  endpoint,
}: {
  title: string;
  description: string;
  endpoint: string;
}) {
  const query = useQuery({
    queryKey: ['self-list', endpoint],
    queryFn: () => listResource<ApiRecord>(endpoint, {}),
  });

  if (query.isLoading) return <PageState title="Carregando dados" />;
  if (query.isError) return <PageState title="Não foi possível carregar" variant="error" />;

  return (
    <section>
      <PageHeader title={title} description={description} />
      <div className="space-y-3">
        {query.data?.results.length ? (
          query.data.results.map((item, index) => (
            <pre key={index} className="overflow-auto rounded-md border border-line bg-white p-4 text-xs text-slate-700 shadow-soft">
              {JSON.stringify(item, null, 2)}
            </pre>
          ))
        ) : (
          <div className="rounded-md border border-line bg-white p-4 text-sm text-muted">Nenhum registro encontrado.</div>
        )}
      </div>
    </section>
  );
}

/**
 * Mostra dados do proprio funcionario autenticado.
 */
export function MyDataPage() {
  const { user } = useAuth();
  const id = user?.funcionario_id;
  const query = useQuery({
    queryKey: ['my-data', id],
    queryFn: async () => {
      const response = await api.get<ApiRecord>(`/funcionario/funcionarios/${id}/meus-dados/`);
      return response.data;
    },
    enabled: Boolean(id),
  });

  if (!id) return <PageState title="Usuário sem vínculo de funcionário" variant="error" />;
  if (query.isLoading) return <PageState title="Carregando seus dados" />;
  if (query.isError || !query.data) return <PageState title="Não foi possível carregar seus dados" variant="error" />;

  return (
    <section>
      <PageHeader title="Meus dados" description="Informações retornadas conforme seu vínculo de funcionário." />
      <div className="grid gap-3 rounded-md border border-line bg-white p-4 md:grid-cols-3">
        {Object.entries(query.data).map(([key, value]) => (
          <div key={key}>
            <p className="text-xs font-semibold uppercase text-muted">{key}</p>
            <p className="mt-1 text-sm text-ink"><SensitiveValue value={value} /></p>
          </div>
        ))}
      </div>
    </section>
  );
}

/**
 * Mostra contratos do proprio funcionario autenticado.
 */
export function MyContractsPage() {
  const { user } = useAuth();
  if (!user?.funcionario_id) return <PageState title="Usuário sem vínculo de funcionário" variant="error" />;
  return (
    <SelfListPage
      title="Meus contratos"
      description="Contratos vinculados ao seu cadastro funcional."
      endpoint={`/funcionario/funcionarios/${user.funcionario_id}/meus-contratos/`}
    />
  );
}

/**
 * Mostra planos de carreira relacionados ao cargo do funcionario.
 */
export function MyCareerPlanPage() {
  const { user } = useAuth();
  if (!user?.funcionario_id) return <PageState title="Usuário sem vínculo de funcionário" variant="error" />;
  return (
    <SelfListPage
      title="Meu plano de carreira"
      description="Planos relacionados ao seu cargo atual."
      endpoint={`/funcionario/funcionarios/${user.funcionario_id}/meu-plano-carreira/`}
    />
  );
}

/**
 * Mostra avaliacoes recebidas pelo funcionario.
 */
export function MyReviewsPage() {
  const { user } = useAuth();
  if (!user?.funcionario_id) return <PageState title="Usuário sem vínculo de funcionário" variant="error" />;
  return (
    <SelfListPage
      title="Minhas avaliações"
      description="Avaliações de desempenho recebidas por você."
      endpoint={`/funcionario/funcionarios/${user.funcionario_id}/minhas-avaliacoes-desempenho/`}
    />
  );
}
