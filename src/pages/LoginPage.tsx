import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { defaultPathForProfile } from '../auth/guards';
import { extractApiError } from '../services/api';
import type { LoginProfile } from '../types';

type LoginPageProps = {
  mode?: 'internal' | 'candidate';
};

/**
 * Tela publica de autenticacao com redirecionamento por perfil.
 */
export function LoginPage({ mode = 'internal' }: LoginPageProps) {
  const { login, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [selectedProfile, setSelectedProfile] = useState<Exclude<LoginProfile, 'candidato'>>('funcionario');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const isCandidateLogin = mode === 'candidate';
  const profile: LoginProfile = isCandidateLogin ? 'candidato' : selectedProfile;

  if (user) return <Navigate to={defaultPathForProfile(user.profile)} replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const session = await login(username, password, profile);
      const fallback = defaultPathForProfile(session.profile);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      const shouldUseFrom = from && (
        (session.profile === 'candidato' && from.startsWith('/candidato')) ||
        (session.profile !== 'candidato' && !from.startsWith('/candidato'))
      );
      navigate(shouldUseFrom ? from : fallback, { replace: true });
    } catch (loginError) {
      setError(extractApiError(loginError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main
      className="flex min-h-screen items-center justify-center bg-white bg-cover bg-center px-6 py-10 lg:justify-end lg:px-12"
      style={{ backgroundImage: "url('/assets/SmartRH_login.png')" }}
    >
      <section className="flex w-full justify-center lg:w-[480px]">
        <form
          onSubmit={submit}
          className="w-full max-w-sm rounded-md border border-[#2f90c8] bg-brand p-6 text-white shadow-soft"
        >
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-white">Entrar</h2>
            <p className="text-sm text-white/75">
              {isCandidateLogin ? 'Acesso exclusivo para candidatos.' : 'Acesso interno SMART RH.'}
            </p>
          </div>
          {error ? <p className="mb-4 rounded-md bg-white p-3 text-sm text-danger">{error}</p> : null}
          {!isCandidateLogin ? (
            <label className="mb-4 block">
              <span className="mb-1 block text-sm font-medium text-white">Perfil de acesso</span>
              <select
                className="light-field focus-ring w-full rounded-md border border-white/70 bg-white px-3 py-2 text-sm text-ink"
                value={selectedProfile}
                onChange={(event) => setSelectedProfile(event.target.value as Exclude<LoginProfile, 'candidato'>)}
              >
                <option value="funcionario">Funcionario</option>
                <option value="rh">RH</option>
              </select>
            </label>
          ) : null}
          <label className="mb-4 block">
            <span className="mb-1 block text-sm font-medium text-white">Usuario</span>
            <input
              className="light-field focus-ring w-full rounded-md border border-white/70 bg-white px-3 py-2 text-sm text-ink placeholder:text-muted"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label className="mb-5 block">
            <span className="mb-1 block text-sm font-medium text-white">Senha</span>
            <input
              className="light-field focus-ring w-full rounded-md border border-white/70 bg-white px-3 py-2 text-sm text-ink placeholder:text-muted"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="focus-ring inline-flex w-full items-center justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-brand hover:bg-[#f4fbfd] disabled:cursor-not-allowed disabled:opacity-60"
          >
            Entrar
          </button>
          {isCandidateLogin ? (
            <div className="mt-5 space-y-2 text-sm text-white/75">
              <p>
                Sem cadastro?{' '}
                <Link className="font-semibold text-white hover:underline" to="/candidato/cadastro">
                  Criar cadastro
                </Link>
              </p>
            </div>
          ) : (
            <div className="mt-5 space-y-2 text-sm text-white/75">
              <p>
                <b>Sem acesso? Contate o seu Rh para validar seu acesso</b>
              </p>
            </div>
          )}
        </form>
      </section>
    </main>
  );
}
