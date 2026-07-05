import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { LockKeyhole } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { defaultPathForProfile } from '../auth/guards';
import { extractApiError } from '../services/api';
import type { LoginProfile } from '../types';

/**
 * Tela publica de autenticacao com redirecionamento por perfil.
 */
export function LoginPage() {
  const { login, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [profile, setProfile] = useState<LoginProfile>('funcionario');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  if (user) return <Navigate to={defaultPathForProfile(user.profile)} replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const session = await login(username, password, profile);
      const fallback = defaultPathForProfile(session.profile);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from || fallback, { replace: true });
    } catch (loginError) {
      setError(extractApiError(loginError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-[1fr_480px]">
      <section className="hidden bg-white px-12 py-10 text-ink lg:flex lg:items-center lg:justify-center">
        <div className="flex flex-col items-center text-center">
          <img
            src="/assets/smart-rh-logo-transparent.png"
            alt="SMART RH - Gestão de Pessoas com Controle e Clareza"
            className="h-auto w-full max-w-xl object-contain"
          />
        </div>
      </section>
      <section className="flex items-center justify-center bg-white px-6 py-10">
        <form
          onSubmit={submit}
          className="w-full max-w-sm rounded-md border border-[#2f90c8] bg-brand p-6 text-white shadow-soft"
        >
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-white text-brand">
              <LockKeyhole className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Entrar</h2>
              <p className="text-sm text-white/75">Use suas credenciais do SMART RH.</p>
            </div>
          </div>
          {error ? <p className="mb-4 rounded-md bg-white p-3 text-sm text-danger">{error}</p> : null}
          <label className="mb-4 block">
            <span className="mb-1 block text-sm font-medium text-white">Perfil de acesso</span>
            <select
              className="light-field focus-ring w-full rounded-md border border-white/70 bg-white px-3 py-2 text-sm text-ink"
              value={profile}
              onChange={(event) => setProfile(event.target.value as LoginProfile)}
            >
              <option value="candidato">Candidato</option>
              <option value="funcionario">Funcionário</option>
              <option value="rh">RH/Admin</option>
            </select>
          </label>
          <label className="mb-4 block">
            <span className="mb-1 block text-sm font-medium text-white">Usuário</span>
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
          <p className="mt-5 text-sm text-white/75">
            Candidato?{' '}
            <Link className="font-semibold text-white hover:underline" to="/candidato/cadastro">
              Criar cadastro
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}
