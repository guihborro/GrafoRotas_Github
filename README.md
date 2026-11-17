# GrafoRotas

**Rotas de menor distância entre municípios paulistas** com **Teoria dos Grafos**,
dados oficiais do **IBGE** e do **OpenStreetMap**.

Projeto da disciplina de Teoria dos Grafos (6º semestre), Bacharelado em Ciência da
Computação, Universidade Presbiteriana Mackenzie. Professor: Prof. Dr. Ivan Carlos
Alcântara de Oliveira.

## Integrantes

- Guilherme Haddad Borro (RA 10427699)
- Rafael Lima (RA 10425819)
- Pedro Augusto Yoshikuni (RA 10410287)
- Tiago Silveira Lopes (RA 10417600)

## Descrição

Cada **vértice** é um município e cada **aresta** é a ligação entre duas cidades vizinhas,
ponderada pela **distância rodoviária** entre elas (OSRM/OpenStreetMap). O grafo é **não
orientado com peso na aresta** (categoria 2), com **215 vértices e 643 arestas**: os municípios
das Regiões Geográficas Intermediárias de São Paulo, Sorocaba e Campinas (IBGE, 2017).

- **Problema central:** caminho de menor distância entre duas cidades, resolvido com o
  **algoritmo de Dijkstra** e conferido por Floyd-Warshall para todos os pares.
- **Análise complementar:** árvore geradora mínima (**Prim**), conferida por Kruskal.
- **Características do grafo:** graus, coloração (Welsh-Powell + clique máxima), euleriano,
  hamiltoniano, pontos de articulação e pontes, planaridade e excentricidade/centro.

### Principais resultados

| Característica | Resultado |
|---|---|
| Conexidade | conexo, biconexo (0 articulações, 0 pontes) |
| Graus | mínimo 5, máximo 9, média 5,98 |
| Número cromático | exatamente 6 (Welsh-Powell = 6 e clique K6) |
| Euleriano | não (124 vértices de grau ímpar) |
| Hamiltoniano | sim: ciclo encontrado e verificado (6.912,7 km) |
| Planar | não (643 > 3n − 6 = 639 e contém K5) |
| Raio / diâmetro | 328,5 km (centro: Iperó) / 653,4 km (Barra do Turvo ↔ Mococa) |
| Árvore geradora mínima | 214 arestas, 3.944,0 km |
| São Paulo → Campinas (Dijkstra) | 135,2 km, 8 trechos |

## Estrutura dos arquivos

| Arquivo | Descrição |
|---|---|
| `main.py` | Menu da aplicação (título + 21 opções) |
| `grafo.py` | Classe `Grafo`: lista de adjacência, leitura/gravação do `grafo.txt`, busca por nome, conexidade, grafo reduzido |
| `algoritmos.py` | Parte 3: Dijkstra, Prim, graus, coloração, euleriano, hamiltoniano, Tarjan, planaridade, excentricidade |
| `testes.py` | 48 testes automatizados (no mínimo 2 por opção do menu); gera `resultados_testes.txt` |
| `coletar_dados.py` | Coleta IBGE + OpenStreetMap; gera `grafo.txt`, `cidades.csv` e `coleta_metadados.json` |
| `gerar_imagens.py` | Figuras do relatório (pasta `imagens/`) |
| `google_maps_api.py` | Integração opcional com o Google Maps (alternativa ao OSM) |
| `grafo.txt` | Grafo modelado (vértices + arestas ponderadas) |
| `cidades.csv` | id, nome, código IBGE, latitude e longitude de cada município |
| `coleta_metadados.json` | Parâmetros, data e verificação da coleta (reprodutibilidade) |
| `resultados_testes.txt` | Entrada, saída e veredito de cada teste |
| `Relatorio_GrafoRotas_Parte3.docx` | Relatório final (Parte 3) |
| `Rubrica_GrafoRotas_Parte3.docx` | Rubrica preenchida (Parte 3) |
| `Relatorio_GrafoRotas_Parte2_Pronta.docx`, `Rubrica_GrafoRotas_Parte2_Pronta.docx` | Entregas da Parte 2 |

