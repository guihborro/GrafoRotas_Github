# =============================================================================
# GrafoRotas - Menu interativo da aplicacao: infraestrutura do grafo (Parte 2),
# solucao do problema central - caminho minimo entre municipios (Dijkstra) - e
# investigacao das caracteristicas do grafo (Parte 3).
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
#   2026-09-02 | Guilherme Haddad Borro | Versao inicial (Parte 2): menu com
#                exibicao, insercao/remocao, grau, conexidade, grafo reduzido,
#                estatisticas e gravacao.
#   2026-10-18 | Guilherme Haddad Borro | Parte 3: titulo da aplicacao; opcao
#                "mostrar conteudo do arquivo"; vertices informados por nome ou
#                id; validacao de pesos; opcoes de Dijkstra, Prim, graus,
#                coloracao, euleriano, hamiltoniano, articulacoes/pontes,
#                planaridade e excentricidade; tratamento de arquivo invalido.
#
# Uso:  python main.py            (le o grafo.txt da pasta atual)
# =============================================================================

import os

import algoritmos as alg
from grafo import ErroFormatoArquivo, Grafo

ARQUIVO = "grafo.txt"
TITULO = "GrafoRotas - Rotas de Menor Distancia entre Municipios Paulistas"
LINHA = "=" * 70
SUBLINHA = "-" * 70


# --------------------------------------------------------------------------- #
# Entrada de dados
# --------------------------------------------------------------------------- #
def ler(msg=""):
    """Le uma linha do usuario. Em fim de entrada (EOF), encerra o programa.

    Remove o BOM (U+FEFF) que alguns terminais (ex.: PowerShell) inserem no
    inicio de uma entrada redirecionada, o que invalidaria a primeira opcao.
    """
    try:
        return input(msg).lstrip("﻿")
    except EOFError:
        print("\nEntrada encerrada. Saindo.")
        raise SystemExit(0)


def ler_int(msg):
    """Le um inteiro; retorna None se o valor for invalido."""
    valor = ler(msg).strip()
    try:
        return int(valor)
    except ValueError:
        print("  Valor invalido: informe um numero inteiro.")
        return None


def ler_float(msg):
    """Le um numero real (aceita virgula decimal); None se invalido."""
    valor = ler(msg).strip().replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        print("  Valor invalido: informe um numero.")
        return None


def ler_vertice(g, msg):
    """Le uma cidade pelo id ou pelo nome (sem acento/caixa). None se invalida."""
    vid, erro = g.buscar_vertice(ler(msg))
    if erro:
        print(f"  {erro[0].upper()}{erro[1:]}.")
    return vid


def ler_sim_nao(msg):
    """True se o usuario responder 's' (padrao: nao)."""
    return ler(msg).strip().lower() in ("s", "sim")


def km(valor):
    """Formata uma distancia em quilometros com uma casa decimal."""
    return f"{valor:.1f} km"


def rotulo(g, v):
    return f"[{v}] {g.nome(v)}"


# --------------------------------------------------------------------------- #
# Carga do arquivo e menu
# --------------------------------------------------------------------------- #
def carregar(caminho=ARQUIVO):
    """Carrega o grafo do arquivo; devolve grafo vazio se ausente ou invalido."""
    if not os.path.exists(caminho):
        print(f"Arquivo '{caminho}' nao encontrado. Iniciando com grafo vazio.")
        print("(Dica: rode 'python coletar_dados.py' para gerar a base real.)")
        return Grafo()
    try:
        g = Grafo().ler_arquivo(caminho)
    except ErroFormatoArquivo as erro:
        print(f"Arquivo '{caminho}' invalido ({erro}). Iniciando com grafo vazio.")
        return Grafo()
    print(f"Grafo carregado de '{caminho}'.")
    return g


def cabecalho(g):
    print("\n" + LINHA)
    print(TITULO.center(70))
    print(f"Tipo {g.tipo} ({g.descricao_tipo()}) | "
          f"{g.numero_vertices()} vertices | {g.numero_arestas()} arestas".center(70))
    print(LINHA)


