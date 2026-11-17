# =============================================================================
# GrafoRotas - Coleta de dados reais (IBGE + OpenStreetMap) e geracao dos
# arquivos grafo.txt, cidades.csv e coleta_metadados.json.
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
#   2026-09-02 | Guilherme Haddad Borro | Versao inicial (Parte 2): IBGE,
#                Nominatim, K vizinhos mais proximos e distancias OSRM.
#   2026-10-18 | Guilherme Haddad Borro | Parte 3: registro dos parametros e da
#                data/hora da coleta em coleta_metadados.json; contagem de
#                fallbacks; etapa que GARANTE a conexidade (o criterio de K
#                vizinhos, sozinho, nao garante grafo conexo).
#   2026-11-16 | Guilherme Haddad Borro | Geocodificacao prefere a sede do
#                municipio (city/town/village) ao limite municipal, que o OSM
#                passou a devolver primeiro para parte das cidades (exigindo
#                o mesmo nome); ate 3 tentativas por consulta ao OSRM.
#
# Uso:  python coletar_dados.py   (requer internet; leva ~15-20 minutos)
# =============================================================================

import csv
import json
import platform
import time
from datetime import datetime, timezone
from math import radians, sin, cos, asin, sqrt

import requests

# --------------------------------------------------------------------------- #
# CONFIGURACAO
# --------------------------------------------------------------------------- #
# Recorte oficial adotado: Regioes Geograficas Intermediarias do IBGE (2017).
# A intermediaria de Sao Paulo sozinha tem ~50 municipios (abaixo do minimo de
# 80 vertices); por isso combinamos intermediarias oficiais e contiguas ate
# ultrapassar o minimo. Para ajustar o recorte, edite a lista abaixo.
INTERMEDIARIAS_ALVO = ["Sao Paulo", "Sorocaba", "Campinas"]

# (Opcional) Se quiser um recorte menor, liste aqui os nomes das Regioes
# Geograficas IMEDIATAS desejadas; se a lista estiver vazia, usa a
# intermediaria inteira definida acima.
IMEDIATAS_ALVO = []          # ex.: ["Sao Paulo", "Osasco", "Guarulhos"]

K_VIZINHOS = 5               # cada cidade liga-se as K mais proximas
PAUSA_SEG = 1.1             # pausa entre chamadas (respeita limites gratuitos)

UA = {"User-Agent": "GrafoRotas-TeoriaDosGrafos/1.0 (projeto academico)"}

# Servicos consultados (registrados nos metadados para reprodutibilidade)
URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios"
URL_NOMINATIM = "https://nominatim.openstreetmap.org/search"
URL_OSRM = "https://router.project-osrm.org/route/v1/driving/"


# --------------------------------------------------------------------------- #
# 1) MUNICIPIOS OFICIAIS (IBGE)
# --------------------------------------------------------------------------- #
def normaliza(txt):
    """Remove acentos e caixa para comparar nomes com seguranca."""
    import unicodedata
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return txt.strip().lower()


def obter_municipios_ibge():
    """Busca na API do IBGE os municipios de SP filtrados pelo recorte oficial.

    Retorna lista de dicts: {codigo_ibge, nome, imediata, intermediaria}.
    """
    url = URL_IBGE
    print("Consultando IBGE:", url)
    resp = requests.get(url, headers=UA, timeout=30)
    resp.raise_for_status()
    dados = resp.json()

    alvos_inter = {normaliza(x) for x in INTERMEDIARIAS_ALVO}
    alvos_imed = {normaliza(x) for x in IMEDIATAS_ALVO}

    selecionados = []
    for m in dados:
        imed = m.get("regiao-imediata", {})
        inter = imed.get("regiao-intermediaria", {}) if imed else {}
        nome_imed = imed.get("nome", "")
        nome_inter = inter.get("nome", "")
        if alvos_imed:
            ok = normaliza(nome_imed) in alvos_imed
        else:
            ok = normaliza(nome_inter) in alvos_inter
        if ok:
            selecionados.append({
                "codigo_ibge": m["id"],
                "nome": m["nome"],
                "imediata": nome_imed,
                "intermediaria": nome_inter,
            })
    selecionados.sort(key=lambda x: x["nome"])
    from collections import Counter
    por_inter = Counter(m["intermediaria"] for m in selecionados)
    print(f"  -> {len(selecionados)} municipios no recorte selecionado.")
    print(f"     por intermediaria: {dict(por_inter)}")
    return selecionados


# --------------------------------------------------------------------------- #
# 2) COORDENADAS (OpenStreetMap / Nominatim)
# --------------------------------------------------------------------------- #
TIPOS_SEDE = ("city", "town", "village")   # area urbana da sede do municipio