## Menu da aplicação

```
======================================================================
   GrafoRotas - Rotas de Menor Distancia entre Municipios Paulistas
Tipo 2 (nao orientado com peso na aresta) | 215 vertices | 643 arestas
======================================================================
 Infraestrutura do grafo
  1. Exibir grafo (lista de adjacencia)
  2. Mostrar conteudo do arquivo (grafo.txt)
  3. Inserir vertice              4. Remover vertice
  5. Inserir aresta               6. Remover aresta
  7. Consultar grau de um vertice
  8. Determinar conexidade        9. Construir grafo reduzido
 10. Gravar grafo em arquivo     11. Recarregar grafo de arquivo
 Solucao do problema: rotas de menor distancia
 12. Caminho minimo entre duas cidades (Dijkstra)
 13. Distancias minimas a partir de uma cidade (Dijkstra)
 14. Arvore geradora minima da malha (Prim)
 Caracteristicas do grafo
 15. Grau dos vertices (sequencia e distribuicao)
 16. Coloracao de vertices (Welsh-Powell)
 17. Grafo euleriano / percurso euleriano
 18. Grafo hamiltoniano / ciclo hamiltoniano
 19. Pontos de articulacao e pontes (cidades/ligacoes criticas)
 20. Planaridade
 21. Excentricidade, raio, diametro e centro
  0. Sair
```

As cidades podem ser informadas pelo **nome** (sem acento, sem diferenciar maiúsculas) ou pelo id.

## Formato do `grafo.txt`

```
T                     # tipo do grafo (2 = nao orientado com peso na aresta)
N                     # numero de vertices
id;nome_da_cidade     # N linhas
...
M                     # numero de arestas
id_u;id_v;peso_km     # M linhas (peso = distancia rodoviaria, km)
```

## Como executar

Requer Python 3.8+.

```bash
pip install -r requirements.txt
python main.py              # menu da aplicacao
python testes.py            # 48 testes; grava resultados_testes.txt
python gerar_imagens.py     # figuras em imagens/
python coletar_dados.py     # nova coleta (internet; ~15-20 min)
```

O menu e os testes usam apenas a biblioteca padrão; `requests` (coleta) e `matplotlib`
(figuras) só são necessários para os scripts correspondentes.

## Coleta e reprodutibilidade

Parâmetros: regiões intermediárias São Paulo, Sorocaba e Campinas; K = 5 vizinhos mais
próximos (haversine); Nominatim com a consulta `"<município>, Sao Paulo, Brasil"` (limit=10,
preferindo o resultado de mesmo nome do tipo city/town/village, isto é, a sede urbana); OSRM
perfil `driving`, com até 3 tentativas por consulta; pausa de 1,1 s entre chamadas. A base atual
foi coletada em **16/11/2026, das 20:08 às 20:39**. Tudo isso está em `coleta_metadados.json`,
que o script grava automaticamente a cada coleta.

Comparada com a base da Parte 2, a nova coleta manteve os 215 municípios e 642 das 643
ligações, com 575 pesos idênticos e diferença média de 0,8 km nos demais. Uma primeira
reexecução mostrou que o OpenStreetMap passou a devolver, para 30 municípios, o ponto do limite
municipal em vez da sede urbana; o script foi corrigido para escolher a sede.

O critério de K vizinhos **não garante** conexidade; por isso `coletar_dados.py` acrescenta,
se necessário, a ligação mais curta entre componentes desconexas. Na coleta atual nenhuma
aresta extra foi necessária, e o teste `test_00a` confirma que as 643 arestas são reproduzidas
exatamente a partir de `cidades.csv`.

## Links

- Repositório: https://github.com/guihborro/GrafoRotas_Github
- Vídeo (YouTube): _a inserir_
