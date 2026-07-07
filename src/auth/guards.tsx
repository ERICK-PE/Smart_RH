import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import type { UserProfile } from '../types';
import { PageState } from '../components/PageState';

/**
 * Define a primeira tela segura para cada perfil reconhecido pelo backend.
 */
export function defaultPathForProfile(profile: UserProfile) {
  if (profile === 'rh_admin') return '/rh/dashboard';
  if (profile === 'lideranca') return '/funcionario/meus-dados';
  if (profile === 'funcionario') return '/funcionario/meus-dados';
  if (profile === 'candidato') return '/candidato/vagas';
  return '/acesso-negado';
}

/**
 * Bloqueia rotas internas quando nao existe sessao autenticada.
 */
export function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) return <PageState title="Carregando sessão" />;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
  return <Outlet />;
}

/**
 * Restringe grupos de rotas ao perfil calculado por /api/auth/me/.
 */
export function ProfileRoute({ profiles }: { profiles: UserProfile[] }) {
  const { user } = useAuth();
  if (!profiles.includes(user?.profile ?? null)) {
    return <Navigate to="/acesso-negado" replace />;
  }
  return <Outlet />;
}