def geocodificar(nome_municipio):
    """Obtem (lat, lon) da SEDE (centro urbano) do municipio via Nominatim.

    Para muitos municipios o OpenStreetMap tem dois resultados: o limite do
    municipio inteiro (addresstype 'municipality', cujo ponto pode cair na
    zona rural, a mais de 20 km da cidade) e a area urbana da sede
    (addresstype 'city', 'town' ou 'village'). Pede-se ate 10 resultados e
    escolhe-se, nesta ordem: a sede com o MESMO nome do municipio; qualquer
    resultado com o mesmo nome (evita, por exemplo, "Mineiros do Tiete" na
    busca por "Tiete"); o primeiro resultado.
    """
    url = URL_NOMINATIM
    params = {"q": f"{nome_municipio}, Sao Paulo, Brasil",
              "format": "json", "limit": 10}
    resp = requests.get(url, params=params, headers=UA, timeout=30)
    resp.raise_for_status()
    r = resp.json()
    if not r:
        return None
    mesmo_nome = [x for x in r if normaliza(x.get("name", "")) == normaliza(nome_municipio)]
    sede = next((x for x in mesmo_nome if x.get("addresstype") in TIPOS_SEDE),
                mesmo_nome[0] if mesmo_nome else r[0])
    return float(sede["lat"]), float(sede["lon"])


# --------------------------------------------------------------------------- #
# 3) DISTANCIA GEOGRAFICA (para escolher vizinhos) e RODOVIARIA (OSRM)
# --------------------------------------------------------------------------- #
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return round(2 * R * asin(sqrt(a)), 1)


TENTATIVAS_OSRM = 3          # o servidor publico tem quedas momentaneas


def distancia_rodoviaria_km(lat1, lon1, lat2, lon2):
    """Distancia rodoviaria real (km) via OSRM (OpenStreetMap).

    Tenta ate TENTATIVAS_OSRM vezes, com espera crescente (5 s, 10 s), antes
    de desistir; retorna None se todas falharem (o chamador usa o fallback).
    """
    url = f"{URL_OSRM}{lon1},{lat1};{lon2},{lat2}?overview=false"
    for tentativa in range(1, TENTATIVAS_OSRM + 1):
        try:
            resp = requests.get(url, headers=UA, timeout=30)
            resp.raise_for_status()
            dados = resp.json()
            if dados.get("code") == "Ok" and dados.get("routes"):
                return round(dados["routes"][0]["distance"] / 1000.0, 1)
            return None                     # resposta valida, mas sem rota
        except Exception as e:
            print(f"   aviso OSRM (tentativa {tentativa}/{TENTATIVAS_OSRM}):", e)
            if tentativa < TENTATIVAS_OSRM:
                time.sleep(5 * tentativa)
    return None


# --------------------------------------------------------------------------- #
# 4) GARANTIA DE CONEXIDADE
# --------------------------------------------------------------------------- #
def garantir_conexidade(cidades, candidatas):
    """Liga componentes desconexas pela menor distancia geografica.

    O criterio de K vizinhos mais proximos NAO garante, por si so, um grafo
    conexo: dois agrupamentos de cidades distantes entre si podem ter todos os
    seus K vizinhos dentro do proprio agrupamento. Esta etapa identifica as
    componentes (union-find) e, enquanto houver mais de uma, acrescenta a
    aresta mais curta (haversine) entre componentes diferentes - a mesma
    ideia do algoritmo de Kruskal aplicada as componentes.
    Retorna a lista de arestas acrescentadas.
    """
    pai = list(range(len(cidades)))

    def raiz(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for u, v in candidatas:
        pai[raiz(u)] = raiz(v)
    acrescentadas = []
    while len({raiz(i) for i in range(len(cidades))}) > 1:
        melhor = min(
            (haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]), i, j)
            for i, a in enumerate(cidades) for j, b in enumerate(cidades)
            if i < j and raiz(i) != raiz(j))
        _, i, j = melhor
        candidatas.add((i, j))
        pai[raiz(i)] = raiz(j)
        acrescentadas.append((i, j))
        print(f"  conexidade: aresta extra {cidades[i]['nome']} - {cidades[j]['nome']}")
    return acrescentadas


