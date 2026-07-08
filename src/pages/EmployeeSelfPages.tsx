import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../auth/AuthContext';
import { listResource, api } from '../services/api';
import type { ApiRecord } from '../types';
import { PageState } from '../components/PageState';
import { Button, PageHeader, SensitiveValue } from '../components/ui';

type DisplayField = {
  key: string;
  label: string;
  format?: 'fileName';
};

type FieldLayout = 'default' | 'profile' | 'stack';

type FilePreviewConfig = {
  idKey: string;
  endpoint: (record: ApiRecord) => string;
};

type DocumentPreview = {
  contentType: string;
  fileName: string;
  recordKey: string;
  url: string;
};

const myDataFields: DisplayField[] = [
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
  { key: 'arquivo', label: 'Arquivo', format: 'fileName' },
];

const payslipFields: DisplayField[] = [
  { key: 'competencia', label: 'Competencia' },
  { key: 'arquivo', label: 'Arquivo', format: 'fileName' },
  { key: 'criado_em', label: 'Criado em' },
];

const careerPlanFields: DisplayField[] = [
  { key: 'fk_id_cargo', label: 'Cargo vinculado' },
  { key: 'descricao', label: 'Descricao' },
  { key: 'requisitos', label: 'Requisitos' },
];

const reviewFields: DisplayField[] = [
  { key: 'fk_id_avaliador', label: 'Avaliador' },
  { key: 'categoria', label: 'Categoria' },
  { key: 'nota', label: 'Nota' },
  { key: 'comentario', label: 'Comentario' },
  { key: 'data_avaliacao', label: 'Data avaliacao' },
];

function gridClass(layout: FieldLayout) {
  if (layout === 'profile') return 'grid gap-x-8 gap-y-4 md:grid-cols-2';
  if (layout === 'stack') return 'grid gap-4';
  return 'grid gap-3 md:grid-cols-2 xl:grid-cols-3';
}

function fileNameFromPath(value: unknown) {
  if (typeof value !== 'string') return value;
  const normalized = value.replaceAll('\\', '/');
  return normalized.split('/').filter(Boolean).pop() ?? value;
}

function fieldValue(record: ApiRecord, field: DisplayField) {
  const value = record[field.key];
  if (field.format === 'fileName') return fileNameFromPath(value);
  return value;
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
            <SensitiveValue value={fieldValue(record, field)} />
          </p>
        </div>
      ))}
    </div>
  );
}

function getCardKey(record: ApiRecord, index: number) {
  return String(
    record.id_contrato ??
      record.id_folha ??
      record.id_plano ??
      record.id_avaliacao ??
      index,
  );
}

function isPdfPreview(preview: DocumentPreview) {
  return preview.contentType.includes('pdf') || preview.fileName.toLowerCase().endsWith('.pdf');
}

/**
 * Renderiza listas do autoatendimento de funcionario.
 */
