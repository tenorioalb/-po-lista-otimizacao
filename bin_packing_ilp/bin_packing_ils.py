#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iterated Local Search (ILS) para o Bin Packing.
Disciplina: Otimizacao Combinatoria e Continua / Pesquisa Operacional.
Exercicio 1 da lista.

Uso:
    python bin_packing_ils.py <arquivo_instancia> <tempo_limite_seg> [opcoes]

Opcoes:
    --first        busca local com FIRST improvement   (padrao)
    --best         busca local com BEST  improvement
    --seed S       semente do gerador aleatorio        (padrao 1)
    --verbose      imprime o progresso da busca

Exemplos:
    python bin_packing_ils.py instancia_exemplo.txt 5
    python bin_packing_ils.py instancia_media.txt 10 --best --seed 42 --verbose
"""

import sys
import time
import math
import random
import argparse


# ---------------------------------------------------------------------------
# 1. Leitura da instancia
# ---------------------------------------------------------------------------
def ler_instancia(caminho):
    """
    Formato (padrao Scholl / Falkenauer / BPPLIB):
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
        raise ValueError(
            "Instancia inconsistente: declarados %d itens, encontrados %d."
            % (n, len(tamanhos)))
    for s in tamanhos:
        if s < 0 or s > C:
            raise ValueError("Item com tamanho invalido (deve valer 0 <= s <= C).")
    return n, C, tamanhos


# ---------------------------------------------------------------------------
# 2. Representacao da solucao
# ---------------------------------------------------------------------------
class Solucao:
    """
    Particao dos itens em recipientes (bins).
        bins   : bins[j] = indices dos itens no recipiente j
        carga  : carga[j] = soma dos tamanhos dos itens do bin j
        bin_de : bin_de[i] = indice do bin que contem o item i

    'carga' e 'bin_de' sao redundantes, mas mante-los atualizados permite
    avaliar cada movimento de forma incremental.
    """

    def __init__(self, C, tamanhos):
        self.C = C
        self.tamanhos = tamanhos
        self.bins = []
        self.carga = []
        self.bin_de = {}

    @staticmethod
    def a_partir_de_bins(C, tamanhos, lista_bins):
        """Constroi uma Solucao descartando bins vazios e recalculando
        'carga' e 'bin_de'."""
        s = Solucao(C, tamanhos)
        s.bins = [list(b) for b in lista_bins if len(b) > 0]
        s.carga = [sum(tamanhos[i] for i in b) for b in s.bins]
        s.bin_de = {}
        for j, b in enumerate(s.bins):
            for i in b:
                s.bin_de[i] = j
        return s

    def copia(self):
        return Solucao.a_partir_de_bins(self.C, self.tamanhos, self.bins)

    def num_bins(self):
        return len(self.bins)

    def soma_quadrados(self):
        """Sum_j (carga_j / C)^2."""
        C = self.C
        return sum((c / C) ** 2 for c in self.carga)


# ---------------------------------------------------------------------------
# 3. Funcao de avaliacao
# ---------------------------------------------------------------------------
# O custo real e o numero de bins (k), mas usar apenas k cria plateaus na
# busca local. Usamos a aptidao de Falkenauer (1996) para GUIAR a busca:
#
#     fitness = (1/m) * Sum_j (carga_j / C)^2          (maximizar)
#
# Ela premia bins bem cheios; concentrar carga em poucos bins leva,
# naturalmente, a eliminacao de bins. Para comparar duas solucoes usamos
# ordem lexicografica: (1) menor numero de bins; (2) maior soma de quadrados.
# ---------------------------------------------------------------------------
EPS = 1e-9


def fitness_falkenauer(sol, expoente=2):
    """Aptidao de Falkenauer (quanto maior, melhor)."""
    m = sol.num_bins()
    if m == 0:
        return 0.0
    C = sol.C
    return sum((c / C) ** expoente for c in sol.carga) / m


