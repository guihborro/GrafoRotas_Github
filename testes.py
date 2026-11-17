# =============================================================================
# GrafoRotas - Testes automatizados e reproduziveis de TODAS as opcoes do menu
# (no minimo dois testes por opcao) e da consistencia da base de dados.
#
# Cada teste executa a propria funcao do menu (main.py) com entradas
# simuladas, captura a saida exibida ao usuario e confere o resultado. Os
# resultados dos algoritmos sao conferidos por implementacoes independentes
# (Floyd-Warshall para caminhos minimos, Kruskal para a arvore geradora
# minima) ou por grafos classicos de resposta conhecida (ciclos, estrela,
# grafo de Petersen, K5). Ao final grava 'resultados_testes.txt' com a
# entrada, a saida e o veredito de cada teste (evidencia para o relatorio).
#
# Teoria dos Grafos - 6o semestre | Bacharelado em Ciencia da Computacao
# Universidade Presbiteriana Mackenzie - Prof. Dr. Ivan Carlos Alcantara de Oliveira
#
# Integrantes:
#   Guilherme Haddad Borro   - RA 10427699
#   Rafael Lima              - RA 10425819
#   Pedro Augusto Yoshikuni  - RA 10410287
#   Tiago Silveira Lopes     - RA 10417600
#
# Historico de alteracoes (data | autor | descricao):
#   2026-10-18 | Guilherme Haddad Borro | Criacao (Parte 3): 2+ testes por
#                opcao do menu (1 a 21), testes da base e log de evidencias.
#   2026-11-16 | Guilherme Haddad Borro | Valores esperados lidos diretamente
#                do grafo.txt (sem numeros fixos), para valer em nova coleta.
#
# Uso:  python testes.py        (ou: python -m unittest testes -v)
# =============================================================================

import csv
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import algoritmos as alg
import main as app
from grafo import Grafo

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_GRAFO = os.path.join(PASTA, "grafo.txt")
ARQ_CIDADES = os.path.join(PASTA, "cidades.csv")
ARQ_LOG = os.path.join(PASTA, "resultados_testes.txt")
INF = float("inf")

BASE = Grafo().ler_arquivo(ARQ_GRAFO)   # base real, lida uma unica vez
REGISTRO = []                           # evidencias gravadas no log

# Valores esperados obtidos por leitura DIRETA das linhas do grafo.txt,
# independente da classe Grafo (assim os testes valem para qualquer coleta).
with open(ARQ_GRAFO, encoding="utf-8") as _f:
    LINHAS_ARQ = _f.read().splitlines()
N_ARQ = int(LINHAS_ARQ[1])
M_ARQ = int(LINHAS_ARQ[2 + N_ARQ])
NOMES_ARQ = {int(l.split(";")[0]): l.split(";")[1] for l in LINHAS_ARQ[2:2 + N_ARQ]}
GRAU_ARQ = {v: 0 for v in NOMES_ARQ}
for _l in LINHAS_ARQ[3 + N_ARQ:3 + N_ARQ + M_ARQ]:
    _u, _v, _ = _l.split(";")
    GRAU_ARQ[int(_u)] += 1
    GRAU_ARQ[int(_v)] += 1
GMIN_ARQ, GMAX_ARQ = min(GRAU_ARQ.values()), max(GRAU_ARQ.values())
IMPARES_ARQ = sum(g % 2 for g in GRAU_ARQ.values())
# cidade de maior grau (menor id em caso de empate), usada nos testes de remocao
V_MAX = min(v for v in GRAU_ARQ if GRAU_ARQ[v] == GMAX_ARQ)
NOME_MAX = NOMES_ARQ[V_MAX]


# --------------------------------------------------------------------------- #
# Utilitarios
# --------------------------------------------------------------------------- #
def base():
    """Copia independente da base real (cada teste parte do estado original)."""
    return BASE.copia()


def id_de(g, nome):
    vid, erro = g.buscar_vertice(nome)
    assert erro is None, erro
    return vid


def grafo_de(arestas, n=None):
    """Grafo pequeno a partir de [(u, v, peso)]; rotulos 'V0', 'V1', ..."""
    g = Grafo()
    for v in range(n or 0):
        g.inserir_vertice(v, f"V{v}")
    for u, v, p in arestas:
        g.inserir_vertice(u, f"V{u}")
        g.inserir_vertice(v, f"V{v}")
        g.inserir_aresta(u, v, p)
    return g


def ciclo(n):
    return grafo_de([(i, (i + 1) % n, 1.0) for i in range(n)])


def petersen():
    """Grafo de Petersen: 3-regular, 2-conexo e classicamente NAO hamiltoniano."""
    externas = [(i, (i + 1) % 5, 1.0) for i in range(5)]
    raios = [(i, i + 5, 1.0) for i in range(5)]
    internas = [(5 + i, 5 + (i + 2) % 5, 1.0) for i in range(5)]
    return grafo_de(externas + raios + internas)


