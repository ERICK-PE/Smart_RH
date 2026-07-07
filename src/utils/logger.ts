type LogContext = Record<string, unknown>;

/**
 * Mantem logs do frontend concentrados e evita registrar dados sensiveis.
 */
function writeLog(level: 'info' | 'warn' | 'error', message: string, context?: LogContext) {
  if (!import.meta.env.DEV && level !== 'error') return;

  const payload = context ? { ...context } : undefined;
  console[level](`[smart-rh] ${message}`, payload ?? '');
}

/**
 * Registra eventos informativos apenas em desenvolvimento.
 */
export function logInfo(message: string, context?: LogContext) {
  writeLog('info', message, context);
}

/**
 * Registra alertas recuperaveis sem interromper a experiencia do usuario.
 */
export function logWarn(message: string, context?: LogContext) {
  writeLog('warn', message, context);
}

/**
 * Registra falhas relevantes, mantendo o conteudo sensivel fora do console.
 */
export function logError(message: string, context?: LogContext) {
  writeLog('error', message, context);
}