def melhor_que(sol_a, sol_b):
    """True se sol_a e estritamente melhor que sol_b (criterio lexicografico)."""
    ka, kb = sol_a.num_bins(), sol_b.num_bins()
    if ka != kb:
        return ka < kb
    return sol_a.soma_quadrados() > sol_b.soma_quadrados() + EPS


def limite_inferior(C, tamanhos):
    """Limite inferior trivial L1 = teto(soma dos tamanhos / C)."""
    return math.ceil(sum(tamanhos) / C - EPS)


# ---------------------------------------------------------------------------
# 4. Solucao inicial - First Fit Decreasing (FFD)
# ---------------------------------------------------------------------------
def first_fit_decreasing(C, tamanhos):
    """Ordena os itens por tamanho decrescente e coloca cada um no primeiro
    bin em que couber; abre um novo bin se nao couber em nenhum."""
    ordem = sorted(range(len(tamanhos)), key=lambda i: -tamanhos[i])
    bins = []
    carga = []
    for i in ordem:
        colocado = False
        for j in range(len(bins)):
            if carga[j] + tamanhos[i] <= C + EPS:
                bins[j].append(i)
                carga[j] += tamanhos[i]
                colocado = True
                break
        if not colocado:
            bins.append([i])
            carga.append(tamanhos[i])
    return Solucao.a_partir_de_bins(C, tamanhos, bins)


# ---------------------------------------------------------------------------
# 5. Busca local (VND: MOVIMENTO + TROCA)
# ---------------------------------------------------------------------------
# MOVIMENTO: retira um item de um bin e o coloca em outro onde caiba.
# TROCA    : troca um item do bin A por um do bin B, respeitando a capacidade.
# Um movimento e melhorante quando aumenta Sum (carga_j / C)^2. Bins vazios
# sao descartados (k diminui). Estrategia de aceitacao: first ou best.
# ---------------------------------------------------------------------------
def _delta_quadrados_move(C, carga_o, carga_d, s):
    """Variacao de Sum (carga/C)^2 ao mover um item de tamanho s do bin de
    carga 'carga_o' para o de carga 'carga_d'."""
    antes = (carga_o / C) ** 2 + (carga_d / C) ** 2
    depois = ((carga_o - s) / C) ** 2 + ((carga_d + s) / C) ** 2
    return depois - antes


def _remover_bins_vazios(sol):
    nova = Solucao.a_partir_de_bins(sol.C, sol.tamanhos, sol.bins)
    sol.bins = nova.bins
    sol.carga = nova.carga
    sol.bin_de = nova.bin_de


def _aplicar_movimento(sol, item, origem, destino):
    sol.bins[origem].remove(item)
    sol.carga[origem] -= sol.tamanhos[item]
    sol.bins[destino].append(item)
    sol.carga[destino] += sol.tamanhos[item]
    sol.bin_de[item] = destino
    if not sol.bins[origem]:
        _remover_bins_vazios(sol)


def _aplicar_troca(sol, a, A, b, B):
    sol.bins[A].remove(a)
    sol.bins[B].remove(b)
    sol.bins[A].append(b)
    sol.bins[B].append(a)
    sol.carga[A] += sol.tamanhos[b] - sol.tamanhos[a]
    sol.carga[B] += sol.tamanhos[a] - sol.tamanhos[b]
    sol.bin_de[a] = B
    sol.bin_de[b] = A


def _passo_movimento(sol, first_improvement, tempo_fim):
    """Procura um movimento melhorante. Retorna True se aplicou algum."""
    C = sol.C
    tam = sol.tamanhos
    melhor_delta = EPS
    melhor = None                       # (item, origem, destino)
    nbins = len(sol.bins)
    for origem in range(nbins):
        carga_o = sol.carga[origem]
        for item in sol.bins[origem]:
            s = tam[item]
            for destino in range(nbins):
                if destino == origem:
                    continue
                if sol.carga[destino] + s > C + EPS:
                    continue
                d = _delta_quadrados_move(C, carga_o, sol.carga[destino], s)
                if d > melhor_delta:
                    if first_improvement:
                        _aplicar_movimento(sol, item, origem, destino)
                        return True
                    melhor_delta = d
                    melhor = (item, origem, destino)
        if time.time() >= tempo_fim:
            break
    if melhor is not None:
        _aplicar_movimento(sol, *melhor)
        return True
    return False


