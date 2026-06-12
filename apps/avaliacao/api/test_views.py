import json
from functools import wraps

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from apps.avaliacao.api.serializers import (
    AnaliseComportamentalWriteSerializer,
    AvaliacaoDesempenhoWriteSerializer,
)
from apps.avaliacao.models import AnaliseComportamental, AvaliacaoDesempenho
from apps.funcionario.models import Funcionario


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


def funcionario_payload(funcionario):
    """Monta payload JSON simples de funcionario para testes."""
    return {
        'id_funcionario': funcionario.id_funcionario,
        'nome': funcionario.nome,
        'email': funcionario.email,
        'status': getattr(funcionario, 'status', None),
        'fk_id_setor': funcionario.fk_id_setor_id,
        'setor_nome': getattr(funcionario.fk_id_setor, 'nome', None),
        'fk_id_cargo': funcionario.fk_id_cargo_id,
        'cargo_nome': getattr(funcionario.fk_id_cargo, 'nome', None),
    }


def analise_payload(analise):
    """Monta payload JSON simples de analise comportamental."""
    funcionario = analise.fk_id_funcionario
    return {
        'id_analise': analise.id_analise,
        'fk_id_funcionario': analise.fk_id_funcionario_id,
        'funcionario_nome': getattr(funcionario, 'nome', None),
        'resultado': analise.resultado,
        'data_analise': analise.data_analise.isoformat() if analise.data_analise else None,
    }


def avaliacao_payload(avaliacao):
    """Monta payload JSON simples de avaliacao de desempenho."""
    funcionario = avaliacao.fk_id_funcionario
    avaliador = avaliacao.fk_id_avaliador
    return {
        'id_avaliacao': avaliacao.id_avaliacao,
        'fk_id_funcionario': avaliacao.fk_id_funcionario_id,
        'funcionario_nome': getattr(funcionario, 'nome', None),
        'fk_id_avaliador': avaliacao.fk_id_avaliador_id,
        'avaliador_nome': getattr(avaliador, 'nome', None),
        'categoria': avaliacao.categoria,
        'nota': str(avaliacao.nota) if avaliacao.nota is not None else None,
        'comentario': avaliacao.comentario,
        'data_avaliacao': avaliacao.data_avaliacao.isoformat() if avaliacao.data_avaliacao else None,
    }


@debug_only
@ensure_csrf_cookie
@require_http_methods(['GET'])
def avaliacao_test_page(request):
    """Renderiza tela de teste de avaliacoes."""
    return render(request, 'avaliacao/avaliacao_teste.html')


@debug_only
@require_http_methods(['GET'])
def avaliacao_test_options(request):
    """Retorna opcoes auxiliares para formularios de avaliacao."""
    funcionarios = (
        Funcionario.objects
        .select_related('fk_id_setor', 'fk_id_cargo')
        .all()
        .order_by('nome', 'id_funcionario')
    )
    return JsonResponse({
        'funcionarios': [funcionario_payload(funcionario) for funcionario in funcionarios],
    })


@debug_only
@require_http_methods(['GET'])
def funcionario_test_collection(request):
    """Lista funcionarios para tela local de avaliacao."""
    funcionarios = (
        Funcionario.objects
        .select_related('fk_id_setor', 'fk_id_cargo')
        .all()
        .order_by('nome', 'id_funcionario')
    )
    return JsonResponse({'results': [funcionario_payload(funcionario) for funcionario in funcionarios]})


@debug_only
@require_http_methods(['GET', 'POST'])
def analise_test_collection(request):
    """Lista ou cria analises pela rota local de teste."""
    if request.method == 'GET':
        analises = (
            AnaliseComportamental.objects
            .select_related('fk_id_funcionario')
            .all()
            .order_by('id_analise')
        )
        return JsonResponse({'results': [analise_payload(analise) for analise in analises]})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = AnaliseComportamentalWriteSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    analise = serializer.save()
    analise = AnaliseComportamental.objects.select_related('fk_id_funcionario').get(pk=analise.pk)
    return JsonResponse(analise_payload(analise), status=201)


@debug_only
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def analise_test_detail(request, pk):
    """Atualiza ou remove analise pela rota local de teste."""
    analise = get_object_or_404(AnaliseComportamental, pk=pk)

    if request.method == 'DELETE':
        analise.delete()
        return JsonResponse({'deleted': True})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = AnaliseComportamentalWriteSerializer(
        analise,
        data=data,
        partial=request.method == 'PATCH',
    )
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    analise = serializer.save()
    analise = AnaliseComportamental.objects.select_related('fk_id_funcionario').get(pk=analise.pk)
    return JsonResponse(analise_payload(analise))


@debug_only
@require_http_methods(['GET', 'POST'])
def avaliacao_test_collection(request):
    """Lista ou cria avaliacoes pela rota local de teste."""
    if request.method == 'GET':
        avaliacoes = (
            AvaliacaoDesempenho.objects
            .select_related('fk_id_funcionario', 'fk_id_avaliador')
            .all()
            .order_by('id_avaliacao')
        )
        return JsonResponse({'results': [avaliacao_payload(avaliacao) for avaliacao in avaliacoes]})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = AvaliacaoDesempenhoWriteSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    avaliacao = serializer.save()
    avaliacao = AvaliacaoDesempenho.objects.select_related('fk_id_funcionario', 'fk_id_avaliador').get(
        pk=avaliacao.pk,
    )
    return JsonResponse(avaliacao_payload(avaliacao), status=201)


@debug_only
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def avaliacao_test_detail(request, pk):
    """Atualiza ou remove avaliacao pela rota local de teste."""
    avaliacao = get_object_or_404(AvaliacaoDesempenho, pk=pk)

    if request.method == 'DELETE':
        avaliacao.delete()
        return JsonResponse({'deleted': True})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = AvaliacaoDesempenhoWriteSerializer(
        avaliacao,
        data=data,
        partial=request.method == 'PATCH',
    )
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    avaliacao = serializer.save()
    avaliacao = AvaliacaoDesempenho.objects.select_related('fk_id_funcionario', 'fk_id_avaliador').get(
        pk=avaliacao.pk,
    )
    return JsonResponse(avaliacao_payload(avaliacao))
