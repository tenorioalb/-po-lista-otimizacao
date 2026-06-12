# Lista de Otimização Combinatória e Contínua — Pesquisa Operacional

Resolução da lista de exercícios da disciplina de **Otimização Combinatória e Contínua / Pesquisa Operacional** (UFAL).
Professores: Bruno Nogueira e Rian Pinheiro.

Alunos: Otto Tenório e Rômulo Siqueira

A lista tem dois exercícios:

1. **Meta-heurística de solução única (busca local) para o Bin Packing.**
2. **Modelos de Programação Linear (Inteira) vistos em aula.**

Todo o código está em **Python 3**.

---

## Estrutura do repositório

| Arquivo | Descrição |
|---|---|
| `bin_packing_ilp/bin_packing_ils.py` | **Exercício 1** — meta-heurística *Iterated Local Search* (ILS) para o Bin Packing |
| `modelos_cplex.py` | **Exercício 2** — todos os modelos de PLI vistos em aula (17 modelos, via CPLEX/docplex) |
| `bin_packing_ilp/bin_packing_ilp.py` | **Exercício 2 (complemento)** — formulação exata do Bin Packing em PuLP/CBC, usada como comparação para o Exercício 1 |
| `bin_packing_ilp/instancia_exemplo.txt` | Instância pequena (10 itens, ótimo = 4 bins) |
| `bin_packing_ilp/instancia_media.txt` | Instância média (60 itens, ótimo = 28 bins) |
| `RELATORIO.md` | Relatório completo, com a descrição detalhada de cada exercício |
| `lista-opt.pdf` | Enunciado da lista |

---

## Exercício 1 — ILS para o Bin Packing

O **Bin Packing** consiste em distribuir `n` itens em o menor número possível de recipientes (bins) sem
exceder a capacidade `C` de cada um. É um problema NP-difícil.

Foi implementada uma **Iterated Local Search (ILS)**, meta-heurística de solução única que alterna
*busca local* (intensificação) e *perturbação* (diversificação):

- **(a) Representação** — partição dos itens em bins (classe `Solucao`), com cargas e índice item→bin
  mantidos de forma incremental.
- **(b) Função de avaliação** — custo real é o número de bins `k`; a busca é guiada pela aptidão de
  **Falkenauer** `Σ (carga_j / C)²`, que premia bins bem cheios e evita *plateaus*.
- **(c) Busca local** — duas vizinhanças (**movimento** de um item e **troca** entre bins) em estilo VND,
  com aceitação **first** ou **best improvement**.
- **(d) Critério de parada** — **tempo limite em segundos** passado pela linha de comando (também para
  ao atingir o limite inferior `L1 = ⌈Σ tamanhos / C⌉`).

Solução inicial via **First Fit Decreasing (FFD)** e perturbação que esvazia os bins menos cheios.

### Como executar

```bash
python bin_packing_ilp/bin_packing_ils.py <arquivo_instancia> <tempo_limite_seg> [opções]
```

Opções:

| Opção | Efeito |
|---|---|
| `--first` | busca local *first improvement* (padrão) |
| `--best` | busca local *best improvement* |
| `--seed S` | semente do gerador aleatório (padrão 1) |
| `--verbose` | imprime o progresso da busca |

Exemplos:

```bash
python bin_packing_ilp/bin_packing_ils.py bin_packing_ilp/instancia_exemplo.txt 3
python bin_packing_ilp/bin_packing_ils.py bin_packing_ilp/instancia_media.txt 10 --best --seed 42 --verbose
```

Não depende de bibliotecas externas (apenas a biblioteca padrão do Python).

---

## Exercício 2 — Modelos de Programação Linear (Inteira)

O arquivo `modelos_cplex.py` reúne os **17 modelos** vistos em aula, resolvidos com **IBM CPLEX** via `docplex`:

| # | Modelo | # | Modelo |
|---|---|---|---|
| 1 | Ração | 10 | Clique Máxima |
| 2 | Dieta | 11 | Padrões (latinhas) |
| 3 | Plantio | 12 | Facilidades |
| 4 | Tintas | 13 | Frequência (coloração) |
| 5 | Transporte | 14 | Caixeiro Viajante (TSP, MTZ) |
| 6 | Fluxo Máximo | 15 | Roteamento de Veículos (CVRP) |
| 7 | Escalonamento | 16 | Bin Packing |
| 8 | Cobertura | 17 | Caminho Mínimo |
| 9 | Mochila 0/1 | | |

### Como executar

```bash
pip install docplex   # requer o solver IBM CPLEX instalado
python modelos_cplex.py
```

> **Nota.** O `docplex` depende do solver comercial CPLEX. Caso o ambiente não disponha do CPLEX, o
> modelo de Bin Packing também está implementado em **PuLP/CBC** (solver gratuito embutido) em
> `bin_packing_ilp/bin_packing_ilp.py`:
>
> ```bash
> pip install pulp
> python bin_packing_ilp/bin_packing_ilp.py bin_packing_ilp/instancia_exemplo.txt
> ```

---

## Formato das instâncias

Padrão da literatura (Scholl / Falkenauer / BPPLIB):

```
linha 1 : n   (número de itens)
linha 2 : C   (capacidade do recipiente)
n linhas: o tamanho de cada item
```

---

## Resultados

| Instância | Itens | ILS (Exerc. 1) | PLI exato | Ótimo |
|---|---|---|---|---|
| `instancia_exemplo.txt` | 10 | 4 bins | 4 bins (ótimo provado) | **4** |
| `instancia_media.txt` | 60 | 28 bins | 28 bins (ótimo provado) | **28** |

Em ambas as instâncias a ILS encontrou a solução ótima, confirmada de forma independente pelo modelo exato de PLI.

Para mais detalhes, veja o [`RELATORIO.md`](RELATORIO.md).
