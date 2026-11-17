# =============================================================================
# GrafoRotas - Algoritmos da Parte 3 aplicados a classe Grafo:
#   * Solucao do problema central: caminho minimo (Dijkstra) entre cidades;
#   * Analise complementar: arvore geradora minima (Prim);
#   * Caracteristicas do grafo: sequencia/distribuicao de graus, coloracao
#     (Welsh-Powell + limite inferior por clique maxima), grafo/percurso
#     euleriano (Hierholzer), grafo/ciclo hamiltoniano (condicoes de Dirac e
#     Ore, condicoes necessarias e busca com retrocesso), pontos de
#     articulacao e pontes (Tarjan) e excentricidade/raio/diametro/centro.
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
#   2026-10-18 | Guilherme Haddad Borro | Criacao do modulo (Parte 3) com
#                Dijkstra, Prim, graus, coloracao, euleriano, hamiltoniano,
#                articulacoes/pontes e excentricidade.
#
# Todas as funcoes recebem um objeto Grafo (grafo.py) e NAO o modificam.
# =============================================================================

import heapq
import random
import sys
import time
from collections import Counter
from statistics import mean, median, pstdev

INFINITO = float("inf")

# A busca hamiltoniana e a DFS de Tarjan sao recursivas; a profundidade
# maxima e o numero de vertices (215 na base real), acima do limite padrao
# de algumas instalacoes quando ha muitos quadros intermediarios.
sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))


# =========================================================================== #
# 1) SOLUCAO DO PROBLEMA: CAMINHO MINIMO (DIJKSTRA)
# =========================================================================== #
def dijkstra(g, origem):
    """Algoritmo de Dijkstra (1959) com fila de prioridade (heap binario).

    Calcula a menor distancia de 'origem' a todos os vertices. Complexidade
    O((V + E) log V). Exige pesos nao negativos (garantido pela classe Grafo,
    que rejeita pesos <= 0).

    Retorna (dist, pred):
      dist[v] = menor distancia origem->v (INFINITO se inalcancavel);
      pred[v] = vertice anterior a v no caminho minimo (None para a origem).
    """
    if origem not in g.adjacencia:
        raise KeyError(f"vertice de origem {origem} nao existe")
    dist = {v: INFINITO for v in g.adjacencia}
    pred = {v: None for v in g.adjacencia}
    dist[origem] = 0.0
    heap = [(0.0, origem)]
    fechados = set()                 # vertices com distancia definitiva
    while heap:
        d, u = heapq.heappop(heap)
        if u in fechados:            # entrada antiga (desatualizada) no heap
            continue
        fechados.add(u)
        for w, peso in g.adjacencia[u].items():
            nova = d + peso          # relaxamento da aresta (u, w)
            if nova < dist[w]:
                dist[w] = nova
                pred[w] = u
                heapq.heappush(heap, (nova, w))
    return dist, pred


def reconstruir_caminho(pred, origem, destino):
    """Reconstroi a sequencia de vertices origem -> destino a partir de pred."""
    caminho = []
    atual = destino
    while atual is not None:
        caminho.append(atual)
        if atual == origem:
            return caminho[::-1]
        atual = pred[atual]
    return []                        # destino inalcancavel a partir da origem


def caminho_minimo(g, origem, destino):
    """Menor caminho entre duas cidades.

    Retorna (distancia_total, [origem, ..., destino]); se nao houver caminho,
    retorna (INFINITO, []).
    """
    if destino not in g.adjacencia:
        raise KeyError(f"vertice de destino {destino} nao existe")
    dist, pred = dijkstra(g, origem)
    if dist[destino] == INFINITO:
        return INFINITO, []
    return dist[destino], reconstruir_caminho(pred, origem, destino)


# =========================================================================== #
# 2) ANALISE COMPLEMENTAR: ARVORE GERADORA MINIMA (PRIM)
# =========================================================================== #
def arvore_geradora_minima(g):
    """Algoritmo de Prim (1957) com heap. Complexidade O(E log V).

    Se o grafo for desconexo, devolve uma floresta geradora minima (uma arvore
    por componente). Retorna (arestas, custo_total), com arestas no formato
    (u, v, peso) na ordem em que foram incorporadas.
    """
    visitados = set()
    arestas = []
    for raiz in sorted(g.adjacencia):
        if raiz in visitados:
            continue
        visitados.add(raiz)
        heap = [(p, raiz, w) for w, p in g.adjacencia[raiz].items()]
        heapq.heapify(heap)
        while heap:
            peso, u, w = heapq.heappop(heap)
            if w in visitados:
                continue
            visitados.add(w)
            arestas.append((u, w, peso))
            for x, px in g.adjacencia[w].items():
                if x not in visitados:
                    heapq.heappush(heap, (px, w, x))
    return arestas, sum(p for _, _, p in arestas)