def menu():
    print(" Infraestrutura do grafo")
    print("  1. Exibir grafo (lista de adjacencia)")
    print("  2. Mostrar conteudo do arquivo (grafo.txt)")
    print("  3. Inserir vertice              4. Remover vertice")
    print("  5. Inserir aresta               6. Remover aresta")
    print("  7. Consultar grau de um vertice")
    print("  8. Determinar conexidade        9. Construir grafo reduzido")
    print(" 10. Gravar grafo em arquivo     11. Recarregar grafo de arquivo")
    print(" Solucao do problema: rotas de menor distancia")
    print(" 12. Caminho minimo entre duas cidades (Dijkstra)")
    print(" 13. Distancias minimas a partir de uma cidade (Dijkstra)")
    print(" 14. Arvore geradora minima da malha (Prim)")
    print(" Caracteristicas do grafo")
    print(" 15. Grau dos vertices (sequencia e distribuicao)")
    print(" 16. Coloracao de vertices (Welsh-Powell)")
    print(" 17. Grafo euleriano / percurso euleriano")
    print(" 18. Grafo hamiltoniano / ciclo hamiltoniano")
    print(" 19. Pontos de articulacao e pontes (cidades/ligacoes criticas)")
    print(" 20. Planaridade")
    print(" 21. Excentricidade, raio, diametro e centro")
    print("  0. Sair")


def grafo_vazio(g):
    """Avisa e retorna True se nao houver vertices para analisar."""
    if g.numero_vertices() == 0:
        print("  Grafo vazio: carregue ou insira vertices primeiro.")
        return True
    return False


# --------------------------------------------------------------------------- #
# Opcoes 1 a 11 - infraestrutura (Parte 2, revisada)
# --------------------------------------------------------------------------- #
def op_exibir(g):
    entrada = ler("Quantos vertices exibir? (Enter = 10, 'tudo' = todos) ").strip().lower()
    if entrada == "tudo":
        print(g.exibir())
        return
    try:
        limite = int(entrada) if entrada else 10
    except ValueError:
        print("  Valor invalido; exibindo os 10 primeiros.")
        limite = 10
    print(g.exibir(limite=max(0, limite)))


def op_mostrar_arquivo(g):
    """Mostra o conteudo bruto (linha a linha) de um arquivo de grafo."""
    caminho = ler(f"Arquivo (Enter = {ARQUIVO}): ").strip() or ARQUIVO
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.read().splitlines()
    except OSError as erro:
        print(f"  Nao foi possivel abrir '{caminho}': {erro.strerror}.")
        return
    entrada = ler("Quantas linhas exibir? (Enter = todas) ").strip()
    limite = len(linhas)
    if entrada:
        try:
            limite = max(0, int(entrada))
        except ValueError:
            print("  Valor invalido; exibindo todas as linhas.")
    print(f"  Conteudo de '{caminho}' ({len(linhas)} linhas):")
    for numero, texto in enumerate(linhas[:limite], 1):
        print(f"  {numero:4d} | {texto}")
    if limite < len(linhas):
        print(f"  ... ({len(linhas) - limite} linhas omitidas)")


def op_inserir_vertice(g):
    vid = ler_int("ID do novo vertice: ")
    if vid is None:
        return
    nome = ler("Nome/rotulo da cidade: ").strip()
    if not nome:
        print("  Nome vazio: vertice nao inserido.")
    elif g.inserir_vertice(vid, nome):
        print(f"  Vertice [{vid}] '{nome}' inserido. "
              f"Total: {g.numero_vertices()} vertices.")
    else:
        print(f"  Vertice [{vid}] ja existe ({g.nome(vid)}).")


def op_remover_vertice(g):
    vid = ler_vertice(g, "Cidade a remover (id ou nome): ")
    if vid is None:
        return
    nome, grau = g.nome(vid), g.grau(vid)
    g.remover_vertice(vid)
    print(f"  Vertice [{vid}] {nome} removido (e suas {grau} arestas). "
          f"Total: {g.numero_vertices()} vertices, {g.numero_arestas()} arestas.")


def op_inserir_aresta(g):
    u = ler_vertice(g, "Cidade de origem (id ou nome): ")
    if u is None:
        return
    v = ler_vertice(g, "Cidade de destino (id ou nome): ")
    if v is None:
        return
    peso = ler_float("Peso (distancia em km): ")
    if peso is None:
        return
    existia = v in g.adjacencia[u]
    if g.inserir_aresta(u, v, peso):
        acao = "atualizada" if existia else "inserida"
        print(f"  Aresta {g.nome(u)} - {g.nome(v)} ({km(peso)}) {acao}. "
              f"Total: {g.numero_arestas()} arestas.")
    elif u == v:
        print("  Nao foi possivel inserir: laco (origem = destino) nao permitido.")
    else:
        print("  Nao foi possivel inserir: o peso deve ser positivo.")


