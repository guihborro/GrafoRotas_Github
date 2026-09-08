# GrafoRotas - Menu interativo das funcionalidades da infraestrutura do grafo.
# Teoria dos Grafos | Bacharelado em Ciencia da Computacao
# Integrantes: Guilherme Haddad Borro - RA 10427699 | Rafael Lima - RA 10425819 | Pedro Augusto Yoshikuni - RA 10410287 | Tiago Silveira Lopes - RA 10417600
# Historico: 2026-09-02

import os
from grafo import Grafo

ARQUIVO = "grafo.txt"
LINHA = "=" * 60


def ler(msg=""):
    """Le uma linha do usuario. Em fim de entrada (EOF), encerra o programa."""
    try:
        return input(msg)
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
    """Le um numero real; retorna None se o valor for invalido."""
    valor = ler(msg).strip().replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        print("  Valor invalido: informe um numero.")
        return None


def carregar():
    """Carrega o grafo de grafo.txt, ou devolve um grafo vazio se nao existir."""
    if os.path.exists(ARQUIVO):
        g = Grafo().ler_arquivo(ARQUIVO)
        print(f"Grafo carregado de '{ARQUIVO}'.")
        return g
    print(f"Arquivo '{ARQUIVO}' nao encontrado. Iniciando com grafo vazio.")
    print("(Dica: rode 'python coletar_dados.py' para gerar a base real.)")
    return Grafo()


def cabecalho(g):
    print("\n" + LINHA)
    print("GrafoRotas - Menu de Operacoes")
    print(f"Tipo {g.tipo} ({g.descricao_tipo()}) | "
          f"{g.numero_vertices()} vertices | {g.numero_arestas()} arestas")
    print(LINHA)


def menu():
    print(" 1. Exibir grafo")
    print(" 2. Inserir vertice")
    print(" 3. Remover vertice")
    print(" 4. Inserir aresta")
    print(" 5. Remover aresta")
    print(" 6. Consultar grau de um vertice")
    print(" 7. Determinar conexidade (componentes conexas)")
    print(" 8. Construir grafo reduzido")
    print(" 9. Estatisticas da malha")
    print("10. Gravar grafo em arquivo")
    print("11. Recarregar grafo de grafo.txt")
    print(" 0. Sair")


# --------------------------------------------------------------------------- #
# Acoes do menu
# --------------------------------------------------------------------------- #
def op_exibir(g):
    entrada = ler("Quantos vertices exibir? (Enter = 10, 'tudo' = todos) ").strip().lower()
    if entrada == "tudo":
        print(g.exibir())
    elif entrada == "":
        print(g.exibir(limite=10))
    else:
        try:
            print(g.exibir(limite=int(entrada)))
        except ValueError:
            print(g.exibir(limite=10))


def op_inserir_vertice(g):
    vid = ler_int("ID do novo vertice: ")
    if vid is None:
        return
    nome = ler("Nome/rotulo da cidade: ").strip()
    if g.inserir_vertice(vid, nome):
        print(f"  Vertice [{vid}] '{nome}' inserido. "
              f"Total: {g.numero_vertices()} vertices.")
    else:
        print(f"  Vertice [{vid}] ja existe.")


def op_remover_vertice(g):
    vid = ler_int("ID do vertice a remover: ")
    if vid is None:
        return
    if g.remover_vertice(vid):
        print(f"  Vertice [{vid}] removido (e suas arestas). "
              f"Total: {g.numero_vertices()} vertices, {g.numero_arestas()} arestas.")
    else:
        print(f"  Vertice [{vid}] nao encontrado.")


def op_inserir_aresta(g):
    u = ler_int("ID de origem: ")
    v = ler_int("ID de destino: ")
    if u is None or v is None:
        return
    peso = ler_float("Peso (distancia em km): ")
    if peso is None:
        return
    if g.inserir_aresta(u, v, peso):
        print(f"  Aresta ({u},{v}) com peso {peso} km inserida. "
              f"Total: {g.numero_arestas()} arestas.")
    else:
        print("  Nao foi possivel inserir (laco nao permitido).")


def op_remover_aresta(g):
    u = ler_int("ID de origem: ")
    v = ler_int("ID de destino: ")
    if u is None or v is None:
        return
    if g.remover_aresta(u, v):
        print(f"  Aresta ({u},{v}) removida. "
              f"Total: {g.numero_arestas()} arestas.")
    else:
        print(f"  Aresta ({u},{v}) nao encontrada.")


def op_grau(g):
    vid = ler_int("ID do vertice: ")
    if vid is None:
        return
    if vid in g.adjacencia:
        print(f"  Grau do vertice [{vid}] '{g.rotulos.get(vid, '')}': {g.grau(vid)}")
    else:
        print(f"  Vertice [{vid}] nao encontrado.")


def op_conexidade(g):
    comps = g.componentes_conexas()
    print(f"  O grafo e conexo? {'SIM' if g.eh_conexo() else 'NAO'}")
    print(f"  Numero de componentes conexas: {len(comps)}")
    tamanhos = sorted((len(c) for c in comps), reverse=True)
    print(f"  Tamanho das componentes: {tamanhos}")


def op_reduzido(g):
    print(g.grafo_reduzido().exibir())


def op_estatisticas(g):
    if g.numero_vertices() == 0:
        print("  Grafo vazio.")
        return
    graus = [g.grau(v) for v in g.adjacencia]
    print(f"  Grau minimo: {min(graus)} | Grau maximo: {max(graus)} | "
          f"Grau medio: {sum(graus) / len(graus):.2f}")
    mais = max(g.adjacencia, key=lambda v: g.grau(v))
    print(f"  Cidade mais conectada: {g.rotulos[mais]} ({g.grau(mais)} ligacoes)")


def op_gravar(g):
    destino = ler("Nome do arquivo (Enter = grafo_salvo.txt): ").strip() or "grafo_salvo.txt"
    g.gravar_arquivo(destino)
    print(f"  Grafo gravado em '{destino}'.")


# --------------------------------------------------------------------------- #
# Laco principal
# --------------------------------------------------------------------------- #
def main():
    g = carregar()
    acoes = {
        "1": op_exibir,
        "2": op_inserir_vertice,
        "3": op_remover_vertice,
        "4": op_inserir_aresta,
        "5": op_remover_aresta,
        "6": op_grau,
        "7": op_conexidade,
        "8": op_reduzido,
        "9": op_estatisticas,
        "10": op_gravar,
    }
    while True:
        cabecalho(g)
        menu()
        escolha = ler("Escolha uma opcao: ").strip()
        if escolha == "0":
            print("Encerrando. Ate mais!")
            break
        if escolha == "11":
            g = carregar()
            continue
        acao = acoes.get(escolha)
        if acao is None:
            print("  Opcao invalida.")
            continue
        acao(g)


if __name__ == "__main__":
    main()