# =========================================================================== #
# 3) CARACTERISTICA: GRAU DOS VERTICES
# =========================================================================== #
def analise_graus(g):
    """Sequencia de graus, distribuicao e estatisticas descritivas.

    Tambem confere o Lema do Aperto de Maos: soma dos graus = 2|E|.
    """
    graus = {v: g.grau(v) for v in g.adjacencia}
    if not graus:
        return None
    valores = list(graus.values())
    maximo = max(valores)
    minimo = min(valores)
    return {
        "graus": graus,
        "sequencia": sorted(valores, reverse=True),
        "distribuicao": dict(sorted(Counter(valores).items())),
        "minimo": minimo,
        "maximo": maximo,
        "medio": mean(valores),
        "mediana": median(valores),
        "desvio": pstdev(valores),
        "soma": sum(valores),
        "arestas": g.numero_arestas(),
        "vertices_grau_maximo": sorted(v for v in graus if graus[v] == maximo),
        "vertices_grau_minimo": sorted(v for v in graus if graus[v] == minimo),
        "isolados": sorted(v for v in graus if graus[v] == 0),
    }


# =========================================================================== #
# 4) CARACTERISTICA: COLORACAO DE VERTICES
# =========================================================================== #
def coloracao_welsh_powell(g):
    """Coloracao gulosa de Welsh e Powell (1967).

    Ordena os vertices por grau decrescente; para cada cor, percorre a lista
    e pinta todo vertice ainda sem cor que nao tenha vizinho com essa cor.
    O numero de cores obtido e um LIMITE SUPERIOR do numero cromatico.
    Retorna (cor, numero_de_cores), com cor = {vertice: indice_da_cor}.
    """
    ordem = sorted(g.adjacencia, key=lambda v: (-g.grau(v), v))
    cor = {}
    cor_atual = 0
    while len(cor) < len(ordem):
        for v in ordem:
            if v in cor:
                continue
            if all(cor.get(w) != cor_atual for w in g.adjacencia[v]):
                cor[v] = cor_atual
        cor_atual += 1
    return cor, cor_atual


def coloracao_valida(g, cor):
    """True se nenhuma aresta liga dois vertices da mesma cor."""
    return all(v in cor for v in g.adjacencia) and all(
        cor[u] != cor[v] for u, v, _ in g.lista_arestas())


def clique_maxima(g):
    """Clique maxima pelo algoritmo de Bron-Kerbosch com pivotamento.

    O tamanho da clique maxima (omega) e um LIMITE INFERIOR do numero
    cromatico: omega(G) <= chi(G). Exponencial no pior caso, mas rapido em
    grafos esparsos como a malha rodoviaria (grau maximo 9).
    """
    melhor = []

    def expandir(r, p, x):
        nonlocal melhor
        if not p and not x:
            if len(r) > len(melhor):
                melhor = list(r)
            return
        if len(r) + len(p) <= len(melhor):      # poda: nao supera a melhor
            return
        pivo = max(p | x, key=lambda u: len(p & set(g.adjacencia[u])))
        for v in list(p - set(g.adjacencia[pivo])):
            viz = set(g.adjacencia[v])
            expandir(r + [v], p & viz, x & viz)
            p = p - {v}
            x = x | {v}

    expandir([], set(g.adjacencia), set())
    return sorted(melhor)


def analise_coloracao(g):
    """Combina Welsh-Powell (limite superior) e clique maxima (limite inferior).

    Se os limites coincidirem, o numero cromatico fica determinado exatamente.
    Um grafo e bipartido se, e somente se, chi(G) <= 2.
    """
    cor, k = coloracao_welsh_powell(g)
    clique = clique_maxima(g)
    classes = {}
    for v, c in cor.items():
        classes.setdefault(c, []).append(v)
    return {
        "cor": cor,
        "num_cores": k,
        "valida": coloracao_valida(g, cor),
        "classes": {c: sorted(vs) for c, vs in sorted(classes.items())},
        "clique": clique,
        "limite_inferior": len(clique),
        "exato": len(clique) == k,
        "bipartido": k <= 2,
    }