def completo(n):
    return grafo_de([(i, j, 1.0) for i in range(n) for j in range(i + 1, n)])


def estrela(folhas):
    return grafo_de([(0, i, 1.0) for i in range(1, folhas + 1)])


def floyd_warshall(g):
    """Todas as distancias minimas por Floyd-Warshall (O(V^3)), independente
    do Dijkstra; usado como referencia de conferencia."""
    vs = sorted(g.adjacencia)
    idx = {v: i for i, v in enumerate(vs)}
    n = len(vs)
    d = [[INF] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0.0
    for u, v, p in g.lista_arestas():
        d[idx[u]][idx[v]] = d[idx[v]][idx[u]] = p
    for k in range(n):
        dk = d[k]
        for i in range(n):
            dik = d[i][k]
            if dik == INF:
                continue
            di = d[i]
            for j in range(n):
                if dik + dk[j] < di[j]:
                    di[j] = dik + dk[j]
    return idx, d


_FW_BASE = None


def fw_base():
    global _FW_BASE
    if _FW_BASE is None:
        _FW_BASE = floyd_warshall(BASE)
    return _FW_BASE


def kruskal(g):
    """Custo da arvore geradora minima por Kruskal (referencia para o Prim)."""
    pai = {v: v for v in g.adjacencia}

    def raiz(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    custo, usadas = 0.0, 0
    for u, v, p in sorted(g.lista_arestas(), key=lambda a: a[2]):
        if raiz(u) != raiz(v):
            pai[raiz(u)] = raiz(v)
            custo += p
            usadas += 1
    return custo, usadas


class TesteMenu(unittest.TestCase):
    """Base: executa uma opcao do menu com entradas simuladas e registra."""

    maxDiff = None

    def rodar(self, opcao, g, entradas, esperado):
        fila = list(entradas)
        saida = io.StringIO()

        def entrada_simulada(msg=""):
            if not fila:
                raise AssertionError(f"opcao {opcao} pediu mais entradas que o previsto")
            valor = fila.pop(0)
            saida.write(f"{msg}{valor}\n")           # eco, como no terminal
            return valor

        with mock.patch("builtins.input", entrada_simulada), redirect_stdout(saida):
            retorno = app.ACOES[str(opcao)](g)
        self.assertEqual(fila, [], "entradas simuladas nao consumidas")
        evidencia = {
            "id": self.id().split(".")[-1],
            "opcao": opcao,
            "descricao": (self._testMethodDoc or "").strip(),
            "entradas": entradas,
            "saida": saida.getvalue(),
            "esperado": esperado,
            "veredito": "FALHOU",
        }
        self.__dict__.setdefault("_evidencias", []).append(evidencia)
        REGISTRO.append(evidencia)
        return saida.getvalue(), retorno

    def aprovado(self):
        """Chamado ao final do teste, apos todas as verificacoes passarem."""
        for evidencia in self.__dict__.get("_evidencias", []):
            evidencia["veredito"] = "APROVADO"


# =========================================================================== #
# Opcoes 1 a 11 - infraestrutura
# =========================================================================== #
class T01Exibir(TesteMenu):
    def test_01a_padrao_dez_vertices(self):
        """Exibir com Enter: cabecalho com totais e os 10 primeiros vertices."""
        out, _ = self.rodar(1, base(), [""], f"{N_ARQ} vertices, {M_ARQ} arestas; 10 linhas e '...'")
        self.assertIn(f"Grafo: {N_ARQ} vertices, {M_ARQ} arestas", out)
        self.assertEqual(out.count("  ["), 10)
        self.assertIn("  ...", out)
        self.aprovado()

    def test_01b_tudo(self):
        """Exibir com 'tudo': a lista de adjacencia de todos os vertices."""
        out, _ = self.rodar(1, base(), ["tudo"], f"{N_ARQ} linhas de vertices, sem '...'")
        self.assertEqual(out.count("  ["), N_ARQ)
        self.assertNotIn("  ...", out)
        self.aprovado()


class T02MostrarArquivo(TesteMenu):
    def test_02a_conteudo_grafo_txt(self):
        """Mostrar as 6 primeiras linhas do grafo.txt (tipo, n e vertices)."""
        total = len(LINHAS_ARQ)
        out, _ = self.rodar(2, base(), [ARQ_GRAFO, "6"],
                            f"{total} linhas; linha 1 = '2', linha 2 = '{N_ARQ}'; {total - 6} omitidas")
        self.assertIn(f"({total} linhas)", out)
        self.assertIn("   1 | 2", out)
        self.assertIn(f"   2 | {N_ARQ}", out)
        self.assertIn(f"{total - 6} linhas omitidas", out)
        self.aprovado()

    def test_02b_arquivo_inexistente(self):
        """Arquivo inexistente: mensagem de erro, sem encerrar o programa."""
        out, _ = self.rodar(2, base(), ["nao_existe.txt"], "mensagem 'Nao foi possivel abrir'")
        self.assertIn("Nao foi possivel abrir 'nao_existe.txt'", out)
        self.aprovado()


class T03InserirVertice(TesteMenu):
    def test_03a_novo_vertice(self):
        """Inserir vertice com id novo: total de vertices aumenta em 1, grau 0."""
        g = base()
        novo = max(GRAU_ARQ) + 1
        out, _ = self.rodar(3, g, [str(novo), "Cidade Teste"], f"{N_ARQ + 1} vertices; grau 0")
        self.assertEqual(g.numero_vertices(), N_ARQ + 1)
        self.assertEqual(g.grau(novo), 0)
        self.assertIn(f"Total: {N_ARQ + 1} vertices", out)
        self.aprovado()

    def test_03b_id_repetido(self):
        """Inserir id ja existente (0): recusado, total inalterado."""
        g = base()
        out, _ = self.rodar(3, g, ["0", "Duplicada"], f"'ja existe'; {N_ARQ} vertices")
        self.assertIn("ja existe", out)
        self.assertEqual(g.numero_vertices(), N_ARQ)
        self.assertEqual(g.nome(0), BASE.nome(0))
        self.aprovado()


class T04RemoverVertice(TesteMenu):
    def test_04a_remove_por_nome(self):
        """Remover pelo nome a cidade de maior grau: some com todas as suas arestas."""
        g = base()
        out, _ = self.rodar(4, g, [NOME_MAX.lower()],
                            f"{NOME_MAX} (grau {GMAX_ARQ}): {N_ARQ - 1} vertices, "
                            f"{M_ARQ} - {GMAX_ARQ} = {M_ARQ - GMAX_ARQ} arestas")
        self.assertEqual((g.numero_vertices(), g.numero_arestas()), (N_ARQ - 1, M_ARQ - GMAX_ARQ))
        self.assertTrue(all(V_MAX not in viz for viz in g.adjacencia.values()))
        self.assertIn("removido", out)
        self.aprovado()

    def test_04b_inexistente(self):
        """Remover vertice inexistente (999): mensagem e grafo inalterado."""
        g = base()
        out, _ = self.rodar(4, g, ["999"], f"'nao encontrado'; {N_ARQ}/{M_ARQ}")
        self.assertIn("nao encontrado", out)
        self.assertEqual((g.numero_vertices(), g.numero_arestas()), (N_ARQ, M_ARQ))
        self.aprovado()


class T05InserirAresta(TesteMenu):
    def test_05a_nova_aresta(self):
        """Inserir Sao Paulo - Campinas (95 km): uma aresta a mais, simetrica."""
        g = base()
        sp, cp = id_de(g, "Sao Paulo"), id_de(g, "Campinas")
        self.assertNotIn(cp, g.adjacencia[sp])               # pre-condicao
        out, _ = self.rodar(5, g, ["Sao Paulo", "Campinas", "95"],
                            f"{M_ARQ + 1} arestas; peso nos 2 sentidos")
        self.assertEqual(g.numero_arestas(), M_ARQ + 1)
        self.assertEqual(g.adjacencia[sp][cp], 95.0)
        self.assertEqual(g.adjacencia[cp][sp], 95.0)
        self.assertIn("inserida", out)
        self.aprovado()

    def test_05b_laco_e_peso_invalido(self):
        """Laco (origem = destino) e peso negativo sao recusados."""
        g = base()
        out1, _ = self.rodar(5, g, ["Campinas", "Campinas", "10"], "laco recusado")
        self.assertIn("laco", out1)
        out2, _ = self.rodar(5, g, ["Campinas", "Sorocaba", "-5"], "peso negativo recusado")
        self.assertIn("peso deve ser positivo", out2)
        self.assertEqual(g.numero_arestas(), M_ARQ)
        self.aprovado()


class T06RemoverAresta(TesteMenu):
    def test_06a_aresta_existente(self):
        """Remover a ligacao mais curta de Sao Paulo: uma aresta a menos."""
        g = base()
        sp = id_de(g, "Sao Paulo")
        viz = min(g.adjacencia[sp], key=g.adjacencia[sp].get)
        out, _ = self.rodar(6, g, ["Sao Paulo", g.nome(viz)],
                            f"Sao Paulo - {g.nome(viz)} removida; {M_ARQ - 1} arestas")
        self.assertEqual(g.numero_arestas(), M_ARQ - 1)
        self.assertNotIn(viz, g.adjacencia[sp])
        self.assertNotIn(sp, g.adjacencia[viz])
        self.assertIn("removida", out)
        self.aprovado()

    def test_06b_aresta_inexistente(self):
        """Remover ligacao inexistente (Sao Paulo - Campinas): mensagem."""
        g = base()
        out, _ = self.rodar(6, g, ["Sao Paulo", "Campinas"], f"'Nao existe aresta'; {M_ARQ}")
        self.assertIn("Nao existe aresta", out)
        self.assertEqual(g.numero_arestas(), M_ARQ)
        self.aprovado()


class T07Grau(TesteMenu):
    def test_07a_grau_por_nome_sem_acento(self):
        """Grau de 'sao paulo' (sem acento e minusculo) e seus vizinhos."""
        g = base()
        sp = id_de(g, "Sao Paulo")
        out, _ = self.rodar(7, g, ["sao paulo"], f"grau {GRAU_ARQ[sp]}")
        self.assertIn(f"Grau de [{sp}] São Paulo: {GRAU_ARQ[sp]}", out)
        self.assertEqual(out.count("    - "), GRAU_ARQ[sp])
        self.aprovado()

    def test_07b_nome_ambiguo(self):
        """Nome ambiguo ('Santa'): pede que o usuario seja mais especifico."""
        out, _ = self.rodar(7, base(), ["Santa"], "mensagem de ambiguidade")
        self.assertIn("ambiguo", out)
        self.aprovado()


class T08Conexidade(TesteMenu):
    def test_08a_base_conexa(self):
        """Base real: grafo conexo, com uma unica componente."""
        out, _ = self.rodar(8, base(), [], f"SIM; 1 componente [{N_ARQ}]")
        self.assertIn("conexo? SIM", out)
        self.assertIn(f"[{N_ARQ}]", out)
        self.aprovado()

    def test_08b_cidade_isolada(self):
        """Removendo todas as ligacoes de Aguai: 2 componentes."""
        g = base()
        ag = id_de(g, "Aguai")
        for w in list(g.adjacencia[ag]):
            g.remover_aresta(ag, w)
        out, _ = self.rodar(8, g, [], f"NAO; componentes [{N_ARQ - 1}, 1]")
        self.assertIn("conexo? NAO", out)
        self.assertIn(f"[{N_ARQ - 1}, 1]", out)
        self.aprovado()


class T09Reduzido(TesteMenu):
    def test_09a_base(self):
        """Base conexa: grafo reduzido com 1 supervertice."""
        out, _ = self.rodar(9, base(), [], "1 vertice, 0 arestas")
        self.assertIn("Grafo: 1 vertices, 0 arestas", out)
        self.aprovado()

    def test_09b_tres_componentes(self):
        """Grafo com 3 componentes: grafo reduzido com 3 supervertices."""
        g = grafo_de([(0, 1, 1.0), (2, 3, 1.0)], n=5)          # {0,1} {2,3} {4}
        out, _ = self.rodar(9, g, [], "3 vertices, 0 arestas")
        self.assertIn("Grafo: 3 vertices, 0 arestas", out)
        self.aprovado()


class T10Gravar(TesteMenu):
    def test_10a_gravar_e_reler(self):
        """Gravar apos remover um vertice e reler: arquivo identico ao grafo."""
        g = base()
        g.remover_vertice(V_MAX)
        with tempfile.TemporaryDirectory() as pasta:
            destino = os.path.join(pasta, "grafo_salvo.txt")
            out, _ = self.rodar(10, g, [destino], "arquivo relido identico ao grafo")
            relido = Grafo().ler_arquivo(destino)
        self.assertEqual(relido.adjacencia, g.adjacencia)
        self.assertEqual(relido.rotulos, g.rotulos)
        self.assertIn(f"{N_ARQ - 1} vertices, {M_ARQ - GMAX_ARQ} arestas", out)
        self.aprovado()

    def test_10b_caminho_invalido(self):
        """Gravar em pasta inexistente: mensagem de erro, sem travar."""
        destino = os.path.join(PASTA, "pasta_inexistente", "x.txt")
        out, _ = self.rodar(10, base(), [destino], "'Nao foi possivel gravar'")
        self.assertIn("Nao foi possivel gravar", out)
        self.aprovado()


class T11Recarregar(TesteMenu):
    def test_11a_recarrega_original(self):
        """Apos alterar o grafo, recarregar o grafo.txt restaura o original."""
        g = base()
        g.remover_vertice(0)
        out, novo = self.rodar(11, g, [ARQ_GRAFO], f"novo grafo com {N_ARQ}/{M_ARQ}")
        self.assertEqual((novo.numero_vertices(), novo.numero_arestas()), (N_ARQ, M_ARQ))
        self.assertIn(f"{N_ARQ} vertices, {M_ARQ} arestas", out)
        self.aprovado()

    def test_11b_arquivo_mal_formado(self):
        """Arquivo com aresta invalida: erro com numero da linha; grafo mantido."""
        g = base()
        with tempfile.TemporaryDirectory() as pasta:
            ruim = os.path.join(pasta, "ruim.txt")
            with open(ruim, "w", encoding="utf-8") as f:
                f.write("2\n2\n0;A\n1;B\n1\n0;1;abc\n")
            out, novo = self.rodar(11, g, [ruim], "erro na linha 6; grafo atual mantido")
        self.assertIs(novo, g)
        self.assertIn("linha 6", out)
        self.assertEqual(g.numero_vertices(), N_ARQ)
        self.aprovado()


# =========================================================================== #
# Opcoes 12 a 14 - solucao do problema
# =========================================================================== #
class T12CaminhoMinimo(TesteMenu):
    def test_12a_sao_paulo_campinas(self):
        """Sao Paulo -> Campinas: distancia igual a de Floyd-Warshall e rota valida."""
        g = base()
        sp, cp = id_de(g, "Sao Paulo"), id_de(g, "Campinas")
        idx, d = fw_base()
        out, _ = self.rodar(12, g, ["Sao Paulo", "Campinas"], f"{d[idx[sp]][idx[cp]]:.1f} km")
        total, cam = alg.caminho_minimo(g, sp, cp)
        self.assertAlmostEqual(total, d[idx[sp]][idx[cp]], places=6)
        self.assertEqual((cam[0], cam[-1]), (sp, cp))
        soma = sum(g.adjacencia[cam[i]][cam[i + 1]] for i in range(len(cam) - 1))
        self.assertAlmostEqual(soma, total, places=6)
        self.assertIn(f"Distancia total: {total:.1f} km", out)
        self.aprovado()

    def test_12b_grafo_conhecido(self):
        """Grafo de 5 vertices com resposta conhecida: V0->V3 = 9 por V0,V2,V1,V3."""
        g = grafo_de([(0, 1, 10), (0, 2, 3), (1, 2, 4), (1, 3, 2),
                      (2, 3, 8), (2, 4, 2), (3, 4, 5)])
        out, _ = self.rodar(12, g, ["V0", "V3"], "9.0 km; rota V0, V2, V1, V3")
        self.assertEqual(alg.caminho_minimo(g, 0, 3), (9.0, [0, 2, 1, 3]))
        self.assertIn("Distancia total: 9.0 km", out)
        self.aprovado()

    def test_12c_sem_caminho(self):
        """Cidades em componentes diferentes: informa que nao existe caminho."""
        g = grafo_de([(0, 1, 1.0), (2, 3, 1.0)])
        out, _ = self.rodar(12, g, ["V0", "V3"], "'Nao existe caminho'")
        self.assertIn("Nao existe caminho", out)
        self.assertEqual(alg.caminho_minimo(g, 0, 3), (INF, []))
        self.aprovado()

    def test_12d_todas_as_origens_conferidas(self):
        """Dijkstra a partir de TODAS as cidades coincide com Floyd-Warshall."""
        g = base()
        idx, d = fw_base()
        out, _ = self.rodar(12, g, ["Sorocaba", "Registro"], "distancia igual a Floyd-Warshall")
        for s in g.adjacencia:
            dist, _ = alg.dijkstra(g, s)
            for v, dv in dist.items():
                self.assertAlmostEqual(dv, d[idx[s]][idx[v]], places=6)
        self.aprovado()


class T13DistanciasOrigem(TesteMenu):
    def test_13a_a_partir_de_sao_paulo(self):
        """De Sao Paulo: todas alcancaveis; a mais proxima e o vizinho mais curto."""
        g = base()
        sp = id_de(g, "Sao Paulo")
        vizinho, peso = min(g.adjacencia[sp].items(), key=lambda it: it[1])
        out, _ = self.rodar(13, g, ["Sao Paulo", "3"], f"{N_ARQ - 1} alcancaveis; 1a = {g.nome(vizinho)}")
        self.assertIn(f"cidades alcancaveis: {N_ARQ - 1} | inalcancaveis: 0", out)
        primeira = out.split("mais proximas pela malha:\n")[1].splitlines()[0]
        self.assertIn(g.nome(vizinho), primeira)
        self.aprovado()

    def test_13b_cidade_isolada(self):
        """Cidade isolada (inserida sem arestas): nenhuma cidade alcancavel."""
        g = base()
        g.inserir_vertice(999, "Ilha Teste")
        out, _ = self.rodar(13, g, ["Ilha Teste", ""], f"0 alcancaveis; {N_ARQ} inalcancaveis")
        self.assertIn(f"cidades alcancaveis: 0 | inalcancaveis: {N_ARQ}", out)
        self.aprovado()


class T14AGM(TesteMenu):
    def test_14a_base_confere_com_kruskal(self):
        """AGM da base: n - 1 arestas e custo igual ao calculado por Kruskal."""
        g = base()
        custo_k, usadas_k = kruskal(g)
        out, _ = self.rodar(14, g, ["n"], f"{N_ARQ - 1} arestas; {custo_k:.1f} km")
        arestas, custo = alg.arvore_geradora_minima(g)
        self.assertEqual(len(arestas), N_ARQ - 1)
        self.assertEqual(usadas_k, N_ARQ - 1)
        self.assertAlmostEqual(custo, custo_k, places=6)
        self.assertIn(f"Custo total da AGM: {custo_k:.1f} km", out)
        self.aprovado()

    def test_14b_grafo_conhecido_e_floresta(self):
        """Quadrado com diagonal (AGM = 1+2+3 = 6) e grafo desconexo (floresta)."""
        g = grafo_de([(0, 1, 1), (1, 2, 2), (2, 3, 3), (3, 0, 4), (0, 2, 5)])
        out, _ = self.rodar(14, g, ["s"], "custo 6.0 km; 3 arestas listadas")
        self.assertIn("Custo total da AGM: 6.0 km", out)
        h = grafo_de([(0, 1, 1.0), (2, 3, 2.0)])
        out2, _ = self.rodar(14, h, ["n"], "Floresta (2 arvores)")
        self.assertIn("Floresta (2 arvores)", out2)
        self.aprovado()


# =========================================================================== #
# Opcoes 15 a 21 - caracteristicas do grafo
# =========================================================================== #
class T15Graus(TesteMenu):
    def test_15a_base(self):
        """Base: graus minimo e maximo e soma dos graus = 2 x |E| (aperto de maos)."""
        out, _ = self.rodar(15, base(), [], f"min {GMIN_ARQ}, max {GMAX_ARQ}, soma {2 * M_ARQ}, aperto de maos OK")
        self.assertIn(f"Grau minimo: {GMIN_ARQ} | maximo: {GMAX_ARQ}", out)
        self.assertIn(f"soma dos graus = {2 * M_ARQ} = 2 x {M_ARQ} arestas -> OK", out)
        r = alg.analise_graus(BASE)
        self.assertEqual(sum(r["distribuicao"].values()), N_ARQ)
        self.aprovado()

    def test_15b_estrela(self):
        """Estrela K1,4: centro com grau 4 e 4 folhas de grau 1."""
        out, _ = self.rodar(15, estrela(4), [], "min 1, max 4; distribuicao {1: 4, 4: 1}")
        self.assertIn("Grau minimo: 1 | maximo: 4", out)
        self.assertEqual(alg.analise_graus(estrela(4))["distribuicao"], {1: 4, 4: 1})
        self.aprovado()


class T16Coloracao(TesteMenu):
    def test_16a_base_numero_cromatico_exato(self):
        """Base: coloracao valida; Welsh-Powell usa tantas cores quanto a clique maxima (chi exato)."""
        r = alg.analise_coloracao(BASE)
        k = r["limite_inferior"]
        out, _ = self.rodar(16, base(), [], f"{k} cores; clique K{k}; chi = {k} exato; nao bipartido")
        self.assertTrue(r["valida"])
        c = r["clique"]
        self.assertTrue(all(v in BASE.adjacencia[u] for i, u in enumerate(c) for v in c[i + 1:]))
        self.assertEqual(r["num_cores"], k)
        self.assertIn(f"EXATAMENTE {k}", out)
        self.assertIn("bipartido? NAO", out)
        self.aprovado()

    def test_16b_ciclo_par_e_impar(self):
        """C6 e bipartido (2 cores); C5 exige 3 cores."""
        out, _ = self.rodar(16, ciclo(6), [], "C6: 2 cores, bipartido SIM")
        self.assertIn("Cores usadas (Welsh-Powell): 2", out)
        self.assertIn("bipartido? SIM", out)
        out2, _ = self.rodar(16, ciclo(5), [], "C5: 3 cores, nao bipartido")
        self.assertIn("Cores usadas (Welsh-Powell): 3", out2)
        self.aprovado()


class T17Euleriano(TesteMenu):
    def test_17a_base(self):
        """Base: muitos vertices de grau impar -> nem euleriano nem semieuleriano."""
        out, _ = self.rodar(17, base(), [], f"{IMPARES_ARQ} impares; NAO; NAO")
        self.assertGreater(IMPARES_ARQ, 2)
        self.assertIn(f"Vertices de grau impar: {IMPARES_ARQ}", out)
        self.assertIn("euleriano (circuito euleriano)? NAO", out)
        self.assertIn("(semieuleriano)? NAO", out)
        self.aprovado()

    def test_17b_casa_e_ciclo(self):
        """'Casinha' (2 impares) tem percurso aberto; C5 tem circuito euleriano."""
        casa = grafo_de([(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 0, 1), (2, 4, 1), (3, 4, 1), (0, 2, 1)])
        out, _ = self.rodar(17, casa, [], "semieuleriano SIM; percurso com as 7 arestas")
        self.assertIn("(semieuleriano)? SIM", out)
        perc = alg.analise_euleriana(casa)["percurso"]
        usadas = {frozenset((perc[i], perc[i + 1])) for i in range(len(perc) - 1)}
        self.assertEqual(len(perc) - 1, 7)
        self.assertEqual(usadas, {frozenset((u, v)) for u, v, _ in casa.lista_arestas()})
        out2, _ = self.rodar(17, ciclo(5), [], "euleriano SIM")
        self.assertIn("euleriano (circuito euleriano)? SIM", out2)
        self.aprovado()


class T18Hamiltoniano(TesteMenu):
    def test_18a_base_ciclo_encontrado(self):
        """Base: ciclo hamiltoniano encontrado e verificado (todas as cidades)."""
        g = base()
        out, _ = self.rodar(18, g, ["n"], f"SIM, ciclo verificado com {N_ARQ} cidades")
        self.assertIn("Possui ciclo hamiltoniano? SIM", out)
        r = alg.analise_hamiltoniana(g)
        self.assertTrue(alg.caminho_hamiltoniano_valido(g, r["ciclo"], ciclo=True))
        self.aprovado()

    def test_18b_petersen(self):
        """Petersen: busca exaustiva PROVA que nao ha ciclo; ha caminho."""
        out, _ = self.rodar(18, petersen(), ["n"], "ciclo NAO; caminho SIM")
        self.assertIn("Possui ciclo hamiltoniano? NAO", out)
        self.assertIn("Possui caminho hamiltoniano? SIM", out)
        self.aprovado()

    def test_18c_estrela(self):
        """Estrela K1,3: articulacao impede ciclo e caminho hamiltonianos."""
        out, _ = self.rodar(18, estrela(3), [], "condicoes necessarias violadas; NAO; NAO")
        self.assertIn("Condicao necessaria violada", out)
        self.assertIn("Possui ciclo hamiltoniano? NAO", out)
        self.assertIn("Possui caminho hamiltoniano? NAO", out)
        self.aprovado()


class T19Articulacoes(TesteMenu):
    def test_19a_base_biconexa(self):
        """Base: nenhuma articulacao e nenhuma ponte (malha 2-conexa)."""
        out, _ = self.rodar(19, base(), [], "0 articulacoes; 0 pontes; biconexa")
        self.assertIn("Pontos de articulacao (cidades criticas): 0", out)
        self.assertIn("Pontes (ligacoes criticas): 0", out)
        self.assertIn("2-conexa", out)
        self.aprovado()

    def test_19b_dois_triangulos(self):
        """Dois triangulos ligados por uma aresta: 2 articulacoes e 1 ponte."""
        g = grafo_de([(0, 1, 1), (1, 2, 1), (2, 0, 1), (3, 4, 1), (4, 5, 1), (5, 3, 1), (2, 3, 7)])
        out, _ = self.rodar(19, g, [], "articulacoes V2 e V3; ponte V2 - V3")
        self.assertEqual(alg.articulacoes_e_pontes(g), ([2, 3], [(2, 3)]))
        self.assertIn("V2 - V3 (7.0 km)", out)
        self.aprovado()

    def test_19c_remocao_confirma(self):
        """Conferencia por forca bruta: nenhuma remocao de cidade desconecta a base."""
        g = base()
        out, _ = self.rodar(19, g, [], "0 articulacoes (conferido removendo cada cidade)")
        self.assertTrue(all(alg.componentes_sem_vertice(g, v) == 1 for v in g.adjacencia))
        self.aprovado()


class T20Planaridade(TesteMenu):
    def test_20a_base_nao_planar(self):
        """Base: contem K5 (Kuratowski) e e confrontada com m <= 3n - 6 -> nao planar."""
        limite = 3 * N_ARQ - 6
        viola = M_ARQ > limite
        out, _ = self.rodar(20, base(), [],
                            f"m = {M_ARQ} vs 3n-6 = {limite} ({'VIOLADA' if viola else 'respeitada'}); "
                            "contem K5; NAO planar")
        self.assertIn(f"m <= 3n - 6 = {limite}; aqui m = {M_ARQ} -> "
                      f"{'VIOLADA' if viola else 'respeitada'}", out)
        self.assertIn("Contem K5 (Kuratowski)? SIM", out)
        self.assertIn("planar? NAO (provado)", out)
        self.aprovado()

    def test_20b_k5_e_k4(self):
        """K5 nao e planar; K4 respeita as condicoes (inconclusivo)."""
        out, _ = self.rodar(20, completo(5), [], "K5: NAO planar")
        self.assertIn("planar? NAO (provado)", out)
        out2, _ = self.rodar(20, completo(4), [], "K4: INCONCLUSIVO")
        self.assertIn("INCONCLUSIVO", out2)
        self.aprovado()


class T21Excentricidade(TesteMenu):
    def test_21a_base_confere_floyd(self):
        """Base: raio, diametro e centro iguais aos obtidos por Floyd-Warshall."""
        g = base()
        idx, d = fw_base()
        ecc = {v: max(d[idx[v]]) for v in g.adjacencia}
        raio, diam = min(ecc.values()), max(ecc.values())
        centro = min(ecc, key=ecc.get)
        out, _ = self.rodar(21, g, ["Campinas"], f"raio {raio:.1f}, diametro {diam:.1f}, centro {g.nome(centro)}")
        self.assertIn(f"Raio: {raio:.1f} km | Diametro: {diam:.1f} km", out)
        self.assertIn(g.nome(centro), out.split("Centro")[1].splitlines()[0])
        self.assertIn("Excentricidade de Campinas", out)
        self.aprovado()

    def test_21b_caminho_p5(self):
        """Caminho P5 (pesos 1): raio 2, diametro 4, centro = vertice do meio."""
        g = grafo_de([(i, i + 1, 1.0) for i in range(4)])
        out, _ = self.rodar(21, g, [""], "raio 2.0; diametro 4.0; centro V2")
        self.assertIn("Raio: 2.0 km | Diametro: 4.0 km", out)
        self.assertIn("Centro (menor excentricidade): V2", out)
        self.aprovado()


# =========================================================================== #
# Consistencia e reprodutibilidade da base de dados
# =========================================================================== #
class T00Base(unittest.TestCase):
    def test_00a_arestas_reproduziveis_k5(self):
        """Todas as arestas do grafo.txt sao exatamente as obtidas aplicando o
        criterio K = 5 vizinhos mais proximos as coordenadas de cidades.csv."""
        try:
            from coletar_dados import K_VIZINHOS, haversine_km
        except ImportError:
            self.skipTest("biblioteca 'requests' nao instalada")
        with open(ARQ_CIDADES, encoding="utf-8") as f:
            cid = [(int(r["id"]), r["nome"], float(r["lat"]), float(r["lon"]))
                   for r in csv.DictReader(f)]
        esperadas = set()
        for i, _, la, lo in cid:
            dists = sorted((haversine_km(la, lo, lb, lob), j)
                           for j, _, lb, lob in cid if j != i)
            esperadas |= {(min(i, j), max(i, j)) for _, j in dists[:K_VIZINHOS]}
        self.assertEqual(esperadas, {(u, v) for u, v, _ in BASE.lista_arestas()})
        self.assertTrue(all(BASE.nome(i) == nome for i, nome, _, _ in cid))

    def test_00b_conexidade_garantida_na_coleta(self):
        """K vizinhos NAO garante conexidade: dois grupos distantes com K=2
        ficam desconexos e garantir_conexidade acrescenta a ligacao que falta."""
        try:
            from coletar_dados import garantir_conexidade
        except ImportError:
            self.skipTest("biblioteca 'requests' nao instalada")
        cidades = [{"nome": f"C{i}", "lat": -23.0 + 0.01 * i, "lon": -46.0} for i in range(3)]
        cidades += [{"nome": f"D{i}", "lat": -21.0 + 0.01 * i, "lon": -48.0} for i in range(3)]
        candidatas = {(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5)}  # K=2 em cada grupo
        extras = garantir_conexidade(cidades, candidatas)
        self.assertEqual(extras, [(2, 3)])                 # par mais proximo entre grupos
        g = grafo_de([(u, v, 1.0) for u, v in candidatas])
        self.assertTrue(g.eh_conexo())


def tearDownModule():
    """Grava o log de evidencias (entrada, saida e veredito de cada teste)."""
    with open(ARQ_LOG, "w", encoding="utf-8") as f:
        f.write("GrafoRotas - Resultados dos testes das opcoes do menu\n")
        f.write("Gerado por testes.py (cada teste executa a opcao com entradas simuladas)\n")
        aprovados = sum(e["veredito"] == "APROVADO" for e in REGISTRO)
        f.write(f"Execucoes registradas: {len(REGISTRO)} | aprovadas: {aprovados}\n")
        for e in sorted(REGISTRO, key=lambda e: (e["opcao"], e["id"])):
            f.write("\n" + "=" * 78 + "\n")
            f.write(f"Opcao {e['opcao']:>2} | {e['id']} | {e['veredito']}\n")
            f.write(f"Descricao: {e['descricao']}\n")
            f.write(f"Entradas: {e['entradas']}\n")
            f.write(f"Esperado: {e['esperado']}\n")
            f.write("-" * 78 + "\n")
            f.write(e["saida"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
