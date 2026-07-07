/**
 * Converte valores crus da API para exibição em tabelas e detalhes.
 */
export function displayValue(value: unknown) {
  if (value === null || value === undefined || value === '') return 'Não informado';
  if (typeof value === 'boolean') return value ? 'Sim' : 'Não';
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    return String(record.nome || record.titulo || record.username || record.id || record.pk || 'Relacionado');
  }
  return String(value);
}

/**
 * Extrai o identificador configurado para operações de CRUD genérico.
 */
export function getRecordId(record: Record<string, unknown>, idField: string) {
  return String(record[idField] ?? '');
}

/**
 * Detecta máscaras aplicadas pelo backend em dados sensíveis.
 */
export function isMasked(value: unknown) {
  return typeof value === 'string' && (value.includes('***') || value.includes('********'));
}
