# Lista de Exercícios — Otimização Combinatória e Contínua / Pesquisa Operacional

Professores: Bruno Nogueira e Rian Pinheiro

Este relatório documenta a solução dos dois exercícios da lista. Todo o código foi escrito em **Python 3**. O Exercício 1 não depende de bibliotecas externas; o Exercício 2 reúne todos os modelos de PLI vistos em aula (`modelos_cplex.py`, com **CPLEX/docplex**) e, adicionalmente, uma formulação de Bin Packing em **PuLP** que serve como método exato de comparação para o Exercício 1.

## Arquivos entregues

| Arquivo | Descrição |
|---|---|
| `bin_packing_ils.py` | Exercício 1 — meta-heurística *Iterated Local Search* para o Bin Packing |
| `modelos_cplex.py` | Exercício 2 — todos os modelos de Programação Linear (Inteira) vistos em aula |
| `bin_packing_ilp.py` | Exercício 2 (complemento) — formulação de PLI do Bin Packing em PuLP, usada como método exato de comparação para o Exercício 1 |
| `instancia_exemplo.txt` | Instância pequena (10 itens, ótimo conhecido = 4 bins) |
| `instancia_media.txt` | Instância média (60 itens, ótimo = 28 bins) |
| `RELATORIO.md` | Este documento |

> **Observação sobre os caminhos.** `modelos_cplex.py` está na pasta `lista/`; os demais arquivos (`bin_packing_ils.py`, `bin_packing_ilp.py`, instâncias e este relatório) estão em `lista/bin_packing_ilp/`.

---

# Exercício 1 — Meta-heurística de solução única para o Bin Packing

Foi implementada uma **Iterated Local Search (ILS)**, que é uma meta-heurística de solução única: ela mantém uma única solução corrente e a melhora alternando duas etapas — uma *busca local* (intensificação) e uma *perturbação* (diversificação para escapar de ótimos locais).

O esqueleto do algoritmo é:

```
s  <- solução inicial (First Fit Decreasing)
s  <- busca_local(s)
melhor <- s
repita enquanto houver tempo:
    s' <- perturbação(melhor)
    s' <- busca_local(s')
    se s' for melhor que 'melhor':   melhor <- s'
retorne melhor
```

## (a) Representação da solução

Uma solução é uma **partição dos itens em recipientes (bins)**. Ela é modelada na classe `Solucao` com três estruturas:

- `bins`: lista de listas — `bins[j]` contém os índices dos itens alocados no recipiente `j`;
- `carga`: lista — `carga[j]` é a soma dos tamanhos dos itens do bin `j`;
- `bin_de`: dicionário — `bin_de[i]` indica em qual bin está o item `i`.

As estruturas `carga` e `bin_de` são redundantes em relação a `bins`, mas mantê-las sempre atualizadas permite **avaliar cada movimento de forma incremental** (em tempo constante), sem recalcular a solução inteira a cada passo — o que torna a busca local muito mais rápida.

Toda solução manipulada é, por construção, **viável**: cada item aparece em exatamente um bin e nenhum bin ultrapassa a capacidade. Movimentos que violariam a capacidade são simplesmente descartados.

## (b) Função de avaliação

O **custo real** de uma solução é o **número de recipientes usados** (`k`), que deve ser minimizado. Esse é o valor reportado como resultado final.

No entanto, usar apenas `k` para *guiar* a busca local é ineficiente: a grande maioria dos movimentos (mover ou trocar um item) não altera `k`. Isso cria um relevo de busca cheio de *plateaus* (regiões planas), em que a busca não tem direção para seguir.

Por isso, a busca é guiada por uma **função de avaliação auxiliar**, a aptidão de **Falkenauer (1996)**:

```
fitness = (1/m) · Σ (carga_j / C)²          (a MAXIMIZAR)
```

onde `m` é o número de bins e `C` a capacidade. Essa função premia recipientes **bem cheios** e penaliza recipientes quase vazios. Concentrar carga em poucos bins (deixando outros quase vazios) aumenta o `fitness` e leva, de forma natural, à **eliminação de bins**.

A comparação entre duas soluções usa a ordem **lexicográfica**: (1) vence quem usa menos bins; (2) em caso de empate, vence quem tem maior `Σ (carga_j / C)²`. Internamente, a busca local maximiza diretamente `Σ (carga_j / C)²`, pois um movimento que aumenta essa soma move a solução na direção de esvaziar algum recipiente.

## (c) Estratégia de busca local

