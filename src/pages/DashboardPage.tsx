import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, BriefcaseBusiness, ClipboardCheck, Gauge, Target, UsersRound } from 'lucide-react';
import type { CSSProperties, ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { PageState } from '../components/PageState';
import { PageHeader } from '../components/ui';
import { api } from '../services/api';

type CountItem = {
  label: string;
  total: number;
};

type DashboardPayload = {
  resumo: {
    funcionarios_ativos: number;
    funcionarios_sem_contrato: number;
    funcionarios_com_plano_percentual: number;
    total_vagas: number;
  };
  empresa: {
    funcionarios_por_setor: CountItem[];
    funcionarios_por_cargo: CountItem[];
    funcionarios_por_status: CountItem[];
  };
  avaliacoes: {
    planos_carreira_cobertura: {
      com_plano: number;
      sem_plano: number;
      percentual_com_plano: number;
    };
    media_avaliacoes: number | null;
    avaliacoes_pendentes: number;
  };
  recrutamento: {
    funil: {
      vagas: number;
      candidatos: number;
      candidaturas: number;
      contratados: number;
    };
    candidatos_por_vaga: CountItem[];
    vagas_por_status: CountItem[];
  };
};

const CHART_GREEN = 'rgb(91, 167, 101)';

function toNumber(value: unknown) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function maxTotal(items: CountItem[]) {
  return Math.max(1, ...items.map((item) => toNumber(item.total)));
}

function SummaryCard({
  label,
  value,
  tone = 'neutral',
  suffix = '',
}: {
  label: string;
  value: number | string;
  tone?: 'neutral' | 'green' | 'yellow' | 'red';
  suffix?: string;
}) {
  const toneStyle: Record<'green' | 'yellow' | 'red', CSSProperties> = {
    green: { backgroundColor: 'rgb(91, 167, 101)', color: '#fff' },
    yellow: { backgroundColor: 'rgb(245, 158, 11)', color: '#fff' },
    red: { backgroundColor: 'rgb(185, 28, 28)', color: '#fff' },
  };
  const toneClass = {
    neutral: 'border-line bg-white dark:border-slate-700 dark:bg-slate-950',
    green: 'border-line dark:border-slate-700',
    yellow: 'border-line dark:border-slate-700',
    red: 'border-line dark:border-slate-700',
  }[tone];
  const labelClass = tone === 'neutral' ? 'text-muted dark:text-slate-400' : 'text-current opacity-75';

  return (
    <article className={`rounded-md border p-4 shadow-soft ${toneClass}`} style={tone === 'neutral' ? undefined : toneStyle[tone]}>
      <p className={`text-xs font-semibold uppercase ${labelClass}`}>{label}</p>
      <p className="mt-2 text-3xl font-bold">
        {value}
        {suffix}
      </p>
    </article>
  );
}

function ChartCard({
  title,
  description,
  icon: Icon,
  children,
}: {
  title: string;
  description: string;
  icon: typeof UsersRound;
  children: ReactNode;
}) {
  return (
    <article className="rounded-md border border-line bg-white p-4 shadow-soft dark:border-slate-700 dark:bg-slate-950">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-panel text-brand dark:bg-slate-900">
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold text-ink dark:text-slate-100">{title}</h3>
          <p className="text-sm text-muted dark:text-slate-400">{description}</p>
        </div>
      </div>
      {children}
    </article>
  );
}

function VerticalBarChart({ items }: { items: CountItem[] }) {
  const max = maxTotal(items);
  if (!items.length) return <p className="text-sm text-muted">Sem dados.</p>;

  return (
    <div className="h-72 overflow-x-auto border-b border-line dark:border-slate-700">
      <div className="flex h-full min-w-full items-end justify-center gap-8 px-4 pb-2">
        {items.map((item) => {
          const height = Math.max(6, (toNumber(item.total) / max) * 100);
          return (
            <div key={item.label} className="flex min-w-24 flex-col items-center gap-2">
              <div className="flex h-40 w-12 items-end rounded-t bg-panel dark:bg-slate-900">
                <div className="w-full rounded-t" style={{ height: `${height}%`, backgroundColor: CHART_GREEN }} />
              </div>
              <span className="text-xs font-bold text-ink dark:text-slate-100">{item.total}</span>
              <span className="max-w-28 text-center text-xs text-muted dark:text-slate-400">{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function HorizontalBarChart({ items }: { items: CountItem[] }) {
  const max = maxTotal(items);
  if (!items.length) return <p className="text-sm text-muted">Sem dados.</p>;

  return (
    <div className="max-h-96 space-y-3 overflow-y-auto pr-2">
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-1 flex items-center justify-between gap-3 text-sm">
            <span className="font-medium text-ink dark:text-slate-100">{item.label}</span>
            <span className="font-bold text-ink dark:text-slate-100">{item.total}</span>
          </div>
          <div className="h-3 rounded-full bg-panel dark:bg-slate-900">
            <div
              className="h-full rounded-full"
              style={{ width: `${(toNumber(item.total) / max) * 100}%`, backgroundColor: CHART_GREEN }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function DonutChart({ items }: { items: CountItem[] }) {
  const total = items.reduce((sum, item) => sum + toNumber(item.total), 0);
  if (!total) return <p className="text-sm text-muted">Sem dados.</p>;

  let offset = 25;
  const colors = [CHART_GREEN, '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];
  const statusColors: Record<string, string> = {
    inativo: '#dc2626',
    inativa: '#dc2626',
    inativos: '#dc2626',
    inativas: '#dc2626',
  };
  const segments = items.map((item, index) => {
    const value = (toNumber(item.total) / total) * 100;
    const normalizedLabel = item.label.toLowerCase().trim();
    const segment = { ...item, value, color: statusColors[normalizedLabel] ?? colors[index % colors.length], offset };
    offset -= value;
    return segment;
  });

  return (
    <div className="flex min-h-72 flex-col items-center justify-center gap-4 text-center">
      <svg viewBox="0 0 42 42" className="h-52 w-52">
        <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="currentColor" strokeWidth="8" className="text-panel dark:text-slate-900" />
        {segments.map((segment) => (
          <circle
            key={segment.label}
            cx="21"
            cy="21"
            r="15.915"
            fill="transparent"
            stroke={segment.color}
            strokeWidth="8"
            strokeDasharray={`${segment.value} ${100 - segment.value}`}
            strokeDashoffset={segment.offset}
          />
        ))}
      </svg>
      <div className="flex flex-wrap justify-center gap-x-5 gap-y-2 text-sm">
        {segments.map((segment) => (
          <div key={segment.label} className="flex items-center justify-center gap-2">
            <span className="h-3 w-3 rounded-full" style={{ backgroundColor: segment.color }} />
            <span className="text-muted dark:text-slate-400">{segment.label}</span>
            <strong className="text-ink dark:text-slate-100">{segment.total}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProgressCoverage({ comPlano, semPlano, percentual }: { comPlano: number; semPlano: number; percentual: number }) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-muted dark:text-slate-400">Com plano</span>
        <strong className="text-ink dark:text-slate-100">{percentual.toFixed(2)}%</strong>
      </div>
      <div className="h-5 rounded-full bg-panel dark:bg-slate-900">
        <div
          className="h-full rounded-full"
          style={{ width: `${Math.min(100, Math.max(0, percentual))}%`, backgroundColor: CHART_GREEN }}
        />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-md bg-panel p-3 dark:bg-slate-900">
          <p className="text-muted dark:text-slate-400">Com plano</p>
          <strong>{comPlano}</strong>
        </div>
        <div className="rounded-md bg-panel p-3 dark:bg-slate-900">
          <p className="text-muted dark:text-slate-400">Sem plano</p>
          <strong>{semPlano}</strong>
        </div>
      </div>
    </div>
  );
}

function GaugeChart({ value }: { value: number | null }) {
  const score = value === null ? 0 : Math.min(10, Math.max(0, value));
  const percent = score / 10;
  const angle = -90 + percent * 180;

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 220 130" className="h-40 w-full max-w-72">
        <path d="M30 110 A80 80 0 0 1 190 110" fill="none" stroke="currentColor" strokeWidth="18" className="text-panel dark:text-slate-900" />
        <path d="M30 110 A80 80 0 0 1 190 110" fill="none" stroke={CHART_GREEN} strokeWidth="18" strokeDasharray={`${percent * 251} 251`} strokeLinecap="round" />
        <line
          x1="110"
          y1="110"
          x2={110 + Math.cos((angle * Math.PI) / 180) * 62}
          y2={110 + Math.sin((angle * Math.PI) / 180) * 62}
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
        />
        <circle cx="110" cy="110" r="6" fill="currentColor" />
      </svg>
      <strong className="text-3xl text-ink dark:text-slate-100">{value === null ? '-' : value.toFixed(2)}</strong>
      <span className="text-sm text-muted dark:text-slate-400">media de 0 a 10</span>
    </div>
  );
}

function FunnelChart({ data }: { data: DashboardPayload['recrutamento']['funil'] }) {
  const steps = [
    { label: 'Vagas', value: data.vagas },
    { label: 'Candidatos', value: data.candidatos },
    { label: 'Candidaturas', value: data.candidaturas },
    { label: 'Contratados', value: data.contratados },
  ];
  const max = Math.max(1, ...steps.map((step) => step.value));

  return (
    <div className="space-y-3">
      {steps.map((step) => (
        <div
          key={step.label}
          className="mx-auto rounded-md px-4 py-3 text-center text-sm font-semibold text-white"
          style={{ width: `${Math.max(32, (step.value / max) * 100)}%`, backgroundColor: CHART_GREEN }}
        >
          {step.label}: {step.value}
        </div>
      ))}
    </div>
  );
}

function contractAlertTone(value: number) {
  if (value >= 3) return 'red';
  if (value > 0 && value < 3) return 'yellow';
  return 'green';
}

/**
 * Painel RH que consolida indicadores administrativos em blocos visuais.
 */
export function DashboardPage() {
  const query = useQuery({
    queryKey: ['dashboard-rh'],
    queryFn: async () => {
      const response = await api.get<DashboardPayload>('/dashboard/rh/');
      return response.data;
    },
  });

  if (query.isLoading) return <PageState title="Carregando indicadores" />;
  if (query.isError || !query.data) return <PageState title="Nao foi possivel carregar o dashboard" variant="error" />;

  const data = query.data;

  return (
    <section>
      <PageHeader title="Dashboard RH" description="Indicadores consolidados para acompanhamento operacional." />

      <div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="Funcionarios ativos" value={data.resumo.funcionarios_ativos} />
        <SummaryCard
          label="Funcionarios sem contrato"
          value={data.resumo.funcionarios_sem_contrato}
          tone={contractAlertTone(data.resumo.funcionarios_sem_contrato)}
        />
        <SummaryCard label="Funcionarios com plano" value={data.resumo.funcionarios_com_plano_percentual.toFixed(2)} suffix="%" />
        <SummaryCard label="Vagas" value={data.resumo.total_vagas} />
      </div>

      <div className="space-y-6">
        <section>
          <h2 className="mb-3 text-lg font-semibold text-ink dark:text-slate-100">Empresa</h2>
          <div className="grid gap-4 xl:grid-cols-3">
            <ChartCard title="Organizacao" description="Funcionarios por setor." icon={UsersRound}>
              <VerticalBarChart items={data.empresa.funcionarios_por_setor} />
            </ChartCard>
            <ChartCard title="Cargos" description="Quantidade por cargo." icon={BriefcaseBusiness}>
              <HorizontalBarChart items={data.empresa.funcionarios_por_cargo} />
            </ChartCard>
            <ChartCard title="Funcionarios" description="Status dos funcionarios." icon={UsersRound}>
              <DonutChart items={data.empresa.funcionarios_por_status} />
            </ChartCard>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-ink dark:text-slate-100">Avaliacoes</h2>
          <div className="grid gap-4 xl:grid-cols-3">
            <ChartCard title="Planos de carreira" description="Funcionarios com plano x sem plano." icon={ClipboardCheck}>
              <ProgressCoverage
                comPlano={data.avaliacoes.planos_carreira_cobertura.com_plano}
                semPlano={data.avaliacoes.planos_carreira_cobertura.sem_plano}
                percentual={data.avaliacoes.planos_carreira_cobertura.percentual_com_plano}
              />
            </ChartCard>
            <ChartCard title="Avaliacoes" description="Media das avaliacoes de desempenho." icon={Gauge}>
              <GaugeChart value={data.avaliacoes.media_avaliacoes} />
            </ChartCard>
            <ChartCard title="Avaliacoes pendentes" description="Funcionarios ativos sem avaliacao registrada." icon={AlertTriangle}>
              <div className="flex min-h-44 flex-col items-center justify-center gap-3 text-center">
                <strong className="text-6xl text-ink dark:text-slate-100">{data.avaliacoes.avaliacoes_pendentes}</strong>
                <Link className="focus-ring inline-flex w-fit rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand/90" to="/rh/avaliacoes">
                  Abrir avaliacoes
                </Link>
              </div>
            </ChartCard>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-ink dark:text-slate-100">Recrutamento</h2>
          <div className="grid gap-4 xl:grid-cols-3">
            <ChartCard title="Funil de recrutamento" description="Vagas, candidatos, candidaturas e contratados." icon={Target}>
              <FunnelChart data={data.recrutamento.funil} />
            </ChartCard>
            <ChartCard title="Candidatos por vaga" description="Concentracao de candidaturas por vaga." icon={UsersRound}>
              <VerticalBarChart items={data.recrutamento.candidatos_por_vaga} />
            </ChartCard>
            <ChartCard title="Vagas abertas x fechadas" description="Quantitativo por status da vaga." icon={BriefcaseBusiness}>
              <DonutChart items={data.recrutamento.vagas_por_status} />
            </ChartCard>
          </div>
        </section>
      </div>
    </section>
  );
}
