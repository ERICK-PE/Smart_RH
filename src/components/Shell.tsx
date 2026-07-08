import {
  BadgeCheck,
  Building2,
  ChevronsLeft,
  ChevronsRight,
  CircleUserRound,
  ClipboardCheck,
  ClipboardList,
  ClipboardPenLine,
  FileSignature,
  FileText,
  IdCard,
  LayoutDashboard,
  LogOut,
  Megaphone,
  Menu,
  Milestone,
  Moon,
  SearchCheck,
  Sun,
  UsersRound,
  type LucideIcon,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useTheme } from '../theme/ThemeContext';
import type { UserProfile } from '../types';
import { BehavioralAnalysisNotifications } from './BehavioralAnalysisNotifications';
import { EmployeeAgentChat } from './EmployeeAgentChat';

type NavChild = {
  label: string;
  to: string;
  profiles: UserProfile[];
};

type NavItem = {
  label: string;
  to: string;
  icon: LucideIcon;
  profiles: UserProfile[];
  children?: NavChild[];
};

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/rh/dashboard', icon: LayoutDashboard, profiles: ['rh_admin'] },
  {
    label: 'Setor+',
    to: '/rh/setores',
    icon: Building2,
    profiles: ['rh_admin'],
    children: [
      { label: 'Cargos', to: '/rh/cargos', profiles: ['rh_admin'] },
      { label: 'Equipe', to: '/lideranca/equipe', profiles: ['rh_admin'] },
      { label: 'Planos', to: '/rh/planos-carreira', profiles: ['rh_admin'] },
    ],
  },
  {
    label: 'Funcionários+',
    to: '/rh/funcionarios',
    icon: IdCard,
    profiles: ['rh_admin'],
    children: [
      { label: 'Contratos', to: '/rh/contratos', profiles: ['rh_admin'] },
      { label: 'Folhas', to: '/rh/folhas-pagamento', profiles: ['rh_admin'] },
    ],
  },
  {
    label: 'Avaliações+',
    to: '/rh/avaliacoes',
    icon: ClipboardCheck,
    profiles: ['rh_admin'],
    children: [
      { label: 'Análises', to: '/rh/analises-comportamentais', profiles: ['rh_admin'] },
    ],
  },
  {
    label: 'Vagas+',
    to: '/rh/vagas',
    icon: Megaphone,
    profiles: ['rh_admin'],
    children: [
      { label: 'Candidatos', to: '/rh/candidatos', profiles: ['rh_admin'] },
    ],
  },
  { label: 'Equipe', to: '/lideranca/equipe', icon: UsersRound, profiles: ['lideranca'] },
  { label: 'Meus dados', to: '/funcionario/meus-dados', icon: BadgeCheck, profiles: ['funcionario', 'lideranca'] },
  { label: 'Contratos', to: '/funcionario/meus-contratos', icon: FileText, profiles: ['funcionario', 'lideranca'] },
  { label: 'Minha folha', to: '/funcionario/minha-folha', icon: FileSignature, profiles: ['funcionario', 'lideranca'] },
  { label: 'Plano', to: '/funcionario/meu-plano-carreira', icon: Milestone, profiles: ['funcionario', 'lideranca'] },
  { label: 'Avaliações', to: '/funcionario/minhas-avaliacoes', icon: ClipboardList, profiles: ['funcionario', 'lideranca'] },
  { label: 'Perfil', to: '/candidato/perfil', icon: CircleUserRound, profiles: ['candidato'] },
  { label: 'Vagas', to: '/candidato/vagas', icon: SearchCheck, profiles: ['candidato'] },
  { label: 'Candidaturas', to: '/candidato/candidaturas', icon: ClipboardPenLine, profiles: ['candidato'] },
];

/**
 * Layout autenticado com navegacao filtrada pelo perfil do usuario.
 */