Foram definidas **duas vizinhanças**:

- **Movimento** — retira um item de um bin e o coloca em outro bin onde ele caiba;
- **Troca** — troca um item do bin A por um item do bin B, desde que ambos continuem respeitando a capacidade.

Um movimento é **melhorante** quando aumenta `Σ (carga_j / C)²`. Sempre que um recipiente fica vazio, ele é descartado e `k` diminui.

A busca local suporta as duas estratégias de aceitação pedidas no enunciado, escolhidas por linha de comando:

- `--first` (**first improvement**, padrão) — aplica o **primeiro** movimento melhorante encontrado;
- `--best` (**best improvement**) — varre toda a vizinhança e aplica o **melhor** movimento.

As duas vizinhanças são combinadas no estilo **VND** (*Variable Neighborhood Descent*): explora-se a vizinhança de movimento até o esgotamento; passa-se então à vizinhança de troca; e, sempre que uma troca melhora a solução, retorna-se à vizinhança de movimento. A busca local termina em um **ótimo local** quando nenhuma das duas vizinhanças oferece melhora.

**Componentes adicionais da ILS:**

- *Solução inicial* — heurística construtiva **First Fit Decreasing (FFD)**: ordena os itens por tamanho decrescente e coloca cada um no primeiro bin em que couber.
- *Perturbação* — escolhe os 2–3 recipientes **menos cheios**, remove todos os seus itens e os reinsere em ordem aleatória via *First Fit*. Esvaziar os bins menos cheios é estratégico, pois são os candidatos naturais a desaparecer.
- *Critério de aceitação* — *better acceptance*: a perturbação sempre parte da melhor solução conhecida, que só é substituída quando há melhora.

## (d) Critério de parada

O algoritmo recebe um **tempo limite em segundos pela linha de comando** (segundo argumento obrigatório). O laço principal da ILS — e também os laços internos da busca local — verificam o relógio e encerram assim que o tempo se esgota, devolvendo a melhor solução encontrada até então.

Como critério de parada antecipada, o algoritmo também para se atingir o **limite inferior** `L1 = ⌈Σ tamanhos / C⌉`: nesse caso a solução é comprovadamente ótima e não há motivo para continuar.

## Como executar (Exercício 1)

```
python bin_packing_ils.py <arquivo_instancia> <tempo_limite_seg> [opções]

Opções:
  --first        busca local first improvement (padrão)
  --best         busca local best improvement
  --seed S       semente do gerador aleatório (padrão 1)
  --verbose      imprime o progresso da busca

Exemplos:
  python bin_packing_ils.py instancia_exemplo.txt 3
  python bin_packing_ils.py instancia_media.txt 10 --best --seed 42 --verbose
```

---

# Exercício 2 — Modelos de Programação Linear (Inteira)

O enunciado pede "todos os modelos de PLI vistos em aula". Eles foram implementados no arquivo **`modelos_cplex.py`**, usando o **IBM CPLEX** através do pacote `docplex`. O arquivo é executável diretamente (`python modelos_cplex.py`) e resolve, em sequência, os 17 modelos abaixo, imprimindo a solução de cada um:

| # | Modelo | Tipo de PL | Variáveis |
|---|---|---|---|
| 1 | Problema da Ração | Linear contínua (máx. lucro) | contínuas |
| 2 | Problema da Dieta | Linear contínua (mín. custo) | contínuas |
| 3 | Problema do Plantio | Linear contínua (máx. lucro) | contínuas |
| 4 | Problema das Tintas | Linear contínua (mín. custo) | contínuas |
| 5 | Problema do Transporte | Linear contínua (mín. custo) | contínuas |
| 6 | Problema do Fluxo Máximo | Linear contínua (máx. fluxo) | contínuas |
| 7 | Escalonamento de Horários | Inteira (mín. recursos) | inteiras |
| 8 | Problema de Cobertura | Inteira binária (*set covering*) | binárias |
| 9 | Problema da Mochila 0/1 | Inteira binária (máx. valor) | binárias |
| 10 | Clique Máxima | Inteira binária | binárias |
| 11 | Problema de Padrões (Latinhas) | Inteira mista | inteiras + auxiliar |
| 12 | Problema das Facilidades | Inteira binária (*facility location*) | binárias |
| 13 | Problema de Frequência (coloração) | Inteira binária | binárias |
| 14 | Caixeiro Viajante (TSP) | Inteira binária, sub-rotas por MTZ | binárias + posição |
| 15 | Roteamento de Veículos (CVRP) | Inteira mista, capacidade por carga | binárias + carga |
| 16 | Empacotamento (Bin Packing) | Inteira binária | binárias |
| 17 | Caminho Mínimo | Inteira binária (fluxo unitário) | binárias |

