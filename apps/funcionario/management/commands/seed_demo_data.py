from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.avaliacao.models import (
    AnaliseComportamental,
    AnaliseComportamentalEnvio,
    AnaliseComportamentalResposta,
    AvaliacaoDesempenho,
)
from apps.candidato_vaga.models import Candidato, CandidatoVaga, Vaga
from apps.funcionario.models import (
    Contrato,
    FolhaPagamento,
    Funcionario,
    FuncionarioAgenteDocumento,
    PlanoCarreira,
)
from apps.setor.models import Cargo, Setor


PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 160] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 58 >>
stream
BT /F1 12 Tf 40 100 Td (Documento ficticio Smart RH) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<< /Root 1 0 R /Size 5 >>
startxref
312
%%EOF
"""


class Command(BaseCommand):
    help = 'Popula o banco com dados ficticios realistas para navegacao e testes visuais.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--login-password',
            default='',
            help='Senha opcional para usuarios demo. Sem valor, usuarios recebem senha inutilizavel.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.login_password = options['login_password']
        self.now = timezone.now()
        self.today = date.today()
        self.counts = {}

        groups = self.seed_groups()
        users = self.seed_users(groups)
        setores = self.seed_setores()
        cargos = self.seed_cargos(setores)
        funcionarios = self.seed_funcionarios(users, setores, cargos)
        self.seed_planos(funcionarios, cargos)
        self.seed_contratos(funcionarios)
        self.seed_folhas(funcionarios)
        candidatos = self.seed_candidatos(users)
        vagas = self.seed_vagas(setores)
        self.seed_candidaturas(candidatos, vagas)
        self.seed_avaliacoes(funcionarios)
        self.seed_analises(funcionarios, setores, users)
        self.seed_agente_documentos(users)

        self.stdout.write(self.style.SUCCESS('Seed demo concluido.'))
        for key in sorted(self.counts):
            self.stdout.write(f'{key}: {self.counts[key]}')

    def bump(self, key, amount=1):
        self.counts[key] = self.counts.get(key, 0) + amount

    def demo_user(self, username, email, group=None, first_name='', last_name='', staff=False):
        User = get_user_model()
        user, created = User.objects.update_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
                'is_staff': staff,
                'is_superuser': False,
            },
        )
        if self.login_password:
            user.set_password(self.login_password)
        elif created or not user.has_usable_password():
            user.set_unusable_password()
        user.save()
        if group:
            user.groups.add(group)
        self.bump('auth_user')
        return user

    def save_pdf_field(self, instance, field_name, file_name):
        field = getattr(instance, field_name)
        if not field:
            field.save(file_name, ContentFile(PDF_BYTES), save=True)

    def write_root_pdf(self, relative_path):
        path = Path(settings.BASE_DIR) / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(PDF_BYTES)

    def seed_groups(self):
        group_names = ['rh', 'lideranca', 'funcionario', 'candidato']
        groups = {}
        for name in group_names:
            groups[name], _ = Group.objects.get_or_create(name=name)
            self.bump('auth_group')
        return groups

    def seed_users(self, groups):
        users = {
            'rh': self.demo_user('demo.rh', 'demo.rh@smartrh.local', groups['rh'], 'Marina', 'Queiroz', staff=True),
            'lideranca': self.demo_user(
                'demo.lideranca',
                'demo.lideranca@smartrh.local',
                groups['lideranca'],
                'Renato',
                'Azevedo',
            ),
            'funcionario': self.demo_user(
                'demo.funcionario',
                'demo.funcionario@smartrh.local',
                groups['funcionario'],
                'Camila',
                'Nogueira',
            ),
            'candidato': self.demo_user(
                'candidato:demo.candidato',
                'demo.candidato@smartrh.local',
                groups['candidato'],
                'Isabela',
                'Macedo',
            ),
        }
        for index in range(1, 13):
            users[f'funcionario_{index}'] = self.demo_user(
                f'demo.colaborador.{index:02d}',
                f'demo.colaborador.{index:02d}@smartrh.local',
                groups['funcionario'],
            )
        for index in range(1, 13):
            users[f'candidato_{index}'] = self.demo_user(
                f'candidato:talento.{index:02d}',
                f'talento.{index:02d}@smartrh.local',
                groups['candidato'],
            )
        return users

    def seed_setores(self):
        data = [
            ('Gente e Cultura', 'Gestao de pessoas, beneficios e desenvolvimento interno.'),
            ('Tecnologia', 'Produtos digitais, infraestrutura e seguranca da informacao.'),
            ('Operacoes', 'Rotina operacional, atendimento interno e melhoria continua.'),
            ('Financeiro', 'Contas, planejamento financeiro e controles administrativos.'),
            ('Comercial', 'Relacionamento com clientes e estrategia de crescimento.'),
            ('Marketing', 'Comunicacao institucional, campanhas e posicionamento de marca.'),
            ('Juridico', 'Contratos, governanca e apoio regulatorio.'),
            ('Suprimentos', 'Compras, fornecedores e controle de materiais.'),
        ]
        setores = []
        for nome, descricao in data:
            setor, _ = Setor.objects.update_or_create(nome=nome, defaults={'descricao': descricao})
            setores.append(setor)
            self.bump('setor')
        return setores

    def seed_cargos(self, setores):
        by_name = {setor.nome: setor for setor in setores}
        data = [
            ('Analista de RH', 'Executa processos de admissao, beneficios e atendimento interno.', 'Gente e Cultura'),
            ('Coordenador de RH', 'Coordena indicadores de pessoas e ciclos de avaliacao.', 'Gente e Cultura'),
            ('Desenvolvedor Backend', 'Construcao de APIs, integracoes e regras de negocio.', 'Tecnologia'),
            ('Desenvolvedor Frontend', 'Interfaces web, acessibilidade e integracao com APIs.', 'Tecnologia'),
            ('Analista de Dados', 'Modelagem de indicadores e paineis gerenciais.', 'Tecnologia'),
            ('Supervisor de Operacoes', 'Acompanha filas, padroes operacionais e SLA.', 'Operacoes'),
            ('Assistente Financeiro', 'Concilia pagamentos, notas e controles financeiros.', 'Financeiro'),
            ('Analista Comercial', 'Prospecao consultiva e acompanhamento de oportunidades.', 'Comercial'),
            ('Designer de Marketing', 'Materiais visuais, campanhas e identidade digital.', 'Marketing'),
            ('Analista Juridico', 'Revisao contratual e apoio a governanca corporativa.', 'Juridico'),
            ('Comprador Senior', 'Negociacao com fornecedores e contratos de compra.', 'Suprimentos'),
            ('Diretor de Operacoes', 'Define estrategia operacional e acompanha metas de area.', 'Operacoes'),
        ]
        cargos = []
        for nome, descricao, setor_nome in data:
            cargo, _ = Cargo.objects.update_or_create(
                nome=nome,
                defaults={'descricao': descricao, 'fk_id_setor': by_name[setor_nome]},
            )
            cargos.append(cargo)
            self.bump('cargo')
        return cargos

    def seed_funcionarios(self, users, setores, cargos):
        cargo_by_name = {cargo.nome: cargo for cargo in cargos}
        data = [
            ('Marina Queiroz', '910.000.001-01', 'marina.queiroz@smartrh.local', '48991010001', 'Coordenador de RH', 'rh'),
            ('Renato Azevedo', '910.000.001-02', 'renato.azevedo@smartrh.local', '48991010002', 'Diretor de Operacoes', 'lideranca'),
            ('Camila Nogueira', '910.000.001-03', 'camila.nogueira@smartrh.local', '48991010003', 'Desenvolvedor Frontend', 'funcionario'),
            ('Bianca Salgado', '910.000.001-04', 'bianca.salgado@smartrh.local', '48991010004', 'Analista de RH', 'funcionario_1'),
            ('Eduardo Ribeiro', '910.000.001-05', 'eduardo.ribeiro@smartrh.local', '48991010005', 'Desenvolvedor Backend', 'funcionario_2'),
            ('Larissa Fontes', '910.000.001-06', 'larissa.fontes@smartrh.local', '48991010006', 'Analista de Dados', 'funcionario_3'),
            ('Otavio Martins', '910.000.001-07', 'otavio.martins@smartrh.local', '48991010007', 'Supervisor de Operacoes', 'funcionario_4'),
            ('Patricia Valenca', '910.000.001-08', 'patricia.valenca@smartrh.local', '48991010008', 'Assistente Financeiro', 'funcionario_5'),
            ('Gustavo Lemos', '910.000.001-09', 'gustavo.lemos@smartrh.local', '48991010009', 'Analista Comercial', 'funcionario_6'),
            ('Helena Costa', '910.000.001-10', 'helena.costa@smartrh.local', '48991010010', 'Designer de Marketing', 'funcionario_7'),
            ('Rafael Duarte', '910.000.001-11', 'rafael.duarte@smartrh.local', '48991010011', 'Analista Juridico', 'funcionario_8'),
            ('Sofia Andrade', '910.000.001-12', 'sofia.andrade@smartrh.local', '48991010012', 'Comprador Senior', 'funcionario_9'),
            ('Mateus Farias', '910.000.001-13', 'mateus.farias@smartrh.local', '48991010013', 'Desenvolvedor Backend', 'funcionario_10'),
            ('Clara Monteiro', '910.000.001-14', 'clara.monteiro@smartrh.local', '48991010014', 'Analista Comercial', 'funcionario_11'),
            ('Daniela Prado', '910.000.001-15', 'daniela.prado@smartrh.local', '48991010015', 'Analista de Dados', 'funcionario_12'),
        ]
        funcionarios = []
        for index, (nome, cpf, email, telefone, cargo_nome, user_key) in enumerate(data):
            cargo = cargo_by_name[cargo_nome]
            funcionario, _ = Funcionario.objects.update_or_create(
                cpf=cpf,
                defaults={
                    'user': users[user_key],
                    'nome': nome,
                    'email': email,
                    'telefone': telefone,
                    'data_admissao': date(2021, 1, 10) + timedelta(days=index * 74),
                    'status': Funcionario.STATUS_INATIVO if index in {10, 14} else Funcionario.STATUS_ATIVO,
                    'fk_id_setor': cargo.fk_id_setor,
                    'fk_id_cargo': cargo,
                },
            )
            funcionarios.append(funcionario)
            self.bump('funcionario')
        return funcionarios

    def seed_planos(self, funcionarios, cargos):
        for index, cargo in enumerate(cargos[:12]):
            creator = funcionarios[index % len(funcionarios)]
            plano, _ = PlanoCarreira.objects.update_or_create(
                fk_id_cargo=cargo,
                descricao=f'Evolucao para atuacao ampliada em {cargo.nome}, com autonomia em entregas criticas.',
                defaults={
                    'fk_id_criador': creator,
                    'requisitos': 'Mentoria trimestral, dominio dos indicadores da area, comunicacao clara e entrega de projeto aplicado.',
                },
            )
            self.bump('plano_carreira')
            PlanoCarreira.objects.update_or_create(
                fk_id_cargo=cargo,
                descricao=f'Ciclo avancado de carreira para {cargo.nome} com foco em impacto transversal.',
                defaults={
                    'fk_id_criador': creator,
                    'requisitos': 'Conduzir iniciativa interdepartamental, documentar resultados e apoiar desenvolvimento de pares.',
                },
            )
            self.bump('plano_carreira')

    def seed_contratos(self, funcionarios):
        tipos = [
            'CLT - Prazo Indeterminado',
            'CLT - Prazo Determinado',
            'CLT - Trabalho Intermitente',
            'Pessoa Juridica',
            'Estagio',
            'Autonomo',
        ]
        for index, funcionario in enumerate(funcionarios[:13]):
            contrato, _ = Contrato.objects.update_or_create(
                fk_id_funcionario=funcionario,
                tipo_contrato=tipos[index % len(tipos)],
                defaults={
                    'salario': Decimal('3200.00') + Decimal(index * 430),
                    'data_inicio': funcionario.data_admissao,
                    'data_fim': None if index % 4 else funcionario.data_admissao + timedelta(days=730),
                },
            )
            self.save_pdf_field(contrato, 'arquivo', f'contrato_{funcionario.nome.replace(" ", "_")}.pdf')
            self.bump('contrato')

    def seed_folhas(self, funcionarios):
        competencias = ['janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro']
        for index, funcionario in enumerate(funcionarios[:14]):
            folha, _ = FolhaPagamento.objects.update_or_create(
                fk_id_funcionario=funcionario,
                competencia=competencias[index % len(competencias)],
                defaults={},
            )
            self.save_pdf_field(folha, 'arquivo', f'folha_{funcionario.nome.replace(" ", "_")}_{competencias[index % len(competencias)]}.pdf')
            self.bump('folha_pagamento')

    def seed_candidatos(self, users):
        data = [
            ('Isabela Macedo', '92000000101', 'isabela.macedo@talentos.local', '48992010001', 'candidato'),
            ('Noah Sampaio', '92000000102', 'noah.sampaio@talentos.local', '48992010002', 'candidato_1'),
            ('Valentina Rocha', '92000000103', 'valentina.rocha@talentos.local', '48992010003', 'candidato_2'),
            ('Theo Albuquerque', '92000000104', 'theo.albuquerque@talentos.local', '48992010004', 'candidato_3'),
            ('Livia Barros', '92000000105', 'livia.barros@talentos.local', '48992010005', 'candidato_4'),
            ('Arthur Campos', '92000000106', 'arthur.campos@talentos.local', '48992010006', 'candidato_5'),
            ('Manuela Correia', '92000000107', 'manuela.correia@talentos.local', '48992010007', 'candidato_6'),
            ('Enzo Teixeira', '92000000108', 'enzo.teixeira@talentos.local', '48992010008', 'candidato_7'),
            ('Alice Moraes', '92000000109', 'alice.moraes@talentos.local', '48992010009', 'candidato_8'),
            ('Davi Pacheco', '92000000110', 'davi.pacheco@talentos.local', '48992010010', 'candidato_9'),
            ('Laura Batista', '92000000111', 'laura.batista@talentos.local', '48992010011', 'candidato_10'),
            ('Miguel Araujo', '92000000112', 'miguel.araujo@talentos.local', '48992010012', 'candidato_11'),
        ]
        candidatos = []
        for nome, cpf, email, telefone, user_key in data:
            candidato, _ = Candidato.objects.update_or_create(
                cpf_candidato=cpf,
                defaults={
                    'user': users[user_key],
                    'nome': nome,
                    'email': email,
                    'telefone': telefone,
                },
            )
            self.save_pdf_field(candidato, 'curriculo', f'curriculo_{nome.replace(" ", "_")}.pdf')
            candidatos.append(candidato)
            self.bump('candidato')
        return candidatos

    def seed_vagas(self, setores):
        setor_cycle = setores
        data = [
            ('Analista de Pessoas Pleno', 'Apoio ao ciclo de gente e cultura.', 'recrutamento, onboarding, indicadores, comunicacao', 'aberta'),
            ('Desenvolvedor Backend Python', 'Construcao de APIs internas.', 'python, django, rest, postgresql, testes', 'aberta'),
            ('Desenvolvedor Frontend React', 'Evolucao da interface Smart RH.', 'react, typescript, acessibilidade, api, testes', 'andamento'),
            ('Analista de Dados de Pessoas', 'Indicadores de RH e paineis executivos.', 'sql, bi, dashboards, estatistica, comunicacao', 'aberta'),
            ('Supervisor de Operacoes', 'Gestao de rotina e SLA operacional.', 'lideranca, indicadores, processos, melhoria continua', 'andamento'),
            ('Assistente Financeiro', 'Controles financeiros e conciliacao.', 'excel, contas a pagar, conciliacao, organizacao', 'fechada'),
            ('Executivo Comercial B2B', 'Atuacao consultiva com clientes corporativos.', 'crm, prospeccao, negociacao, metas', 'aberta'),
            ('Designer de Conteudo Digital', 'Criacao visual para campanhas internas.', 'design, figma, campanhas, identidade visual', 'cancelada'),
            ('Analista Juridico Contratual', 'Revisao de contratos e apoio regulatorio.', 'contratos, compliance, lgpd, organizacao', 'andamento'),
            ('Comprador de Servicos', 'Gestao de fornecedores e compras recorrentes.', 'negociacao, fornecedores, contratos, planejamento', 'aberta'),
            ('Coordenador de Treinamento', 'Trilhas de aprendizagem e desenvolvimento.', 'treinamento, facilitacao, indicadores, cultura', 'fechada'),
            ('Especialista em Produto Interno', 'Descoberta e priorizacao de melhorias.', 'produto, discovery, requisitos, metricas', 'aberta'),
        ]
        vagas = []
        for index, (titulo, descricao, requisitos, status) in enumerate(data):
            vaga, _ = Vaga.objects.update_or_create(
                titulo=titulo,
                defaults={
                    'descricao': descricao,
                    'requisitos': requisitos,
                    'data_publicacao': self.today - timedelta(days=45 - index * 3),
                    'status': status,
                    'fk_id_setor': setor_cycle[index % len(setor_cycle)],
                },
            )
            vagas.append(vaga)
            self.bump('vaga')
        return vagas

    def seed_candidaturas(self, candidatos, vagas):
        classificacoes = [
            (True, 'aprovado', 92),
            (True, 'aprovado', 78),
            (None, 'pendente_revisao_rh', 58),
            (False, 'reprovado_tecnico', 28),
        ]
        created = 0
        for index in range(20):
            candidato = candidatos[index % len(candidatos)]
            vaga = vagas[(index * 2 + index // 3) % len(vagas)]
            aprovado, classificacao, pontuacao = classificacoes[index % len(classificacoes)]
            defaults = {
                'status_processo': 'andamento' if classificacao != 'aprovado' else 'em_analise_rh',
                'triagem_automatica_aprovada': aprovado,
                'triagem_automatica_motivo': f'Pontuacao de aderencia calculada em {pontuacao}% para requisitos da vaga.',
                'triagem_automatica_palavras_chave': vaga.requisitos,
                'triagem_automatica_pontuacao': pontuacao,
                'triagem_automatica_classificacao': classificacao,
            }
            obj = CandidatoVaga.objects.filter(cpf_candidato=candidato, id_vaga=vaga).first()
            if obj:
                for field, value in defaults.items():
                    setattr(obj, field, value)
                obj.save()
            else:
                CandidatoVaga.objects.create(cpf_candidato=candidato, id_vaga=vaga, **defaults)
            created += 1
        self.bump('candidato_vaga', created)

    def seed_avaliacoes(self, funcionarios):
        categorias = ['90º', '180º', '360º']
        comentarios = [
            'Entrega consistente, boa colaboracao e abertura para feedbacks.',
            'Evoluiu na organizacao das demandas e comunica riscos com antecedencia.',
            'Demonstra dominio tecnico e pode ampliar compartilhamento de conhecimento.',
            'Mantem postura colaborativa mesmo em periodos de maior volume.',
        ]
        for index, funcionario in enumerate(funcionarios[:14]):
            avaliador = funcionarios[(index + 1) % len(funcionarios)]
            AvaliacaoDesempenho.objects.update_or_create(
                fk_id_funcionario=funcionario,
                fk_id_avaliador=avaliador,
                data_avaliacao=self.today - timedelta(days=60 - index),
                defaults={
                    'categoria': categorias[index % len(categorias)],
                    'nota': Decimal('6.50') + Decimal((index % 5) * 0.7).quantize(Decimal('0.01')),
                    'comentario': comentarios[index % len(comentarios)],
                },
            )
            self.bump('avaliacao_desempenho')

    def seed_analises(self, funcionarios, setores, users):
        perguntas = [
            {'id': 'sentimento', 'titulo': 'Termometro de sentimento'},
            {'id': 'desenvolvimento', 'titulo': 'Apoio ao desenvolvimento profissional'},
            {'id': 'reconhecimento', 'titulo': 'Senso de reconhecimento'},
            {'id': 'ambiente_fisico', 'titulo': 'Ambiente fisico'},
            {'id': 'clima', 'titulo': 'Clima geral'},
            {'id': 'lideranca', 'titulo': 'Percepcao sobre lideranca'},
            {'id': 'colegas', 'titulo': 'Relacao com colegas'},
        ]
        for index, setor in enumerate(setores[:6]):
            envio, _ = AnaliseComportamentalEnvio.objects.update_or_create(
                titulo=f'Pulso organizacional {setor.nome}',
                fk_id_setor=setor,
                defaults={
                    'fk_id_funcionario': None,
                    'perguntas': perguntas,
                    'criado_por': users['rh'],
                },
            )
            self.bump('analise_comportamental_envio')
            for funcionario in Funcionario.objects.filter(fk_id_setor=setor, status=Funcionario.STATUS_ATIVO)[:2]:
                respostas = {
                    'sentimento': ['Feliz', 'Neutro', 'Muito Feliz'][index % 3],
                    'observacao': 'Rotina clara, com oportunidades de alinhamento entre areas.',
                    'desenvolvimento': 'Na maioria das vezes',
                    'reconhecimento': 'Valorizado',
                    'ambiente_fisico': 4,
                    'clima': 4 if index % 2 == 0 else 3,
                    'lideranca': 'Apoiador',
                    'colegas': 4,
                }
                status_resposta = AnaliseComportamentalResposta.STATUS_RESPONDIDO if index % 2 == 0 else AnaliseComportamentalResposta.STATUS_PENDENTE
                AnaliseComportamentalResposta.objects.update_or_create(
                    fk_id_envio=envio,
                    fk_id_funcionario=funcionario,
                    defaults={
                        'respostas': respostas,
                        'status': status_resposta,
                        'respondido_em': self.now - timedelta(days=index) if status_resposta == AnaliseComportamentalResposta.STATUS_RESPONDIDO else None,
                    },
                )
                self.bump('analise_comportamental_resposta')
                if status_resposta == AnaliseComportamentalResposta.STATUS_RESPONDIDO:
                    AnaliseComportamental.objects.update_or_create(
                        fk_id_funcionario=funcionario,
                        data_analise=self.today - timedelta(days=index),
                        defaults={
                            'resultado': (
                                'Resumo executivo: colaborador relata experiencia positiva, com bom alinhamento de equipe. '
                                'Sinais de atencao moderados apenas em integracao entre areas. Recomendacao: manter conversas de acompanhamento.'
                            ),
                        },
                    )
                    self.bump('analise_comportamental')

    def seed_agente_documentos(self, users):
        docs = [
            ('Politica de Beneficios 2026', 'imp_doc/politica_beneficios_2026.pdf', 'Regras ficticias de beneficios internos, elegibilidade e canais de suporte.'),
            ('Manual de Ferias e Banco de Horas', 'imp_doc/manual_ferias_banco_horas.pdf', 'Orientacoes ficticias sobre solicitacao de ferias, banco de horas e aprovacao.'),
            ('Guia de Desenvolvimento Interno', 'imp_doc/guia_desenvolvimento_interno.pdf', 'Trilhas ficticias de aprendizagem, mentoria e ciclos de carreira.'),
            ('Politica de Trabalho Hibrido', 'imp_doc/politica_trabalho_hibrido.pdf', 'Diretrizes ficticias para rotina hibrida, presenca e comunicacao.'),
            ('Conduta e Etica Corporativa', 'imp_doc/conduta_etica_corporativa.pdf', 'Codigo ficticio de conduta, confidencialidade e relacionamento profissional.'),
        ]
        for titulo, arquivo, conteudo in docs:
            self.write_root_pdf(arquivo)
            FuncionarioAgenteDocumento.objects.update_or_create(
                titulo=titulo,
                defaults={
                    'arquivo': arquivo,
                    'conteudo_extraido': conteudo,
                    'ativo': True,
                    'criado_por': users['rh'],
                },
            )
            self.bump('agente_documento')
