"""
Questão 2 — Modelos de Programação Linear (Inteira) resolvidos com CPLEX (docplex).

 1. Ração          2. Dieta            3. Plantio          4. Tintas
 5. Transporte     6. Fluxo Máximo     7. Escalonamento    8. Cobertura
 9. Mochila       10. Clique Máxima   11. Padrões         12. Facilidades
13. Frequência    14. TSP             15. CVRP            16. Bin Packing
17. Caminho Mínimo
"""

from docplex.mp.model import Model

SEPARATOR = "=" * 60


def print_header(numero, nome):
    print(f"\n{SEPARATOR}")
    print(f"  Problema {numero}: {nome}")
    print(SEPARATOR)


def problema_racao():
    print_header(1, "Problema da Ração")

    mdl = Model(name="Racao")

    amgs = mdl.continuous_var(name="AMGS", lb=0)
    re   = mdl.continuous_var(name="RE",   lb=0)

    # Lucro por unidade: AMGS = 20 - 5 - 4 = 11 ; RE = 30 - 2 - 16 = 12
    mdl.maximize(11 * amgs + 12 * re)

    mdl.add_constraint(1 * amgs + 4 * re <= 10000, "carne")
    mdl.add_constraint(5 * amgs + 2 * re <= 30000, "cereais")

    sol = mdl.solve()
    if sol:
        print(f"  AMGS produzido : {sol[amgs]:.2f} unidades")
        print(f"  RE produzido   : {sol[re]:.2f} unidades")
        print(f"  Lucro máximo   : R$ {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_dieta():
    print_header(2, "Problema da Dieta")

    mdl = Model(name="Dieta")

    n = 6
    preco    = [35, 30, 60, 50, 27, 22]
    vitA     = [1,  0,  2,  2,  1,  2]
    vitC     = [0,  1,  3,  1,  3,  2]
    min_vitA = 9
    min_vitC = 19

    x = [mdl.continuous_var(name=f"x{i+1}", lb=0) for i in range(n)]

    mdl.minimize(mdl.sum(preco[i] * x[i] for i in range(n)))

    mdl.add_constraint(mdl.sum(vitA[i] * x[i] for i in range(n)) >= min_vitA, "vitaminaA")
    mdl.add_constraint(mdl.sum(vitC[i] * x[i] for i in range(n)) >= min_vitC, "vitaminaC")

    sol = mdl.solve()
    if sol:
        print("  Quantidades de cada ingrediente:")
        for i in range(n):
            print(f"    Ingrediente {i+1}: {sol[x[i]]:.4f}")
        print(f"  Custo mínimo: R$ {mdl.objective_value:.4f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_plantio():
    print_header(3, "Problema do Plantio")

    mdl = Model(name="Plantio")

    fazendas = [0, 1, 2]
    area_fazenda = [400, 650, 350]
    agua_fazenda = [1800, 2200, 950]

    culturas      = [0, 1, 2]   # milho, arroz, feijão
    area_max_cult = [660, 880, 400]
    agua_por_area = [5.5, 4.0, 3.5]
    lucro_area    = [5000, 4000, 1800]

    # x[i][j] = área plantada da cultura j na fazenda i
    x = [[mdl.continuous_var(name=f"x_f{i+1}_c{j+1}", lb=0)
          for j in culturas] for i in fazendas]

    mdl.maximize(mdl.sum(lucro_area[j] * x[i][j]
                         for i in fazendas for j in culturas))

    for i in fazendas:
        mdl.add_constraint(
            mdl.sum(x[i][j] for j in culturas) <= area_fazenda[i],
            f"area_f{i+1}"
        )

    for i in fazendas:
        mdl.add_constraint(
            mdl.sum(agua_por_area[j] * x[i][j] for j in culturas) <= agua_fazenda[i],
            f"agua_f{i+1}"
        )

    for j in culturas:
        mdl.add_constraint(
            mdl.sum(x[i][j] for i in fazendas) <= area_max_cult[j],
            f"area_max_c{j+1}"
        )

    # Proporção plantada igual em todas as fazendas
    for i in fazendas[1:]:
        mdl.add_constraint(
            mdl.sum(x[i][j] for j in culturas) * area_fazenda[0] ==
            mdl.sum(x[0][j] for j in culturas) * area_fazenda[i],
            f"proporcao_f{i+1}"
        )

    sol = mdl.solve()
    if sol:
        nomes_cult = ["Milho", "Arroz", "Feijão"]
        print("  Área plantada (acres):")
        for i in fazendas:
            for j in culturas:
                print(f"    Fazenda {i+1} - {nomes_cult[j]}: {sol[x[i][j]]:.2f}")
        print(f"  Lucro máximo: R$ {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_tintas():
    print_header(4, "Problema das Tintas")

    mdl = Model(name="Tintas")

    solA_sr = mdl.continuous_var(name="SolA_SR", lb=0)
    solB_sr = mdl.continuous_var(name="SolB_SR", lb=0)
    sec_sr  = mdl.continuous_var(name="SEC_SR",  lb=0)
    cor_sr  = mdl.continuous_var(name="COR_SR",  lb=0)

    solA_sn = mdl.continuous_var(name="SolA_SN", lb=0)
    solB_sn = mdl.continuous_var(name="SolB_SN", lb=0)
    sec_sn  = mdl.continuous_var(name="SEC_SN",  lb=0)
    cor_sn  = mdl.continuous_var(name="COR_SN",  lb=0)

    custo = (1.5 * solA_sr + 1.0 * solB_sr + 4.0 * sec_sr + 6.0 * cor_sr +
             1.5 * solA_sn + 1.0 * solB_sn + 4.0 * sec_sn + 6.0 * cor_sn)
    mdl.minimize(custo)

    mdl.add_constraint(solA_sr + solB_sr + sec_sr + cor_sr == 1000, "vol_SR")
    mdl.add_constraint(solA_sn + solB_sn + sec_sn + cor_sn == 250, "vol_SN")

    mdl.add_constraint(
        0.30 * solA_sr + 0.60 * solB_sr + sec_sr >= 0.25 * 1000, "sec_min_SR")
    mdl.add_constraint(
        0.70 * solA_sr + 0.40 * solB_sr + cor_sr >= 0.50 * 1000, "cor_min_SR")
    mdl.add_constraint(
        0.30 * solA_sn + 0.60 * solB_sn + sec_sn >= 0.20 * 250, "sec_min_SN")
    mdl.add_constraint(
        0.70 * solA_sn + 0.40 * solB_sn + cor_sn >= 0.50 * 250, "cor_min_SN")

    sol = mdl.solve()
    if sol:
        print("  Compras para SR (1000 L):")
        print(f"    SolA: {sol[solA_sr]:.2f} L | SolB: {sol[solB_sr]:.2f} L"
              f" | SEC: {sol[sec_sr]:.2f} L | COR: {sol[cor_sr]:.2f} L")
        print("  Compras para SN (250 L):")
        print(f"    SolA: {sol[solA_sn]:.2f} L | SolB: {sol[solB_sn]:.2f} L"
              f" | SEC: {sol[sec_sn]:.2f} L | COR: {sol[cor_sn]:.2f} L")
        print(f"  Custo mínimo: R$ {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_transporte():
    print_header(5, "Problema do Transporte")

    mdl = Model(name="Transporte")

    fab = [0, 1, 2]
    dep = [0, 1, 2]
    oferta  = [120, 80, 80]
    demanda = [150, 70, 60]
    custo = [[8,  5,  6],
             [15, 10, 12],
             [3,  9,  10]]

    x = [[mdl.continuous_var(name=f"x_{i+1}_{j+1}", lb=0)
          for j in dep] for i in fab]

    mdl.minimize(mdl.sum(custo[i][j] * x[i][j] for i in fab for j in dep))

    for i in fab:
        mdl.add_constraint(
            mdl.sum(x[i][j] for j in dep) <= oferta[i], f"oferta_{i+1}")

    for j in dep:
        mdl.add_constraint(
            mdl.sum(x[i][j] for i in fab) >= demanda[j], f"demanda_{j+1}")

    sol = mdl.solve()
    if sol:
        print("  Fluxo transportado (Fábrica -> Depósito):")
        for i in fab:
            for j in dep:
                v = sol[x[i][j]]
                if v > 0.001:
                    print(f"    F{i+1} -> D{j+1}: {v:.2f} unidades")
        print(f"  Custo mínimo: R$ {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_fluxo_maximo():
    print_header(6, "Problema do Fluxo Máximo")

    mdl = Model(name="FluxoMaximo")

    nos = list(range(8))
    s, t = 0, 7

    # (origem, destino, capacidade)
    arcos = [
        (0, 1, 5), (0, 2, 4), (0, 3, 6),
        (1, 2, 4), (1, 4, 6),
        (2, 3, 3), (2, 5, 4),
        (3, 5, 6), (3, 6, 5),
        (4, 5, 5), (4, 7, 5),
        (5, 4, 5), (5, 7, 3),
        (6, 5, 7), (6, 7, 6),
    ]

    f = {(u, v): mdl.continuous_var(name=f"f_{u}_{v}", lb=0, ub=cap)
         for u, v, cap in arcos}

    mdl.maximize(mdl.sum(f[(s, v)] for (u, v, _) in arcos if u == s))

    for n in nos:
        if n == s or n == t:
            continue
        entrada = mdl.sum(f[(u, v)] for (u, v, _) in arcos if v == n)
        saida   = mdl.sum(f[(u, v)] for (u, v, _) in arcos if u == n)
        mdl.add_constraint(entrada == saida, f"conservacao_{n}")

    sol = mdl.solve()
    if sol:
        nos_nome = ["s", "v1", "v2", "v3", "v4", "v5", "v6", "t"]
        print("  Fluxo nos arcos:")
        for (u, v, cap) in arcos:
            fv = sol[f[(u, v)]]
            if fv > 0.001:
                print(f"    {nos_nome[u]} -> {nos_nome[v]}: {fv:.2f} / {cap}")
        print(f"  Fluxo máximo: {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_escalonamento():
    print_header(7, "Escalonamento de Horários")

    mdl = Model(name="Escalonamento")

    d = [3, 4, 3, 2, 2, 3, 2]   # demanda diária (dias 1..7)
    dias = list(range(7))

    # x[i] = enfermeiras que começam no dia i e trabalham 4 dias consecutivos
    x = [mdl.integer_var(name=f"x{i+1}", lb=0) for i in dias]

    mdl.minimize(mdl.sum(x))

    for j in dias:
        trabalhando = mdl.sum(x[(j - k) % 7] for k in range(4))
        mdl.add_constraint(trabalhando >= d[j], f"demanda_dia{j+1}")

    sol = mdl.solve()
    if sol:
        print(f"  Demanda diária: {d}")
        print("  Enfermeiras que iniciam em cada dia:")
        for i in dias:
            print(f"    Dia {i+1}: {int(sol[x[i]])} enfermeiras")
        print(f"  Total de enfermeiras: {int(mdl.objective_value)}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_cobertura():
    print_header(8, "Problema de Cobertura")

    mdl = Model(name="Cobertura")

    n_bairros = 7
    bairros = list(range(n_bairros))

    # adjacências (incluindo o próprio bairro)
    adj = {
        0: [0, 1, 3],
        1: [0, 1, 2, 4],
        2: [1, 2, 5],
        3: [0, 3, 4, 6],
        4: [1, 3, 4, 5],
        5: [2, 4, 5],
        6: [3, 6],
    }

    x = [mdl.binary_var(name=f"x{i}") for i in bairros]

    mdl.minimize(mdl.sum(x))

    for i in bairros:
        mdl.add_constraint(
            mdl.sum(x[j] for j in adj[i]) >= 1, f"cobertura_{i}")

    sol = mdl.solve()
    if sol:
        print("  Escolas construídas nos bairros:")
        escolhidos = [i for i in bairros if sol[x[i]] > 0.5]
        print(f"    Bairros: {[i+1 for i in escolhidos]}")
        print(f"  Total de escolas: {int(mdl.objective_value)}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_mochila():
    print_header(9, "Problema da Mochila")

    mdl = Model(name="Mochila")

    pesos   = [4, 3, 3, 2, 5, 2]
    valores = [3, 5, 2, 3, 6, 4]
    W = 10   # capacidade
    n = len(pesos)

    x = [mdl.binary_var(name=f"x{i+1}") for i in range(n)]

    mdl.maximize(mdl.sum(valores[i] * x[i] for i in range(n)))

    mdl.add_constraint(
        mdl.sum(pesos[i] * x[i] for i in range(n)) <= W, "capacidade")

    sol = mdl.solve()
    if sol:
        print(f"  Capacidade: {W} kg")
        print("  Itens selecionados (peso | valor):")
        peso_total = 0
        for i in range(n):
            if sol[x[i]] > 0.5:
                print(f"    Item {i+1}: {pesos[i]} kg | R$ {valores[i]}")
                peso_total += pesos[i]
        print(f"  Peso total usado: {peso_total} kg")
        print(f"  Valor máximo: R$ {int(mdl.objective_value)}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_clique_maxima():
    print_header(10, "Problema da Clique Máxima")

    mdl = Model(name="CliqueMaxima")

    V = list(range(7))
    E = {(0,1),(0,2),(1,2),(1,3),(1,4),(2,4),(3,4),(3,5),(4,5),(5,6)}
    E_set = E | {(v, u) for (u, v) in E}

    x = [mdl.binary_var(name=f"x{v}") for v in V]

    mdl.maximize(mdl.sum(x))

    # pares sem aresta não podem estar ambos na clique
    for i in V:
        for j in V:
            if i < j and (i, j) not in E_set and (j, i) not in E_set:
                mdl.add_constraint(x[i] + x[j] <= 1, f"naoclique_{i}_{j}")

    sol = mdl.solve()
    if sol:
        clique = [v for v in V if sol[x[v]] > 0.5]
        print(f"  Clique máxima: vértices {[v+1 for v in clique]}")
        print(f"  Tamanho da clique: {int(mdl.objective_value)}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_padroes():
    print_header(11, "Problema de Padrões (Latinhas)")

    mdl = Model(name="Padroes")

    padroes = [0, 1, 2, 3]
    tam_folha     = [1, 2, 1, 1]
    num_corpo     = [1, 2, 0, 4]
    num_tampa     = [7, 3, 9, 4]
    tempo_imp     = [2, 3, 2, 1]
    folhas_tam1   = 200
    folhas_tam2   = 90
    preco_latinha = 50
    custo_corpo   = 5
    custo_tampa   = 3
    tempo_max     = 100

    y = [mdl.integer_var(name=f"y{p+1}", lb=0) for p in padroes]
    total_corpos = mdl.sum(num_corpo[p] * y[p] for p in padroes)
    total_tampas = mdl.sum(num_tampa[p] * y[p] for p in padroes)

    # 1 latinha = 1 corpo + 2 tampas
    latinhas = mdl.integer_var(name="latinhas", lb=0)
    mdl.add_constraint(latinhas <= total_corpos,     "lim_corpo")
    mdl.add_constraint(2 * latinhas <= total_tampas, "lim_tampa")

    corpos_nao_usados = total_corpos - latinhas
    lucro = (preco_latinha * latinhas
             - custo_corpo * corpos_nao_usados
             - custo_tampa * total_tampas)
    mdl.maximize(lucro)

    mdl.add_constraint(
        mdl.sum(y[p] for p in padroes if tam_folha[p] == 1) <= folhas_tam1,
        "folhas_t1")
    mdl.add_constraint(
        mdl.sum(y[p] for p in padroes if tam_folha[p] == 2) <= folhas_tam2,
        "folhas_t2")
    mdl.add_constraint(
        mdl.sum(tempo_imp[p] * y[p] for p in padroes) <= tempo_max,
        "tempo")

    sol = mdl.solve()
    if sol:
        print("  Impressões por padrão:")
        for p in padroes:
            print(f"    Padrão {p+1}: {int(sol[y[p]])} impressões")
        print(f"  Latinhas montadas: {int(sol[latinhas])}")
        print(f"  Lucro máximo: {mdl.objective_value:.2f} u")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_facilidades():
    print_header(12, "Problema das Facilidades")

    mdl = Model(name="Facilidades")

    N = 4   # depósitos candidatos
    M = 5   # clientes
    centros  = list(range(N))
    clientes = list(range(M))

    f = [100, 150, 80, 120]   # custo de instalação
    c = [                      # custo de atendimento c[i][j]
        [10, 8,  5, 12,  9],
        [7,  11, 6,  8,  10],
        [12,  5, 9,  7,   8],
        [6,   9, 8, 10,   6],
    ]

    y = [mdl.binary_var(name=f"y{i+1}") for i in centros]
    x = [[mdl.binary_var(name=f"x{i+1}_{j+1}")
          for j in clientes] for i in centros]

    mdl.minimize(
        mdl.sum(f[i] * y[i] for i in centros) +
        mdl.sum(c[i][j] * x[i][j] for i in centros for j in clientes)
    )

    for j in clientes:
        mdl.add_constraint(
            mdl.sum(x[i][j] for i in centros) == 1, f"atend_{j+1}")

    for i in centros:
        for j in clientes:
            mdl.add_constraint(x[i][j] <= y[i], f"link_{i+1}_{j+1}")

    sol = mdl.solve()
    if sol:
        instalados = [i for i in centros if sol[y[i]] > 0.5]
        print(f"  Depósitos instalados: {[i+1 for i in instalados]}")
        print("  Atendimento (Depósito -> Clientes):")
        for i in instalados:
            atendidos = [j+1 for j in clientes if sol[x[i][j]] > 0.5]
            print(f"    Depósito {i+1} -> Clientes {atendidos}")
        print(f"  Custo total mínimo: R$ {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_frequencia():
    print_header(13, "Problema de Frequência (Coloração de Grafos)")

    mdl = Model(name="Frequencia")

    n_antenas = 6
    antenas = list(range(n_antenas))
    interferencias = [(0,1),(0,2),(1,2),(1,3),(2,4),(3,4),(3,5),(4,5)]

    K = n_antenas
    freq = list(range(K))

    x = [[mdl.binary_var(name=f"x{a}_{k}") for k in freq] for a in antenas]
    z = [mdl.binary_var(name=f"z{k}") for k in freq]

    mdl.minimize(mdl.sum(z))

    for a in antenas:
        mdl.add_constraint(mdl.sum(x[a][k] for k in freq) == 1, f"uma_freq_{a}")

    for (a, b) in interferencias:
        for k in freq:
            mdl.add_constraint(x[a][k] + x[b][k] <= 1, f"interf_{a}_{b}_{k}")

    for k in freq:
        for a in antenas:
            mdl.add_constraint(x[a][k] <= z[k], f"uso_{a}_{k}")

    # quebra de simetria
    for k in freq[1:]:
        mdl.add_constraint(z[k] <= z[k-1], f"simetria_{k}")

    sol = mdl.solve()
    if sol:
        print("  Atribuição de frequências:")
        for a in antenas:
            freq_usada = [k+1 for k in freq if sol[x[a][k]] > 0.5]
            print(f"    Antena {a+1}: Frequência {freq_usada[0]}")
        print(f"  Número mínimo de frequências: {int(mdl.objective_value)}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_tsp():
    print_header(14, "Problema do Caixeiro Viajante (TSP)")

    mdl = Model(name="TSP")

    n = 6
    cidades = list(range(n))
    dist = [
        [0,  10, 20, 15, 30, 25],
        [10,  0, 35, 20, 10, 15],
        [20, 35,  0, 30, 20, 10],
        [15, 20, 30,  0, 25, 20],
        [30, 10, 20, 25,  0, 15],
        [25, 15, 10, 20, 15,  0],
    ]

    x = [[mdl.binary_var(name=f"x{i}_{j}") if i != j else None
          for j in cidades] for i in cidades]

    # u[i] = posição na rota (eliminação de sub-rotas, formulação MTZ)
    u = [mdl.integer_var(name=f"u{i}", lb=1, ub=n) for i in cidades]

    mdl.minimize(mdl.sum(
        dist[i][j] * x[i][j]
        for i in cidades for j in cidades if i != j
    ))

    for j in cidades:
        mdl.add_constraint(
            mdl.sum(x[i][j] for i in cidades if i != j) == 1, f"entrada_{j}")

    for i in cidades:
        mdl.add_constraint(
            mdl.sum(x[i][j] for j in cidades if i != j) == 1, f"saida_{i}")

    for i in cidades[1:]:
        for j in cidades[1:]:
            if i != j:
                mdl.add_constraint(
                    u[i] - u[j] + n * x[i][j] <= n - 1,
                    f"mtz_{i}_{j}")

    sol = mdl.solve()
    if sol:
        print("  Rota encontrada:")
        rota = [0]
        atual = 0
        for _ in range(n - 1):
            for j in cidades:
                if j != atual and sol[x[atual][j]] > 0.5:
                    rota.append(j)
                    atual = j
                    break
        rota.append(0)
        print(f"    {' -> '.join(str(c+1) for c in rota)}")
        print(f"  Custo total: {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_cvrp():
    print_header(15, "Roteamento de Veículos Capacitado (CVRP)")

    mdl = Model(name="CVRP")

    n_clientes = 5
    deposito   = 0
    nos = list(range(n_clientes + 1))   # 0 = depósito, 1..5 = clientes
    clientes = list(range(1, n_clientes + 1))

    demanda = {0: 0, 1: 10, 2: 15, 3: 20, 4: 10, 5: 25}
    capacidade_veiculo = 50
    K = 3   # veículos disponíveis

    dist = [
        [0,  12, 18, 25, 14, 20],
        [12,  0, 10, 22, 16, 18],
        [18, 10,  0, 15, 20, 12],
        [25, 22, 15,  0, 18, 10],
        [14, 16, 20, 18,  0, 14],
        [20, 18, 12, 10, 14,  0],
    ]

    veiculos = list(range(K))

    x = {(i, j, k): mdl.binary_var(name=f"x{i}_{j}_{k}")
         for i in nos for j in nos for k in veiculos if i != j}

    mdl.minimize(mdl.sum(
        dist[i][j] * x[(i, j, k)]
        for i in nos for j in nos for k in veiculos if i != j
    ))

    for j in clientes:
        mdl.add_constraint(
            mdl.sum(x[(i, j, k)] for i in nos for k in veiculos if i != j) == 1,
            f"visita_{j}")

    for k in veiculos:
        for h in clientes:
            mdl.add_constraint(
                mdl.sum(x[(i, h, k)] for i in nos if i != h) ==
                mdl.sum(x[(h, j, k)] for j in nos if j != h),
                f"fluxo_{h}_{k}")

    for k in veiculos:
        mdl.add_constraint(
            mdl.sum(x[(deposito, j, k)] for j in clientes) <= 1,
            f"saida_dep_{k}")

    # carga acumulada (capacidade + eliminação de sub-rotas)
    Q = {(i, k): mdl.continuous_var(name=f"Q{i}_{k}", lb=0, ub=capacidade_veiculo)
         for i in nos for k in veiculos}

    for k in veiculos:
        for i in nos:
            for j in clientes:
                if i != j:
                    mdl.add_constraint(
                        Q[(j, k)] >= Q[(i, k)] + demanda[j] * x[(i, j, k)]
                        - capacidade_veiculo * (1 - x[(i, j, k)]),
                        f"carga_{i}_{j}_{k}")

    sol = mdl.solve()
    if sol:
        print("  Rotas dos veículos:")
        for k in veiculos:
            rota = []
            atual = deposito
            visitados = set()
            for _ in range(n_clientes):
                prox = None
                for j in nos:
                    if j != atual and j not in visitados:
                        if sol[x[(atual, j, k)]] > 0.5:
                            prox = j
                            break
                if prox is None:
                    break
                rota.append(prox)
                visitados.add(prox)
                atual = prox
            if rota:
                print(f"    Veículo {k+1}: 0 -> {' -> '.join(map(str,rota))} -> 0")
        print(f"  Custo total: {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_bin_packing():
    print_header(16, "Problema de Empacotamento (Bin Packing)")

    mdl = Model(name="BinPacking")

    tamanhos = [0.5, 0.3, 0.7, 0.4, 0.6, 0.2, 0.8, 0.35]
    n = len(tamanhos)
    itens = list(range(n))
    B = n   # número máximo de bins (pior caso)
    bins = list(range(B))
    capacidade = 1.0

    x = [[mdl.binary_var(name=f"x{i}_{b}") for b in bins] for i in itens]
    y = [mdl.binary_var(name=f"y{b}") for b in bins]

    mdl.minimize(mdl.sum(y))

    for i in itens:
        mdl.add_constraint(mdl.sum(x[i][b] for b in bins) == 1, f"item_{i}")

    for b in bins:
        mdl.add_constraint(
            mdl.sum(tamanhos[i] * x[i][b] for i in itens) <= capacidade * y[b],
            f"cap_{b}")

    # quebra de simetria
    for b in bins[1:]:
        mdl.add_constraint(y[b] <= y[b-1], f"sim_{b}")

    sol = mdl.solve()
    if sol:
        print(f"  Itens (tamanhos): {tamanhos}")
        print("  Alocação nos bins:")
        for b in bins:
            if sol[y[b]] > 0.5:
                conteudo = [i+1 for i in itens if sol[x[i][b]] > 0.5]
                soma = sum(tamanhos[i-1] for i in conteudo)
                print(f"    Bin {b+1}: itens {conteudo} | carga = {soma:.2f}")
        print(f"  Número mínimo de bins: {int(mdl.objective_value)}")
    else:
        print("  Sem solução viável.")
    mdl.end()


def problema_caminho_minimo():
    print_header(17, "Problema do Caminho Mínimo")

    mdl = Model(name="CaminhoMinimo")

    nos_nome = ["a", "b", "c", "d", "e", "f", "g"]
    nos = list(range(7))
    s = 0   # origem: a
    t = 6   # destino: g

    arestas = [
        (0, 1, 7), (0, 3, 5),
        (1, 2, 8), (1, 3, 9), (1, 4, 7),
        (2, 4, 5),
        (3, 4, 15),(3, 5, 6),
        (4, 2, 5), (4, 5, 8), (4, 6, 9),
        (5, 6, 11),
    ]

    # grafo não-direcionado: arcos nos dois sentidos
    arcos_dir = {(u, v, w) for (u, v, w) in arestas}
    arcos_inv = {(v, u, w) for (u, v, w) in arestas}
    arcos = list(arcos_dir | arcos_inv)

    x = {(u, v): mdl.binary_var(name=f"x{u}_{v}") for (u, v, w) in arcos}

    mdl.minimize(mdl.sum(w * x[(u, v)] for (u, v, w) in arcos))

    for n in nos:
        saida   = mdl.sum(x[(u, v)] for (u, v, w) in arcos if u == n)
        entrada = mdl.sum(x[(u, v)] for (u, v, w) in arcos if v == n)
        if n == s:
            mdl.add_constraint(saida - entrada == 1, "fonte")
        elif n == t:
            mdl.add_constraint(entrada - saida == 1, "sorvedouro")
        else:
            mdl.add_constraint(saida == entrada, f"fluxo_{n}")

    sol = mdl.solve()
    if sol:
        caminho = [s]
        atual = s
        for _ in range(len(nos)):
            for (u, v, w) in arcos:
                if u == atual and sol[x[(u, v)]] > 0.5:
                    caminho.append(v)
                    atual = v
                    break
            if atual == t:
                break
        print(f"  Origem: {nos_nome[s]} | Destino: {nos_nome[t]}")
        print(f"  Caminho mínimo: {' -> '.join(nos_nome[n] for n in caminho)}")
        print(f"  Custo total: {mdl.objective_value:.2f}")
    else:
        print("  Sem solução viável.")
    mdl.end()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  QUESTÃO 2 — Modelos de Programação Linear (Inteira)")
    print("  Solucionados com IBM CPLEX via docplex")
    print("=" * 60)

    problema_racao()
    problema_dieta()
    problema_plantio()
    problema_tintas()
    problema_transporte()
    problema_fluxo_maximo()
    problema_escalonamento()
    problema_cobertura()
    problema_mochila()
    problema_clique_maxima()
    problema_padroes()
    problema_facilidades()
    problema_frequencia()
    problema_tsp()
    problema_cvrp()
    problema_bin_packing()
    problema_caminho_minimo()

    print(f"\n{'='*60}")
    print("  Todos os 17 modelos resolvidos com sucesso!")
    print("=" * 60)