# =========================================================================== #
# 5) CARACTERISTICA: GRAFO EULERIANO / PERCURSO EULERIANO
# =========================================================================== #
def _conexo_nas_arestas(g):
    """True se todas as arestas estao numa mesma componente conexa."""
    com_arestas = [v for v in g.adjacencia if g.grau(v) > 0]
    if not com_arestas:
        return True
    visitados = set()
    g._dfs(com_arestas[0], visitados)
    return all(v in visitados for v in com_arestas)


def hierholzer(g, inicio):
    """Algoritmo de Hierholzer (1873): constroi o percurso euleriano.

    Pressupoe que o percurso existe e comeca em 'inicio'. O(E).
    """
    restante = {v: set(viz) for v, viz in g.adjacencia.items()}
    pilha = [inicio]
    percurso = []
    while pilha:
        u = pilha[-1]
        if restante[u]:
            w = restante[u].pop()
            restante[w].discard(u)       # aresta nao orientada: remove os 2 lados
            pilha.append(w)
        else:
            percurso.append(pilha.pop())
    return percurso[::-1]


def analise_euleriana(g):
    """Teorema de Euler (1736): um grafo conexo (nas arestas) e
      - euleriano (tem circuito euleriano) se todos os graus sao pares;
      - semieuleriano (tem percurso/trilha euleriana aberta) se tem
        exatamente 2 vertices de grau impar.
    Quando existe, o percurso e construido por Hierholzer.
    """
    impares = sorted(v for v in g.adjacencia if g.grau(v) % 2 == 1)
    conexo = _conexo_nas_arestas(g)
    tem_arestas = g.numero_arestas() > 0
    euleriano = conexo and tem_arestas and not impares
    semieuleriano = conexo and len(impares) == 2
    percurso = None
    if euleriano:
        inicio = next(v for v in sorted(g.adjacencia) if g.grau(v) > 0)
        percurso = hierholzer(g, inicio)
    elif semieuleriano:
        percurso = hierholzer(g, impares[0])
    return {
        "conexo": conexo,
        "impares": impares,
        "euleriano": euleriano,
        "semieuleriano": semieuleriano,
        "percurso": percurso,
        # para tornar o grafo euleriano seria preciso "duplicar" ao menos
        # (impares / 2) caminhos (ideia do Problema do Carteiro Chines)
        "pares_a_corrigir": len(impares) // 2,
    }


# =========================================================================== #
# 6) CARACTERISTICA: PONTOS DE ARTICULACAO E PONTES (TARJAN)
# =========================================================================== #
def articulacoes_e_pontes(g):
    """Algoritmo de Tarjan (1972/1974) baseado em DFS, O(V + E).

    Ponto de articulacao: cidade cuja remocao desconecta a malha.
    Ponte: ligacao cuja remocao desconecta a malha.
    Retorna (lista_de_articulacoes, lista_de_pontes (u, v)).
    """
    descoberta = {}     # ordem de descoberta de cada vertice na DFS
    menor = {}          # menor ordem alcancavel pela subarvore (low-link)
    articulacoes = set()
    pontes = []
    tempo = [0]

    def dfs(u, pai):
        descoberta[u] = menor[u] = tempo[0]
        tempo[0] += 1
        filhos = 0
        for w in g.adjacencia[u]:
            if w not in descoberta:
                filhos += 1
                dfs(w, u)
                menor[u] = min(menor[u], menor[w])
                if pai is not None and menor[w] >= descoberta[u]:
                    articulacoes.add(u)
                if menor[w] > descoberta[u]:
                    pontes.append((min(u, w), max(u, w)))
            elif w != pai:
                menor[u] = min(menor[u], descoberta[w])
        if pai is None and filhos > 1:          # raiz com 2+ filhos na DFS
            articulacoes.add(u)

    for v in sorted(g.adjacencia):
        if v not in descoberta:
            dfs(v, None)
    return sorted(articulacoes), sorted(pontes)


def componentes_sem_vertice(g, vertice):
    """Numero de componentes conexas apos remover 'vertice' (sem alterar g)."""
    h = g.copia()
    h.remover_vertice(vertice)
    return len(h.componentes_conexas())