def op_remover_aresta(g):
    u = ler_vertice(g, "Cidade de origem (id ou nome): ")
    if u is None:
        return
    v = ler_vertice(g, "Cidade de destino (id ou nome): ")
    if v is None:
        return
    if g.remover_aresta(u, v):
        print(f"  Aresta {g.nome(u)} - {g.nome(v)} removida. "
              f"Total: {g.numero_arestas()} arestas.")
    else:
        print(f"  Nao existe aresta entre {g.nome(u)} e {g.nome(v)}.")


def op_grau(g):
    vid = ler_vertice(g, "Cidade (id ou nome): ")
    if vid is None:
        return
    print(f"  Grau de {rotulo(g, vid)}: {g.grau(vid)}")
    for w, p in sorted(g.adjacencia[vid].items(), key=lambda item: item[1]):
        print(f"    - {g.nome(w)} ({km(p)})")


def op_conexidade(g):
    comps = g.componentes_conexas()
    print(f"  O grafo e conexo? {'SIM' if g.eh_conexo() else 'NAO'}")
    print(f"  Numero de componentes conexas: {len(comps)}")
    tamanhos = sorted((len(c) for c in comps), reverse=True)
    print(f"  Tamanho das componentes: {tamanhos}")
    for comp in sorted(comps, key=len)[:-1][:10]:          # componentes menores
        nomes = ", ".join(g.nome(v) for v in sorted(comp)[:5])
        print(f"    componente isolada com {len(comp)} cidade(s): {nomes}")


def op_reduzido(g):
    print(g.grafo_reduzido().exibir())


def op_gravar(g):
    destino = ler("Nome do arquivo (Enter = grafo_salvo.txt): ").strip() or "grafo_salvo.txt"
    try:
        g.gravar_arquivo(destino)
    except OSError as erro:
        print(f"  Nao foi possivel gravar '{destino}': {erro.strerror}.")
        return
    print(f"  Grafo gravado em '{destino}' "
          f"({g.numero_vertices()} vertices, {g.numero_arestas()} arestas).")


def op_recarregar(g):
    """Recarrega de um arquivo; mantem o grafo atual se o arquivo for invalido."""
    caminho = ler(f"Arquivo (Enter = {ARQUIVO}): ").strip() or ARQUIVO
    try:
        novo = Grafo().ler_arquivo(caminho)
    except OSError as erro:
        print(f"  Nao foi possivel abrir '{caminho}': {erro.strerror}. Grafo mantido.")
        return g
    except ErroFormatoArquivo as erro:
        print(f"  Arquivo invalido ({erro}). Grafo mantido.")
        return g
    print(f"  Grafo recarregado de '{caminho}': "
          f"{novo.numero_vertices()} vertices, {novo.numero_arestas()} arestas.")
    return novo


# --------------------------------------------------------------------------- #
# Opcoes 12 a 14 - solucao do problema (Parte 3)
# --------------------------------------------------------------------------- #
def op_caminho_minimo(g):
    """Problema central: rota de menor distancia entre duas cidades."""
    if grafo_vazio(g):
        return
    origem = ler_vertice(g, "Cidade de origem (id ou nome): ")
    if origem is None:
        return
    destino = ler_vertice(g, "Cidade de destino (id ou nome): ")
    if destino is None:
        return
    if origem == destino:
        print(f"  Origem e destino sao a mesma cidade ({g.nome(origem)}): distancia 0.0 km.")
        return
    total, caminho = alg.caminho_minimo(g, origem, destino)
    if not caminho:
        print(f"  Nao existe caminho entre {g.nome(origem)} e {g.nome(destino)} "
              "(cidades em componentes diferentes).")
        return
    print(f"  Rota de menor distancia: {g.nome(origem)} -> {g.nome(destino)}")
    print(f"  {'Passo':>5}  {'Cidade':<32}{'Trecho':>11}{'Acumulado':>12}")
    acumulado = 0.0
    for i, v in enumerate(caminho):
        trecho = g.adjacencia[caminho[i - 1]][v] if i else 0.0
        acumulado += trecho
        print(f"  {i:>5}  {g.nome(v):<32}{km(trecho):>11}{km(acumulado):>12}")
    print(f"  Distancia total: {km(total)} | trechos: {len(caminho) - 1} | "
          f"cidades intermediarias: {max(0, len(caminho) - 2)}")


