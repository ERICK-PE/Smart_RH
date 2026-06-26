import json
from functools import wraps

from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from apps.funcionario.api.serializers import FuncionarioAgenteDocumentoWriteSerializer, FuncionarioWriteSerializer
from apps.funcionario.models import Funcionario
from apps.funcionario.services.agente_documentos import answer_question_with_openai, load_important_document_sources
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


def funcionario_payload(funcionario):
    """Monta payload JSON simples de funcionario para tela de teste."""
    return {
        'id_funcionario': funcionario.id_funcionario,
        'nome': funcionario.nome,
        'cpf': funcionario.cpf,
        'email': funcionario.email,
        'telefone': funcionario.telefone,
        'data_admissao': funcionario.data_admissao.isoformat() if funcionario.data_admissao else None,
        'status': funcionario.status,
        'fk_id_setor': funcionario.fk_id_setor_id,
        'setor_nome': getattr(funcionario.fk_id_setor, 'nome', None),
        'fk_id_cargo': funcionario.fk_id_cargo_id,
        'cargo_nome': getattr(funcionario.fk_id_cargo, 'nome', None),
    }


@debug_only
@ensure_csrf_cookie
@require_http_methods(['GET'])
def funcionario_test_page(request):
    """Renderiza tela de teste de funcionarios."""
    return render(request, 'funcionario/funcionario_teste.html')


@debug_only
@ensure_csrf_cookie
@require_http_methods(['GET'])
def agente_test_page(request):
    """Renderiza tela de teste do agente interno de RH."""
    return render(request, 'funcionario/agente_teste.html')


@debug_only
@require_http_methods(['POST'])
def agente_test_upload(request):
    """Recebe upload debug para validar persistencia em imp_doc."""
    serializer = FuncionarioAgenteDocumentoWriteSerializer(data={
        'titulo': request.POST.get('titulo') or getattr(request.FILES.get('arquivo'), 'name', ''),
        'arquivo': request.FILES.get('arquivo'),
        'ativo': request.POST.get('ativo', 'true') not in {'false', '0', 'off'},
    })
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    documento = serializer.save()
    return JsonResponse({
        'id_documento': documento.id_documento,
        'titulo': documento.titulo,
        'arquivo': documento.arquivo.name,
        'ativo': documento.ativo,
    }, status=201)


@debug_only
@require_http_methods(['POST'])
def agente_test_perguntar(request):
    """Executa pergunta debug lendo documentos atuais em imp_doc."""
    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    pergunta = (data.get('pergunta') or '').strip()
    if len(pergunta) < 5:
        return JsonResponse({'pergunta': 'Pergunta deve ter pelo menos 5 caracteres.'}, status=400)

    documentos = load_important_document_sources()
    if not documentos:
        return JsonResponse({'detail': 'Nenhum documento importante legivel encontrado em imp_doc.'}, status=404)

    try:
        resposta = answer_question_with_openai(pergunta, documentos)
    except ValueError as exc:
        return JsonResponse({'detail': str(exc)}, status=503)

    return JsonResponse({
        'pergunta': pergunta,
        **resposta,
    })


@debug_only
@require_http_methods(['GET'])
def funcionario_test_options(request):
    """Retorna opcoes auxiliares para formulario de funcionario."""
    return JsonResponse({
        'setores': [
            {'id_setor': setor.id_setor, 'nome': setor.nome}
            for setor in Setor.objects.all().order_by('nome')
        ],
        'cargos': [
            {'id_cargo': cargo.id_cargo, 'nome': cargo.nome}
            for cargo in Cargo.objects.all().order_by('nome')
        ],
        'status': [
            {'value': value, 'label': label}
            for value, label in Funcionario.STATUS_CHOICES
        ],
    })


@debug_only
@require_http_methods(['GET', 'POST'])
def funcionario_test_collection(request):
    """Lista ou cria funcionarios pela rota local de teste."""
    if request.method == 'GET':
        funcionarios = (
            Funcionario.objects
            .select_related('fk_id_setor', 'fk_id_cargo')
            .all()
            .order_by('id_funcionario')
        )
        return JsonResponse({
            'results': [funcionario_payload(funcionario) for funcionario in funcionarios],
        })

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = FuncionarioWriteSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    funcionario = serializer.save()
    funcionario = Funcionario.objects.select_related('fk_id_setor', 'fk_id_cargo').get(pk=funcionario.pk)
    return JsonResponse(funcionario_payload(funcionario), status=201)


@debug_only
@require_http_methods(['PUT', 'PATCH', 'DELETE'])
def funcionario_test_detail(request, pk):
    """Atualiza ou remove funcionario pela rota local de teste."""
    funcionario = get_object_or_404(Funcionario, pk=pk)

    if request.method == 'DELETE':
        funcionario.delete()
        return JsonResponse({'deleted': True})

    data = parse_json_body(request)
    if data is None:
        return JsonResponse({'detail': 'JSON invalido.'}, status=400)

    serializer = FuncionarioWriteSerializer(
        funcionario,
        data=data,
        partial=request.method == 'PATCH',
    )
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    funcionario = serializer.save()
    funcionario = Funcionario.objects.select_related('fk_id_setor', 'fk_id_cargo').get(pk=funcionario.pk)
    return JsonResponse(funcionario_payload(funcionario))