# =========================================================================== #
# 7) CARACTERISTICA: GRAFO HAMILTONIANO / CICLO HAMILTONIANO
# =========================================================================== #
class _TempoEsgotado(Exception):
    """Interrompe a busca com retrocesso quando o limite de tempo acaba."""


def caminho_hamiltoniano_valido(g, seq, ciclo):
    """Confere se 'seq' visita cada vertice uma unica vez seguindo arestas."""
    if len(seq) != g.numero_vertices() or set(seq) != set(g.adjacencia):
        return False
    if any(seq[i + 1] not in g.adjacencia[seq[i]] for i in range(len(seq) - 1)):
        return False
    return (not ciclo) or (len(seq) >= 3 and seq[0] in g.adjacencia[seq[-1]])


def heuristica_posa(g, ciclo, limite_segundos, semente=2026):
    """Heuristica de rotacao-extensao de Posa (1976) para ciclo/caminho
    hamiltoniano.

    Mantem um caminho simples e tenta estende-lo pela ponta; quando a ponta
    nao tem vizinho livre, escolhe um vizinho w da ponta que ja esta no
    caminho e inverte o trecho apos w (rotacao), criando uma nova ponta.
    Reinicia com nova partida quando estagna. Nao prova inexistencia, mas
    qualquer sequencia devolvida e conferida por caminho_hamiltoniano_valido.
    A semente fixa torna o resultado reprodutivel.
    """
    rng = random.Random(semente)
    n = g.numero_vertices()
    vertices = sorted(g.adjacencia)
    prazo = time.perf_counter() + limite_segundos
    while time.perf_counter() < prazo:
        caminho = [rng.choice(vertices)]
        posicao = {caminho[0]: 0}
        sem_progresso = 0
        melhor = 1
        while sem_progresso < 20 * n and time.perf_counter() < prazo:
            ponta = caminho[-1]
            livres = [w for w in g.adjacencia[ponta] if w not in posicao]
            if livres:                                   # extensao
                # prefere o vizinho com menos vizinhos livres (Warnsdorff)
                menor = min(sum(1 for x in g.adjacencia[w] if x not in posicao)
                            for w in livres)
                w = rng.choice([w for w in livres if sum(
                    1 for x in g.adjacencia[w] if x not in posicao) == menor])
                posicao[w] = len(caminho)
                caminho.append(w)
                if len(caminho) > melhor:
                    melhor, sem_progresso = len(caminho), 0
                continue
            if len(caminho) == n and (not ciclo or caminho[0] in g.adjacencia[ponta]):
                return caminho
            sem_progresso += 1
            if rng.random() < 0.1:                       # troca a ponta ativa
                caminho.reverse()
                posicao = {v: i for i, v in enumerate(caminho)}
                continue
            opcoes = [w for w in g.adjacencia[ponta]
                      if w in posicao and posicao[w] < len(caminho) - 2]
            if not opcoes:
                caminho.reverse()
                posicao = {v: i for i, v in enumerate(caminho)}
                continue
            i = posicao[rng.choice(opcoes)]              # rotacao de Posa
            caminho[i + 1:] = caminho[:i:-1]
            for j in range(i + 1, len(caminho)):
                posicao[caminho[j]] = j
    return None


