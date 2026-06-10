from django.conf import settings
from django.test import SimpleTestCase
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from apps.api_mixins import ResumoActionMixin
from apps.pagination import StandardResultsSetPagination


class DummySerializer:
    def __init__(self, queryset, many=False, **kwargs):
        self.data = list(queryset)


class DummyPaginatedView(ResumoActionMixin):
    def get_serializer_context(self):
        return {'view': self}

    def paginate_queryset(self, queryset):
        return list(queryset)[:2]

    def get_paginated_response(self, data):
        return Response({
            'count': 3,
            'next': 'http://testserver/?page=2',
            'previous': None,
            'results': data,
        })


class APIPaginationConfigurationTests(SimpleTestCase):
    def test_rest_framework_usa_paginacao_global(self):
        self.assertEqual(
            settings.REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS'],
            'apps.pagination.StandardResultsSetPagination',
        )
        self.assertEqual(settings.REST_FRAMEWORK['PAGE_SIZE'], 20)

    def test_paginacao_aceita_page_size_com_limite(self):
        paginator = StandardResultsSetPagination()

        self.assertEqual(paginator.page_size, 20)
        self.assertEqual(paginator.page_size_query_param, 'page_size')
        self.assertEqual(paginator.max_page_size, 100)

    def test_paginacao_aplica_page_size_em_lista(self):
        request = Request(APIRequestFactory().get('/teste/?page_size=2'))
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset([1, 2, 3], request)

        self.assertEqual(page, [1, 2])

    def test_helper_pagina_actions_com_listas_manuais(self):
        view = DummyPaginatedView()

        response = view.paginated_serializer_response([1, 2, 3], DummySerializer)

        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'], [1, 2])