export function Shell() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const displayName = user?.nome || user?.username || 'Usuário';
  const visibleItems = navItems.filter((item) => item.profiles.includes(user?.profile ?? null));

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  function isPathActive(path: string) {
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  }

  return (
    <div className="min-h-screen bg-[#f6fbfd] transition-colors dark:bg-[#1f2930]">
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex-col border-r border-line bg-white transition-all duration-200 dark:border-slate-700 dark:bg-slate-950 ${
          isMobileSidebarOpen ? 'flex w-60' : 'hidden'
        } lg:flex ${
          isSidebarCollapsed ? 'lg:w-20' : 'lg:w-60'
        }`}
      >
        <div
          className={`relative flex h-16 shrink-0 items-center border-b border-line dark:border-slate-700 ${
            isSidebarCollapsed ? 'justify-center px-3' : 'gap-3 px-6 pr-12'
          }`}
        >
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-brand text-sm font-bold text-white">
            RH
          </div>
          {!isSidebarCollapsed && (
            <div>
              <p className="text-sm font-semibold text-ink dark:text-slate-100">SMART RH</p>
            </div>
          )}
          <button
            type="button"
            onClick={() => setIsSidebarCollapsed((current) => !current)}
            className="focus-ring absolute -right-3 top-1/2 z-40 hidden h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full border border-line bg-white text-ink shadow-md transition-colors hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800 lg:flex"
            aria-label={isSidebarCollapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'}
            title={isSidebarCollapsed ? 'Expandir menu' : 'Recolher menu'}
          >
            {isSidebarCollapsed ? <ChevronsRight className="h-3.5 w-3.5" /> : <ChevronsLeft className="h-3.5 w-3.5" />}
          </button>
        </div>

        <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto overflow-x-hidden py-4 pl-3">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            const visibleChildren = item.children?.filter((child) => child.profiles.includes(user?.profile ?? null)) ?? [];
            const childActive = visibleChildren.some((child) => isPathActive(child.to));

            return (
              <div key={item.to}>
                <NavLink
                  to={item.to}
                  aria-label={item.label}
                  title={isSidebarCollapsed ? item.label : undefined}
                  className={({ isActive }) =>
                    `flex items-center rounded-l-md rounded-r-none py-2.5 text-[15px] font-semibold transition-colors ${
                      isSidebarCollapsed ? 'justify-center px-0' : 'gap-3.5 pl-3 pr-0'
                    } ${
                      isActive || childActive
                        ? 'bg-brand text-white'
                        : 'text-slate-700 hover:bg-panel hover:text-ink dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                    }`
                  }
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {!isSidebarCollapsed && item.label}
                </NavLink>
                {!isSidebarCollapsed && visibleChildren.length ? (
                  <div className="mt-1 space-y-1 pl-11">
                    {visibleChildren.map((child) => (
                      <NavLink
                        key={child.to}
                        to={child.to}
                        className={({ isActive }) =>
                          `block rounded-l-md rounded-r-none py-1.5 pl-2 pr-0 text-sm font-medium transition-colors ${
                            isActive
                              ? 'bg-brand/15 text-brand dark:bg-brand/20 dark:text-sky-300'
                              : 'text-slate-500 hover:bg-panel hover:text-ink dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'
                          }`
                        }
                      >
                        {child.label}
                      </NavLink>
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })}
        </nav>
      </aside>

      <div
        className={`transition-all duration-200 ${
          isMobileSidebarOpen ? 'pl-60' : 'pl-0'
        } ${isSidebarCollapsed ? 'lg:pl-20' : 'lg:pl-60'}`}
      >
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-white/95 px-4 backdrop-blur transition-colors dark:border-slate-700 dark:bg-slate-950/95 lg:px-8">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md text-muted hover:bg-panel hover:text-ink dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white lg:hidden"
              aria-label={isMobileSidebarOpen ? 'Fechar menu lateral' : 'Abrir menu lateral'}
              onClick={() => setIsMobileSidebarOpen((current) => !current)}
            >
              <Menu className="h-5 w-5" />
            </button>
            <p className="truncate text-base font-semibold text-ink dark:text-slate-100 sm:text-lg">
              BEM VINDO(A) {displayName}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <BehavioralAnalysisNotifications />
            <button
              type="button"
              onClick={toggleTheme}
              className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-line bg-white text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
              aria-pressed={theme === 'dark'}
              aria-label={theme === 'dark' ? 'Alternar para tema claro' : 'Alternar para tema escuro'}
              title={theme === 'dark' ? 'Tema claro' : 'Tema escuro'}
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md bg-red-600 text-white hover:bg-red-700 dark:bg-red-600 dark:text-white dark:hover:bg-red-700"
              aria-label="Sair"
              title="Sair"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>
        <main className="px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
      <EmployeeAgentChat />
    </div>
  );
}
