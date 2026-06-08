from rest_framework.decorators import action
from rest_framework.response import Response


class ResumoActionMixin:
    @action(detail=False, methods=['get'], url_path='resumo')
    def resumo(self, request):
        return Response({
            'total': self.get_queryset().count(),
        })
