import { Bot, ChevronDown, MessageCircle, Minus, Send, Smile, UserRound, X } from 'lucide-react';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useAuth } from '../auth/AuthContext';
import { api, extractApiError } from '../services/api';

type ChatMessage = {
  id: number;
  sender: 'agent' | 'user';
  text: string;
  time: string;
};

type AgentResponse = {
  pergunta?: string;
  resposta?: string;
  detail?: string;
};

function nowLabel() {
  return new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date());
}

function agentText(data: AgentResponse) {
  return data.resposta || data.detail || 'Nao foi possivel gerar resposta agora.';
}

/**
 * Chat flutuante do agente interno para funcionarios, lideranca e RH/admin.
 */
export function EmployeeAgentChat() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const welcomedUserRef = useRef<number | string | null>(null);
  const displayName = user?.nome || user?.username || 'funcionario';
  const canUseAgent = user?.profile === 'funcionario' || user?.profile === 'lideranca' || user?.profile === 'rh_admin';
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  useEffect(() => {
    if (!canUseAgent) {
      welcomedUserRef.current = null;
      setMessages([]);
      return;
    }

    const userKey = user?.id ?? displayName;
    if (welcomedUserRef.current === userKey) return;

    welcomedUserRef.current = userKey;

    setMessages([
      {
        id: 1,
        sender: 'agent',
        text: `Bem vindo ${displayName}, em que posso ajudar?`,
        time: nowLabel(),
      },
    ]);
  }, [canUseAgent, displayName, user?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen, isMinimized]);

  if (!canUseAgent) return null;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const pergunta = message.trim();
    if (!pergunta || isSending) return;

    const sentAt = nowLabel();
    setMessages((current) => [
      ...current,
      {
        id: Date.now(),
        sender: 'user',
        text: pergunta,
        time: sentAt,
      },
    ]);
    setMessage('');
    setIsSending(true);

    try {
      const response = await api.post<AgentResponse>('/funcionario/agente/perguntar/', { pergunta });
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          sender: 'agent',
          text: agentText(response.data),
          time: nowLabel(),
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          sender: 'agent',
          text: extractApiError(error),
          time: nowLabel(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-50">
      {isOpen && !isMinimized ? (
        <section className="mb-4 flex h-[34rem] w-[21rem] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-xl border border-line bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-950">
          <header className="flex h-12 shrink-0 items-center justify-between bg-[#08231f] px-4 text-white">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <UserRound className="h-4 w-4" />
              <span>Agente RH</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsMinimized(true)}
                className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white/15 hover:bg-white/25"
                aria-label="Minimizar chat do agente"
              >
                <Minus className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white/15 hover:bg-white/25"
                aria-label="Fechar chat do agente"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-[#f7f7f7] px-4 py-4 dark:bg-slate-900">
            {messages.map((item) => (
              <article key={item.id} className={item.sender === 'user' ? 'flex justify-end' : 'block'}>
                {item.sender === 'agent' ? (
                  <div className="mb-1 flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                    <span>{item.time}</span>
                    <span className="inline-flex h-6 w-8 items-center justify-center rounded-full bg-slate-200 dark:bg-slate-800">
                      <Smile className="h-3.5 w-3.5" />
                    </span>
                  </div>
                ) : null}
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    item.sender === 'agent'
                      ? 'rounded-bl-none bg-[#b8f3ea] text-slate-950'
                      : 'rounded-br-none bg-brand text-white'
                  }`}
                >
                  {item.text}
                </div>
                {item.sender === 'user' ? (
                  <p className="mt-1 text-right text-xs text-slate-500 dark:text-slate-400">{item.time}</p>
                ) : null}
              </article>
            ))}
            {isSending ? (
              <div className="max-w-[70%] rounded-2xl rounded-bl-none bg-[#b8f3ea] px-4 py-3 text-sm text-slate-950">
                Consultando documentos...
              </div>
            ) : null}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={submit} className="flex shrink-0 items-end gap-2 border-t border-line bg-white px-3 py-3 dark:border-slate-700 dark:bg-slate-950">
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Digite sua mensagem"
              rows={2}
              maxLength={500}
              className="focus-ring min-h-12 flex-1 resize-none rounded-2xl border border-transparent bg-panel px-4 py-2 text-sm text-ink outline-none placeholder:text-muted dark:bg-slate-900 dark:text-slate-100"
            />
            <button
              type="submit"
              disabled={isSending || !message.trim()}
              className="focus-ring inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-brand hover:bg-panel disabled:cursor-not-allowed disabled:text-slate-300 dark:hover:bg-slate-900"
              aria-label="Enviar pergunta ao agente"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>
        </section>
      ) : null}

      <button
        type="button"
        onClick={() => {
          setIsOpen((current) => !current || isMinimized);
          setIsMinimized(false);
        }}
        className="focus-ring ml-auto flex h-14 w-14 items-center justify-center rounded-full bg-[#08231f] text-white shadow-xl transition-transform hover:scale-105"
        aria-label={isOpen && !isMinimized ? 'Recolher chat do agente' : 'Abrir chat do agente'}
      >
        {isOpen && !isMinimized ? <ChevronDown className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
      {!isOpen ? (
        <span className="absolute -left-1 -top-1 inline-flex h-5 w-5 items-center justify-center rounded-full bg-brand text-white shadow">
          <Bot className="h-3.5 w-3.5" />
        </span>
      ) : null}
    </div>
  );
}
