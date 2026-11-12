# Norte – Programação Dinâmica

**Global Solution 2026.2 · CitizenTech · Engenharia de Software (2º ano) · FIAP**
Disciplina: **Dynamic Programming** · Equipe **Acesstech** · Turma **2ESPI**

> O Norte é um assistente que ajuda qualquer cidadão a entender e buscar seus direitos do dia a dia.
> Nesta disciplina, a equipe implementou em Python os **algoritmos** que fazem o Norte funcionar:
> entender o relato, montar o plano de ação da semana e indicar o atendimento gratuito mais perto.

---

## Ficha da CitizenTech

| Campo | Preenchimento |
|---|---|
| Nome da CitizenTech | **Norte** – orientação de direitos para o cidadão |
| Cidade e bairro | São Paulo (SP) – Brasilândia, Zona Norte |
| Cidadão beneficiado | Qualquer cidadão com dúvida sobre direitos do dia a dia, com prioridade para pessoas de baixa renda, idosos e pessoas com deficiência |
| Problema, em uma frase | Cidadãos não entendem quais direitos têm nem o que fazer quando eles são desrespeitados, e por isso perdem dinheiro, benefícios e prazos |
| Como funciona | A pessoa conta o problema com as próprias palavras, a triagem identifica uma das 10 áreas da vida e o Norte devolve um plano de ação com leis vigentes, prazos com semáforo, documentos e o atendimento gratuito certo |
| O que cada parte faz | Agile: design da solução · Database: banco de dados · Java: API REST · **Dynamic Programming: algoritmos (este repositório)** · Data Science: previsões · Network: rede do ponto de atendimento · AR-VR: vídeo 3D |
| Base de leis | Repositório aberto [ctresb/leis](https://github.com/ctresb/leis) (licença MIT) |
| Link do repositório | https://github.com/GuilhermeKuskowski/norte-python |
| Indicador de impacto | Pessoas orientadas por área e % que procurou atendimento depois do relatório |
| ODS conectados | 1, 3, 5, 8, 10 e 16 |

## Integrantes

| Nome | RM |
|---|---|
| Enzo de Faria Ferreira | 562448 |
| Guilherme Eduardo de Lima | 566045 |
| Guilherme de Paula Kuskowski | 562471 |

---

## 1. Qual necessidade o algoritmo resolve

Quem mais precisa do Norte tem três dificuldades que viram três problemas de computação:

| Dificuldade real do cidadão | Problema computacional | Técnica de PD |
|---|---|---|
| Escreve do seu jeito ("recisão", "benefisio", "sego") ou manda áudio transcrito com erros, e não sabe o nome jurídico do problema | Reconhecer palavras com erro de digitação e descobrir a área | **Memoização** (distância de edição) |
| Tem pouco tempo livre (bicos, trabalho por aplicativo) e muitas coisas para fazer, cada uma com um prazo | Escolher quais ações cabem nas horas disponíveis com o maior benefício | **Tabulação** (mochila 0/1) |
| Não sabe onde fica o atendimento gratuito, e às vezes precisa de um caminho sem escadas | Menor caminho no mapa do bairro, com e sem trechos inacessíveis | **Grafos** (Floyd-Warshall) |

As três partes trabalham juntas num único fluxo:

```
relato ─► [1. Triagem · memoização] ─► áreas do caso ─► ações da curadoria + prazos
                                                              │
                     [2. Plano da semana · tabulação] ◄───────┘
                                │
                     [3. Atendimento gratuito · grafos] ─► Plano de Ação em linguagem simples
```

---

## 2. Algoritmos abordados

### 2.1 Memoização – distância de edição na triagem (`norte/triagem.py`)

**Por que esta técnica:** uma busca exata por palavras-chave falha justamente com quem tem baixa escolaridade ou usa leitor de tela e áudio. A distância de edição (Levenshtein) conta quantas letras precisam ser inseridas, removidas ou trocadas para uma palavra virar outra, então "depozitado" ainda é reconhecido como "depositado".

**Recorrência** (`d(i, j)` = distância entre os `i` primeiros caracteres de A e os `j` primeiros de B):

```
d(i, 0) = i        d(0, j) = j
d(i, j) = d(i-1, j-1)                                   se A[i-1] == B[j-1]
d(i, j) = 1 + min(d(i-1, j), d(i, j-1), d(i-1, j-1))    caso contrário
```

A recursão pura recalcula os mesmos pares `(i, j)` muitas vezes. Com `functools.lru_cache`, cada par é calculado uma vez só.

**Duas camadas de memoização:**
1. dentro de cada comparação, os subproblemas `(i, j)`;
2. entre atendimentos, o resultado de cada **par de palavras** (relato × vocabulário). Os relatos repetem muito as mesmas palavras ("inss", "nome", "demitida"), então a maior parte das comparações passa a vir do cache.

A tolerância cresce com o tamanho da palavra (até 3 letras: exata; 4 a 8: 1 erro; mais de 8: 2 erros), e uma poda pelo tamanho evita calcular pares que não têm chance. Cada palavra do relato pontua uma vez por área, no termo de maior peso. Entram no plano a área com mais pontos e as que chegam a 60% dela (um relato pode tocar duas áreas, como caução + multa).

O arquivo também traz a **versão ingênua** (para comparar) e uma **versão tabulada** com duas linhas da tabela (para conferir nos testes e comparar memoização x tabulação).

### 2.2 Tabulação – mochila 0/1 no plano da semana (`norte/plano.py`)

**Por que esta técnica:** é uma escolha com limite. Cada ação tem um custo (tempo) e um benefício; o tempo livre da pessoa é a capacidade da mochila.

- **capacidade** = horas livres na semana, em blocos de 30 minutos;
- **custo** = duração estimada da ação, em blocos de 30 minutos;
- **benefício** = impacto da ação (1 a 10, definido pela curadoria) × peso do semáforo do prazo (vermelho 3, amarelo 2, verde e sem prazo 1).

```
T[0][c] = 0
T[i][c] = max( T[i-1][c],                          ← não faz a ação i
               T[i-1][c - custo_i] + beneficio_i )  ← faz a ação i (se couber)
```

A tabela é preenchida de baixo para cima com dois laços `for`, sem recursão. As ações escolhidas são recuperadas andando de trás para frente na tabela (se `T[i][c] != T[i-1][c]`, a ação `i` entrou). Depois, as ações da semana são ordenadas pelo prazo mais próximo.

**Exemplo (Márcia, 4 h = 8 blocos):** extrato do FGTS (1 bloco, benefício 8), seguro-desemprego (2 blocos, 9), conferir a rescisão no sindicato (4 blocos, 7) e reclamação trabalhista (6 blocos, 9). A tabela escolhe as três primeiras (7 blocos, benefício 24) em vez de "seguro + reclamação" (8 blocos, benefício 18). A reclamação, que tem 2 anos de prazo, vai para "próximas semanas".

**Exemplo (José):** o recurso ao INSS vence em 6 dias (semáforo vermelho, peso 3), então o benefício triplica e ele aparece em primeiro lugar.

### 2.3 Grafos – Floyd-Warshall no atendimento gratuito (`norte/atendimento.py`)

**Por que esta técnica:** o bairro é naturalmente um grafo. Vértices são esquinas, pontos de referência e locais de atendimento (Defensoria, Procon, CRAS, Juizado, Conselho Tutelar...). Arestas são trechos de rua com o tempo de caminhada e a marcação **acessível** (sem escada, ladeira forte ou calçada ruim). O grafo fica numa lista de adjacência e numa matriz de distâncias.

**Floyd-Warshall é programação dinâmica em grafos:**

```
dist_k[i][j] = min( dist_{k-1}[i][j],  dist_{k-1}[i][k] + dist_{k-1}[k][j] )
```

`dist_k[i][j]` é o menor tempo de `i` até `j` usando só os `k` primeiros vértices como intermediários. Uma matriz `proximo` guarda o próximo passo para remontar a rota.

**Por que Floyd-Warshall e não só Dijkstra:** o Norte atende muitas pessoas no mesmo bairro, e o bairro tem poucas dezenas de vértices. Calcular todas as distâncias uma vez (`O(V³)`) e guardar o resultado (memoizado por modo: comum e acessível) deixa cada consulta em `O(1)`. Dijkstra (`O((V+E) log V)` por origem) foi implementado para **conferir** os resultados nos testes e para **comparar** o custo no benchmark. Bellman-Ford não foi necessário porque não existem tempos negativos.

**Rota acessível:** para o Carlos (cego) e o Seu José (idoso), o Norte só usa trechos acessíveis:

| Origem → destino | Rota mais rápida | Rota acessível |
|---|---|---|
| Ponto de ônibus → Defensoria | 13 min, pela Escadaria da Vila | 20 min, pela Praça da Matriz e Terminal |
| Conjunto habitacional → Delegacia da Mulher | 6 min, pela Viela do Morro | 20 min, pela Feira livre e Av. Central |

---

## 3. Noção de eficiência

Complexidades (`m`, `n` = tamanho das palavras; `T` = palavras do relato; `K` = palavras-chave; `n` ações; `C` = blocos de tempo; `V` vértices; `E` arestas):

| Parte | Versão ingênua | Versão com PD | Memória |
|---|---|---|---|
| Distância de edição | `O(3^(m+n))` | `O(m·n)` | `O(m·n)` (memo) ou `O(n)` (tabulada) |
| Triagem de um relato | `T·K` comparações exponenciais | `T·K·O(m·n)`, e pares repetidos em `O(1)` pelo cache | cache de até 200 mil pares |
| Plano da semana | `O(2^n · n)` (todas as combinações) | `O(n·C)` | `O(n·C)` |
| Menor caminho | exponencial (todos os caminhos simples) | Floyd-Warshall `O(V³)` uma vez + `O(1)` por consulta | `O(V²)` |

Resultados medidos com `python benchmarks/comparar_eficiencia.py` (Python 3.13; tempos mudam conforme o computador, a tendência não). Tabelas completas em [`benchmarks/resultados.md`](benchmarks/resultados.md).

| Medição | Sem otimização | Com PD |
|---|---|---|
| Distância de edição, palavras de 9 letras | 2.193.844 chamadas recursivas · ~200 ms | 100 subproblemas · ~0,05 ms |
| Distância de edição, palavras de 20 letras | inviável | ~0,3 ms |
| Triagem de 500 relatos com erros | ~17 ms por relato (sem cache de pares) | ~7 ms por relato (66% das comparações vêm do cache) |
| Mochila com 18 ações | 262.144 combinações · ~140 ms | 399 células · ~0,05 ms |
| Mochila com 100 ações | 1,27 × 10³⁰ combinações · inviável | ~0,24 ms |
| Menor caminho, grade 5×5 | todos os caminhos · ~21 ms | ~0,5 ms |
| 1.000 consultas num bairro de 100 vértices | Dijkstra a cada consulta · ~96 ms | Floyd-Warshall · ~24 ms no total |

**Por que o tamanho do cenário importa:** um relato real tem de 10 a 30 palavras, e o vocabulário das 10 áreas tem 185 termos, então são milhares de comparações por atendimento. Sem memoização, uma única palavra de 10 letras já trava o sistema. Um caso pode gerar 5 a 7 ações; com as trilhas das outras áreas e casos com várias áreas, a força bruta dobra de custo a cada ação nova. No mapa, o número de caminhos simples explode (mais de 1 milhão numa grade 6×6).

**O limite da escolha (trade-off honesto):** o benchmark mostra que, numa grade de **400 vértices**, Dijkstra passa a ser mais rápido que Floyd-Warshall (cerca de 0,5 s contra 1,6 s), porque `V³` cresce rápido. Para o mapa de um bairro (dezenas de vértices) Floyd-Warshall é a melhor escolha; para a cidade inteira, o Norte trocaria para Dijkstra (ou A*) por consulta.

---

## 4. Funcionalidades implementadas

1. **Triagem tolerante a erros nas 10 áreas** (trabalho, INSS, consumo, moradia, família, violência, saúde, idosos e PcD, trânsito, serviços públicos), mostrando quais palavras foram reconhecidas e como ("recisao→rescisao"). Se nada for reconhecido, a pessoa escolhe a área numa lista.
2. **Plano de ação com regras da curadoria:** cada ação traz o artigo da lei e o link oficial. Só são citadas normas marcadas como vigentes (`revogada: false`) no acervo ctresb/leis; os cabeçalhos foram conferidos no repositório em 09/11/2026.
3. **Alertas de prazo com semáforo:** vermelho (até 15 dias), amarelo (até 60), verde, sem prazo curto, a confirmar (sem data informada) e prazo vencido. Ex.: 30 dias para recorrer no INSS, 7 a 120 dias para o seguro-desemprego, 2 anos para a reclamação trabalhista, 30 dias para a defesa da multa.
4. **Plano da semana (mochila):** escolhe o que cabe nas horas livres da pessoa e deixa o resto para as próximas semanas.
5. **Estimativa de valores:** FGTS não depositado + reflexo na multa de 40% (Lei 8.036/1990) e devolução em dobro de cobrança indevida (CDC, art. 42).
6. **"Preciso de advogado?"** por área, com os limites de 20 e 40 salários mínimos no Juizado Especial Cível, 60 no Juizado Especial Federal (salário mínimo 2026: R$ 1.621,00) e as regras do trabalho, da família, do trânsito e da violência.
7. **Atendimento gratuito do mais perto ao mais longe**, com rota passo a passo, horário de funcionamento e **modo rota acessível**.
8. **Checklist de documentos** das ações da semana, sem repetição.
9. **Perfil prioritário:** pessoa idosa ou com deficiência recebe também os direitos de prioridade (e a gratuidade no transporte só aparece para 65+).
10. **Modo discreto** sinalizado nos casos de violência.
11. **Menu interativo** no terminal e **modo demonstração** com as 6 personas.
12. **20 testes automáticos** e **benchmark** de eficiência.

---

## 5. Como executar

Requisitos: **Python 3.10 ou mais novo**. Usa só a biblioteca padrão (não precisa instalar nada).

```bash
# entrar na pasta do projeto
cd norte-dp

# demonstração com as 6 personas (data fixa para o resultado ser sempre o mesmo)
python main.py --demo --hoje 2026-11-19

# um caso só
python main.py --caso jose --hoje 2026-11-19

# menu interativo (conte o seu caso)
python main.py

# testes de funcionamento
python -m unittest discover -s tests -v

# comparação de eficiência (leva cerca de 20 segundos)
python benchmarks/comparar_eficiencia.py
```

Casos disponíveis em `--caso`: `marcia`, `jose`, `juliana`, `rafael`, `ana_paula`, `carlos`.

## 6. Exemplo de entrada e saída

**Entrada** (caso `marcia` em `dados/casos_exemplo.json`): relato *"fui demitida sem justa causa depois de 9 anos, assinei a recisão e acho que o fgts nao foi depozitado em varios meses"*, 4 horas livres, demitida em 27/10/2026, salário R$ 1.850,00, 7 meses sem FGTS, saindo do ponto de ônibus.

**Saída** (trecho de `python main.py --caso marcia --hoje 2026-11-19`):

```
1) SEU ASSUNTO (triagem)
   • Trabalho e emprego – reconheci: demitida, justa, causa, recisao→rescisao, fgts

2) QUANTO PODE ESTAR EM JOGO (estimativa)
   • FGTS de 7 meses sem depósito: R$ 1.036,00 + reflexo na multa de 40%: R$ 414,40 = R$
     1.450,40 (Lei 8.036/1990, arts. 15 e 18, § 1º)

3) O QUE FAZER ESTA SEMANA (você tem 4 h; plano usa 3 h 30 min)
  1. Dar entrada no seguro-desemprego (entre o 7º e o 120º dia após a demissão)
   [VERDE – em dia] até 24/02/2027 (97 dias) · cerca de 60 min
  2. Pedir o extrato do FGTS (app FGTS ou agência da Caixa) ...
  3. Levar a rescisão ao sindicato ou ao atendimento gratuito ...

   Para as próximas semanas:
  4. Entrar com reclamação trabalhista ...
   [VERDE – em dia] até 27/10/2028 (708 dias) · cerca de 180 min
   Lei: Constituição Federal de 1988, art. 7º, XXIX – https://www.planalto.gov.br/...

4) PRECISO DE ADVOGADO?
   • Trabalho e emprego: Não é obrigatório: na Justiça do Trabalho o empregado pode
     reclamar pessoalmente (CLT, art. 791). O sindicato e a Defensoria ajudam de graça.

5) ONDE BUSCAR ATENDIMENTO GRATUITO – rota mais rápida a pé
     • Sindicato da categoria (sede regional) – 10 min a pé · seg a sex, 8h às 17h
       rota: Ponto de ônibus da Rua das Flores → Praça da Matriz → Sindicato ...

6) CHECKLIST DE DOCUMENTOS (para as ações desta semana)
   [ ] Termo de rescisão (TRCT)
   [ ] Carteira de trabalho
   ...
```

---

## 7. Estrutura de pastas

```
norte-dp/
├── README.md                    este arquivo
├── main.py                      menu interativo, --demo e --caso
├── norte/
│   ├── triagem.py               MEMOIZAÇÃO: distância de edição e classificação do relato
│   ├── plano.py                 TABULAÇÃO: mochila 0/1 do plano da semana
│   ├── atendimento.py           GRAFOS: Floyd-Warshall (e Dijkstra para conferência)
│   ├── orientador.py            junta as três partes e escreve o plano de ação
│   ├── prazos.py                semáforo de prazos (peso de urgência da mochila)
│   ├── calculos.py              estimativas de valores e "preciso de advogado?"
│   └── dados.py                 leitura dos arquivos JSON
├── dados/
│   ├── areas.json               10 áreas: vocabulário da triagem, órgãos e ações da curadoria
│   ├── leis.json                normas citadas, vigência e link oficial
│   ├── bairro.json              mapa simulado do bairro (grafo)
│   └── casos_exemplo.json       casos fictícios das personas
├── tests/
│   └── test_norte.py            20 testes (unittest)
└── benchmarks/
    ├── comparar_eficiencia.py   versão ingênua x versão com PD
    └── resultados.md            última execução do benchmark
```

## 8. Dados, privacidade e limites

- **Nenhum dado pessoal real.** As personas e os relatos são fictícios (os mesmos do documento de Agile). O mapa é um bairro **simulado**, com nomes genéricos e sem endereços reais.
- **Leis:** cabeçalhos (número, data, vigência e link oficial `normas.leg.br`) conferidos no repositório aberto [ctresb/leis](https://github.com/ctresb/leis) em 09/11/2026; o texto dos artigos citados foi conferido no próprio acervo. CLT e Decreto 3.048/1999 apontam para o Planalto. Salário mínimo de 2026: R$ 1.621,00.
- **Valores, tempos e impactos** das ações são estimativas do protótipo; na versão final, a curadoria jurídica mantém essas regras.
- O Norte dá **orientação, não consultoria jurídica**: todo plano termina indicando o atendimento gratuito.

## 9. ODS

| ODS | Como estes algoritmos contribuem |
|---|---|
| 1 – Erradicação da pobreza | Prioriza prazos de benefícios (INSS/BPC) para a pessoa não perder o direito |
| 3 – Saúde e bem-estar | Orienta sobre negativa de plano de saúde e SUS |
| 5 – Igualdade de gênero | Encaminha casos de violência à rede de proteção, com modo discreto |
| 8 – Trabalho decente | Estima FGTS não depositado e organiza a cobrança dos direitos da rescisão |
| 10 – Redução das desigualdades | Triagem tolerante a erros e rota acessível para quem mais tem dificuldade |
| 16 – Paz, justiça e instituições eficazes | Explica quando dá para ir ao Juizado sem advogado e indica o atendimento gratuito mais perto |
