# Coleta com usuários: resultados SIMULADOS

> **Atenção: nada nesta pasta foi respondido por pessoas.** Os dados foram gerados por
> `ml/training/coleta/simular.py` a partir de suposições escritas no próprio arquivo, para
> montar e testar a análise antes da coleta real. Os números servem de exemplo de formato
> e **não podem ser apresentados como resultado da pesquisa**. Quando a coleta real
> terminar, rode os mesmos comandos sobre os dados reais (ver "Com os dados reais") e
> use a pasta `docs/resultados/coleta/`.

## O que foi simulado

10 participantes (P01 a P10), cada um com 8 a 12 tarefas da semana, 101 tarefas no total.
As principais suposições, todas ajustáveis no início de `simular.py`:

- cada pessoa prioriza com pesos próprios, em média com um pouco mais de peso para o
  impacto (0,44) e menos para o prazo (0,38) do que a regra que rotulou a base (0,35 e 0,45);
- 12% das prioridades da ficha fogem do padrão (ruído de julgamento);
- quando a sugestão difere da ficha, a pessoa aceita assim mesmo em 30% dos casos;
- uma tarefa foi salva sem sugestão (serviço de ML fora do ar);
- a nota SUS de cada pessoa sai de uma distribuição com média perto de 78.

## Medidas do Quadro 7

| Medida | Resultado simulado |
| --- | --- |
| Taxa de aceitação | 82 de 100 sugestões confirmadas (82%) |
| Concordância cega (sugestão × ficha) | acurácia 0,78; F1 macro 0,733 (100 tarefas) |
| Concordância após a sugestão (sugestão × confirmada) | acurácia 0,82; F1 macro 0,790 |
| Influência da sugestão | 6 das 22 sugestões que contrariavam a ficha foram aceitas assim mesmo (27%) |
| Utilidade percebida | 73 de 100 avaliadas responderam "sim" (82% quando aceita, 33% quando ajustada) |
| Disponibilidade | 1 de 101 tarefas salva sem sugestão (1%) |
| Confiança média do modelo | 0,90 nas aceitas e 0,81 nas ajustadas |

Comparação com a base simulada: o F1 macro cego (0,733) ficou 0,12 abaixo do obtido na
base mockada (0,856). Por classe, na ficha: alta 0,89, média 0,69 e baixa 0,62.

Matrizes de confusão: [`matriz-cega.png`](matriz-cega.png) e
[`matriz-confirmada.png`](matriz-confirmada.png).

Direção dos ajustes (ficha × sugestão): as pessoas subiram 10 sugestões e baixaram 12.
Nas tarefas com prazo acima de 14 dias, 5 de 10 foram subidas. Nas tarefas com prazo de
até 3 dias, nenhuma foi subida e 6 de 40 foram baixadas. O detalhe por prazo, impacto,
esforço e categoria está em `metricas.json` (`direcao_ficha` e `direcao_ajustes`).

## Questionário

**SUS (parte B):** média 75,5 (mediana 76,25; desvio 7,6; de 62,5 a 87,5). 8 dos 10
participantes ficaram acima da referência de 68 pontos. Ver [`sus.png`](sus.png).

**Parte C (mediana e % de respostas 4 ou 5):**

| Item | Aspecto | Mediana | Concordam |
| --- | --- | --- | --- |
| C1 | Qualidade | 4,5 | 90% |
| C2 | Qualidade | 4 | 70% |
| C3 | Compreensão | 4 | 70% |
| C4 | Compreensão | 4 | 100% |
| C5 | Confiança | 4 | 70% |
| C6 | Controle | 5 | 100% |
| C7 | Utilidade | 4 | 100% |
| C8 | Organização | 4 | 70% |
| C9 | Satisfação | 4 | 90% |
| C10 | Satisfação | 4 | 90% |

Ver [`likert-parte-c.png`](likert-parte-c.png). O perfil (parte A) e as respostas abertas
(parte D) estão em `metricas.json`.

**Observação:** 30 ocorrências, agrupadas pelos temas confiança (8), melhoria (7),
usabilidade (6), discordância (6) e clareza (3).

## Retreino (RF12)

A versão 2 foi treinada com a base mockada e as tarefas dos participantes, rotuladas com a
prioridade confirmada e peso 10. A avaliação deixou um participante de fora por vez e
testou na ficha dele (101 tarefas, incluindo a que ficou sem sugestão):

| Modelo | Acurácia na ficha | F1 macro na ficha | F1 macro na base mockada |
| --- | --- | --- | --- |
| v1 (só base mockada) | 0,782 | 0,733 | 0,828 |
| v2 (base + coleta) | 0,792 | 0,764 | 0,827 |

O ganho simulado é pequeno (3 pontos de F1) e a v2 não piora na base mockada. Com dados
simulados, o modelo v2 **não** é salvo em `ml/models`.

## Arquivos

- `dados/`: os quatro CSVs de entrada simulados (`registros`, `ficha`, `questionario`, `observacao`).
- `metricas.json`: todas as medidas, por participante e por atributo.
- `retreino.json`: comparação v1 × v2.
- `tarefas-anonimizadas.csv`: registros cruzados com a ficha, sem os títulos das tarefas.
- `*.png`: gráficos, marcados como "DADOS SIMULADOS".

## Com os dados reais

1. Monte `participantes.csv` com `email,participante` (por exemplo, `ana@exemplo.com,P01`).
   Não publique esse arquivo.
2. Exporte os registros do banco publicado (a partir de `api/`):

   ```bash
   DATABASE_URL="postgresql+psycopg://..." python -m app.exportar_coleta participantes.csv --saida ../coleta
   ```

3. Na mesma pasta `coleta/`, salve as planilhas digitadas com estas colunas:
   - `ficha.csv`: `participante,titulo,prioridade` (título igual ao cadastrado na aplicação);
   - `questionario.csv`: `participante,A1_faixa_etaria,A2_ocupacao,A3_frequencia_lista,A4_metodo_atual,B1..B10,C1..C10,D1..D4`;
   - `observacao.csv`: `participante,momento,ocorrencia,tarefa,tema`.
4. Analise e retreine (a partir de `ml/training`):

   ```bash
   python -m coleta.analisar ../../coleta --saida ../../docs/resultados/coleta
   python -m coleta.retreinar ../../coleta --saida ../../docs/resultados/coleta
   ```

   Se a v2 for melhor na ficha, `--salvar` grava `ml/models/modelo-v2.*`.
5. Depois de conferir a exportação, apague as contas de teste, como promete o termo:

   ```bash
   python -m app.exportar_coleta participantes.csv --apagar-contas
   ```

Publique no repositório só `tarefas-anonimizadas.csv`, os resultados e os gráficos. Os
arquivos com títulos de tarefas e e-mails ficam fora do Git.
