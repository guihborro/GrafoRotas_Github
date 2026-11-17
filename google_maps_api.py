# =============================================================================
# GrafoRotas - Integracao opcional com a API do Google Maps (alternativa ao
# OpenStreetMap) para obter a distancia rodoviaria entre dois pontos.
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
#   2026-09-02 | Guilherme Haddad Borro | Versao inicial (Parte 2).
#   2026-10-18 | Guilherme Haddad Borro | Parte 3: cabecalho no formato padrao
#                (sem alteracao funcional; modulo nao usado pela base atual).
# =============================================================================

import os

# A chave NAO deve ser versionada no GitHub. Configure-a como variavel de
# ambiente: export GOOGLE_MAPS_API_KEY="sua_chave_aqui"
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
URL_BASE = "https://maps.googleapis.com/maps/api/distancematrix/json"


def distancia_rodoviaria(origem_latlon, destino_latlon):
    """Retorna a distancia rodoviaria (km) entre dois pontos via Google Maps.

    origem_latlon / destino_latlon: tuplas (latitude, longitude).
    Retorna None se a chave nao estiver configurada ou em caso de erro,
    permitindo que o chamador use a distancia geografica como fallback.

    Exemplo de uso (quando a chave estiver disponivel):
        km = distancia_rodoviaria((-23.55, -46.63), (-22.91, -47.06))
    """
    if not API_KEY:
        return None
    try:
        import requests  # importado sob demanda para nao exigir a dependencia
        params = {
            "origins": f"{origem_latlon[0]},{origem_latlon[1]}",
            "destinations": f"{destino_latlon[0]},{destino_latlon[1]}",
            "mode": "driving",
            "key": API_KEY,
        }
        resp = requests.get(URL_BASE, params=params, timeout=10)
        dados = resp.json()
        metros = dados["rows"][0]["elements"][0]["distance"]["value"]
        return round(metros / 1000.0, 1)
    except Exception:
        return None