# --------------------------------------------------------------------------- #
# PIPELINE PRINCIPAL
# --------------------------------------------------------------------------- #
def main():
    inicio_coleta = datetime.now(timezone.utc).astimezone()
    # 1) municipios oficiais
    municipios = obter_municipios_ibge()
    if len(municipios) < 80:
        print(f"ATENCAO: recorte tem {len(municipios)} municipios (< 80 exigidos).")
        print("Ajuste INTERMEDIARIA_ALVO/IMEDIATAS_ALVO no topo do arquivo.")

    # 2) coordenadas via OpenStreetMap
    print("\nGeocodificando municipios (OpenStreetMap/Nominatim)...")
    cidades = []
    sem_coordenada = []
    for i, m in enumerate(municipios):
        coord = geocodificar(m["nome"])
        if coord is None:
            print(f"  [{i}] {m['nome']}: SEM coordenada, ignorado.")
            sem_coordenada.append(m["nome"])
            continue
        cidades.append({**m, "lat": coord[0], "lon": coord[1]})
        print(f"  [{len(cidades)-1}] {m['nome']}: {coord[0]:.4f}, {coord[1]:.4f}")
        time.sleep(PAUSA_SEG)

    # 3) arestas: cada cidade -> K vizinhas mais proximas (por haversine)
    print("\nDefinindo arestas (K vizinhos mais proximos)...")
    candidatas = set()
    for i, a in enumerate(cidades):
        dists = []
        for j, b in enumerate(cidades):
            if i == j:
                continue
            dists.append((haversine_km(a["lat"], a["lon"], b["lat"], b["lon"]), j))
        dists.sort()
        for _, j in dists[:K_VIZINHOS]:
            candidatas.add((min(i, j), max(i, j)))
    print(f"  -> {len(candidatas)} arestas candidatas.")

    # 3b) o criterio de K vizinhos nao garante conexidade: corrige se preciso
    extras = garantir_conexidade(cidades, candidatas)
    print(f"  -> {len(extras)} aresta(s) acrescentada(s) para garantir a conexidade.")

    # 4) distancia rodoviaria real de cada aresta (OSRM)
    print("\nObtendo distancias rodoviarias reais (OpenStreetMap/OSRM)...")
    arestas = []
    fallbacks = []
    for n, (u, v) in enumerate(sorted(candidatas), 1):
        a, b = cidades[u], cidades[v]
        km = distancia_rodoviaria_km(a["lat"], a["lon"], b["lat"], b["lon"])
        if km is None:  # fallback: distancia geografica, registrada nos metadados
            km = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            fallbacks.append([u, v])
        arestas.append((u, v, km))
        if n % 25 == 0:
            print(f"  {n}/{len(candidatas)} arestas processadas...")
        time.sleep(PAUSA_SEG)

    # 5) gravacao dos arquivos
    with open("cidades.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "nome", "codigo_ibge", "lat", "lon"])
        for idc, c in enumerate(cidades):
            w.writerow([idc, c["nome"], c["codigo_ibge"], c["lat"], c["lon"]])

    # tipo do grafo: 2 = nao orientado com peso na aresta
    TIPO_GRAFO = 2
    with open("grafo.txt", "w", encoding="utf-8") as f:
        f.write(f"{TIPO_GRAFO}\n")
        f.write(f"{len(cidades)}\n")
        for idc, c in enumerate(cidades):
            f.write(f"{idc};{c['nome']}\n")
        f.write(f"{len(arestas)}\n")
        for u, v, km in arestas:
            f.write(f"{u};{v};{km}\n")

    # 6) metadados: parametros e data da coleta, para que ela possa ser
    #    reproduzida e auditada (os servicos do OSM evoluem com o tempo)
    metadados = {
        "data_hora_inicio": inicio_coleta.isoformat(timespec="seconds"),
        "data_hora_fim": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "parametros": {
            "uf": "SP (codigo IBGE 35)",
            "intermediarias_alvo": INTERMEDIARIAS_ALVO,
            "imediatas_alvo": IMEDIATAS_ALVO,
            "k_vizinhos": K_VIZINHOS,
            "criterio_aresta": "u-v se v esta entre os K mais proximos de u (haversine) ou vice-versa",
            "consulta_nominatim": "'<municipio>, Sao Paulo, Brasil' (format=json, limit=10); prefere o resultado de mesmo nome com addresstype city/town/village (sede)",
            "tentativas_osrm": TENTATIVAS_OSRM,
            "perfil_osrm": "driving, overview=false (distancia da rota mais rapida)",
            "pausa_entre_chamadas_s": PAUSA_SEG,
            "user_agent": UA["User-Agent"],
        },
        "servicos": {"ibge": URL_IBGE, "nominatim": URL_NOMINATIM, "osrm": URL_OSRM},
        "ambiente": {"python": platform.python_version(),
                     "requests": requests.__version__},
        "resultado": {
            "municipios_ibge": len(municipios),
            "municipios_sem_coordenada": sem_coordenada,
            "vertices": len(cidades),
            "arestas": len(arestas),
            "arestas_extras_conexidade": extras,
            "arestas_com_fallback_haversine": fallbacks,
        },
    }
    with open("coleta_metadados.json", "w", encoding="utf-8") as f:
        json.dump(metadados, f, ensure_ascii=False, indent=2)

    print("\n==================== COLETA CONCLUIDA ====================")
    print(f"Municipios (vertices): {len(cidades)}")
    print(f"Ligacoes (arestas):    {len(arestas)}")
    print(f"Arestas extras p/ conexidade: {len(extras)} | fallbacks haversine: {len(fallbacks)}")
    print("Arquivos gerados: cidades.csv, grafo.txt e coleta_metadados.json")
    print("Fontes: IBGE (municipios) e OpenStreetMap (coordenadas e distancias).")


if __name__ == "__main__":
    main()