def _passo_troca(sol, first_improvement, tempo_fim):
    """Procura uma troca melhorante. Retorna True se aplicou alguma."""
    C = sol.C
    tam = sol.tamanhos
    melhor_delta = EPS
    melhor = None                       # (a, A, b, B)
    nbins = len(sol.bins)
    for A in range(nbins):
        cA = sol.carga[A]
        for B in range(A + 1, nbins):
            cB = sol.carga[B]
            for a in sol.bins[A]:
                sa = tam[a]
                for b in sol.bins[B]:
                    sb = tam[b]
                    if abs(sa - sb) < EPS:
                        continue
                    nova_A = cA - sa + sb
                    nova_B = cB - sb + sa
                    if nova_A > C + EPS or nova_B > C + EPS:
                        continue
                    antes = (cA / C) ** 2 + (cB / C) ** 2
                    depois = (nova_A / C) ** 2 + (nova_B / C) ** 2
                    d = depois - antes
                    if d > melhor_delta:
                        if first_improvement:
                            _aplicar_troca(sol, a, A, b, B)
                            return True
                        melhor_delta = d
                        melhor = (a, A, b, B)
        if time.time() >= tempo_fim:
            break
    if melhor is not None:
        _aplicar_troca(sol, *melhor)
        return True
    return False


def busca_local(sol, first_improvement, tempo_fim):
    """Aplica movimento + troca ate um otimo local ou esgotar o tempo."""
    melhorou = True
    while melhorou:
        if time.time() >= tempo_fim:
            break
        melhorou = False
        if _passo_movimento(sol, first_improvement, tempo_fim):
            melhorou = True
            continue
        if _passo_troca(sol, first_improvement, tempo_fim):
            melhorou = True
    return sol


# ---------------------------------------------------------------------------
# 6. Perturbacao (diversificacao do ILS)
# ---------------------------------------------------------------------------
# Esvazia os k bins menos cheios (k = 2 ou 3) e reinsere seus itens, em ordem
# aleatoria, via First Fit. Os bins menos cheios sao os candidatos naturais
# a desaparecer.
# ---------------------------------------------------------------------------
def perturbacao(sol, rng):
    m = sol.num_bins()
    if m <= 1:
        return sol
    k = min(rng.randint(2, 3), m - 1)
    ordem = sorted(range(m), key=lambda j: sol.carga[j])   # do menos ao mais cheio
    alvo = set(ordem[:k])

    mantidos = [list(sol.bins[j]) for j in range(m) if j not in alvo]
    soltos = [i for j in alvo for i in sol.bins[j]]
    rng.shuffle(soltos)

    C = sol.C
    tam = sol.tamanhos
    carga = [sum(tam[i] for i in b) for b in mantidos]
    for i in soltos:
        colocado = False
        for j in range(len(mantidos)):
            if carga[j] + tam[i] <= C + EPS:
                mantidos[j].append(i)
                carga[j] += tam[i]
                colocado = True
                break
        if not colocado:
            mantidos.append([i])
            carga.append(tam[i])
    return Solucao.a_partir_de_bins(C, tam, mantidos)