def busca_retrocesso_hamiltoniana(g, ciclo, limite_segundos):
    """Busca exaustiva com retrocesso (backtracking) e podas.

    Podas: (a) todo vertice nao visitado precisa de vizinhos disponiveis
    suficientes (2 para ciclo; no maximo um vertice "sem saida" para
    caminho); (b) os vertices nao visitados devem continuar alcancaveis a
    partir da ponta. Usa a ordem de Warnsdorff. Se terminar dentro do prazo
    sem encontrar, PROVA que nao existe. Retorna (sequencia | None, status).
    """
    n = g.numero_vertices()
    prazo = time.perf_counter() + limite_segundos
    ordem = sorted(g.adjacencia, key=lambda v: (g.grau(v), v))
    partidas = ordem[:1] if ciclo else ordem   # para ciclo, 1 partida basta

    for inicio in partidas:
        caminho = [inicio]
        visitados = {inicio}

        def livres(v):
            return sum(1 for x in g.adjacencia[v] if x not in visitados)

        def viavel(ponta):
            restantes = [v for v in g.adjacencia if v not in visitados]
            sem_saida = 0
            for v in restantes:
                disp = livres(v) + (ponta in g.adjacencia[v])
                if ciclo:
                    disp += inicio in g.adjacencia[v]
                    if disp < 2:
                        return False
                elif disp < 1:
                    return False
                elif disp == 1:
                    sem_saida += 1
            if sem_saida > 1:
                return False
            # todos os restantes alcancaveis a partir da ponta?
            alcancados = set()
            pilha = [w for w in g.adjacencia[ponta] if w not in visitados]
            while pilha:
                v = pilha.pop()
                if v in alcancados:
                    continue
                alcancados.add(v)
                pilha.extend(w for w in g.adjacencia[v]
                             if w not in visitados and w not in alcancados)
            return len(alcancados) == len(restantes)

        def estender(u):
            if time.perf_counter() > prazo:
                raise _TempoEsgotado
            if len(caminho) == n:
                return (not ciclo) or (inicio in g.adjacencia[u])
            if not viavel(u):
                return False
            candidatos = [w for w in g.adjacencia[u] if w not in visitados]
            candidatos.sort(key=lambda w: (livres(w), w))
            for w in candidatos:
                visitados.add(w)
                caminho.append(w)
                if estender(w):
                    return True
                visitados.discard(w)
                caminho.pop()
            return False

        try:
            if estender(inicio):
                return caminho, "encontrado"
        except _TempoEsgotado:
            return None, "tempo esgotado"
    return None, "inexistente"


def buscar_hamiltoniano(g, ciclo=True, limite_segundos=5.0):
    """Procura ciclo (ciclo=True) ou caminho hamiltoniano.

    O problema e NP-completo (Karp, 1972), por isso combina: (1) heuristica
    de Posa durante metade do tempo, rapida em grafos com grau minimo alto;
    (2) busca exaustiva com retrocesso no tempo restante, capaz de provar a
    inexistencia em grafos pequenos (com ate 30 vertices a busca exaustiva
    roda sozinha, pois termina rapido). Retorna (sequencia | None, status),
    com status em {"encontrado", "inexistente", "tempo esgotado"}.
    """
    n = g.numero_vertices()
    if n == 0 or (ciclo and n < 3):
        return None, "inexistente"
    if n == 1:
        return [next(iter(g.adjacencia))], "encontrado"
    if n <= 30:
        return busca_retrocesso_hamiltoniana(g, ciclo, limite_segundos)
    seq = heuristica_posa(g, ciclo, limite_segundos / 2)
    if seq and caminho_hamiltoniano_valido(g, seq, ciclo):
        return seq, "encontrado"
    seq, status = busca_retrocesso_hamiltoniana(g, ciclo, limite_segundos / 2)
    if seq and not caminho_hamiltoniano_valido(g, seq, ciclo):
        return None, "tempo esgotado"          # salvaguarda (nao deve ocorrer)
    return seq, status