function SelfListPage({
  title,
  description,
  endpoint,
  fields,
  filePreview,
  fieldLayout = 'default',
}: {
  title: string;
  description: string;
  endpoint: string;
  fields: DisplayField[];
  filePreview?: FilePreviewConfig;
  fieldLayout?: FieldLayout;
}) {
  const [preview, setPreview] = useState<DocumentPreview | null>(null);
  const [previewError, setPreviewError] = useState('');
  const query = useQuery({
    queryKey: ['self-list', endpoint],
    queryFn: () => listResource<ApiRecord>(endpoint, {}),
  });

  useEffect(() => {
    return () => {
      if (preview?.url) URL.revokeObjectURL(preview.url);
    };
  }, [preview?.url]);

  function closePreview() {
    setPreview((current) => {
      if (current?.url) URL.revokeObjectURL(current.url);
      return null;
    });
  }

  async function openPreview(record: ApiRecord, index: number) {
    if (!filePreview) return;
    setPreviewError('');
    try {
      const response = await api.get<Blob>(filePreview.endpoint(record), {
        responseType: 'blob',
      });
      const contentType = String(response.headers['content-type'] ?? response.data.type ?? '');
      const fileName = String(fileNameFromPath(record.arquivo) ?? 'documento');
      const url = URL.createObjectURL(response.data);
      const recordKey = getCardKey(record, index);
      setPreview((current) => {
        if (current?.url) URL.revokeObjectURL(current.url);
        return { contentType, fileName, recordKey, url };
      });
    } catch {
      setPreviewError('Nao foi possivel carregar o documento.');
    }
  }

  if (query.isLoading) return <PageState title="Carregando dados" />;
  if (query.isError) return <PageState title="Nao foi possivel carregar" variant="error" />;

  return (
    <section>
      <PageHeader title={title} description={description} />
      {previewError ? (
        <p className="mb-3 rounded-md border border-danger/30 bg-red-50 p-3 text-sm text-danger dark:bg-red-950/30">
          {previewError}
        </p>
      ) : null}
      <div className="space-y-3">
        {query.data?.results.length ? (
          query.data.results.map((item, index) => {
            const cardKey = getCardKey(item, index);
            const activePreview = preview?.recordKey === cardKey ? preview : null;
            const hasFile = Boolean(item.arquivo);

            return (
              <article
                key={cardKey}
                className="rounded-md border border-line bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-950"
              >
                <FieldGrid record={item} fields={fields} layout={fieldLayout} />
                {filePreview && hasFile ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {activePreview ? (
                      <Button variant="secondary" onClick={closePreview}>
                        Fechar documento
                      </Button>
                    ) : (
                      <Button variant="secondary" onClick={() => void openPreview(item, index)}>
                        Visualizar documento
                      </Button>
                    )}
                  </div>
                ) : null}
                {activePreview ? (
                  <div className="mt-4 rounded-md border border-line bg-panel p-3 dark:border-slate-700 dark:bg-slate-900">
                    <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <p className="text-sm font-semibold text-ink dark:text-slate-100">{activePreview.fileName}</p>
                      <a
                        href={activePreview.url}
                        download={activePreview.fileName}
                        className="text-sm font-semibold text-brand hover:underline"
                      >
                        Baixar documento
                      </a>
                    </div>
                    {isPdfPreview(activePreview) ? (
                      <iframe
                        title={`Visualizacao de ${activePreview.fileName}`}
                        src={activePreview.url}
                        className="h-[70vh] w-full rounded-md border border-line bg-white dark:border-slate-700"
                      />
                    ) : (
                      <div className="rounded-md border border-line bg-white p-4 text-sm text-muted dark:border-slate-700 dark:bg-slate-950 dark:text-slate-400">
                        Visualizacao direta de Word depende do suporte do navegador. Use o botao baixar documento para
                        abrir o arquivo localmente.
                      </div>
                    )}
                  </div>
                ) : null}
              </article>
            );
          })
        ) : (
          <div className="rounded-md border border-line bg-white p-4 text-sm text-muted dark:border-slate-700 dark:bg-slate-950">
            Nenhum registro encontrado.
          </div>
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

  if (!id) return <PageState title="Usuario sem vinculo de funcionario" variant="error" />;
  if (query.isLoading) return <PageState title="Carregando seus dados" />;
  if (query.isError || !query.data) return <PageState title="Nao foi possivel carregar seus dados" variant="error" />;

  return (
    <section>
      <PageHeader title="Meus dados" description="Informacoes retornadas conforme seu vinculo de funcionario." />
      <div className="rounded-md border border-line bg-white p-4 dark:border-slate-700 dark:bg-slate-950">
        <FieldGrid record={query.data} fields={myDataFields} layout="profile" />
      </div>
    </section>
  );
}

/**
 * Mostra contratos do proprio funcionario autenticado.
 */
export function MyContractsPage() {
  const { user } = useAuth();
  if (!user?.funcionario_id) return <PageState title="Usuario sem vinculo de funcionario" variant="error" />;
  return (
    <SelfListPage
      title="Meus contratos"
      description="Contratos vinculados ao seu cadastro funcional."
      endpoint={`/funcionario/funcionarios/${user.funcionario_id}/meus-contratos/`}
      fields={contractFields}
      filePreview={{
        idKey: 'id_contrato',
        endpoint: (record) =>
          `/funcionario/funcionarios/${user.funcionario_id}/meus-contratos/${String(record.id_contrato)}/arquivo/`,
      }}
    />
  );
}

/**
 * Mostra folhas de pagamento do proprio funcionario autenticado.
 */
export function MyPayslipsPage() {
  const { user } = useAuth();
  if (!user?.funcionario_id) return <PageState title="Usuario sem vinculo de funcionario" variant="error" />;
  return (
    <SelfListPage
      title="Minha folha de pagamento"
      description="Arquivos de folha de pagamento vinculados ao seu cadastro funcional."
      endpoint={`/funcionario/funcionarios/${user.funcionario_id}/folha-pagamento/`}
      fields={payslipFields}
      filePreview={{
        idKey: 'id_folha',
        endpoint: (record) =>
          `/funcionario/funcionarios/${user.funcionario_id}/folha-pagamento/${String(record.id_folha)}/arquivo/`,
      }}
    />
  );
}

/**
 * Mostra planos de carreira relacionados ao cargo do funcionario.
 */
export function MyCareerPlanPage() {
  const { user } = useAuth();
  if (!user?.funcionario_id) return <PageState title="Usuario sem vinculo de funcionario" variant="error" />;
  return (
    <SelfListPage
      title="Meu plano de carreira"
      description="Planos relacionados ao seu cargo atual."
      endpoint={`/funcionario/funcionarios/${user.funcionario_id}/meu-plano-carreira/`}
      fields={careerPlanFields}
      fieldLayout="stack"
    />
  );
}

/**
 * Mostra avaliacoes recebidas pelo funcionario.
 */
export function MyReviewsPage() {
  const { user } = useAuth();
  if (!user?.funcionario_id) return <PageState title="Usuario sem vinculo de funcionario" variant="error" />;
  return (
    <SelfListPage
      title="Minhas avaliacoes"
      description="Avaliacoes de desempenho recebidas por voce."
      endpoint={`/funcionario/funcionarios/${user.funcionario_id}/minhas-avaliacoes-desempenho/`}
      fields={reviewFields}
      fieldLayout="stack"
    />
  );
}