Cada modelo encapsula seus próprios dados de instância (didáticos) e segue o mesmo padrão: definição das variáveis de decisão, função objetivo, restrições e impressão da solução ótima. Modelos sobre grafos (TSP, CVRP, fluxo, caminho mínimo, clique, frequência) usam formulações clássicas — eliminação de sub-rotas via **MTZ** no TSP, controle de capacidade por carga acumulada no CVRP, e conservação de fluxo nos problemas de fluxo/caminho.

### Como executar (`modelos_cplex.py`)

```
# requer IBM CPLEX + docplex:
pip install docplex

python modelos_cplex.py
```

> **Nota de portabilidade.** O `docplex` depende do solver comercial CPLEX. Caso o ambiente de correção não disponha do CPLEX, o modelo de Bin Packing está também implementado em PuLP/CBC (solver gratuito embutido) em `bin_packing_ilp.py`, documentado a seguir; os demais modelos podem ser portados para PuLP no mesmo padrão, se necessário.

## Formulação do modelo de Bin Packing (em PuLP)

Além dos modelos acima, a **formulação de PLI do Bin Packing** está implementada de forma independente em `bin_packing_ilp.py`, usando PuLP/CBC. Ela serve como **método exato de comparação** para avaliar a qualidade da meta-heurística do Exercício 1 (ver a seção de resultados ao final).

**Conjuntos e dados**

- `I = {0,…,n−1}` — itens; `J = {0,…,m−1}` — recipientes disponíveis (`m` é um limite superior para o número de bins);
- `s_i` — tamanho do item `i`; `C` — capacidade de cada recipiente.

**Variáveis de decisão (binárias)**

- `y_j = 1` se o recipiente `j` é utilizado, `0` caso contrário;
- `x_ij = 1` se o item `i` é colocado no recipiente `j`, `0` caso contrário.

**Modelo**

```
minimizar    Σ_j  y_j

sujeito a
  (1)  Σ_j  x_ij = 1                para todo i        (cada item em exatamente um bin)
  (2)  Σ_i  s_i · x_ij ≤ C · y_j    para todo j        (capacidade; só usa o bin se y_j = 1)
  (3)  x_ij ∈ {0,1},  y_j ∈ {0,1}
```

**Restrições de quebra de simetria** (opcionais; aceleram o solver eliminando soluções equivalentes que diferem apenas na numeração dos bins):

```
  (4)  y_j ≥ y_{j+1}    para j = 0,…,m−2   (bins usados "da esquerda para a direita")
  (5)  x_00 = 1                            (o item 0 é fixado no primeiro bin)
```

O número de bins modelados (`m`) é obtido pela heurística FFD: quanto menor esse limite superior, menos variáveis o modelo tem. O modelo é resolvido pelo solver **CBC**, embutido no PuLP.

## Como executar (Bin Packing em PuLP)

```
# instalação única da dependência:
pip install pulp

python bin_packing_ilp.py <arquivo_instancia> [tempo_limite_seg]

Exemplos:
  python bin_packing_ilp.py instancia_exemplo.txt
  python bin_packing_ilp.py instancia_media.txt 60
```

---

# Formato das instâncias

Ambos os programas leem o mesmo formato, padrão na literatura (Scholl / Falkenauer / BPPLIB):

```
linha 1 : n   (número de itens)
linha 2 : C   (capacidade do recipiente)
n linhas: o tamanho de cada item
```

O leitor é tolerante a espaços e quebras de linha extras. Tamanhos inteiros ou fracionários são aceitos (basta que `0 ≤ s_i ≤ C`).

# Resultados dos testes

| Instância | Itens | ILS (Exerc. 1) | PLI (Exerc. 2) | Ótimo |
|---|---|---|---|---|
| `instancia_exemplo.txt` | 10 | 4 bins | 4 bins (ótimo provado) | **4** |
| `instancia_media.txt` | 60 | 28 bins | 28 bins (ótimo provado) | **28** |

Em ambas as instâncias a meta-heurística ILS encontrou a **solução ótima**, confirmada de forma independente pelo modelo exato de PLI. Na instância média, o limite inferior trivial `L1` vale 27, mas o solver provou que o ótimo real é 28 — ou seja, a ILS atingiu o melhor valor possível.