def analise_hamiltoniana(g, limite_segundos=5.0):
    """Investiga se o grafo e hamiltoniano combinando:

      * condicoes SUFICIENTES: Dirac (1952) - grau minimo >= n/2;
        Ore (1960) - grau(u) + grau(v) >= n para todo par nao adjacente;
      * condicoes NECESSARIAS para ciclo: grafo conexo, grau minimo >= 2 e
        ausencia de pontos de articulacao (grafo 2-conexo);
      * condicao NECESSARIA para caminho: nenhuma remocao de vertice gera
        mais de 2 componentes;
      * busca com retrocesso (com limite de tempo) para exibir um certificado.
    """
    n = g.numero_vertices()
    graus = [g.grau(v) for v in g.adjacencia] or [0]
    conexo = g.eh_conexo()
    articulacoes, _ = articulacoes_e_pontes(g)
    dirac = n >= 3 and min(graus) >= n / 2
    vertices = sorted(g.adjacencia)
    ore = n >= 3 and all(
        g.grau(u) + g.grau(v) >= n
        for i, u in enumerate(vertices) for v in vertices[i + 1:]
        if v not in g.adjacencia[u])

    # --- ciclo hamiltoniano ---
    motivos_ciclo = []
    if n < 3:
        motivos_ciclo.append("menos de 3 vertices")
    if not conexo:
        motivos_ciclo.append("grafo desconexo")
    if min(graus) < 2:
        motivos_ciclo.append("existe vertice com grau menor que 2")
    if articulacoes:
        motivos_ciclo.append(f"existem {len(articulacoes)} pontos de articulacao")
    if motivos_ciclo:
        ciclo, status_ciclo = None, "inexistente"
    else:
        ciclo, status_ciclo = buscar_hamiltoniano(g, True, limite_segundos)

    # --- caminho hamiltoniano ---
    motivos_caminho = []
    if not conexo:
        motivos_caminho.append("grafo desconexo")
    else:
        criticos = [v for v in articulacoes if componentes_sem_vertice(g, v) > 2]
        if criticos:
            motivos_caminho.append(
                f"a remocao de {g.nome(criticos[0])} gera mais de 2 componentes")
    if ciclo:
        caminho, status_caminho = ciclo, "encontrado"   # todo ciclo contem caminho
    elif motivos_caminho:
        caminho, status_caminho = None, "inexistente"
    else:
        caminho, status_caminho = buscar_hamiltoniano(g, False, limite_segundos)

    return {
        "n": n,
        "grau_minimo": min(graus),
        "dirac": dirac,
        "ore": ore,
        "articulacoes": articulacoes,
        "motivos_sem_ciclo": motivos_ciclo,
        "ciclo": ciclo,
        "status_ciclo": status_ciclo,
        "motivos_sem_caminho": motivos_caminho,
        "caminho": caminho,
        "status_caminho": status_caminho,
    }


# =========================================================================== #
# 8) CARACTERISTICA: PLANARIDADE (CONDICOES NECESSARIAS)
# =========================================================================== #
def analise_planaridade(g):
    """Verifica duas condicoes que, se violadas, provam que o grafo NAO e
    planar (nao pode ser desenhado no plano sem cruzamento de arestas):

      * Corolario da formula de Euler: grafo planar simples com n >= 3
        vertices tem no maximo 3n - 6 arestas;
      * Teorema de Kuratowski (1930): grafo planar nao contem subdivisao de
        K5 ou K3,3; em particular, nao contem uma clique K5.

    Se nenhuma condicao for violada, o resultado e inconclusivo (seria
    necessario um teste completo, como o de Hopcroft-Tarjan).
    """
    n = g.numero_vertices()
    m = g.numero_arestas()
    limite = 3 * n - 6 if n >= 3 else None
    viola_euler = limite is not None and m > limite
    clique = clique_maxima(g)
    contem_k5 = len(clique) >= 5
    return {
        "n": n,
        "m": m,
        "limite_arestas": limite,
        "viola_euler": viola_euler,
        "clique": clique,
        "contem_k5": contem_k5,
        "planar": False if (viola_euler or contem_k5) else None,  # None = inconclusivo
    }


# =========================================================================== #
# 9) CARACTERISTICA: EXCENTRICIDADE, RAIO, DIAMETRO E CENTRO
# =========================================================================== #
def excentricidades(g):
    """Executa Dijkstra a partir de cada vertice (O(V (V+E) log V)).

    excentricidade(v) = maior distancia minima de v a qualquer outro vertice.
    raio = menor excentricidade; diametro = maior excentricidade;
    centro = vertices de excentricidade minima (melhor localizacao para um
    ponto de apoio que precise atender toda a regiao no pior caso).
    """
    if g.numero_vertices() == 0:
        return None
    ecc = {}
    mais_distante = {}
    soma_distancias = {}
    for v in g.adjacencia:
        dist, _ = dijkstra(g, v)
        alvo = max(dist, key=lambda w: (dist[w], -w))
        ecc[v] = dist[alvo]
        mais_distante[v] = alvo
        soma_distancias[v] = sum(dist.values())
    raio = min(ecc.values())
    diametro = max(ecc.values())
    centro = sorted(v for v in ecc if ecc[v] == raio)
    periferia = sorted(v for v in ecc if ecc[v] == diametro)
    # centro de massa (mediana do grafo): menor soma das distancias
    mediana = min(soma_distancias, key=lambda v: (soma_distancias[v], v))
    return {
        "ecc": ecc,
        "mais_distante": mais_distante,
        "raio": raio,
        "diametro": diametro,
        "centro": centro,
        "periferia": periferia,
        "mediana": mediana,
        "distancia_media_mediana": soma_distancias[mediana] / max(1, len(ecc) - 1),
    }
