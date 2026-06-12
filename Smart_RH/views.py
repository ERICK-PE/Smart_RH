from django.http import HttpResponse

def index_view(request):
    """Responde rota inicial simples do projeto Django."""
    return HttpResponse('Teste de rota')    
