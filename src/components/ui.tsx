import { AlertTriangle, Check, Eye, Pencil, Plus, Trash2, X } from 'lucide-react';
import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { api, extractApiError, listResource } from '../services/api';
import type { ApiRecord, FieldConfig, ResourceConfig } from '../types';
import { displayValue, getRecordId, isMasked } from '../utils/formatters';
import { PageState } from './PageState';

/**
 * Cabecalho padrao para telas operacionais.
 */
export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-ink dark:text-slate-100">{title}</h1>
        {description ? <p className="mt-1 max-w-3xl text-sm text-muted dark:text-slate-400">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

/**
 * Botao base com variantes visuais consistentes.
 */
export function Button({
  children,
  type = 'button',
  variant = 'primary',
  onClick,
  disabled,
}: {
  children: ReactNode;
  type?: 'button' | 'submit';
  variant?: 'primary' | 'secondary' | 'danger';
  onClick?: () => void;
  disabled?: boolean;
}) {
  const styles = {
    primary: 'bg-brand text-white hover:bg-[#2f90c8]',
    secondary: 'border border-line bg-white text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800',
    danger: 'bg-danger text-white hover:bg-[#8f1c14]',
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`focus-ring inline-flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-60 ${styles[variant]}`}
    >
      {children}
    </button>
  );
}

/**
 * Exibe dados sensiveis sem tentar desfazer mascaras do backend.
 */
export function SensitiveValue({ value }: { value: unknown }) {
  return (
    <span className={isMasked(value) || value === null ? 'text-muted dark:text-slate-400' : 'text-ink dark:text-slate-100'}>
      {displayValue(value)}
    </span>
  );
}

/**
 * Modal simples usado por formularios e confirmacoes.
 */
function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-auto rounded-md bg-white shadow-soft dark:bg-slate-950">
        <div className="flex items-center justify-between border-b border-line px-5 py-4 dark:border-slate-700">
          <h2 className="text-base font-semibold text-ink dark:text-slate-100">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="focus-ring rounded-md p-2 text-muted hover:bg-panel dark:text-slate-400 dark:hover:bg-slate-800"
            aria-label="Fechar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

function fileNameFromPath(value: unknown) {
  const rendered = displayValue(value);
  return rendered.split(/[\\/]/).pop() || rendered;
}

function dateOnly(value: unknown) {
  if (!value) return displayValue(value);
  const text = String(value);
  const dateOnlyMatch = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (dateOnlyMatch) return `${dateOnlyMatch[3]}/${dateOnlyMatch[2]}/${dateOnlyMatch[1]}`;
  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) return displayValue(value);
  return parsed.toLocaleDateString('pt-BR');
}

function renderCellValue(value: unknown, maxLength?: number, format?: 'fileName' | 'date' | 'resultModal') {
  const rendered = format === 'fileName' ? fileNameFromPath(value) : format === 'date' ? dateOnly(value) : displayValue(value);
  if (!maxLength || rendered.length <= maxLength) return rendered;
  return `${rendered.slice(0, maxLength).trimEnd()}...`;
}

function renderInlineBold(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    const match = part.match(/^\*\*([^*]+)\*\*$/);
    if (match) {
      return <strong key={`${part}-${index}`}>{match[1]}</strong>;
    }
    return part;
  });
}

