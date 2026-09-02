# Sessão experimental — geografia da fase 1

Workspace para fechar os quatro parâmetros que bloqueiam a substituição da
`06_anon_endereco.py`. Nada aqui roda pela pipeline: são medições de apoio
à decisão.

## O que precisa ser decidido

| # | Decisão | Depende de |
|---|---|---|
| 1 | **Eixo geográfico**: território de saúde ou geografia do IBGE | exp. 01 e 02 |
| 2 | **Nível** dentro do eixo escolhido | exp. 02 |
| 3 | **Valor de k** | exp. 02 |
| 4 | **Largura da faixa de distância** | exp. 03 (bloqueado) |

## O que já se sabe, e que restringe o espaço

**As duas partições não se encaixam.** A base carrega o território de saúde
(micro-área ⊂ área) e a geografia do IBGE (setor ⊂ bairro), que dividem a
mesma cidade com limites diferentes. Publicar as duas em resolução fina é
pior que publicar qualquer uma sozinha, porque a interseção de duas
partições é sempre mais fina que ambas. **Escolher um eixo é obrigatório**,
não preferência.

**Os dois eixos têm custo muito diferente.** No eixo da saúde, micro-área e
área já são colunas da base — custo zero. No eixo do IBGE, `no_bairro` é
nativo mas é texto livre (existe a variante `no_bairro_filtro`, indício de
que já foi preciso normalizar), e **setor censitário não existe na base**:
exigiria a malha do IBGE mais ponto-em-polígono sobre os ~3,5 mil domicílios
geolocalizados. É dependência externa real, com biblioteca geoespacial.

**Município é partição trivial.** A base é de um município só, então esse
nível tem k = N e não informa nada. É o nível que a migration 06 usa hoje.

**A micro-área provavelmente é fina demais.** Estimativa a confirmar no
exp. 01: ~950 cidadãos por equipe, 2 a 4 agentes por equipe, logo 22 a 44
micro-áreas de ~240 a ~475 pessoas — mais fina que um setor censitário
urbano. Se confirmar, ela sai como nível publicável e vira só o nível G0 da
hierarquia (suprimido pela `14_anon_territorio.py`).

## Regra de decisão

Publicar **o nível mais fino** que satisfaça, simultaneamente:

1. `k ≥ 20` no bucket geográfico isolado;
2. `k ≥ 20` no **par** (bucket, faixa de distância) — não em cada um
   separadamente. O anel em torno da unidade cruzado com o polígono do
   bucket pode ter interseção pequena;
3. um k que ainda se sustente quando a fase 2 acrescentar sexo e mês/ano de
   nascimento ao conjunto de quase-identificadores.

O item 3 é o que evita retrabalho: um nível que dá k = 20 sobre geografia
isolada pode dar k = 1 sobre {geografia, sexo, mês/ano}. O exp. 02 mede os
dois de uma vez justamente por isso.

Se nenhum nível satisfizer os três, a saída é alargar a banda de distância
(o que degrada a distribuição de distância) ou subir um nível na hierarquia
(o que degrada a resolução espacial). A troca é explícita e deve ser
registrada.

## Ordem de execução

```
01_micro_areas.py        →  confirma se a micro-área é mais fina que o setor
02_k_por_nivel.py        →  elimina os níveis inviáveis, com e sem fase 2
     ↓
[ geocodificar as 12 unidades à mão → unidades_coordenadas.csv ]
     ↓
03_faixa_de_distancia.py →  fecha a largura da banda e o k do par
```

O passo do meio é **trabalho manual e humano**: doze endereços consultados
no cadastro público do CNES. Precisa acontecer antes da `02_anon_unidade_saude.py`
rodar na base de trabalho, porque ela substitui o CNES usado na consulta.

## Como rodar

Os scripts leem a conexão do `.env` na raiz do projeto, igual à pipeline:

```bash
python experimentos/geografia/01_micro_areas.py
python experimentos/geografia/02_k_por_nivel.py
python experimentos/geografia/03_faixa_de_distancia.py
```

Cada um imprime um resumo legível e grava um JSON em `resultados/`
(ignorado pelo Git).

Variáveis opcionais: `ENV_FILE` para apontar outro `.env`,
`STATEMENT_TIMEOUT_MS` para dar mais folga em tabela grande.

## Disciplina destas medições

Os scripts abrem a sessão como **read-only** no Postgres, então nenhum
`UPDATE`/`DELETE`/DDL é possível nem por acidente. Só emitem **agregado** —
contagens, quantis e nomes de coluna. Nenhum CEP, endereço, coordenada ou
identificador entra na saída ou no JSON, o que permite rodar contra a base
real e compartilhar o resultado sem triagem.

`unidades_coordenadas.csv` é a **única** exceção: contém coordenadas de
unidades de saúde, que são entidades institucionais de endereço público.
Nenhuma coordenada de domicílio ou de cidadão deve ser colocada ali.
