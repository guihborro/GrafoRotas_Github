# =============================================================================
# GrafoRotas - Geracao das figuras do relatorio: esboco, malha completa,
# estatisticas do dataset e resultados dos algoritmos da Parte 3 (rotas de
# Dijkstra, arvore geradora minima, coloracao e ciclo hamiltoniano).
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
#   2026-09-02 | Guilherme Haddad Borro | Versao inicial (Parte 2): esboco e
#                malha completa.
#   2026-10-18 | Guilherme Haddad Borro | Parte 3: figuras salvas em imagens/;
#                histogramas (pesos, graus, fator de desvio) e mapas das rotas
#                de Dijkstra, da AGM, da coloracao e do ciclo hamiltoniano.
#
# Uso:  python gerar_imagens.py   (requer matplotlib)
# =============================================================================

import csv
import os
import sys
from math import asin, cos, radians, sin, sqrt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import algoritmos as alg
from grafo import Grafo

PASTA_IMG = "imagens"
AZUL = "#2563EB"
AZUL_ESC = "#1E3A5F"
CINZA = "#94A3B8"
TXT = "#0F172A"
LARANJA = "#EA580C"
VERDE = "#16A34A"
PALETA = ["#2563EB", "#EA580C", "#16A34A", "#9333EA", "#DC2626", "#0891B2", "#CA8A04"]


def salvar(fig, nome):
    os.makedirs(PASTA_IMG, exist_ok=True)
    caminho = os.path.join(PASTA_IMG, nome)
    fig.savefig(caminho, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"{caminho} gerado")


