import json
from functools import wraps

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from apps.candidato_vaga.api.serializers import (
    CandidatoWriteSerializer,
    CandidatoRegistrationSerializer,
    CandidatoVagaWriteSerializer,
    VagaWriteSerializer,
)
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga
from apps.setor.models import Setor


def debug_only(view_func):
    """Restringe rota de teste ao ambiente DEBUG."""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        """Executa view decorada apenas quando DEBUG esta ativo."""
        if not settings.DEBUG:
            raise Http404()
        return view_func(request, *args, **kwargs)

    return wrapped


def parse_json_body(request):
    """Converte corpo JSON da requisicao ou sinaliza erro."""
    if not request.body:
        return {}

    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return None


def parse_candidate_body(request):
    """Aceita JSON ou multipart com arquivo de curriculo."""
    content_type = request.content_type or ''
    if content_type.startswith('multipart/form-data'):
        data = request.POST.copy()
        if request.FILES.get('curriculo'):
            data['curriculo'] = request.FILES['curriculo']
        return data

    return parse_json_body(request)


def file_name(value):
    """Retorna caminho do arquivo de curriculo para JSON de teste."""
    return getattr(value, 'name', value) or None


def candidato_payload(candidato):
    """Monta payload JSON simples de candidato para tela de teste."""
    return {
        'cpf_candidato': candidato.cpf_candidato,
        'user_id': candidato.user_id,
        'nome': candidato.nome,
        'email': candidato.email,
        'telefone': candidato.telefone,
        'curriculo': file_name(candidato.curriculo),
    }


def vaga_payload(vaga):
    """Monta payload JSON simples de vaga para tela de teste."""
    return {
        'id_vaga': vaga.id_vaga,
        'titulo': vaga.titulo,
        'descricao': vaga.descricao,
        'data_publicacao': vaga.data_publicacao.isoformat() if vaga.data_publicacao else None,
        'status': vaga.status,
        'fk_id_setor': vaga.fk_id_setor_id,
        'setor_nome': getattr(vaga.fk_id_setor, 'nome', None),
    }


def candidatura_payload(candidatura):
    """Monta payload JSON simples de candidatura para tela de teste."""
    candidato = candidatura.cpf_candidato
    vaga = candidatura.id_vaga
    return {
        'cpf_candidato': candidatura.cpf_candidato_id,
        'candidato_nome': getattr(candidato, 'nome', None),
        'id_vaga': candidatura.id_vaga_id,
        'vaga_titulo': getattr(vaga, 'titulo', None),
        'status_vaga': getattr(vaga, 'status', None),
        'status_processo': candidatura.status_processo,
    }


@debug_only
@ensure_csrf_cookie
@require_http_methods(['GET'])
def candidato_vaga_test_page(request):
    """Renderiza tela de teste de candidatos e vagas."""
    return render(request, 'candidato_vaga/candidato_vaga_teste.html')


@debug_only
@require_http_methods(['GET'])
def candidato_vaga_test_options(request):
    """Retorna opcoes auxiliares para formularios de candidatura."""
    return JsonResponse({
        'setores': [
            {'id_setor': setor.id_setor, 'nome': setor.nome}
            for setor in Setor.objects.all().order_by('nome')
        ],
        'candidatos': [
            {'cpf_candidato': candidato.cpf_candidato, 'nome': candidato.nome}
            for candidato in Candidato.objects.all().order_by('nome', 'cpf_candidato')
        ],
        'vagas': [
            {'id_vaga': vaga.id_vaga, 'titulo': vaga.titulo, 'status': vaga.status}
            for vaga in Vaga.objects.all().order_by('titulo', 'id_vaga')
        ],
    })


@debug_only
@require_http_methods(['GET', 'POST'])
def candidato_test_collection(request):
    """Lista ou cria candidatos pela rota local de teste."""
    if request.method == 'GET':
        candidatos = Candidato.objects.all().order_by('nome', 'cpf_candidato')
        return JsonResponse({'results': [candidato_payload(candidato) for candidato in candidatos]})

    data = parse_candidate_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = CandidatoRegistrationSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    candidato = serializer.save()
    return JsonResponse(candidato_payload(candidato), status=201)


@debug_only
@require_http_methods(['POST', 'PUT', 'PATCH', 'DELETE'])
def candidato_test_detail(request, cpf_candidato):
    """Atualiza ou remove candidato pela rota local de teste."""
    candidato = get_object_or_404(Candidato, pk=cpf_candidato)

    if request.method == 'DELETE':
        candidato.delete()
        return JsonResponse({'deleted': True})

    data = parse_candidate_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = CandidatoWriteSerializer(candidato, data=data, partial=request.method in ['PATCH', 'POST'])
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    candidato = serializer.save()
    return JsonResponse(candidato_payload(candidato))


@debug_only
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def vaga_test_detail(request, pk):
    """Atualiza ou remove vaga pela rota local de teste."""
    vaga = get_object_or_404(Vaga, pk=pk)

    if request.method == 'DELETE':
        vaga.delete()
        return JsonResponse({'deleted': True})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = VagaWriteSerializer(vaga, data=data, partial=request.method == 'PATCH')
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    vaga = serializer.save()
    vaga = Vaga.objects.select_related('fk_id_setor').get(pk=vaga.pk)
    return JsonResponse(vaga_payload(vaga))


@debug_only
@require_http_methods(['GET', 'POST'])
def vaga_test_collection(request):
    """Lista ou cria vagas pela rota local de teste."""
    if request.method == 'GET':
        vagas = Vaga.objects.select_related('fk_id_setor').all().order_by('id_vaga')
        return JsonResponse({'results': [vaga_payload(vaga) for vaga in vagas]})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = VagaWriteSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    vaga = serializer.save()
    vaga = Vaga.objects.select_related('fk_id_setor').get(pk=vaga.pk)
    return JsonResponse(vaga_payload(vaga), status=201)


@debug_only
@require_http_methods(['GET', 'POST'])
def candidatura_test_collection(request):
    """Lista ou cria candidaturas pela rota local de teste."""
    if request.method == 'GET':
        candidaturas = (
            CandidatoVaga.objects
            .select_related('cpf_candidato', 'id_vaga')
            .all()
            .order_by('cpf_candidato', 'id_vaga')
        )
        return JsonResponse({'results': [candidatura_payload(candidatura) for candidatura in candidaturas]})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    data.setdefault('status_processo', 'candidatado')
    serializer = CandidatoVagaWriteSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    candidatura = serializer.save()
    candidatura = CandidatoVaga.objects.select_related('cpf_candidato', 'id_vaga').get(
        cpf_candidato_id=candidatura.cpf_candidato_id,
        id_vaga_id=candidatura.id_vaga_id,
    )
    return JsonResponse(candidatura_payload(candidatura), status=201)


@debug_only
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def candidatura_test_detail(request, cpf_candidato, id_vaga):
    """Atualiza ou remove candidatura pela rota local de teste."""
    candidatura = get_object_or_404(
        CandidatoVaga,
        cpf_candidato_id=cpf_candidato,
        id_vaga_id=id_vaga,
    )

    if request.method == 'DELETE':
        candidatura.delete()
        return JsonResponse({'deleted': True})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = CandidatoVagaWriteSerializer(candidatura, data=data, partial=request.method == 'PATCH')
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    candidatura = serializer.save()
    candidatura = CandidatoVaga.objects.select_related('cpf_candidato', 'id_vaga').get(
        cpf_candidato_id=candidatura.cpf_candidato_id,
        id_vaga_id=candidatura.id_vaga_id,
    )
    return JsonResponse(candidatura_payload(candidatura))
