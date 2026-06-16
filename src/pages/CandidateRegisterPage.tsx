import { useState, type ChangeEvent, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FileUp, X } from 'lucide-react';
import { api, extractApiError } from '../services/api';
import { Button, PageHeader } from '../components/ui';

const MAX_FILE_SIZE = 2 * 1024 * 1024;

const initial = {
  username: '',
  password: '',
  cpf_candidato: '',
  nome: '',
  email: '',
  telefone: '',
  curriculo: '',
};

type ResumeAttachment = {
  name: string;
  type: string;
  size: number;
  dataUrl: string;
};

/**
 * Tela publica de registro de usuario candidato.
 */
export function CandidateRegisterPage() {
  const [values, setValues] = useState(initial);
  const [attachments, setAttachments] = useState<ResumeAttachment[]>([]);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  function update(name: keyof typeof initial, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  /**
   * Remove anexo antes do envio do cadastro publico.
   */
  function removeAttachment(name: string) {
    setAttachments((current) => current.filter((file) => file.name !== name));
  }

  /**
   * Le arquivos locais e os converte para data URL no campo curriculo.
   */
  async function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files || []);
    setError('');

    const converted = await Promise.all(
      files.map(
        (file) =>
          new Promise<ResumeAttachment>((resolve, reject) => {
            if (file.size > MAX_FILE_SIZE) {
              reject(new Error(`O arquivo ${file.name} excede 2 MB.`));
              return;
            }

            const reader = new FileReader();
            reader.onload = () =>
              resolve({
                name: file.name,
                type: file.type || 'application/octet-stream',
                size: file.size,
                dataUrl: String(reader.result),
              });
            reader.onerror = () => reject(new Error(`Não foi possível ler ${file.name}.`));
            reader.readAsDataURL(file);
          }),
      ),
    ).catch((fileError: Error) => {
      setError(fileError.message);
      return [];
    });

    setAttachments((current) => {
      const names = new Set(current.map((file) => file.name));
      return [...current, ...converted.filter((file) => !names.has(file.name))];
    });
    event.target.value = '';
  }

  /**
   * Combina texto do curriculo e anexos em payload unico para a API atual.
   */
  function buildCurriculoPayload() {
    if (attachments.length === 0) return values.curriculo;

    return [
      values.curriculo,
      '',
      '[ANEXOS_CURRICULO_JSON]',
      JSON.stringify(attachments),
      '[/ANEXOS_CURRICULO_JSON]',
    ]
      .filter(Boolean)
      .join('\n');
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.post('/candidato/candidatos/registrar/', {
        ...values,
        curriculo: buildCurriculoPayload(),
      });
      navigate('/login', { replace: true });
    } catch (registerError) {
      setError(extractApiError(registerError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f6fbfd] px-4 py-8 dark:bg-[#1f2930]">
      <div className="mx-auto max-w-3xl rounded-md border border-line bg-white p-6 shadow-soft dark:border-slate-700 dark:bg-slate-950">
        <PageHeader title="Cadastro de candidato" description="Crie seu acesso para acompanhar vagas e candidaturas." />
        {error ? (
          <pre className="mb-4 whitespace-pre-wrap rounded-md bg-red-50 p-3 font-sans text-sm text-danger dark:bg-red-950/30">
            {error}
          </pre>
        ) : null}
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
          {([
            ['username', 'Usuário', 'text'],
            ['password', 'Senha', 'password'],
            ['cpf_candidato', 'CPF', 'text'],
            ['nome', 'Nome', 'text'],
            ['email', 'E-mail', 'email'],
            ['telefone', 'Telefone', 'text'],
          ] as const).map(([name, label, type]) => (
            <label key={name}>
              <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">{label}</span>
              <input
                className="focus-ring w-full rounded-md border px-3 py-2 text-sm"
                type={type}
                value={values[name]}
                onChange={(event) => update(name, event.target.value)}
                required={['username', 'password', 'cpf_candidato', 'email'].includes(name)}
              />
            </label>
          ))}
          <label className="md:col-span-2">
            <span className="mb-1 block text-sm font-medium text-ink dark:text-slate-100">Currículo</span>
            <textarea
              className="focus-ring min-h-36 w-full rounded-md border px-3 py-2 text-sm"
              value={values.curriculo}
              onChange={(event) => update('curriculo', event.target.value)}
            />
          </label>
          <div className="rounded-md border border-line bg-panel p-4 dark:border-slate-700 dark:bg-slate-900 md:col-span-2">
            <label className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span className="flex items-center gap-2 text-sm font-medium text-ink dark:text-slate-100">
                <FileUp className="h-4 w-4 text-brand" />
                Anexar arquivos ou imagens
              </span>
              <input
                type="file"
                multiple
                accept="image/*,.pdf,.doc,.docx,.txt"
                onChange={handleFiles}
                className="max-w-full text-sm"
              />
            </label>
            {attachments.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {attachments.map((file) => (
                  <span
                    key={file.name}
                    className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-xs font-medium text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                  >
                    {file.name}
                    <button
                      type="button"
                      onClick={() => removeAttachment(file.name)}
                      className="rounded-sm text-muted hover:text-danger dark:text-slate-400"
                      aria-label={`Remover ${file.name}`}
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </span>
                ))}
              </div>
            ) : null}
          </div>
          <div className="flex items-center justify-between md:col-span-2">
            <Link to="/login" className="text-sm font-semibold text-brand hover:underline">
              Voltar ao login
            </Link>
            <Button type="submit" disabled={submitting}>
              Criar cadastro
            </Button>
          </div>
        </form>
      </div>
    </main>
  );
}
