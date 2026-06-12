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
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404()
        return view_func(request, *args, **kwargs)

    return wrapped


def parse_json_body(request):
    if not request.body:
        return {}

    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return None


def setor_payload(setor):
    return {
        'id_setor': setor.id_setor,
        'nome': setor.nome,
        'descricao': setor.descricao,
    }


def cargo_payload(cargo):
    return {
        'id_cargo': cargo.id_cargo,
        'nome': cargo.nome,
        'descricao': cargo.descricao,
    }


@debug_only
@ensure_csrf_cookie
@require_http_methods(['GET'])
def setor_test_page(request):
    return render(request, 'setor/setor_teste.html')


@debug_only
@require_http_methods(['GET', 'POST'])
def setor_test_collection(request):
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
    if request.method == 'GET':
        cargos = Cargo.objects.all().order_by('id_cargo')
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
