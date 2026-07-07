import json
from functools import wraps

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from apps.setor.api.serializers import CargoWriteSerializer, SetorWriteSerializer
from apps.setor.models import Cargo, Setor


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


def setor_payload(setor):
    """Monta payload JSON simples de setor para tela de teste."""
    return {
        'id_setor': setor.id_setor,
        'nome': setor.nome,
        'descricao': setor.descricao,
    }


def cargo_payload(cargo):
    """Monta payload JSON simples de cargo para tela de teste."""
    return {
        'id_cargo': cargo.id_cargo,
        'nome': cargo.nome,
        'descricao': cargo.descricao,
        'fk_id_setor': cargo.fk_id_setor_id,
        'setor_nome': getattr(cargo.fk_id_setor, 'nome', None),
    }


@debug_only
@ensure_csrf_cookie
@require_http_methods(['GET'])
def setor_test_page(request):
    """Renderiza tela de teste de setor e cargo."""
    return render(request, 'setor/setor_teste.html')


@debug_only
@require_http_methods(['GET', 'POST'])
def setor_test_collection(request):
    """Lista ou cria setores pela rota local de teste."""
    if request.method == 'GET':
        setores = Setor.objects.all().order_by('id_setor')
        return JsonResponse({'results': [setor_payload(setor) for setor in setores]})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = SetorWriteSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    setor = serializer.save()
    return JsonResponse(setor_payload(setor), status=201)


@debug_only
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def setor_test_detail(request, pk):
    """Atualiza ou remove setor pela rota local de teste."""
    setor = get_object_or_404(Setor, pk=pk)

    if request.method == 'DELETE':
        setor.delete()
        return JsonResponse({'deleted': True})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = SetorWriteSerializer(setor, data=data, partial=request.method == 'PATCH')
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    setor = serializer.save()
    return JsonResponse(setor_payload(setor))


@debug_only
@require_http_methods(['GET', 'POST'])
def cargo_test_collection(request):
    """Lista ou cria cargos pela rota local de teste."""
    if request.method == 'GET':
        cargos = Cargo.objects.select_related('fk_id_setor').all().order_by('id_cargo')
        return JsonResponse({'results': [cargo_payload(cargo) for cargo in cargos]})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = CargoWriteSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    cargo = serializer.save()
    return JsonResponse(cargo_payload(cargo), status=201)


@debug_only
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def cargo_test_detail(request, pk):
    """Atualiza ou remove cargo pela rota local de teste."""
    cargo = get_object_or_404(Cargo, pk=pk)

    if request.method == 'DELETE':
        cargo.delete()
        return JsonResponse({'deleted': True})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = CargoWriteSerializer(cargo, data=data, partial=request.method == 'PATCH')
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    cargo = serializer.save()
    return JsonResponse(cargo_payload(cargo))
