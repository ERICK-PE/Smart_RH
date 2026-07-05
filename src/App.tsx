import { Navigate, Route, Routes } from 'react-router-dom';
import { Shell } from './components/Shell';
import { ResourcePage } from './components/ui';
import { ProtectedRoute, ProfileRoute, defaultPathForProfile } from './auth/guards';
import { useAuth } from './auth/AuthContext';
import { resources } from './resources';
import { LoginPage } from './pages/LoginPage';
import { CandidateRegisterPage } from './pages/CandidateRegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { EmployeeAdminProfilePage } from './pages/EmployeeAdminProfilePage';
import { LeadershipEmployeeDetailPage, LeadershipTeamPage } from './pages/LeadershipPages';
import {
  MyCareerPlanPage,
  MyContractsPage,
  MyDataPage,
  MyReviewsPage,
} from './pages/EmployeeSelfPages';
import {
  CandidateApplicationsPage,
  CandidateJobsPage,
  CandidateProfilePage,
  CandidateResumePage,
} from './pages/CandidatePages';
import { RecruitingProcessPage } from './pages/RecruitingProcessPage';
import { PageState } from './components/PageState';

/**
 * Redireciona a raiz para a area inicial do perfil autenticado.
 */
function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={defaultPathForProfile(user?.profile ?? null)} replace />;
}

/**
 * Tela unica para recusas de permissao vindas dos guards do frontend.
 */
function AccessDeniedPage() {
  return (
    <PageState
      title="Acesso negado"
      description="Seu usuário não possui permissão para acessar esta área."
      variant="error"
    />
  );
}

/**
 * Define todas as rotas publicas e protegidas do SMART RH.
 */
export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/candidato/cadastro" element={<CandidateRegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<Shell />}>
          <Route index element={<HomeRedirect />} />
          <Route path="/acesso-negado" element={<AccessDeniedPage />} />

          <Route element={<ProfileRoute profiles={['rh_admin']} />}>
            <Route path="/rh/dashboard" element={<DashboardPage />} />
            <Route path="/rh/setores" element={<ResourcePage config={resources.setores} />} />
            <Route path="/rh/cargos" element={<ResourcePage config={resources.cargos} />} />
            <Route path="/rh/funcionarios" element={<ResourcePage config={resources.funcionarios} />} />
            <Route path="/rh/funcionarios/:id" element={<EmployeeAdminProfilePage />} />
            <Route path="/rh/contratos" element={<ResourcePage config={resources.contratos} />} />
            <Route path="/rh/planos-carreira" element={<ResourcePage config={resources.planos} />} />
            <Route path="/rh/avaliacoes" element={<ResourcePage config={resources.avaliacoes} />} />
            <Route path="/rh/analises-comportamentais" element={<ResourcePage config={resources.analises} />} />
            <Route path="/rh/vagas" element={<ResourcePage config={resources.vagas} />} />
            <Route path="/rh/vagas/:id/processos" element={<RecruitingProcessPage />} />
            <Route path="/rh/candidatos" element={<ResourcePage config={resources.candidatosAdmin} />} />
          </Route>

          <Route element={<ProfileRoute profiles={['lideranca', 'rh_admin']} />}>
            <Route path="/lideranca/equipe" element={<LeadershipTeamPage />} />
            <Route path="/lideranca/funcionarios/:id" element={<LeadershipEmployeeDetailPage />} />
          </Route>

          <Route element={<ProfileRoute profiles={['funcionario']} />}>
            <Route path="/funcionario/meus-dados" element={<MyDataPage />} />
            <Route path="/funcionario/meus-contratos" element={<MyContractsPage />} />
            <Route path="/funcionario/meu-plano-carreira" element={<MyCareerPlanPage />} />
            <Route path="/funcionario/minhas-avaliacoes" element={<MyReviewsPage />} />
          </Route>

          <Route element={<ProfileRoute profiles={['candidato']} />}>
            <Route path="/candidato/perfil" element={<CandidateProfilePage />} />
            <Route path="/candidato/curriculo" element={<CandidateResumePage />} />
            <Route path="/candidato/vagas" element={<CandidateJobsPage />} />
            <Route path="/candidato/candidaturas" element={<CandidateApplicationsPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