def op_distancias_origem(g):
    """Arvore de caminhos minimos: distancias de uma cidade a todas as outras."""
    if grafo_vazio(g):
        return
    origem = ler_vertice(g, "Cidade de origem (id ou nome): ")
    if origem is None:
        return
    entrada = ler("Quantas cidades listar em cada extremo? (Enter = 5) ").strip()
    try:
        qtd = max(1, int(entrada)) if entrada else 5
    except ValueError:
        print("  Valor invalido; usando 5.")
        qtd = 5
    dist, pred = alg.dijkstra(g, origem)
    alcancaveis = sorted((d, v) for v, d in dist.items() if v != origem and d < alg.INFINITO)
    inalcancaveis = [v for v, d in dist.items() if d == alg.INFINITO]
    print(f"  Origem: {rotulo(g, origem)} | cidades alcancaveis: {len(alcancaveis)} | "
          f"inalcancaveis: {len(inalcancaveis)}")
    if not alcancaveis:
        return
    media = sum(d for d, _ in alcancaveis) / len(alcancaveis)
    print(f"  Distancia media as demais cidades: {km(media)}")
    print(f"  {qtd} mais proximas pela malha:")
    for d, v in alcancaveis[:qtd]:
        print(f"    {g.nome(v):<32}{km(d):>11}  ({len(alg.reconstruir_caminho(pred, origem, v)) - 1} trechos)")
    print(f"  {qtd} mais distantes pela malha:")
    for d, v in alcancaveis[::-1][:qtd]:
        print(f"    {g.nome(v):<32}{km(d):>11}  ({len(alg.reconstruir_caminho(pred, origem, v)) - 1} trechos)")


def op_agm(g):
    """Analise complementar: menor conjunto de ligacoes que conecta a malha."""
    if grafo_vazio(g):
        return
    arestas, custo = alg.arvore_geradora_minima(g)
    total = sum(p for _, _, p in g.lista_arestas())
    componentes = g.numero_vertices() - len(arestas)
    tipo = "Arvore" if componentes == 1 else f"Floresta ({componentes} arvores)"
    print(f"  {tipo} geradora minima (Prim): {len(arestas)} arestas")
    print(f"  Custo total da AGM: {km(custo)} | soma de todas as arestas: {km(total)}")
    if total:
        print(f"  A AGM usa {100 * custo / total:.1f}% da extensao total modelada.")
    print("  5 maiores ligacoes da AGM (trechos indispensaveis mais longos):")
    for u, v, p in sorted(arestas, key=lambda a: -a[2])[:5]:
        print(f"    {g.nome(u)} - {g.nome(v)}: {km(p)}")
    if ler_sim_nao("Exibir todas as arestas da AGM? (s/N) "):
        for u, v, p in arestas:
            print(f"    {g.nome(u)} - {g.nome(v)}: {km(p)}")


# --------------------------------------------------------------------------- #
# Opcoes 15 a 21 - caracteristicas do grafo (Parte 3)
# --------------------------------------------------------------------------- #
def op_graus(g):
    if grafo_vazio(g):
        return
    r = alg.analise_graus(g)
    print(f"  Grau minimo: {r['minimo']} | maximo: {r['maximo']} | medio: {r['medio']:.2f} | "
          f"mediana: {r['mediana']} | desvio padrao: {r['desvio']:.2f}")
    print(f"  Lema do aperto de maos: soma dos graus = {r['soma']} = 2 x {r['arestas']} arestas"
          f" -> {'OK' if r['soma'] == 2 * r['arestas'] else 'INCONSISTENTE'}")
    print("  Distribuicao dos graus (grau: quantidade de cidades):")
    maior = max(r["distribuicao"].values())
    for grau, qtd in r["distribuicao"].items():
        barra = "#" * max(1, round(40 * qtd / maior))
        print(f"    {grau:>3}: {qtd:>4}  {barra}")
    print("  Cidades de grau maximo: "
          + ", ".join(g.nome(v) for v in r["vertices_grau_maximo"]))
    if r["isolados"]:
        print(f"  Vertices isolados (grau 0): {len(r['isolados'])}")
    seq = r["sequencia"]
    print(f"  Sequencia de graus (ordem decrescente, {len(seq)} valores): "
          + " ".join(map(str, seq[:30])) + (" ..." if len(seq) > 30 else ""))


