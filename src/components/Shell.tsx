import {
  BadgeCheck,
  BrainCircuit,
  BriefcaseBusiness,
  Building2,
  ChevronsLeft,
  ChevronsRight,
  CircleUserRound,
  ClipboardCheck,
  ClipboardList,
  ClipboardPenLine,
  FileSignature,
  FileText,
  FileUser,
  IdCard,
  LayoutDashboard,
  LogOut,
  Megaphone,
  Menu,
  Milestone,
  Moon,
  SearchCheck,
  Sun,
  TrendingUp,
  UserSearch,
  UsersRound,
  type LucideIcon,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useTheme } from '../theme/ThemeContext';
import type { UserProfile } from '../types';

type NavItem = {
  label: string;
  to: string;
  icon: LucideIcon;
  profiles: UserProfile[];
};

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/rh/dashboard', icon: LayoutDashboard, profiles: ['rh_admin'] },
  { label: 'Setores', to: '/rh/setores', icon: Building2, profiles: ['rh_admin'] },
  { label: 'Cargos', to: '/rh/cargos', icon: BriefcaseBusiness, profiles: ['rh_admin'] },
  { label: 'Funcionários', to: '/rh/funcionarios', icon: IdCard, profiles: ['rh_admin'] },
  { label: 'Contratos', to: '/rh/contratos', icon: FileSignature, profiles: ['rh_admin'] },
  { label: 'Folhas', to: '/rh/folhas-pagamento', icon: FileText, profiles: ['rh_admin'] },
  { label: 'Planos', to: '/rh/planos-carreira', icon: TrendingUp, profiles: ['rh_admin'] },
  { label: 'Avaliações', to: '/rh/avaliacoes', icon: ClipboardCheck, profiles: ['rh_admin'] },
  { label: 'Análises', to: '/rh/analises-comportamentais', icon: BrainCircuit, profiles: ['rh_admin'] },
  { label: 'Vagas', to: '/rh/vagas', icon: Megaphone, profiles: ['rh_admin'] },
  { label: 'Candidatos', to: '/rh/candidatos', icon: UserSearch, profiles: ['rh_admin'] },
  { label: 'Equipe', to: '/lideranca/equipe', icon: UsersRound, profiles: ['lideranca', 'rh_admin'] },
  { label: 'Meus dados', to: '/funcionario/meus-dados', icon: BadgeCheck, profiles: ['funcionario', 'lideranca'] },
  { label: 'Contratos', to: '/funcionario/meus-contratos', icon: FileText, profiles: ['funcionario', 'lideranca'] },
  { label: 'Minha folha', to: '/funcionario/minha-folha', icon: FileSignature, profiles: ['funcionario', 'lideranca'] },
  { label: 'Plano', to: '/funcionario/meu-plano-carreira', icon: Milestone, profiles: ['funcionario', 'lideranca'] },
  { label: 'Avaliações', to: '/funcionario/minhas-avaliacoes', icon: ClipboardList, profiles: ['funcionario', 'lideranca'] },
  { label: 'Perfil', to: '/candidato/perfil', icon: CircleUserRound, profiles: ['candidato'] },
  { label: 'Currículo', to: '/candidato/curriculo', icon: FileUser, profiles: ['candidato'] },
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
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const displayName = user?.nome || user?.username || 'Usuário';
  const visibleItems = navItems.filter((item) => item.profiles.includes(user?.profile ?? null));

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="min-h-screen bg-[#f6fbfd] transition-colors dark:bg-[#1f2930]">
      <aside
        className={`fixed inset-y-0 left-0 z-30 hidden flex-col border-r border-line bg-white transition-all duration-200 dark:border-slate-700 dark:bg-slate-950 lg:flex ${
          isSidebarCollapsed ? 'w-20' : 'w-72'
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
              <p className="max-w-44 truncate text-xs text-muted dark:text-slate-400">{displayName}</p>
            </div>
          )}
          <button
            type="button"
            onClick={() => setIsSidebarCollapsed((current) => !current)}
            className="focus-ring absolute -right-3 top-1/2 z-40 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full border border-line bg-white text-ink shadow-md transition-colors hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            aria-label={isSidebarCollapsed ? 'Expandir menu lateral' : 'Recolher menu lateral'}
            title={isSidebarCollapsed ? 'Expandir menu' : 'Recolher menu'}
          >
            {isSidebarCollapsed ? <ChevronsRight className="h-3.5 w-3.5" /> : <ChevronsLeft className="h-3.5 w-3.5" />}
          </button>
        </div>

        <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto overflow-x-hidden px-3 py-4">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                aria-label={item.label}
                title={isSidebarCollapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `flex items-center rounded-md py-2.5 text-[15px] font-semibold transition-colors ${
                    isSidebarCollapsed ? 'justify-center px-0' : 'gap-3.5 px-3'
                  } ${
                    isActive
                      ? 'bg-brand text-white'
                      : 'text-slate-700 hover:bg-panel hover:text-ink dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                  }`
                }
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!isSidebarCollapsed && item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <div className={`transition-all duration-200 ${isSidebarCollapsed ? 'lg:pl-20' : 'lg:pl-72'}`}>
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-white/95 px-4 backdrop-blur transition-colors dark:border-slate-700 dark:bg-slate-950/95 lg:px-8">
          <div className="flex items-center gap-3">
            <Menu className="h-5 w-5 text-muted dark:text-slate-400 lg:hidden" />
            <p className="truncate text-base font-semibold text-ink dark:text-slate-100 sm:text-lg">
              BEM VINDO(A) {displayName}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleTheme}
              className="focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
              aria-pressed={theme === 'dark'}
              aria-label={theme === 'dark' ? 'Alternar para tema claro' : 'Alternar para tema escuro'}
              title={theme === 'dark' ? 'Tema claro' : 'Tema escuro'}
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              <span>{theme === 'dark' ? 'Claro' : 'Escuro'}</span>
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="focus-ring inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:bg-panel dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            >
              <LogOut className="h-4 w-4" />
              Sair
            </button>
          </div>
        </header>
        <main className="px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
