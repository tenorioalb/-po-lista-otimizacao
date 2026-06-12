#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelo de Programacao Linear Inteira (PLI) para o Bin Packing.
Disciplina: Otimizacao Combinatoria e Continua / Pesquisa Operacional.
Exercicio 2 da lista.

Formulacao classica (atribuicao item-recipiente):
    minimizar   Sum_j y_j
    sujeito a
      (1) Sum_j x_ij = 1                 cada item em um recipiente
      (2) Sum_i s_i x_ij <= C * y_j      capacidade e abertura do bin
      (3) x_ij, y_j in {0,1}
    quebra de simetria (opcional):
      (4) y_j >= y_{j+1}                  bins usados da esquerda p/ direita
      (5) x_00 = 1                        fixa o item 0 no primeiro bin

Uso:
    python bin_packing_ilp.py <arquivo_instancia> [tempo_limite_seg]

Requer PuLP (inclui o solver CBC):   pip install pulp
"""

import sys
import math

try:
    import pulp
except ImportError:
    sys.exit("ERRO: o pacote 'pulp' nao esta instalado.\n"
             "      Instale com:  pip install pulp")


def ler_instancia(caminho):
    """
    Formato:
        linha 1 : n  -> numero de itens
        linha 2 : C  -> capacidade do recipiente
        linhas seguintes: o tamanho de cada item
    """
    with open(caminho, "r") as arq:
        tokens = arq.read().split()
    if len(tokens) < 2:
        raise ValueError("Arquivo de instancia vazio ou invalido.")
    numeros = [float(t) for t in tokens]
    n = int(numeros[0])
    C = numeros[1]
    tamanhos = numeros[2:2 + n]
    if len(tamanhos) != n:
        raise ValueError("Instancia inconsistente: numero de itens nao confere.")
    return n, C, tamanhos


def limite_superior_ffd(C, tamanhos):
    """First Fit Decreasing: limite superior para o numero de bins.
    Quanto menor, menos variaveis o modelo tem."""
    ordem = sorted(range(len(tamanhos)), key=lambda i: -tamanhos[i])
    carga = []
    for i in ordem:
        for j in range(len(carga)):
            if carga[j] + tamanhos[i] <= C + 1e-9:
                carga[j] += tamanhos[i]
                break
        else:
            carga.append(tamanhos[i])
    return len(carga)


def resolver(n, C, tamanhos, tempo_limite):
    m = limite_superior_ffd(C, tamanhos)             # limite superior de bins
    lb = math.ceil(sum(tamanhos) / C - 1e-9)         # limite inferior L1

    I = range(n)
    J = range(m)

    modelo = pulp.LpProblem("Bin_Packing", pulp.LpMinimize)

    x = {(i, j): pulp.LpVariable("x_%d_%d" % (i, j), cat="Binary")
         for i in I for j in J}
    y = {j: pulp.LpVariable("y_%d" % j, cat="Binary") for j in J}

    modelo += pulp.lpSum(y[j] for j in J), "numero_de_recipientes"

    for i in I:
        modelo += pulp.lpSum(x[i, j] for j in J) == 1, "atribuicao_item_%d" % i

    for j in J:
        modelo += (pulp.lpSum(tamanhos[i] * x[i, j] for i in I) <= C * y[j],
                   "capacidade_bin_%d" % j)

    for j in range(m - 1):
        modelo += y[j] >= y[j + 1], "simetria_%d" % j

    if n > 0:
        modelo += x[0, 0] == 1, "fixa_item_0"

    solver = pulp.PULP_CBC_CMD(
        msg=False,
        timeLimit=(tempo_limite if tempo_limite and tempo_limite > 0 else None))
    modelo.solve(solver)

    status = pulp.LpStatus[modelo.status]

    bins = []
    valor = pulp.value(modelo.objective)
    if valor is not None:
        for j in J:
            conteudo = [i for i in I
                        if pulp.value(x[i, j]) is not None
                        and pulp.value(x[i, j]) > 0.5]
            if conteudo:
                bins.append(conteudo)

    return status, bins, lb, m


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python bin_packing_ilp.py <arquivo_instancia> "
                 "[tempo_limite_seg]")
    caminho = sys.argv[1]
    tempo = float(sys.argv[2]) if len(sys.argv) > 2 else 0   # 0 = sem limite

    n, C, tamanhos = ler_instancia(caminho)

    print("=" * 64)
    print(" Bin Packing  -  Modelo de Programacao Linear Inteira (PLI)")
    print("=" * 64)
    print(" Instancia          : %s" % caminho)
    print(" Numero de itens    : %d" % n)
    print(" Capacidade do bin  : %g" % C)
    print(" Tempo limite       : %s"
          % ("%g s" % tempo if tempo else "sem limite"))
    print(" Solver             : CBC (via PuLP)")
    print("-" * 64)

    status, bins, lb, ub = resolver(n, C, tamanhos, tempo)

    print(" Status do solver   : %s" % status)
    print(" Limite inferior    : %d" % lb)
    print(" Limite superior FFD: %d   (qtd. de bins modelados)" % ub)
    if bins:
        print(" Recipientes usados : %d" % len(bins))
        if status == "Optimal":
            print("   >>> solucao OTIMA comprovada pelo solver")
        else:
            print("   (solucao viavel encontrada; otimalidade nao comprovada "
                  "dentro do tempo)")
        print("-" * 64)
        print(" Alocacao  (bin: itens  ->  [carga / capacidade]):")
        for j, b in enumerate(bins):
            carga = sum(tamanhos[i] for i in b)
            itens = ", ".join(str(i) for i in sorted(b))
            print("   bin %3d: %-44s [%g / %g]" % (j + 1, itens, carga, C))
    else:
        print(" Nenhuma solucao foi encontrada.")
    print("=" * 64)


if __name__ == "__main__":
    main()