def op_coloracao(g):
    if grafo_vazio(g):
        return
    r = alg.analise_coloracao(g)
    print(f"  Cores usadas (Welsh-Powell): {r['num_cores']} | coloracao valida? "
          f"{'SIM' if r['valida'] else 'NAO'}")
    print(f"  Clique maxima (Bron-Kerbosch): {r['limite_inferior']} vertices -> "
          + ", ".join(g.nome(v) for v in r["clique"]))
    if r["exato"]:
        print(f"  Como omega(G) = {r['limite_inferior']} <= chi(G) <= {r['num_cores']}, "
              f"o numero cromatico e EXATAMENTE {r['num_cores']}.")
    else:
        print(f"  Numero cromatico entre {r['limite_inferior']} e {r['num_cores']}.")
    print(f"  O grafo e bipartido? {'SIM' if r['bipartido'] else 'NAO'}")
    print("  Particoes (conjuntos independentes de cidades sem ligacao direta):")
    for c, vs in r["classes"].items():
        exemplos = ", ".join(g.nome(v) for v in vs[:4])
        print(f"    Cor {c + 1}: {len(vs):>3} cidades (ex.: {exemplos}{', ...' if len(vs) > 4 else ''})")


def op_euleriano(g):
    if grafo_vazio(g):
        return
    r = alg.analise_euleriana(g)
    print(f"  Conexo (considerando as arestas)? {'SIM' if r['conexo'] else 'NAO'}")
    print(f"  Vertices de grau impar: {len(r['impares'])}")
    print(f"  E euleriano (circuito euleriano)? {'SIM' if r['euleriano'] else 'NAO'}")
    print(f"  Tem percurso euleriano aberto (semieuleriano)? "
          f"{'SIM' if r['semieuleriano'] else 'NAO'}")
    if r["percurso"]:
        seq = " -> ".join(g.nome(v) for v in r["percurso"][:20])
        print(f"  Percurso (Hierholzer, {len(r['percurso']) - 1} arestas): {seq}"
              + (" -> ..." if len(r["percurso"]) > 20 else ""))
    elif r["impares"]:
        print(f"  Motivo: o Teorema de Euler exige 0 (circuito) ou 2 (percurso) vertices "
              f"de grau impar; ha {len(r['impares'])}. Para percorrer todas as ligacoes "
              f"seria preciso repetir trechos ligando ao menos {r['pares_a_corrigir']} "
              "pares de cidades de grau impar.")


def op_hamiltoniano(g):
    if grafo_vazio(g):
        return
    print("  Analisando (busca limitada a 10 s)...")
    r = alg.analise_hamiltoniana(g, limite_segundos=10.0)
    print(f"  n = {r['n']} | grau minimo = {r['grau_minimo']} | n/2 = {r['n'] / 2:g}")
    print(f"  Condicao de Dirac (grau minimo >= n/2): {'SIM' if r['dirac'] else 'NAO'}")
    print(f"  Condicao de Ore (grau(u)+grau(v) >= n p/ nao adjacentes): "
          f"{'SIM' if r['ore'] else 'NAO'}")
    if r["dirac"] or r["ore"]:
        print("  -> Condicao suficiente satisfeita: o grafo E hamiltoniano.")
    else:
        print("  -> Condicoes suficientes nao satisfeitas (nada se conclui por elas).")
    print(f"  Pontos de articulacao: {len(r['articulacoes'])}")
    for motivo in r["motivos_sem_ciclo"]:
        print(f"  Condicao necessaria violada: {motivo}.")
    status = {"encontrado": "SIM (ciclo encontrado e verificado)",
              "inexistente": "NAO",
              "tempo esgotado": "INCONCLUSIVO (tempo esgotado)"}
    print(f"  Possui ciclo hamiltoniano? {status[r['status_ciclo']]}")
    if r["status_ciclo"] != "encontrado":
        print(f"  Possui caminho hamiltoniano? {status[r['status_caminho']].replace('ciclo', 'caminho')}")
    seq = r["ciclo"] or r["caminho"]
    if seq:
        fechado = seq + [seq[0]] if r["ciclo"] else seq
        extensao = sum(g.adjacencia[fechado[i]][fechado[i + 1]] for i in range(len(fechado) - 1))
        tipo = "ciclo" if r["ciclo"] else "caminho"
        print(f"  Extensao do {tipo} encontrado: {km(extensao)} "
              f"(visita as {len(seq)} cidades uma unica vez)")
        print("  Inicio: " + " -> ".join(g.nome(v) for v in fechado[:8]) + " -> ...")
        if ler_sim_nao("Exibir a sequencia completa? (s/N) "):
            print("  " + " -> ".join(g.nome(v) for v in fechado))


