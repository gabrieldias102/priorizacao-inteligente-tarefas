# Resultados da fase 1: comparação dos modelos

Base mockada de 3.000 tarefas (2.400 para treino e 600 para teste, semente 42), rotulada pela regra `S = 0,45·U + 0,35·I + 0,10·C + 0,10·R`, com 10% dos rótulos trocados para uma classe vizinha. Hiperparâmetros escolhidos por validação cruzada de 5 dobras com F1 macro. Os números abaixo são do conjunto de teste.

| Modelo | F1 macro (validação) | Acurácia (teste) | F1 macro (teste) |
| --- | --- | --- | --- |
| Classe majoritária (linha de base) | | 0,375 | 0,182 |
| Regra sem ruído (teto prático) | | 0,905 | 0,906 |
| Regressão Logística (C = 10) | 0,775 | 0,742 | 0,746 |
| **Árvore de Decisão** (min_samples_leaf = 5) | **0,851** | **0,853** | **0,856** |
| Random Forest (100 árvores, min_samples_leaf = 5) | 0,846 | 0,847 | 0,849 |

A Árvore de Decisão foi escolhida pela validação cruzada e salva em `ml/models/modelo-v1.joblib`. Ela fica a cerca de 5 pontos do teto da regra. A Regressão Logística fica atrás porque a urgência muda em degraus conforme o prazo, o que um modelo linear aproxima mal.

Prazo e impacto são os atributos mais importantes nos três modelos, coerente com os pesos da regra. A classe média é a mais difícil (F1 de 0,80 na árvore), porque recebe ruído dos dois lados.

Arquivos:

- `metricas.json`: todas as métricas, por classe, hiperparâmetros e importância dos atributos.
- `matriz-*.png`: matrizes de confusão de cada algoritmo.
- `ml/notebooks/01_comparacao_modelos.ipynb`: o passo a passo com tabelas e gráficos.

Para reproduzir: `cd ml/training && python -m treino.treinar`.
