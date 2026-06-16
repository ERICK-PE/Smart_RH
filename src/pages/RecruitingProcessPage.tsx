import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api, extractApiError, listResource } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';

/**
 * Tela RH para acompanhar e atualizar status de processos seletivos por vaga.
 */
export function RecruitingProcessPage() {
  const { id } = useParams();
  const [error, setError] = useState('');
  const [statuses, setStatuses] = useState<Record<string, string>>({});
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['recruiting-process', id],
    queryFn: () => listResource<ApiRecord>(`/candidato/vagas/${id}/rh/processos/`, {}),
    enabled: Boolean(id),
  });

  const update = useMutation({
    mutationFn: ({ cpf, status }: { cpf: string; status: string }) =>
      api.patch(`/candidato/vagas/${id}/rh/processos/${cpf}/`, { status_processo: status }),
    onSuccess: () => {
      setError('');
      void queryClient.invalidateQueries({ queryKey: ['recruiting-process', id] });
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  if (query.isLoading) return <PageState title="Carregando processos" />;
  if (query.isError) return <PageState title="Não foi possível carregar processos" variant="error" />;

  return (
    <section>
      <PageHeader title="Processos seletivos" description="Atualização de status por candidato e vaga." />
      {error ? <pre className="mb-4 whitespace-pre-wrap rounded-md bg-red-50 p-3 font-sans text-sm text-danger">{error}</pre> : null}
      <div className="overflow-hidden rounded-md border border-line bg-white">
        <table className="min-w-full divide-y divide-line text-sm">
          <thead className="bg-panel">
            <tr>
              <th className="px-4 py-3 text-left">Candidato</th>
              <th className="px-4 py-3 text-left">Vaga</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-right">Atualizar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {query.data?.results.map((item, index) => {
              const cpf = String(item.cpf_candidato);
              return (
                <tr key={`${cpf}-${index}`}>
                  <td className="px-4 py-3"><SensitiveValue value={item.cpf_candidato} /></td>
                  <td className="px-4 py-3"><SensitiveValue value={item.id_vaga} /></td>
                  <td className="px-4 py-3"><SensitiveValue value={item.status_processo} /></td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      <input
                        className="focus-ring w-44 rounded-md border border-line px-2 py-1"
                        value={statuses[cpf] ?? String(item.status_processo ?? '')}
                        onChange={(event) => setStatuses((current) => ({ ...current, [cpf]: event.target.value }))}
                      />
                      <Button onClick={() => update.mutate({ cpf, status: statuses[cpf] ?? String(item.status_processo ?? '') })}>
                        Salvar
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