def op_articulacoes(g):
    if grafo_vazio(g):
        return
    articulacoes, pontes = alg.articulacoes_e_pontes(g)
    print(f"  Pontos de articulacao (cidades criticas): {len(articulacoes)}")
    for v in articulacoes:
        print(f"    - {rotulo(g, v)}: sua remocao gera "
              f"{alg.componentes_sem_vertice(g, v)} componentes")
    print(f"  Pontes (ligacoes criticas): {len(pontes)}")
    for u, v in pontes:
        print(f"    - {g.nome(u)} - {g.nome(v)} ({km(g.adjacencia[u][v])})")
    if not articulacoes and not pontes and g.eh_conexo() and g.numero_vertices() > 2:
        print("  A malha e 2-conexa (biconexa): a perda de UMA cidade ou de UMA ligacao")
        print("  qualquer nao isola nenhuma parte da regiao.")


def op_planaridade(g):
    if grafo_vazio(g):
        return
    r = alg.analise_planaridade(g)
    if r["limite_arestas"] is not None:
        print(f"  Formula de Euler: grafo planar tem m <= 3n - 6 = {r['limite_arestas']}; "
              f"aqui m = {r['m']} -> {'VIOLADA' if r['viola_euler'] else 'respeitada'}")
    print(f"  Contem K5 (Kuratowski)? {'SIM' if r['contem_k5'] else 'NAO'} "
          f"(clique maxima com {len(r['clique'])} vertices)")
    resposta = {False: "NAO (provado)", None: "INCONCLUSIVO pelas condicoes necessarias"}
    print(f"  O grafo e planar? {resposta[r['planar']]}")


def op_excentricidade(g):
    if grafo_vazio(g):
        return
    if not g.eh_conexo():
        print("  Grafo desconexo: excentricidades infinitas (raio/diametro indefinidos).")
        return
    r = alg.excentricidades(g)
    print(f"  Raio: {km(r['raio'])} | Diametro: {km(r['diametro'])}")
    print("  Centro (menor excentricidade): "
          + ", ".join(g.nome(v) for v in r["centro"]))
    a = r["periferia"][0]
    b = r["mais_distante"][a]
    print(f"  Par mais distante (diametro): {g.nome(a)} <-> {g.nome(b)}")
    print(f"  Mediana do grafo (menor distancia media as demais): "
          f"{g.nome(r['mediana'])} ({km(r['distancia_media_mediana'])} em media)")
    print("  5 cidades mais centrais (menor excentricidade):")
    for v in sorted(r["ecc"], key=lambda v: (r["ecc"][v], v))[:5]:
        print(f"    {g.nome(v):<32}{km(r['ecc'][v]):>11}")
    consulta = ler("Consultar a excentricidade de uma cidade? (id/nome ou Enter) ").strip()
    if consulta:
        vid, erro = g.buscar_vertice(consulta)
        if erro:
            print(f"  {erro[0].upper()}{erro[1:]}.")
        else:
            print(f"  Excentricidade de {g.nome(vid)}: {km(r['ecc'][vid])} "
                  f"(cidade mais distante: {g.nome(r['mais_distante'][vid])})")


# --------------------------------------------------------------------------- #
# Laco principal
# --------------------------------------------------------------------------- #
ACOES = {
    "1": op_exibir, "2": op_mostrar_arquivo, "3": op_inserir_vertice,
    "4": op_remover_vertice, "5": op_inserir_aresta, "6": op_remover_aresta,
    "7": op_grau, "8": op_conexidade, "9": op_reduzido, "10": op_gravar,
    "11": op_recarregar, "12": op_caminho_minimo, "13": op_distancias_origem,
    "14": op_agm, "15": op_graus, "16": op_coloracao, "17": op_euleriano,
    "18": op_hamiltoniano, "19": op_articulacoes, "20": op_planaridade,
    "21": op_excentricidade,
}


def main():
    g = carregar()
    while True:
        cabecalho(g)
        menu()
        escolha = ler("Escolha uma opcao: ").strip()
        if escolha == "0":
            print("Encerrando. Ate mais!")
            break
        acao = ACOES.get(escolha)
        if acao is None:
            print("  Opcao invalida.")
            continue
        print(SUBLINHA)
        resultado = acao(g)
        if isinstance(resultado, Grafo):          # opcao 11 troca o grafo atual
            g = resultado
        ler("\n[Enter para voltar ao menu]")


if __name__ == "__main__":
    main()