def carregar_coordenadas(caminho="cidades.csv"):
    """Le cidades.csv -> dict {id: (nome, lat, lon)}."""
    coords = {}
    with open(caminho, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            coords[int(row["id"])] = (row["nome"], float(row["lat"]), float(row["lon"]))
    return coords


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia geografica (linha reta sobre a esfera), em km."""
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(a))


def mapa_base(ax, g, coords, titulo, cor_aresta=CINZA, alpha=0.35):
    """Desenha todas as arestas em cinza claro como fundo de um mapa."""
    for u, v, _ in g.lista_arestas():
        ax.plot([coords[u][2], coords[v][2]], [coords[u][1], coords[v][1]],
                color=cor_aresta, lw=0.5, alpha=alpha, zorder=1)
    ax.set_title(titulo, fontsize=12, color=TXT, weight="bold", pad=10)
    ax.set_xlabel("Longitude", fontsize=9, color=TXT)
    ax.set_ylabel("Latitude", fontsize=9, color=TXT)
    ax.grid(True, color="#E2E8F0", lw=0.5)
    ax.set_facecolor("#FBFCFE")


# --- Esboco conceitual (independente do dataset) --------------------------- #
def gerar_esboco():
    pos = {
        "Sao Paulo": (0.40, 0.45), "Guarulhos": (0.55, 0.62),
        "Santo Andre": (0.55, 0.28), "Sao Bernardo do Campo": (0.42, 0.18),
        "Mogi das Cruzes": (0.80, 0.55), "Jundiai": (0.22, 0.72),
        "Osasco": (0.20, 0.42), "Sao Jose dos Campos": (0.86, 0.78),
    }
    arestas = [
        ("Sao Paulo", "Guarulhos", 15), ("Sao Paulo", "Santo Andre", 16),
        ("Sao Paulo", "Osasco", 16), ("Sao Paulo", "Sao Bernardo do Campo", 17),
        ("Santo Andre", "Sao Bernardo do Campo", 5), ("Guarulhos", "Mogi das Cruzes", 36),
        ("Mogi das Cruzes", "Sao Jose dos Campos", 62), ("Osasco", "Jundiai", 40),
        ("Guarulhos", "Sao Jose dos Campos", 73), ("Jundiai", "Sao Paulo", 49),
    ]
    fig, ax = plt.subplots(figsize=(9, 6.2))
    for a, b, km in arestas:
        xa, ya = pos[a]; xb, yb = pos[b]
        ax.plot([xa, xb], [ya, yb], color=CINZA, lw=1.8, zorder=1)
        ax.text((xa + xb) / 2, (ya + yb) / 2, f"{km} km", fontsize=8.5,
                color=AZUL_ESC, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85),
                zorder=2)
    for nome, (x, y) in pos.items():
        ax.scatter([x], [y], s=1500, color=AZUL, edgecolors="white", linewidths=2, zorder=3)
        ax.text(x, y - 0.075, nome, fontsize=8.5, ha="center", va="top",
                color=TXT, weight="bold", zorder=4)
    ax.set_title("Esboco da modelagem: cidades (vertices) e distancias (arestas ponderadas)",
                 fontsize=12, color=TXT, weight="bold", pad=14)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    plt.tight_layout()
    salvar(fig, "esboco_grafo.png")


# --- Malha completa (dados reais) ------------------------------------------ #
def gerar_malha(g, coords):
    n, m = g.numero_vertices(), g.numero_arestas()
    fig, ax = plt.subplots(figsize=(11, 8.5))
    for u, v, _ in g.lista_arestas():
        ax.plot([coords[u][2], coords[v][2]], [coords[u][1], coords[v][1]],
                color=CINZA, lw=0.6, alpha=0.55, zorder=1)
    graus = {v: g.grau(v) for v in g.adjacencia}
    ax.scatter([coords[v][2] for v in g.adjacencia], [coords[v][1] for v in g.adjacencia],
               s=[30 + graus[v] * 22 for v in g.adjacencia], c=AZUL,
               edgecolors="white", linewidths=0.7, zorder=2)
    for v in sorted(g.adjacencia, key=lambda v: graus[v], reverse=True)[:14]:
        ax.text(coords[v][2], coords[v][1] + 0.02, coords[v][0], fontsize=7.5,
                ha="center", va="bottom", color=TXT, zorder=3)
    mapa_base(ax, Grafo(), coords,
              f"Malha modelada: {n} municipios e {m} ligacoes (tamanho do no = grau)")
    salvar(fig, "rede_completa.png")


# --- Estatisticas do dataset ----------------------------------------------- #
def gerar_estatisticas(g, coords):
    pesos = [p for _, _, p in g.lista_arestas()]
    fatores = [p / haversine_km(coords[u][1], coords[u][2], coords[v][1], coords[v][2])
               for u, v, p in g.lista_arestas()]
    graus = alg.analise_graus(g)["distribuicao"]
    fig, eixos = plt.subplots(1, 3, figsize=(15, 4.2))
    eixos[0].hist(pesos, bins=20, color=AZUL, edgecolor="white")
    eixos[0].set_title("Pesos das arestas (km rodoviarios)", fontsize=11, weight="bold")
    eixos[0].set_xlabel("Distancia (km)"); eixos[0].set_ylabel("Arestas")
    eixos[1].bar(list(graus), list(graus.values()), color=VERDE, edgecolor="white")
    eixos[1].set_title("Distribuicao dos graus", fontsize=11, weight="bold")
    eixos[1].set_xlabel("Grau"); eixos[1].set_ylabel("Municipios")
    eixos[2].hist(fatores, bins=20, color=LARANJA, edgecolor="white")
    eixos[2].set_title("Fator de desvio (rodovia / linha reta)", fontsize=11, weight="bold")
    eixos[2].set_xlabel("Fator"); eixos[2].set_ylabel("Arestas")
    for ax in eixos:
        ax.grid(True, axis="y", color="#E2E8F0", lw=0.5)
        ax.set_axisbelow(True)
    plt.tight_layout()
    salvar(fig, "estatisticas_dataset.png")


# --- Rotas de menor distancia (Dijkstra) ----------------------------------- #
def gerar_rotas(g, coords, pares):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    mapa_base(ax, g, coords, "Rotas de menor distancia calculadas pelo algoritmo de Dijkstra")
    ax.scatter([coords[v][2] for v in g.adjacencia], [coords[v][1] for v in g.adjacencia],
               s=12, c=CINZA, zorder=2)
    for i, (a, b) in enumerate(pares):
        origem, _ = g.buscar_vertice(a)
        destino, _ = g.buscar_vertice(b)
        total, cam = alg.caminho_minimo(g, origem, destino)
        cor = PALETA[i % len(PALETA)]
        ax.plot([coords[v][2] for v in cam], [coords[v][1] for v in cam], color=cor, lw=2.6,
                zorder=3, label=f"{g.nome(origem)} -> {g.nome(destino)}: {total:.1f} km "
                                f"({len(cam) - 1} trechos)")
        ax.scatter([coords[v][2] for v in cam], [coords[v][1] for v in cam], s=28, c=cor, zorder=4)
        for v in (origem, destino):
            ax.text(coords[v][2], coords[v][1] + 0.03, coords[v][0], fontsize=8.5,
                    ha="center", va="bottom", color=TXT, weight="bold", zorder=5)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    salvar(fig, "rotas_dijkstra.png")


# --- Arvore geradora minima (Prim) ----------------------------------------- #
def gerar_agm(g, coords):
    arestas, custo = alg.arvore_geradora_minima(g)
    fig, ax = plt.subplots(figsize=(11, 8.5))
    mapa_base(ax, g, coords, f"Arvore geradora minima (Prim): {len(arestas)} ligacoes, "
                             f"{custo:.1f} km", alpha=0.25)
    for u, v, _ in arestas:
        ax.plot([coords[u][2], coords[v][2]], [coords[u][1], coords[v][1]],
                color=VERDE, lw=1.8, zorder=2)
    ax.scatter([coords[v][2] for v in g.adjacencia], [coords[v][1] for v in g.adjacencia],
               s=16, c=AZUL_ESC, zorder=3)
    salvar(fig, "agm_prim.png")


# --- Coloracao (Welsh-Powell) ---------------------------------------------- #
def gerar_coloracao(g, coords):
    r = alg.analise_coloracao(g)
    fig, ax = plt.subplots(figsize=(11, 8.5))
    mapa_base(ax, g, coords, f"Coloracao de Welsh-Powell: {r['num_cores']} cores "
                             f"(clique K{r['limite_inferior']} destacada)")
    for c, vs in r["classes"].items():
        ax.scatter([coords[v][2] for v in vs], [coords[v][1] for v in vs], s=40,
                   c=PALETA[c % len(PALETA)], edgecolors="white", linewidths=0.6,
                   zorder=3, label=f"Cor {c + 1} ({len(vs)} cidades)")
    clique = r["clique"]
    for i, u in enumerate(clique):
        for v in clique[i + 1:]:
            ax.plot([coords[u][2], coords[v][2]], [coords[u][1], coords[v][1]],
                    color=TXT, lw=1.4, zorder=2)
    ax.legend(loc="lower right", fontsize=8.5, framealpha=0.95)
    salvar(fig, "coloracao.png")


# --- Ciclo hamiltoniano ---------------------------------------------------- #
def gerar_hamiltoniano(g, coords):
    r = alg.analise_hamiltoniana(g)
    if not r["ciclo"]:
        print("ciclo hamiltoniano nao encontrado; figura nao gerada")
        return
    seq = r["ciclo"] + [r["ciclo"][0]]
    total = sum(g.adjacencia[seq[i]][seq[i + 1]] for i in range(len(seq) - 1))
    fig, ax = plt.subplots(figsize=(11, 8.5))
    mapa_base(ax, g, coords, f"Ciclo hamiltoniano encontrado: {len(r['ciclo'])} cidades, "
                             f"{total:.1f} km", alpha=0.2)
    ax.plot([coords[v][2] for v in seq], [coords[v][1] for v in seq], color="#9333EA",
            lw=1.4, zorder=2)
    ax.scatter([coords[v][2] for v in g.adjacencia], [coords[v][1] for v in g.adjacencia],
               s=14, c=AZUL_ESC, zorder=3)
    salvar(fig, "ciclo_hamiltoniano.png")


if __name__ == "__main__":
    gerar_esboco()
    if not (os.path.exists("cidades.csv") and os.path.exists("grafo.txt")):
        print("cidades.csv/grafo.txt nao encontrados: rode coletar_dados.py primeiro.")
        sys.exit(0)
    grafo = Grafo().ler_arquivo("grafo.txt")
    coordenadas = carregar_coordenadas("cidades.csv")
    gerar_malha(grafo, coordenadas)
    gerar_estatisticas(grafo, coordenadas)
    gerar_rotas(grafo, coordenadas, [("Sao Paulo", "Campinas"), ("Sorocaba", "Registro"),
                                     ("Barra do Turvo", "Mococa")])
    gerar_agm(grafo, coordenadas)
    gerar_coloracao(grafo, coordenadas)
    gerar_hamiltoniano(grafo, coordenadas)