# ---------------------------------------------------------------------------
# 7. Iterated Local Search - laco principal
# ---------------------------------------------------------------------------
# s  <- FFD ; s <- busca_local(s)
# repita ate o tempo acabar:
#     s' <- busca_local(perturbacao(melhor))
#     se s' for melhor que 'melhor':  melhor <- s'   (better acceptance)
# ---------------------------------------------------------------------------
def iterated_local_search(C, tamanhos, tempo_limite, first_improvement,
                          seed, verbose):
    rng = random.Random(seed)
    inicio = time.time()
    tempo_fim = inicio + tempo_limite
    lb = limite_inferior(C, tamanhos)

    atual = first_fit_decreasing(C, tamanhos)
    atual = busca_local(atual, first_improvement, tempo_fim)
    melhor = atual.copia()

    iteracoes = 0
    if verbose:
        print("  [inicial]  bins=%d   (limite inferior=%d)"
              % (melhor.num_bins(), lb))

    while time.time() < tempo_fim and melhor.num_bins() > lb:
        iteracoes += 1
        candidata = perturbacao(melhor.copia(), rng)
        candidata = busca_local(candidata, first_improvement, tempo_fim)
        if melhor_que(candidata, melhor):
            melhor = candidata.copia()
            if verbose:
                print("  [iter %d]  bins=%d   t=%.2fs"
                      % (iteracoes, melhor.num_bins(), time.time() - inicio))

    return melhor, iteracoes, lb, time.time() - inicio


# ---------------------------------------------------------------------------
# 8. Validacao e saida
# ---------------------------------------------------------------------------
def validar(sol, n, C, tamanhos):
    """Confere se a solucao e viavel: itens alocados uma unica vez e nenhum
    recipiente excede a capacidade."""
    vistos = []
    for b in sol.bins:
        for i in b:
            vistos.append(i)
        if sum(tamanhos[i] for i in b) > C + 1e-6:
            return False, "um recipiente excede a capacidade"
    if sorted(vistos) != list(range(n)):
        return False, "ha itens faltando ou duplicados"
    return True, "ok"


def main():
    parser = argparse.ArgumentParser(
        description="Iterated Local Search (ILS) para o Bin Packing.")
    parser.add_argument("instancia", help="caminho do arquivo da instancia")
    parser.add_argument("tempo", type=float,
                        help="tempo limite em segundos (criterio de parada)")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--first", action="store_true",
                       help="busca local first improvement (padrao)")
    grupo.add_argument("--best", action="store_true",
                       help="busca local best improvement")
    parser.add_argument("--seed", type=int, default=1,
                        help="semente do gerador aleatorio (padrao 1)")
    parser.add_argument("--verbose", action="store_true",
                        help="imprime o progresso da busca")
    args = parser.parse_args()

    first_improvement = not args.best

    n, C, tamanhos = ler_instancia(args.instancia)

    print("=" * 64)
    print(" Bin Packing  -  Iterated Local Search (ILS)")
    print("=" * 64)
    print(" Instancia          : %s" % args.instancia)
    print(" Numero de itens    : %d" % n)
    print(" Capacidade do bin  : %g" % C)
    print(" Busca local        : %s improvement"
          % ("first" if first_improvement else "best"))
    print(" Tempo limite       : %g s" % args.tempo)
    print("-" * 64)

    melhor, iteracoes, lb, gasto = iterated_local_search(
        C, tamanhos, args.tempo, first_improvement, args.seed, args.verbose)

    ok, msg = validar(melhor, n, C, tamanhos)

    print("-" * 64)
    print(" RESULTADO")
    print("   Recipientes usados : %d" % melhor.num_bins())
    print("   Limite inferior    : %d" % lb)
    if melhor.num_bins() == lb:
        print("   >>> solucao comprovadamente OTIMA (atingiu o limite inferior)")
    print("   Iteracoes do ILS   : %d" % iteracoes)
    print("   Tempo gasto        : %.2f s" % gasto)
    print("   Solucao viavel     : %s" % ("SIM" if ok else "NAO (" + msg + ")"))
    print("-" * 64)
    print(" Alocacao final  (bin: itens  ->  [carga / capacidade]):")
    for j, b in enumerate(melhor.bins):
        carga = sum(tamanhos[i] for i in b)
        itens = ", ".join(str(i) for i in sorted(b))
        print("   bin %3d: %-44s [%g / %g]" % (j + 1, itens, carga, C))
    print("=" * 64)


if __name__ == "__main__":
    main()
