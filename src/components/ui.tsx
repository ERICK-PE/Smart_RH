import { AlertTriangle, Check, Eye, Pencil, Plus, Search, Trash2, X } from 'lucide-react';
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

function renderCellValue(value: unknown, maxLength?: number) {
  const rendered = displayValue(value);
  if (!maxLength || rendered.length <= maxLength) return rendered;
  return `${rendered.slice(0, maxLength).trimEnd()}...`;
}

/**
 * Formulario generico orientado por configuracao de campos.
 */
function ResourceForm({
  fields,
  initial,
  onSubmit,
  submitting,
}: {
  fields: FieldConfig[];
  initial?: ApiRecord | null;
  onSubmit: (data: ApiRecord | FormData) => void;
  submitting?: boolean;
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
          Salvar
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
  const [open, setOpen] = useState(false);
  const relation = field.relation;
  const query = useQuery({
    queryKey: ['relation-options', relation?.endpoint],
    queryFn: () => listResource<ApiRecord>(relation?.endpoint ?? '', { page: 1, page_size: 100 }),
    enabled: Boolean(relation),
  });
  const rows = query.data?.results ?? [];
  const selected = rows.find((row) => String(row[relation?.idField ?? '']) === value);

  return (
    <div className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((current) => !current)}
        className="focus-ring flex w-full items-center justify-between rounded-md border border-line bg-white px-3 py-2 text-left text-sm text-ink disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
      >
        <span>{selected ? relationDisplay(selected, field) : 'Selecione'}</span>
        <span className="text-xs text-muted dark:text-slate-400">abrir lista</span>
      </button>
      <input className="sr-only" tabIndex={-1} value={value} required={required} onChange={() => undefined} />

      {open ? (
        <div className="absolute z-20 mt-2 max-h-72 w-full overflow-auto rounded-md border border-line bg-white shadow-soft dark:border-slate-700 dark:bg-slate-950">
          {query.isLoading ? (
            <div className="px-3 py-3 text-sm text-muted dark:text-slate-400">Carregando opções...</div>
          ) : rows.length === 0 ? (
            <div className="px-3 py-3 text-sm text-muted dark:text-slate-400">Nenhum registro disponível.</div>
          ) : (
            <table className="min-w-full text-sm">
              <thead className="bg-panel dark:bg-slate-900">
                <tr>
                  <th className="px-3 py-2 text-left font-semibold text-ink dark:text-slate-100">ID</th>
                  <th className="px-3 py-2 text-left font-semibold text-ink dark:text-slate-100">{field.label}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line dark:divide-slate-700">
                {rows.map((row) => {
                  const optionValue = String(row[relation?.idField ?? '']);
                  return (
                    <tr
                      key={optionValue}
                      className="cursor-pointer hover:bg-panel dark:hover:bg-slate-900"
                      onClick={() => {
                        onChange(optionValue);
                        setOpen(false);
                      }}
                    >
                      <td className="px-3 py-2 text-muted dark:text-slate-400">{optionValue}</td>
                      <td className="px-3 py-2 text-ink dark:text-slate-100">{relationDisplay(row, field)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      ) : null}
    </div>
  );
}

/**
 * Tela CRUD generica para recursos DRF paginados.
 */
export function ResourcePage({ config }: { config: ResourceConfig }) {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<ApiRecord | null>(null);
  const [viewing, setViewing] = useState<ApiRecord | null>(null);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState<ApiRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const queryKey = useMemo(() => [config.endpoint, page, search, filters], [config.endpoint, page, search, filters]);

  const query = useQuery({
    queryKey,
    queryFn: () =>
      listResource<ApiRecord>(config.endpoint, {
        page,
        search: search || undefined,
        ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value)),
      }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [config.endpoint] });

  const saveMutation = useMutation({
    mutationFn: async ({ record, payload }: { record?: ApiRecord | null; payload: ApiRecord | FormData }) => {
      const id = record ? getRecordId(record, config.idField) : null;
      if (id) return api.patch(`${config.endpoint}${id}/`, payload);
      return api.post(config.endpoint, payload);
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

      <div className="mb-4 flex flex-col gap-3 rounded-md border border-line bg-white p-4 md:flex-row md:items-center dark:border-slate-700 dark:bg-slate-950">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted" />
          <input
            className="focus-ring w-full rounded-md border border-line bg-white py-2 pl-9 pr-3 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            placeholder={config.searchPlaceholder || 'Buscar'}
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </div>
        {config.filters?.map((filter) => (
          <label key={filter.name} className="min-w-48">
            <span className="mb-1 block text-xs font-semibold uppercase text-muted dark:text-slate-400">{filter.label}</span>
            {filter.type === 'select' ? (
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
                        <SensitiveValue value={renderCellValue(row[column.key], column.maxLength)} />
                        {column.maxLength ? (
                          <span className="sr-only">{displayValue(row[column.key])}</span>
                        ) : null}
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
                            className="focus-ring rounded-md border border-line p-2 text-danger hover:bg-red-50 dark:border-slate-700 dark:hover:bg-red-950/30"
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
        <Modal title={`Novo ${config.title}`} onClose={() => setCreating(false)}>
          <ResourceForm
            fields={config.fields}
            submitting={saveMutation.isPending}
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
