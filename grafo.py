# =============================================================================
# GrafoRotas - Infraestrutura do grafo (classe Grafo): lista de adjacencia,
# leitura/gravacao do grafo.txt, busca de vertices por nome, conexidade e
# grafo reduzido.
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
#   2026-09-02 | Guilherme Haddad Borro | Versao inicial (Parte 2): lista de
#                adjacencia, I/O do grafo.txt, insercao/remocao, conexidade
#                por DFS e grafo reduzido.
#   2026-10-18 | Guilherme Haddad Borro | Parte 3: busca de vertice por nome
#                (sem acento/caixa), copia do grafo, lista publica de arestas,
#                validacao do arquivo (erros de formato com numero da linha) e
#                rejeicao de pesos nao positivos.
# =============================================================================

import copy
import unicodedata


def normalizar_texto(texto):
    """Remove acentos, espacos extras e caixa para comparar nomes de cidades.

    Ex.: normalizar_texto("  São  Paulo ") -> "sao paulo"
    """
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


class ErroFormatoArquivo(ValueError):
    """Erro levantado quando o grafo.txt nao segue o formato esperado."""


class Grafo:
    """Grafo nao orientado, ponderado nas arestas, representado por lista de
    adjacencia.

    Estruturas de dados:
      - self.rotulos: dict {id_vertice -> nome/rotulo da cidade}
      - self.adjacencia: dict {id_vertice -> {id_vizinho -> peso}}
        A adjacencia usa dicionario aninhado para permitir consulta,
        insercao e remocao de arestas em tempo medio O(1).
    """

    # Tipo do grafo (primeiro elemento do arquivo grafo.txt).
    # A classificacao segue a categoria adotada no projeto:
    #   2 = nao orientado com peso na aresta (categoria deste projeto)
    #   6 = orientado com peso na aresta
    TIPOS = {
        1: "nao orientado sem peso",
        2: "nao orientado com peso na aresta",
        5: "orientado sem peso",
        6: "orientado com peso na aresta",
    }

    def __init__(self, tipo=2):
        self.tipo = tipo        # tipo/categoria do grafo (ver TIPOS)
        self.rotulos = {}       # id_vertice -> nome da cidade
        self.adjacencia = {}    # id_vertice -> {id_vizinho: peso}

    def descricao_tipo(self):
        """Descricao textual do tipo do grafo."""
        return self.TIPOS.get(self.tipo, "desconhecido")

    def copia(self):
        """Copia independente do grafo (usada nos testes e em simulacoes)."""
        return copy.deepcopy(self)

    # ------------------------------------------------------------------ #
    # Manipulacao de vertices
    # ------------------------------------------------------------------ #
    def inserir_vertice(self, id_vertice, rotulo=""):
        """Insere um novo vertice. Retorna True se inserido, False se ja existe."""
        if id_vertice in self.adjacencia:
            return False
        self.adjacencia[id_vertice] = {}
        self.rotulos[id_vertice] = rotulo
        return True

    def remover_vertice(self, id_vertice):
        """Remove um vertice e todas as arestas incidentes a ele."""
        if id_vertice not in self.adjacencia:
            return False
        # remove as referencias a este vertice nas listas dos vizinhos
        for vizinho in list(self.adjacencia[id_vertice].keys()):
            self.adjacencia[vizinho].pop(id_vertice, None)
        del self.adjacencia[id_vertice]
        self.rotulos.pop(id_vertice, None)
        return True

    # ------------------------------------------------------------------ #
    # Manipulacao de arestas
    # ------------------------------------------------------------------ #
    def inserir_aresta(self, u, v, peso):
        """Insere (ou atualiza) a aresta nao orientada {u, v} com o peso dado.

        Cria os vertices ausentes. Retorna False, sem alterar o grafo, para
        laco (u == v) ou peso nao positivo: distancias rodoviarias sao sempre
        positivas e o algoritmo de Dijkstra exige pesos nao negativos.
        """
        if u == v or peso <= 0:
            return False
        if u not in self.adjacencia:
            self.inserir_vertice(u)
        if v not in self.adjacencia:
            self.inserir_vertice(v)
        self.adjacencia[u][v] = peso
        self.adjacencia[v][u] = peso
        return True

    def remover_aresta(self, u, v):
        """Remove a aresta nao orientada {u, v}, se existir."""
        if u in self.adjacencia and v in self.adjacencia[u]:
            del self.adjacencia[u][v]
            del self.adjacencia[v][u]
            return True
        return False

    # ------------------------------------------------------------------ #
    # Consultas
    # ------------------------------------------------------------------ #
    def numero_vertices(self):
        return len(self.adjacencia)

    def numero_arestas(self):
        return sum(len(viz) for viz in self.adjacencia.values()) // 2

    def grau(self, id_vertice):
        """Grau do vertice (numero de arestas incidentes)."""
        return len(self.adjacencia.get(id_vertice, {}))

    def nome(self, id_vertice):
        """Rotulo do vertice; se nao houver rotulo, devolve o proprio id."""
        return self.rotulos.get(id_vertice) or str(id_vertice)

    def buscar_vertice(self, texto):
        """Localiza um vertice pelo id (numero) ou pelo nome da cidade.

        A comparacao de nomes ignora acentos e maiusculas. Se nao houver nome
        exatamente igual, aceita um trecho do nome desde que ele identifique
        uma unica cidade. Retorna (id, None) em caso de sucesso ou
        (None, mensagem_de_erro) caso contrario.
        """
        texto = str(texto).strip()
        if not texto:
            return None, "nenhum vertice informado"
        if texto.lstrip("-").isdigit():
            vid = int(texto)
            if vid in self.adjacencia:
                return vid, None
            return None, f"vertice [{vid}] nao encontrado"
        alvo = normalizar_texto(texto)
        exatos = [v for v, r in self.rotulos.items() if normalizar_texto(r) == alvo]
        if len(exatos) == 1:
            return exatos[0], None
        parciais = [v for v, r in self.rotulos.items() if alvo in normalizar_texto(r)]
        if len(parciais) == 1:
            return parciais[0], None
        if not parciais:
            return None, f"cidade '{texto}' nao encontrada"
        opcoes = ", ".join(f"[{v}] {self.rotulos[v]}" for v in sorted(parciais)[:6])
        return None, f"'{texto}' e ambiguo; seja mais especifico ({opcoes} ...)"

    # ------------------------------------------------------------------ #
    # Persistencia: leitura e gravacao do arquivo grafo.txt
    # ------------------------------------------------------------------ #
    def ler_arquivo(self, caminho="grafo.txt"):
        """Le o grafo a partir do arquivo texto (formato descrito no relatorio).

        Formato: a primeira linha e o tipo do grafo; a segunda, o numero de
        vertices; seguem N linhas 'id;nome'; depois o numero de arestas; e, por
        fim, M linhas 'id_u;id_v;peso'.

        Levanta ErroFormatoArquivo (com o numero da linha) se o conteudo nao
        seguir o formato; nesse caso o grafo atual NAO e alterado.
        """
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = [(n, ln.strip()) for n, ln in enumerate(f, 1) if ln.strip()]

        novo = Grafo()
        pos = 0

        def proxima(descricao):
            nonlocal pos
            if pos >= len(linhas):
                raise ErroFormatoArquivo(f"fim inesperado do arquivo: faltou {descricao}")
            item = linhas[pos]
            pos += 1
            return item

        try:
            num, txt = proxima("o tipo do grafo")
            novo.tipo = int(txt)
            num, txt = proxima("o numero de vertices")
            n = int(txt)
            for _ in range(n):
                num, txt = proxima("uma linha de vertice")
                partes = txt.split(";")
                novo.inserir_vertice(int(partes[0]), partes[1] if len(partes) > 1 else "")
            num, txt = proxima("o numero de arestas")
            m = int(txt)
            for _ in range(m):
                num, txt = proxima("uma linha de aresta")
                u, v, peso = txt.split(";")
                u, v, peso = int(u), int(v), float(peso)
                if u not in novo.adjacencia or v not in novo.adjacencia:
                    raise ErroFormatoArquivo(f"linha {num}: aresta com vertice nao declarado")
                if not novo.inserir_aresta(u, v, peso):
                    raise ErroFormatoArquivo(f"linha {num}: laco ou peso nao positivo")
        except ValueError as erro:
            if isinstance(erro, ErroFormatoArquivo):
                raise
            raise ErroFormatoArquivo(f"linha {num}: conteudo invalido '{txt}'") from erro

        # so substitui o estado atual depois que o arquivo inteiro foi validado
        self.tipo, self.rotulos, self.adjacencia = novo.tipo, novo.rotulos, novo.adjacencia
        return self

    def gravar_arquivo(self, caminho="grafo.txt"):
        """Grava o estado atual do grafo no arquivo texto."""
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(f"{self.tipo}\n")
            f.write(f"{self.numero_vertices()}\n")
            for id_v in sorted(self.adjacencia):
                f.write(f"{id_v};{self.rotulos.get(id_v, '')}\n")
            arestas = self.lista_arestas()
            f.write(f"{len(arestas)}\n")
            for u, v, peso in arestas:
                f.write(f"{u};{v};{peso}\n")
        return caminho

    def lista_arestas(self):
        """Lista de arestas unicas (u < v) como (u, v, peso), ordenada."""
        return sorted((u, v, peso)
                      for u in self.adjacencia
                      for v, peso in self.adjacencia[u].items() if u < v)

    # mantido por compatibilidade com o codigo da Parte 2
    _lista_arestas = lista_arestas

    # ------------------------------------------------------------------ #
    # Exibicao
    # ------------------------------------------------------------------ #
    def exibir(self, limite=None):
        """Retorna uma representacao textual do grafo (lista de adjacencia)."""
        linhas = [f"Grafo: {self.numero_vertices()} vertices, "
                  f"{self.numero_arestas()} arestas"]
        for i, id_v in enumerate(sorted(self.adjacencia)):
            if limite is not None and i >= limite:
                linhas.append("  ...")
                break
            nome = self.rotulos.get(id_v, "")
            vizinhos = ", ".join(
                f"{self.rotulos.get(w, w)}({p} km)"
                for w, p in sorted(self.adjacencia[id_v].items())
            )
            linhas.append(f"  [{id_v}] {nome} -> {vizinhos}")
        return "\n".join(linhas)

    # ------------------------------------------------------------------ #
    # Conexidade (busca em profundidade)
    # ------------------------------------------------------------------ #
    def _dfs(self, inicio, visitados):
        """Busca em profundidade iterativa a partir de 'inicio'."""
        pilha = [inicio]
        while pilha:
            atual = pilha.pop()
            if atual in visitados:
                continue
            visitados.add(atual)
            for vizinho in self.adjacencia[atual]:
                if vizinho not in visitados:
                    pilha.append(vizinho)

    def componentes_conexas(self):
        """Retorna a lista de componentes conexas (cada uma como conjunto de ids)."""
        visitados = set()
        componentes = []
        for v in self.adjacencia:
            if v not in visitados:
                atual = set()
                self._dfs(v, atual)
                visitados |= atual
                componentes.append(atual)
        return componentes

    def eh_conexo(self):
        """True se o grafo possui uma unica componente conexa."""
        if self.numero_vertices() == 0:
            return True
        return len(self.componentes_conexas()) == 1

    # ------------------------------------------------------------------ #
    # Grafo reduzido
    # ------------------------------------------------------------------ #
    def grafo_reduzido(self):
        """Constroi o grafo reduzido: cada componente conexa vira um supervertice.

        Como o grafo e nao orientado, o grafo reduzido possui um vertice por
        componente conexa e nenhuma aresta entre supervertices (as componentes
        sao, por definicao, desconexas entre si). E util para diagnosticar se a
        malha modelada esta totalmente conectada.
        """
        reduzido = Grafo()
        for i, comp in enumerate(self.componentes_conexas()):
            exemplo = self.rotulos.get(next(iter(comp)), "")
            rotulo = f"Componente {i} ({len(comp)} cidades, ex.: {exemplo})"
            reduzido.inserir_vertice(i, rotulo)
        return reduzido