function splitSectionBody(body: string) {
  return body
    .replace(/\s+-\s+/g, '\n- ')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

function AnalysisResultText({ value }: { value: unknown }) {
  const text = displayValue(value);
  const sections = text
    .replace(/\s+(?=\d+\.\s*\*\*)/g, '\n')
    .split(/\n+/)
    .map((section) => section.trim())
    .filter(Boolean);

  if (sections.length === 0 || text === 'Não informado') {
    return <p className="text-sm text-muted dark:text-slate-400">{text}</p>;
  }

  return (
    <div className="space-y-5">
      {sections.map((section, index) => {
        const match = section.match(/^\d+\.\s*\*\*([^*]+)\*\*\s*:?\s*(.*)$/s);
        if (!match) {
          return (
            <p key={`${section}-${index}`} className="whitespace-pre-wrap text-sm leading-6 text-slate-700 dark:text-slate-200">
              {renderInlineBold(section)}
            </p>
          );
        }

        const [, title, body] = match;
        const lines = splitSectionBody(body);
        const bullets = lines.filter((line) => line.startsWith('- '));
        const paragraphs = lines.filter((line) => !line.startsWith('- '));

        return (
          <section key={`${title}-${index}`} className="rounded-md border border-line bg-panel p-4 dark:border-slate-700 dark:bg-slate-900">
            <h3 className="mb-3 text-sm font-semibold text-ink dark:text-slate-100">{title}</h3>
            <div className="space-y-2 text-sm leading-6 text-slate-700 dark:text-slate-200">
              {paragraphs.map((paragraph) => (
                <p key={paragraph}>{renderInlineBold(paragraph)}</p>
              ))}
              {bullets.length ? (
                <ul className="list-disc space-y-1 pl-5">
                  {bullets.map((bullet) => (
                    <li key={bullet}>{renderInlineBold(bullet.replace(/^- /, ''))}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          </section>
        );
      })}
    </div>
  );
}

/**
 * Formulario generico orientado por configuracao de campos.
 */
function ResourceForm({
  fields,
  initial,
  onSubmit,
  submitting,
  submitLabel = 'Salvar',
}: {
  fields: FieldConfig[];
  initial?: ApiRecord | null;
  onSubmit: (data: ApiRecord | FormData) => void;
  submitting?: boolean;
  submitLabel?: string;
}) {
  const [values, setValues] = useState<ApiRecord>({});
  const hasFileField = fields.some((field) => field.type === 'file');

  useEffect(() => {
    const next: ApiRecord = {};
    fields.forEach((field) => {
      if (field.type === 'file') {
        next[field.name] = '';
        return;
      }
      const value = initial?.[field.name];
      if (field.relation && value && typeof value === 'object') {
        next[field.name] = String((value as ApiRecord)[field.relation.idField] ?? '');
        return;
      }
      next[field.name] = typeof value === 'object' ? '' : (value ?? '');
    });
    setValues(next);
  }, [fields, initial]);

  function update(name: string, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  function updateFile(name: string, file: File | null) {
    setValues((current) => ({ ...current, [name]: file ?? '' }));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    const payload: ApiRecord | FormData = hasFileField ? new FormData() : {};
    fields.forEach((field) => {
      if (field.submit === false) return;
      if (field.readOnly) return;
      const value = values[field.name];
      if (!field.required && value === '') return;
      if (payload instanceof FormData) {
        if (value instanceof File) {
          payload.append(field.name, value);
        } else if (value !== '' && value !== null && value !== undefined) {
          payload.append(field.name, String(value));
        }
        return;
      }
      payload[field.name] = value === '' ? null : value;
    });
    onSubmit(payload);
  }

  return (
    <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
      {fields.map((field) => (
        <label key={field.name} className={field.type === 'textarea' ? 'md:col-span-2' : ''}>
          <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">{field.label}</span>
          {field.relation ? (
            <RelationPicker
              field={field}
              value={String(values[field.name] ?? '')}
              required={field.required}
              disabled={field.readOnly}
              onChange={(value) => update(field.name, value)}
            />
          ) : field.type === 'textarea' ? (
            <textarea
              className="focus-ring min-h-28 w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              value={String(values[field.name] ?? '')}
              required={field.required}
              readOnly={field.readOnly}
              onChange={(event) => update(field.name, event.target.value)}
            />
          ) : field.type === 'select' ? (
            <select
              className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              value={String(values[field.name] ?? '')}
              required={field.required}
              disabled={field.readOnly}
              onChange={(event) => update(field.name, event.target.value)}
            >
              <option value="">Selecione</option>
              {field.options?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : field.type === 'file' ? (
            <input
              className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              type="file"
              accept=".pdf,.doc,.docx"
              required={field.required}
              disabled={field.readOnly}
              onChange={(event) => updateFile(field.name, event.target.files?.[0] ?? null)}
            />
          ) : (
            <input
              className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              type={field.type || 'text'}
              value={String(values[field.name] ?? '')}
              required={field.required}
              readOnly={field.readOnly}
              onChange={(event) => update(field.name, event.target.value)}
            />
          )}
        </label>
      ))}
      <div className="flex justify-end gap-2 md:col-span-2">
        <Button type="submit" disabled={submitting}>
          <Check className="h-4 w-4" />
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}

/**
 * Monta o texto visivel de uma opcao relacionada no seletor expansivel.
 */
function relationDisplay(record: ApiRecord, field: FieldConfig) {
  if (!field.relation) return displayValue(record);
  const label = displayValue(record[field.relation.labelField]);
  const secondary = field.relation.secondaryFields
    ?.map((key) => displayValue(record[key]))
    .filter((value) => value !== 'Não informado')
    .join(' · ');
  return secondary ? `${label} · ${secondary}` : label;
}

/**
 * Campo de selecao para relacionamentos carregados de endpoints DRF.
 */
function RelationPicker({
  field,
  value,
  required,
  disabled,
  onChange,
}: {
  field: FieldConfig;
  value: string;
  required?: boolean;
  disabled?: boolean;
  onChange: (value: string) => void;
}) {
  const relation = field.relation;
  const query = useQuery({
    queryKey: ['relation-options', relation?.endpoint],
    queryFn: () => listResource<ApiRecord>(relation?.endpoint ?? '', { page: 1, page_size: 100 }),
    enabled: Boolean(relation),
  });
  const rows = query.data?.results ?? [];

  return (
    <select
      className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm text-ink disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
      value={value}
      required={required}
      disabled={disabled || query.isLoading}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">Selecione</option>
      {rows.map((row) => {
        const optionValue = String(row[relation?.idField ?? '']);
        return (
          <option key={optionValue} value={optionValue}>
            {relationDisplay(row, field)}
          </option>
        );
      })}
    </select>
  );
}

function RelationFilterSelect({
  filter,
  value,
  onChange,
}: {
  filter: NonNullable<ResourceConfig['filters']>[number];
  value: string;
  onChange: (value: string) => void;
}) {
  const relation = filter.relation;
  const query = useQuery({
    queryKey: ['relation-options', relation?.endpoint],
    queryFn: () => listResource<ApiRecord>(relation?.endpoint ?? '', { page: 1, page_size: 100 }),
    enabled: Boolean(relation),
  });

  return (
    <select
      className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
      value={value}
      disabled={query.isLoading}
      onChange={(event) => onChange(event.target.value)}
    >
      <option value="">Todos</option>
      {(query.data?.results ?? []).map((row) => {
        const optionValue = String(row[relation?.idField ?? '']);
        return (
          <option key={optionValue} value={optionValue}>
            {displayValue(row[relation?.labelField ?? ''])}
          </option>
        );
      })}
    </select>
  );
}

/**
 * Tela CRUD generica para recursos DRF paginados.
 */
export function ResourcePage({ config }: { config: ResourceConfig }) {
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<ApiRecord | null>(null);
  const [viewing, setViewing] = useState<ApiRecord | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<ApiRecord | null>(null);
  const [expandedResult, setExpandedResult] = useState<{ title: string; value: unknown } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const queryKey = useMemo(() => [config.endpoint, page, filters], [config.endpoint, page, filters]);

  const query = useQuery({
    queryKey,
    queryFn: () =>
      listResource<ApiRecord>(config.endpoint, {
        page,
        ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value)),
      }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [config.endpoint] });

  const saveMutation = useMutation({
    mutationFn: async ({ record, payload }: { record?: ApiRecord | null; payload: ApiRecord | FormData }) => {
      const id = record ? getRecordId(record, config.idField) : null;
      if (id) return api.patch(`${config.endpoint}${id}/`, payload);
      return api.post(config.createEndpoint ?? config.endpoint, payload);
    },
    onSuccess: () => {
      setCreating(false);
      setEditing(null);
      setError(null);
      void invalidate();
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const deleteMutation = useMutation({
    mutationFn: async (record: ApiRecord) => api.delete(`${config.endpoint}${getRecordId(record, config.idField)}/`),
    onSuccess: () => {
      setDeleting(null);
      setError(null);
      void invalidate();
    },
    onError: (mutationError) => setError(extractApiError(mutationError)),
  });

  const rows = query.data?.results ?? [];

  return (
    <section>
      <PageHeader
        title={config.title}
        description={config.description}
        action={
          config.allowCreate ? (
            <Button onClick={() => setCreating(true)}>
              <Plus className="h-4 w-4" />
              Novo
            </Button>
          ) : null
        }
      />

      <div className="mb-4 flex flex-col gap-3 rounded-md border border-line bg-white p-4 sm:flex-row sm:flex-wrap sm:items-center sm:justify-around dark:border-slate-700 dark:bg-slate-950">
        {config.filters?.map((filter) => (
          <label key={filter.name} className="w-full sm:w-48">
            <span className="mb-1 block text-xs font-semibold uppercase text-muted dark:text-slate-400">{filter.label}</span>
            {filter.relation ? (
              <RelationFilterSelect
                filter={filter}
                value={filters[filter.name] ?? ''}
                onChange={(value) => {
                  setFilters((current) => ({ ...current, [filter.name]: value }));
                  setPage(1);
                }}
              />
            ) : filter.type === 'select' ? (
              <select
                className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                value={filters[filter.name] ?? ''}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, [filter.name]: event.target.value }));
                  setPage(1);
                }}
              >
                <option value="">Todos</option>
                {filter.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                className="focus-ring w-full rounded-md border border-line bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                type={filter.type === 'date' ? 'date' : 'text'}
                value={filters[filter.name] ?? ''}
                onChange={(event) => {
                  setFilters((current) => ({ ...current, [filter.name]: event.target.value }));
                  setPage(1);
                }}
              />
            )}
          </label>
        ))}
      </div>

      {error ? (
        <div className="mb-4 flex items-start gap-2 rounded-md border border-danger/30 bg-red-50 p-3 text-sm text-danger">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <pre className="whitespace-pre-wrap font-sans">{error}</pre>
        </div>
      ) : null}

      <div className="overflow-hidden rounded-md border border-line bg-white dark:border-slate-700 dark:bg-slate-950">
        {query.isLoading ? (
          <PageState title="Carregando dados" />
        ) : query.isError ? (
          <PageState title="Não foi possível carregar" variant="error" />
        ) : rows.length === 0 ? (
          <PageState title="Nenhum registro encontrado" variant="empty" />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-line text-sm">
              <thead className="bg-panel dark:bg-slate-900">
                <tr>
                  {config.columns.map((column) => (
                    <th key={column.key} className="px-4 py-3 text-left font-semibold text-ink dark:text-slate-100">
                      {column.label}
                    </th>
                  ))}
                  <th className="w-32 px-4 py-3 text-right font-semibold text-ink dark:text-slate-100">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line dark:divide-slate-700">
                {rows.map((row) => (
                  <tr key={getRecordId(row, config.idField)} className="hover:bg-panel/70 dark:hover:bg-slate-900">
                    {config.columns.map((column) => (
                      <td key={column.key} className="px-4 py-3 text-slate-700 dark:text-slate-200">
                        {column.format === 'resultModal' ? (
                          <button
                            type="button"
                            onClick={() => setExpandedResult({ title: column.label, value: row[column.key] })}
                            className="focus-ring rounded-md px-2 py-1 text-sm font-semibold text-brand hover:bg-panel dark:hover:bg-slate-800"
                          >
                            Ver resultado
                          </button>
                        ) : (
                          <>
                            <SensitiveValue value={renderCellValue(row[column.key], column.maxLength, column.format)} />
                            {column.maxLength ? (
                              <span className="sr-only">{displayValue(row[column.key])}</span>
                            ) : null}
                          </>
                        )}
                      </td>
                    ))}
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        {config.detailSections ? (
                          <button
                            type="button"
                            onClick={() => setViewing(row)}
                            className="focus-ring rounded-md border border-line p-2 text-muted hover:bg-panel hover:text-ink dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                            aria-label="Detalhes"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                        ) : null}
                        {config.allowEdit ? (
                          <button
                            type="button"
                            onClick={() => setEditing(row)}
                            className="focus-ring rounded-md border border-line p-2 text-muted hover:bg-panel hover:text-ink dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                            aria-label="Editar"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                        ) : null}
                        {config.rowLinks?.map((link) => (
                          <Link
                            key={link.label}
                            to={link.to(row)}
                            className="focus-ring rounded-md border border-line px-2 py-2 text-xs font-semibold text-brand hover:bg-panel dark:border-slate-700 dark:hover:bg-slate-800"
                          >
                            {link.label}
                          </Link>
                        ))}
                        {config.allowDelete ? (
                          <button
                            type="button"
                            onClick={() => setDeleting(row)}
                            className="focus-ring rounded-md bg-red-600 p-2 text-white hover:bg-red-700 dark:bg-red-600 dark:text-white dark:hover:bg-red-700"
                            aria-label="Excluir"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm text-muted dark:border-slate-700 dark:text-slate-400">
          <span>{query.data?.count ?? 0} registros</span>
          <div className="flex gap-2">
            <Button variant="secondary" disabled={page === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>
              Anterior
            </Button>
            <Button variant="secondary" disabled={!query.data?.next} onClick={() => setPage((current) => current + 1)}>
              Próxima
            </Button>
          </div>
        </div>
      </div>

      {creating ? (
        <Modal title={config.createTitle ?? `Novo ${config.title}`} onClose={() => setCreating(false)}>
          <ResourceForm
            fields={config.fields}
            submitting={saveMutation.isPending}
            submitLabel={config.createSubmitLabel}
            onSubmit={(payload) => saveMutation.mutate({ payload })}
          />
        </Modal>
      ) : null}

      {editing ? (
        <Modal title={`Editar ${config.title}`} onClose={() => setEditing(null)}>
          <ResourceForm
            fields={config.fields}
            initial={editing}
            submitting={saveMutation.isPending}
            onSubmit={(payload) => saveMutation.mutate({ record: editing, payload })}
          />
        </Modal>
      ) : null}

      {viewing ? (
        <Modal title={`Detalhes - ${config.title}`} onClose={() => setViewing(null)}>
          <div className="grid gap-4">
            {config.detailSections?.map((section) => (
              <section key={section.title} className="rounded-md border border-line bg-panel p-4 dark:border-slate-700 dark:bg-slate-900">
                <h3 className="mb-3 text-sm font-semibold text-ink dark:text-slate-100">{section.title}</h3>
                <dl className="grid gap-3">
                  {section.fields.map((field) => (
                    <div key={field.key}>
                      <dt className="text-xs font-semibold uppercase text-muted dark:text-slate-400">{field.label}</dt>
                      <dd className="mt-1 whitespace-pre-wrap text-sm text-ink dark:text-slate-100">
                        {displayValue(viewing[field.key])}
                      </dd>
                    </div>
                  ))}
                </dl>
              </section>
            ))}
          </div>
        </Modal>
      ) : null}

      {expandedResult ? (
        <Modal title={expandedResult.title} onClose={() => setExpandedResult(null)}>
          <AnalysisResultText value={expandedResult.value} />
        </Modal>
      ) : null}

      {deleting ? (
        <Modal title="Confirmar exclusão" onClose={() => setDeleting(null)}>
          <p className="mb-5 text-sm text-slate-700 dark:text-slate-300">Esta ação removerá o registro selecionado.</p>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDeleting(null)}>
              Cancelar
            </Button>
            <Button variant="danger" disabled={deleteMutation.isPending} onClick={() => deleteMutation.mutate(deleting)}>
              <Trash2 className="h-4 w-4" />
              Excluir
            </Button>
          </div>
        </Modal>
      ) : null}
    </section>
  );
}
