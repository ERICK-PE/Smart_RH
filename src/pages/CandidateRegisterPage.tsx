import { useState, type ChangeEvent, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FileUp, X } from 'lucide-react';
import { api, extractApiError } from '../services/api';
import { Button, PageHeader } from '../components/ui';

const MAX_RESUME_FILE_SIZE = 5 * 1024 * 1024;
const RESUME_ACCEPT = '.pdf,.doc,.docx';
const RESUME_ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx'];
const RESUME_ALLOWED_CONTENT_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

const initial = {
  username: '',
  password: '',
  cpf_candidato: '',
  nome: '',
  email: '',
  telefone: '',
};

function resumeExtension(file: File) {
  const index = file.name.lastIndexOf('.');
  return index >= 0 ? file.name.slice(index).toLowerCase() : '';
}

function validateResumeFile(file: File) {
  if (!RESUME_ALLOWED_EXTENSIONS.includes(resumeExtension(file))) {
    return 'Curriculo deve ser PDF, DOC ou DOCX.';
  }
  if (file.type && !RESUME_ALLOWED_CONTENT_TYPES.includes(file.type)) {
    return 'Tipo de arquivo do curriculo nao permitido.';
  }
  if (file.size > MAX_RESUME_FILE_SIZE) {
    return 'Curriculo deve ter no maximo 5MB.';
  }
  return '';
}

function formatFileSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Tela publica de registro de usuario candidato.
 */
export function CandidateRegisterPage() {
  const [values, setValues] = useState(initial);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  function update(name: keyof typeof initial, value: string) {
    setValues((current) => ({ ...current, [name]: value }));
  }

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setError('');

    if (!file) {
      setResumeFile(null);
      return;
    }

    const validationError = validateResumeFile(file);
    if (validationError) {
      setResumeFile(null);
      setError(validationError);
      event.target.value = '';
      return;
    }

    setResumeFile(file);
  }

  function removeResumeFile() {
    setResumeFile(null);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const formData = new FormData();
      Object.entries(values).forEach(([key, value]) => {
        formData.append(key, value);
      });
      if (resumeFile) formData.append('curriculo', resumeFile);

      await api.post('/candidato/candidatos/registrar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
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
            ['username', 'Usuario', 'text'],
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
          <div className="md:col-span-2 rounded-md border border-line bg-panel p-4 dark:border-slate-700 dark:bg-slate-900">
            <label className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <span className="flex items-center gap-2 text-sm font-medium text-ink dark:text-slate-100">
                <FileUp className="h-4 w-4 text-brand" />
                Anexar curriculo PDF ou Word
              </span>
              <input
                type="file"
                accept={RESUME_ACCEPT}
                onChange={handleFile}
                className="max-w-full text-sm"
              />
            </label>
            {resumeFile ? (
              <span className="mt-3 inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-xs font-medium text-ink dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100">
                {resumeFile.name} ({formatFileSize(resumeFile.size)})
                <button
                  type="button"
                  onClick={removeResumeFile}
                  className="rounded-sm text-muted hover:text-danger dark:text-slate-400"
                  aria-label={`Remover ${resumeFile.name}`}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </span>
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
