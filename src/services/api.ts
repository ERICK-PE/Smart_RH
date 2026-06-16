import axios, { AxiosError, type AxiosRequestConfig } from 'axios';
import type { PaginatedResponse, SessionUser, TokenPair } from '../types';
import { logError, logInfo, logWarn } from '../utils/logger';

const ACCESS_TOKEN_KEY = 'smart-rh.access';
const REFRESH_TOKEN_KEY = 'smart-rh.refresh';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Retorna o access token armazenado no navegador.
 */
export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Retorna o refresh token usado para renovar sessoes expiradas.
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Persiste tokens emitidos pelo Simple JWT apos login ou renovacao.
 */
export function setTokens(tokens: TokenPair) {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

/**
 * Remove credenciais locais quando o usuario sai ou a sessao expira.
 */
export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

/**
 * Renova o access token sem expor refresh token em logs ou mensagens.
 */
async function refreshAccessToken() {
  const refresh = getRefreshToken();
  if (!refresh) {
    logWarn('Refresh token ausente durante renovacao de sessao.');
    return null;
  }

  const response = await axios.post<TokenPair | { access: string }>(
    `${api.defaults.baseURL}/auth/token/refresh/`,
    { refresh },
  );
  const access = response.data.access;
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  logInfo('Access token renovado com sucesso.');
  return access;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;
    if (error.response?.status !== 401 || !original || original._retry) {
      return Promise.reject(error);
    }

    original._retry = true;
    refreshing = refreshing || refreshAccessToken().finally(() => {
      refreshing = null;
    });
    const access = await refreshing;
    if (!access) {
      clearTokens();
      logWarn('Sessao encerrada apos falha de renovacao.');
      return Promise.reject(error);
    }

    original.headers = {
      ...original.headers,
      Authorization: `Bearer ${access}`,
    };
    return api(original);
  },
);

/**
 * Autentica o usuario no endpoint JWT do backend.
 */
export async function login(username: string, password: string) {
  const response = await api.post<TokenPair>('/auth/token/', { username, password });
  setTokens(response.data);
  logInfo('Login realizado com sucesso.');
  return response.data;
}

/**
 * Busca o contrato de sessao usado para rotas e menus por perfil.
 */
export async function fetchMe() {
  const response = await api.get<SessionUser>('/auth/me/');
  return response.data;
}

/**
 * Lista recursos paginados no formato padrao do Django REST Framework.
 */
export async function listResource<T>(
  endpoint: string,
  params: Record<string, string | number | undefined>,
) {
  const response = await api.get<PaginatedResponse<T>>(endpoint, { params });
  return response.data;
}

/**
 * Converte erros da API em texto exibivel sem vazar detalhes tecnicos.
 */
export function extractApiError(error: unknown) {
  if (!axios.isAxiosError(error)) {
    logError('Erro inesperado fora do Axios.');
    return 'Não foi possível concluir a operação.';
  }
  const data = error.response?.data;
  if (!data) {
    logError('Erro de API sem payload de resposta.', { status: error.response?.status });
    return 'Não foi possível concluir a operação.';
  }
  if (typeof data === 'string') return data;
  if (typeof data === 'object') {
    logWarn('Erro de validacao recebido da API.', { status: error.response?.status });
    return Object.entries(data)
      .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(', ') : String(value)}`)
      .join('\n');
  }
  return 'Não foi possível concluir a operação.';
}
