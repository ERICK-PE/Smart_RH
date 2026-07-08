from __future__ import annotations

import os

from apps.avaliacao.api.serializers import ANALISE_COMPORTAMENTAL_PERGUNTAS
from apps.funcionario.services.agente_documentos import (
    DEFAULT_OPENAI_MODEL,
    OpenAI,
    extract_openai_output_text,
    get_openai_api_key,
    normalize_whitespace,
)


SYSTEM_PROMPT = """
Você é um agente de IA especializado em análise de clima organizacional e bem-estar
comportamental no ambiente de trabalho. Sua função é interpretar as respostas de
funcionários a uma pesquisa comportamental interna e gerar um relatório claro e
acionável para a equipe de RH e lideranças.

## FORMULÁRIO DE REFERÊNCIA
As respostas que você receberá seguem sempre esta estrutura de 6 blocos:

1. Termômetro de sentimento — Muito Infeliz / Infeliz / Neutro / Feliz / Muito Feliz
   (+ campo aberto opcional de observação)
2. Desenvolvimento profissional (sentir-se apoiado) — Sempre / Na maioria das vezes /
   Às vezes / Raramente / Nunca
3. Senso de reconhecimento — Muito valorizado / Valorizado / Neutro / Pouco valorizado /
   Não valorizado
4. Ambiente de trabalho — nota de 1 a 5 para (a) ambiente físico e (b) clima geral
5. Percepção sobre liderança — Inspirador / Apoiador / Neutra / Crítico / Autoritário
6. Relação com colegas e equipe — nota de 1 a 5

## OBJETIVO
A partir das respostas de um único funcionário, você deve:
- Traduzir as respostas em um panorama objetivo do estado emocional e organizacional.
- Identificar padrões, contradições e correlações entre os blocos.
- Sinalizar pontos de atenção que mereçam acompanhamento do RH.
- Sugerir ações concretas e proporcionais, nunca alarmistas.

## LIMITES ÉTICOS OBRIGATÓRIOS
- Você NÃO é um profissional de saúde mental e NÃO deve diagnosticar depressão,
  ansiedade, burnout ou qualquer condição clínica.
- Trate os dados como confidenciais. Não invente causas, relações pessoais ou intenções.
- Evite julgamentos de valor sobre o funcionário.
- Se houver sinais relevantes de sofrimento, priorize encaminhamento humano imediato.
- Baseie a análise estritamente nos dados fornecidos.

## FORMATO DE SAÍDA
Estruture sempre a resposta assim:

1. **Resumo executivo** (2-4 linhas)
2. **Panorama por dimensão**
3. **Sinais de atenção**
4. **Padrões e correlações**
5. **Recomendações**
6. **Nível de urgência**: Baixo / Moderado / Alto — com justificativa.

Use linguagem profissional, direta e empática. Evite jargão psicológico.
""".strip()


QUESTION_LABELS = {
    question['id']: question['pergunta']
    for question in ANALISE_COMPORTAMENTAL_PERGUNTAS
}


def answer_value(respostas: dict, question_id: str) -> str:
    value = respostas.get(question_id)
    if value is None or value == '':
        return 'não respondido'
    return str(value)


def build_behavioral_analysis_task_prompt(resposta, respostas: dict) -> str:
    funcionario = resposta.fk_id_funcionario
    setor = getattr(funcionario, 'fk_id_setor', None)
    data_resposta = getattr(resposta, 'respondido_em', None)
    data_resposta_text = data_resposta.strftime('%d/%m/%Y') if data_resposta else 'não respondido'

    return f"""
Analise as respostas comportamentais abaixo, referentes ao funcionário identificado,
seguindo integralmente o contexto e o formato de saída definidos.

DADOS DO RESPONDENTE
- Identificador: {getattr(funcionario, 'nome', 'não respondido')}
- Setor: {getattr(setor, 'nome', 'não respondido')}
- Data da resposta: {data_resposta_text}

RESPOSTAS

1. Termômetro de sentimento: {answer_value(respostas, 'sentimento')}
   Observação aberta: {answer_value(respostas, 'sentimento_observacao')}

2. Desenvolvimento profissional (sente-se apoiado?): {answer_value(respostas, 'desenvolvimento_profissional')}

3. Senso de reconhecimento: {answer_value(respostas, 'reconhecimento')}

4. Ambiente de trabalho
   a) Ambiente físico (1-5): {answer_value(respostas, 'ambiente_fisico')}
   b) Clima geral (1-5): {answer_value(respostas, 'clima_geral')}

5. Percepção sobre liderança: {answer_value(respostas, 'lideranca_empresa')}

6. Relação com colegas e equipe (1-5): {answer_value(respostas, 'relacao_colegas')}

Gere o relatório completo conforme o formato de saída estabelecido.
""".strip()


def generate_behavioral_analysis_report(resposta, respostas: dict) -> str:
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError('OPEN_API_KEY nao configurada.')
    if OpenAI is None:
        raise ValueError('Dependencia openai nao instalada.')

    client = OpenAI(api_key=api_key, timeout=30.0)
    model = os.environ.get('OPENAI_AGENT_MODEL', DEFAULT_OPENAI_MODEL)
    response = client.responses.create(
        model=model,
        input=[
            {
                'role': 'system',
                'content': SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': build_behavioral_analysis_task_prompt(resposta, respostas),
            },
        ],
    )

    return (
        extract_openai_output_text(response)
        or 'Não foi possível gerar relatório comportamental com as respostas enviadas.'
    )


def fallback_behavioral_analysis_report(error_message: str) -> str:
    safe_error = normalize_whitespace(error_message) or 'erro não identificado'
    return (
        'Relatório comportamental automático não gerado.\n\n'
        f'Motivo técnico: {safe_error}\n\n'
        'Ação recomendada: RH deve revisar manualmente as respostas preenchidas.'
    )
