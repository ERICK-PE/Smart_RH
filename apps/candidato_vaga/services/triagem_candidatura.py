from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
import zipfile

from django.core.files.storage import default_storage

from apps.funcionario.services.agente_documentos import extract_text_from_document_bytes


STOPWORDS = {
    'a', 'ao', 'aos', 'as', 'com', 'como', 'da', 'das', 'de', 'do', 'dos', 'e',
    'em', 'experiencia', 'minima', 'minimas', 'minimo', 'minimos', 'na', 'nas',
    'no', 'nos', 'o', 'os', 'ou', 'para', 'por', 'que', 'requisito',
    'requisitos', 'sobre', 'ter', 'vaga',
}
MAX_KEYWORDS = 30


@dataclass(frozen=True)
class TriagemCandidaturaResult:
    """Resultado da triagem automatica feita no momento da candidatura."""
    aprovado: bool
    motivo: str
    palavras_chave: list[str]
    palavras_encontradas: list[str]
    palavras_faltantes: list[str]


def normalize_text(value: str) -> str:
    """Normaliza texto para comparacao case-insensitive e sem acento."""
    normalized = unicodedata.normalize('NFKD', value or '')
    without_accents = ''.join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.lower()


def extract_requirement_keywords(vaga) -> list[str]:
    """Extrai palavras-chave dos requisitos minimos descritos na vaga."""
    text = normalize_text(getattr(vaga, 'descricao', '') or '')
    keywords = []
    for token in re.findall(r'[a-z0-9][a-z0-9+#.-]{2,}', text):
        token = token.strip('.-')
        if len(token) < 3 or token in STOPWORDS or token in keywords:
            continue
        keywords.append(token)
        if len(keywords) >= MAX_KEYWORDS:
            break
    return keywords


def extract_curriculo_text(candidato) -> str:
    """Le curriculo salvo no storage e extrai texto do documento."""
    curriculo = getattr(candidato, 'curriculo', None)
    filename = getattr(curriculo, 'name', curriculo) or ''
    if not filename:
        raise ValueError('Candidato sem curriculo para triagem.')

    with default_storage.open(filename, 'rb') as uploaded_file:
        data = uploaded_file.read()

    return extract_text_from_document_bytes(filename, data)


def analisar_candidatura(candidato, vaga) -> TriagemCandidaturaResult:
    """Compara requisitos da vaga com texto extraido do curriculo."""
    keywords = extract_requirement_keywords(vaga)
    if not keywords:
        return TriagemCandidaturaResult(
            aprovado=True,
            motivo='Vaga sem requisitos minimos descritos para triagem automatica.',
            palavras_chave=[],
            palavras_encontradas=[],
            palavras_faltantes=[],
        )

    try:
        curriculo_text = normalize_text(extract_curriculo_text(candidato))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        return TriagemCandidaturaResult(
            aprovado=False,
            motivo=str(exc),
            palavras_chave=keywords,
            palavras_encontradas=[],
            palavras_faltantes=keywords,
        )

    found = [keyword for keyword in keywords if keyword in curriculo_text]
    missing = [keyword for keyword in keywords if keyword not in curriculo_text]
    approved = not missing
    reason = (
        'Curriculo contem as palavras-chave dos requisitos minimos.'
        if approved
        else 'Curriculo nao contem todas as palavras-chave dos requisitos minimos.'
    )

    return TriagemCandidaturaResult(
        aprovado=approved,
        motivo=reason,
        palavras_chave=keywords,
        palavras_encontradas=found,
        palavras_faltantes=missing,
    )
