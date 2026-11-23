"""Exporta receitas, atestados e SOAP pseudo-anonimizados, numa execução só.

Os três arquivos compartilham o `paciente_id` (permutação aleatória dos
cidadãos, sem mapeamento salvo), o deslocamento de datas por paciente
(múltiplo de 7 dias entre -26 e +26 semanas, nunca zero, não salvo) e o mapa
de nomes fictícios, então a mesma pessoa e o mesmo nome aparecem iguais nos
três. Ligam-se pelo `atendimento_prof_id`. Texto livre passa por
`_anon_texto.Anonimizador`.

Do paciente vão só sexo, idade no atendimento (90+ agrupado) e o ID
pseudônimo. A unidade sai como "Unidade de Saúde N", com a numeração da
migration 02. Ficam de fora nome, CPF, CNS, endereço, telefone, nome do
profissional e os códigos RNDS/prescrição digital da receita.

Uso: 04_exporta.py <pasta de saída>
Grava, para envio: 04_receitas_medicamento.csv, 05_atestados.csv, 06_soap.csv.
Só para conferência local (têm o texto original): 05_atestados_verificacao.csv,
06_soap_verificacao.csv e os *_residuo.txt."""

import csv
import os
import random
import re
import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

from _anon_texto import (CNS_RE, CPF_RE, PALAVRA, PARTICULAS, Anonimizador, Paciente,
                        cns_valido, cpf_valido, monta_lexicos, normalizar, parecido)

RAIZ = Path(__file__).resolve().parents[3]
SEXO = {"FEMININO": "F", "MASCULINO": "M"}
MUNICIPIOS = {"Doutor Severiano": "Município 1", "Portalegre": "Município 2"}
# Descrição pelo conteúdo: o PEC não tem tabela de domínio para tp_atestado.
TIPO_ATESTADO = {1: "em branco (texto livre)", 2: "padrão (afastamento)",
                 5: "modelo 'encontra-se em acompanhamento' (condição clínica)",
                 None: "versão antiga do PEC (sem tipo)"}
COLUNAS_UNIDADE = ["ta_unidade_saude", "tb_unidade_saude", "tb_dim_unidade_saude",
                   "tl_unidade_saude"]


def conecta():
    load_dotenv(RAIZ / ".env")
    return psycopg2.connect(host=os.environ["DB_HOST"], port=os.environ["DB_PORT"],
                            user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
                            dbname=os.environ["DB_NAME"], connect_timeout=15,
                            options="-c client_encoding=utf8")


SQL_RECEITAS = r"""
with cid_atend as (
    select r.co_atend_prof,
           string_agg(distinct c.nu_cid10 || ' - ' || c.no_cid10, ' | ') as cids,
           string_agg(distinct p.co_ciap || ' - ' || p.ds_ciap, ' | ') as ciaps
    from rl_evolucao_avaliacao_ciap_cid r
    left join tb_cid10 c on c.co_cid10 = r.co_cid10
    left join tb_ciap p on p.co_seq_ciap = r.co_ciap
    where r.co_atend_prof in (select co_atend_prof from tb_receita_medicamento)
    group by r.co_atend_prof
)
select
    rm.co_seq_receita_medicamento            as receita_id,
    rm.co_atend_prof                         as atendimento_prof_id,
    cid.co_seq_cidadao                       as _cidadao,
    -- receita
    rm.no_posologia                          as posologia,
    rm.ds_recomendacao                       as recomendacao,
    m.no_principio_ativo                     as medicamento,
    m.ds_concentracao                        as concentracao,
    ff.no_forma_farmaceutica                 as forma_farmaceutica,
    m.ds_unidade_fornecimento                as unidade_fornecimento,
    am.no_aplicacao_medicamento              as via_administracao,
    tr.no_tipo_receita                       as tipo_receita,
    rm.qt_receitada                          as qt_receitada,
    rm.ds_dose                               as dose,
    rm.qt_dose                               as qt_dose,
    um.no_unidade_medida                     as unidade_medida_dose,
    rm.qt_dose_manha, rm.qt_dose_tarde, rm.qt_dose_noite,
    rm.st_dose_unica                         as dose_unica,
    tf.no_tipo_frequencia                    as tipo_frequencia,
    rm.ds_frequencia_dose                    as frequencia_dose,
    rm.qt_periodo_frequencia                 as qt_periodo_frequencia,
    umtf.no_unidade_medida_tempo             as unidade_tempo_frequencia,
    rm.qt_duracao_tratamento                 as qt_duracao_tratamento,
    umtt.no_unidade_medida_tempo             as unidade_tempo_tratamento,
    rm.dt_inicio_tratamento, rm.dt_fim_tratamento,
    rm.st_uso_continuo                       as uso_continuo,
    rm.co_receita_uso_continuo_grupo         as receita_uso_continuo_grupo_id,
    rm.st_registro_manual                    as registro_manual,
    rm.st_interrompido                       as interrompido,
    rm.dt_interrupcao,
    rm.ds_observacao_interrupcao             as observacao_interrupcao,
    rc.nu_cid10 || ' - ' || rc.no_cid10      as receita_cid10,
    rp.co_ciap || ' - ' || rp.ds_ciap        as receita_ciap,
    -- atendimento
    ap.dt_inicio::date                       as data_atendimento,
    tap.no_tipo_atend_prof                   as tipo_atendimento_prof,
    ta.no_tipo_atend                         as tipo_atendimento,
    la.no_local_atend                        as local_atendimento,
    cbo.co_cbo_2002                          as cbo_profissional,
    cbo.no_cbo                               as ocupacao_profissional,
    us.no_unidade_saude                      as _unidade,
    ap.st_cancelado                          as atendimento_cancelado,
    ca.cids                                  as cids_atendimento,
    ca.ciaps                                 as ciaps_atendimento,
    -- paciente
    cid.no_sexo                              as sexo,
    date_part('year', age(ap.dt_inicio::date, cid.dt_nascimento))::int as _idade
from tb_receita_medicamento rm
left join tb_medicamento m             on m.co_seq_medicamento = rm.co_medicamento
left join tb_forma_farmaceutica ff     on ff.co_forma_farmaceutica = m.co_forma_farmaceutica
left join tb_aplicacao_medicamento am  on am.co_aplicacao_medicamento = rm.co_aplicacao_medicamento
left join tb_tipo_receita tr           on tr.co_tipo_receita = rm.tp_receita
left join tb_unidade_medida um         on um.co_unidade_medida = rm.co_unidade_medida_dose
left join tb_receita_tipo_frequencia tf on tf.co_receita_tipo_frequencia = rm.tp_frequencia_dose
left join tb_unidade_medida_tempo umtf on umtf.co_unidade_medida_tempo = rm.tp_un_medida_tempo_frequencia
left join tb_unidade_medida_tempo umtt on umtt.co_unidade_medida_tempo = rm.tp_un_medida_tempo_tratamento
left join tb_cid10 rc                  on rc.co_cid10 = rm.co_cid10
left join tb_ciap rp                   on rp.co_seq_ciap = rm.co_ciap
left join tb_atend_prof ap             on ap.co_seq_atend_prof = rm.co_atend_prof
left join tb_tipo_atend_prof tap       on tap.co_tipo_atend_prof = ap.tp_atend_prof
left join tb_tipo_atend ta             on ta.co_tipo_atend = ap.tp_atend
left join tb_lotacao lo                on lo.co_ator_papel = ap.co_lotacao
left join tb_cbo cbo                   on cbo.co_cbo = lo.co_cbo
left join tb_atend a                   on a.co_seq_atend = ap.co_atend
left join tb_local_atend la            on la.co_local_atend = a.tp_local_atend
left join tb_unidade_saude us          on us.co_seq_unidade_saude = a.co_unidade_saude
left join tb_prontuario pr             on pr.co_seq_prontuario = a.co_prontuario
left join tb_cidadao cid               on cid.co_seq_cidadao = pr.co_cidadao
left join cid_atend ca                 on ca.co_atend_prof = rm.co_atend_prof
order by rm.co_seq_receita_medicamento
"""

# ta_/tl_atestado não têm atestado nem texto fora da tb_.
SQL_ATESTADOS = r"""
select
    at.co_seq_atestado                       as atestado_id,
    at.co_atend_prof                         as atendimento_prof_id,
    cid.co_seq_cidadao                       as _cidadao,
    at.tp_atestado                           as _tipo,
    at.ds_atestado                           as texto_atestado,
    at.dt_afastamento::date                  as dt_afastamento,
    at.nu_dias                               as dias_afastamento,
    c.nu_cid10 || ' - ' || c.no_cid10        as cid10_atestado,
    at.st_assinado_digitalmente              as assinado_digitalmente,
    ap.dt_inicio::date                       as data_atendimento,
    tap.no_tipo_atend_prof                   as tipo_atendimento_prof,
    ta.no_tipo_atend                         as tipo_atendimento,
    cbo.co_cbo_2002                          as cbo_profissional,
    cbo.no_cbo                               as ocupacao_profissional,
    us.no_unidade_saude                      as _unidade,
    cid.no_sexo                              as sexo,
    date_part('year', age(ap.dt_inicio::date, cid.dt_nascimento))::int as _idade
from tb_atestado at
left join tb_cid10 c             on c.co_cid10 = at.co_cid10
left join tb_atend_prof ap       on ap.co_seq_atend_prof = at.co_atend_prof
left join tb_tipo_atend_prof tap on tap.co_tipo_atend_prof = ap.tp_atend_prof
left join tb_tipo_atend ta       on ta.co_tipo_atend = ap.tp_atend
left join tb_lotacao lo          on lo.co_ator_papel = ap.co_lotacao
left join tb_cbo cbo             on cbo.co_cbo = lo.co_cbo
left join tb_atend a             on a.co_seq_atend = ap.co_atend
left join tb_unidade_saude us    on us.co_seq_unidade_saude = a.co_unidade_saude
left join tb_prontuario pr       on pr.co_seq_prontuario = at.co_prontuario
left join tb_cidadao cid         on cid.co_seq_cidadao = pr.co_cidadao
order by at.co_seq_atestado
"""

# Uma linha por atendimento com algum texto do SOAP (sem contar só marcação,
# como "<p><br></p>"). ta_/tl_evolucao_* não têm atendimento nem texto fora da tb_.
COM_CONTEUDO = r"btrim(regexp_replace(regexp_replace(coalesce({c}, ''), '<[^>]*>', '', 'g'), '&nbsp;|\s', '', 'g')) <> ''"
SQL_SOAP = r"""
with soap as (
    select ap.co_seq_atend_prof as co_atend_prof, s.ds_subjetivo, o.ds_objetivo, av.ds_avaliacao, p.ds_plano
    from tb_atend_prof ap
    left join tb_evolucao_subjetivo s on s.co_atend_prof = ap.co_seq_atend_prof
    left join tb_evolucao_objetivo o  on o.co_atend_prof = ap.co_seq_atend_prof
    left join tb_evolucao_avaliacao av on av.co_atend_prof = ap.co_seq_atend_prof
    left join tb_evolucao_plano p     on p.co_atend_prof = ap.co_seq_atend_prof
    where """ + " or ".join(COM_CONTEUDO.format(c=c) for c in
                           ("s.ds_subjetivo", "o.ds_objetivo", "av.ds_avaliacao", "p.ds_plano")) + r"""
), problema as (
    select r.co_atend_prof,
           string_agg(distinct c.nu_cid10 || ' - ' || c.no_cid10, ' | ') as cids,
           string_agg(distinct cp.co_ciap || ' - ' || cp.ds_ciap, ' | ') as ciaps,
           string_agg(nullif(btrim(r.ds_nota), ''), ' | ') as notas
    from rl_evolucao_avaliacao_ciap_cid r
    left join tb_cid10 c on c.co_cid10 = r.co_cid10
    left join tb_ciap cp on cp.co_seq_ciap = r.co_ciap
    group by r.co_atend_prof
)
select
    soap.co_atend_prof                       as atendimento_prof_id,
    cid.co_seq_cidadao                       as _cidadao,
    soap.ds_subjetivo                        as subjetivo,
    soap.ds_objetivo                         as objetivo,
    soap.ds_avaliacao                        as avaliacao,
    soap.ds_plano                            as plano,
    pb.cids                                  as cids_atendimento,
    pb.ciaps                                 as ciaps_atendimento,
    pb.notas                                 as notas_cid_ciap,
    (select count(*) from tb_receita_medicamento x where x.co_atend_prof = soap.co_atend_prof) as qt_receitas,
    (select count(*) from tb_atestado x where x.co_atend_prof = soap.co_atend_prof) as qt_atestados,
    ap.dt_inicio::date                       as data_atendimento,
    tap.no_tipo_atend_prof                   as tipo_atendimento_prof,
    ta.no_tipo_atend                         as tipo_atendimento,
    la.no_local_atend                        as local_atendimento,
    cbo.co_cbo_2002                          as cbo_profissional,
    cbo.no_cbo                               as ocupacao_profissional,
    us.no_unidade_saude                      as _unidade,
    cid.no_sexo                              as sexo,
    date_part('year', age(ap.dt_inicio::date, cid.dt_nascimento))::int as _idade
from soap
join tb_atend_prof ap            on ap.co_seq_atend_prof = soap.co_atend_prof
left join problema pb            on pb.co_atend_prof = soap.co_atend_prof
left join tb_tipo_atend_prof tap on tap.co_tipo_atend_prof = ap.tp_atend_prof
left join tb_tipo_atend ta       on ta.co_tipo_atend = ap.tp_atend
left join tb_lotacao lo          on lo.co_ator_papel = ap.co_lotacao
left join tb_cbo cbo             on cbo.co_cbo = lo.co_cbo
left join tb_atend a             on a.co_seq_atend = ap.co_atend
left join tb_local_atend la      on la.co_local_atend = a.tp_local_atend
left join tb_unidade_saude us    on us.co_seq_unidade_saude = a.co_unidade_saude
left join tb_prontuario pr       on pr.co_seq_prontuario = a.co_prontuario
left join tb_cidadao cid         on cid.co_seq_cidadao = pr.co_cidadao
order by soap.co_atend_prof
"""

CAMPOS_PACIENTE = """,
    cid.no_cidadao as _no_cidadao, cid.no_social as _no_social, cid.no_mae as _no_mae,
    cid.no_pai as _no_pai, cid.no_responsavel as _no_responsavel,
    cid.no_cuidador as _no_cuidador, cid.nu_cpf as _cpf, cid.nu_cns as _cns
from """

TEXTO_RECEITA = ["posologia", "recomendacao", "dose", "observacao_interrupcao"]
DATAS_RECEITA = ["dt_inicio_tratamento", "dt_fim_tratamento", "dt_interrupcao", "data_atendimento"]
DATAS_ATESTADO = ["dt_afastamento", "data_atendimento"]
TEXTO_SOAP = ["subjetivo", "objetivo", "avaliacao", "plano", "notas_cid_ciap"]
DATAS_SOAP = ["data_atendimento"]


def rotulos_unidade(cur) -> dict[str, str]:
    """Mesmo mapeamento da migration 02: nomes distintos ordenados."""
    nomes: set[str] = set()
    for tabela in COLUNAS_UNIDADE:
        cur.execute("select to_regclass(%s)", (f"public.{tabela}",))
        if cur.fetchone()[0] is None:
            continue
        cur.execute(f"select distinct no_unidade_saude from {tabela} "
                    "where no_unidade_saude is not null and btrim(no_unidade_saude) <> ''")
        nomes |= {r[0] for r in cur.fetchall()}
    return {n: f"Unidade de Saúde {i}" for i, n in enumerate(sorted(nomes), start=1)}


def com_paciente(sql: str) -> str:
    """Acrescenta os campos do cadastro que o anonimizador procura no texto
    (prefixo `_`: não vão para o CSV)."""
    i = sql.index("\nfrom ")
    return sql[:i] + CAMPOS_PACIENTE + sql[i + len("\nfrom "):]


def consulta(cur, sql: str) -> list[dict]:
    cur.execute(sql)
    nomes = [d[0] for d in cur.description]
    return [dict(zip(nomes, l)) for l in cur.fetchall()]


def paciente_de(reg: dict) -> Paciente:
    sexo = SEXO.get(reg["sexo"])
    nomes = [(reg["_no_cidadao"], sexo), (reg["_no_social"], sexo), (reg["_no_mae"], "F"),
             (reg["_no_pai"], "M"), (reg["_no_responsavel"], None), (reg["_no_cuidador"], None)]
    return Paciente(sexo, [(n, s) for n, s in nomes if n and n.strip()], reg["_cpf"], reg["_cns"])


def palavras_comuns(textos: list[str]) -> set[str]:
    """Palavras que aparecem em minúscula (>= 3 vezes) em texto de caixa mista:
    são palavra comum, não nome (ex.: "rosa", "dores", "graça")."""
    conta = Counter()
    for t in textos:
        if not t or t.isupper() or t.islower():
            continue
        conta.update(normalizar(w) for w in PALAVRA.findall(re.sub(r"<[^>]*>", " ", t))
                     if w.islower())
    return {w for w, n in conta.items() if n >= 3}


def lexicos(cur, textos: list[str]):
    nomes, proprios = [], []
    cur.execute("select no_cidadao, no_social, no_mae, no_pai, no_responsavel, no_cuidador, no_sexo "
                "from tb_cidadao")
    for cidadao, social, mae, pai, resp, cuid, sexo in cur.fetchall():
        s = SEXO.get(sexo)
        nomes += [(cidadao, s), (social, s), (mae, "F"), (pai, "M"), (resp, None), (cuid, None)]
        proprios += [(cidadao, s), (social, s)]
    cur.execute("select no_civil_profissional, no_social_profissional, no_sexo from tb_prof")
    for civil, social, sexo in cur.fetchall():
        nomes += [(civil, SEXO.get(sexo)), (social, SEXO.get(sexo))]
    return monta_lexicos([(n, s) for n, s in nomes if n], palavras_comuns(textos), proprios)


def uma_linha(v):
    # Quebra de linha e tab dentro do campo desalinham a importação em planilha.
    if isinstance(v, str):
        return " ".join(v.replace("\t", " ").splitlines())
    return "" if v is None else v


def idade_saida(idade):
    return None if idade is None else ("90+" if idade >= 90 else idade)


def grava(caminho: Path, cabecalho: list[str], linhas):
    # `;` + BOM: separador e codificação que o Excel em pt-BR abre direto.
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        w.writerow(cabecalho)
        for l in linhas:
            w.writerow([uma_linha(v) for v in l])


def main(pasta: Path) -> None:
    cur = conecta().cursor()
    unidade = rotulos_unidade(cur)
    receitas = consulta(cur, com_paciente(SQL_RECEITAS))
    atestados = consulta(cur, com_paciente(SQL_ATESTADOS))
    soap = consulta(cur, com_paciente(SQL_SOAP))

    textos = ([r[c] for r in receitas for c in TEXTO_RECEITA] + [a["texto_atestado"] for a in atestados]
              + [s[c] for s in soap for c in TEXTO_SOAP])
    anon = Anonimizador(unidade, lexicos(cur, textos), MUNICIPIOS)
    cur.connection.close()          # daqui em diante não precisa do banco

    sorteio = random.SystemRandom()
    cidadaos = sorted({r["_cidadao"] for r in receitas + atestados + soap if r["_cidadao"] is not None})
    pseudo = list(range(1, len(cidadaos) + 1))
    sorteio.shuffle(pseudo)
    paciente_id = dict(zip(cidadaos, pseudo))
    semanas = [s for s in range(-26, 27) if s != 0]
    delta = {c: timedelta(weeks=sorteio.choice(semanas)) for c in cidadaos}
    # Atendimento sem cidadão ligado: deslocamento próprio da linha.
    delta_de = lambda c: delta[c] if c is not None else timedelta(weeks=sorteio.choice(semanas))

    def rotulo(bruto):
        return unidade.get(bruto, bruto and "Unidade de Saúde ?")

    # receitas
    cols_r = [c for c in receitas[0] if not c.startswith("_")]
    saida_r = []
    for r in receitas:
        d, pac, ano = delta_de(r["_cidadao"]), paciente_de(r), r["data_atendimento"].year
        for c in TEXTO_RECEITA:
            r[c] = anon.anonimiza(r[c], pac, d, ano)
        for c in DATAS_RECEITA:
            if r[c] is not None:
                r[c] = r[c] + d
        v = [r[c] for c in cols_r]
        saida_r.append(v[:2] + [paciente_id.get(r["_cidadao"])] + v[2:]
                       + [rotulo(r["_unidade"]), idade_saida(r["_idade"])])
    grava(pasta / "04_receitas_medicamento.csv",
          cols_r[:2] + ["paciente_id"] + cols_r[2:] + ["unidade_saude", "idade_anos"], saida_r)
    cont_receitas = Counter(anon.contagem)

    # atestados
    cols_a = [c for c in atestados[0] if not c.startswith("_")]
    saida_a, verif = [], []
    for a in atestados:
        d, pac, ano = delta_de(a["_cidadao"]), paciente_de(a), a["data_atendimento"].year
        original = a["texto_atestado"]
        a["texto_atestado"] = anon.anonimiza(original, pac, d, ano)
        for c in DATAS_ATESTADO:
            if a[c] is not None:
                a[c] = a[c] + d
        v = [a[c] for c in cols_a]
        saida_a.append(v[:2] + [paciente_id.get(a["_cidadao"]), a["_tipo"], TIPO_ATESTADO.get(a["_tipo"])]
                       + v[2:] + [rotulo(a["_unidade"]), idade_saida(a["_idade"])])
        verif.append((a["atestado_id"], a["_tipo"], original, a["texto_atestado"], pac))
    grava(pasta / "05_atestados.csv",
          cols_a[:2] + ["paciente_id", "tipo_atestado", "tipo_atestado_desc"] + cols_a[2:]
          + ["unidade_saude", "idade_anos"], saida_a)
    grava(pasta / "05_atestados_verificacao.csv",
          ["atestado_id", "tipo_atestado", "texto_original", "texto_pseudoanonimizado"],
          [v[:4] for v in verif])
    cont_atest = anon.contagem - cont_receitas

    # SOAP
    cols_s = [c for c in soap[0] if not c.startswith("_")]
    saida_s, verif_s = [], []
    for s in soap:
        d, pac = delta_de(s["_cidadao"]), paciente_de(s)
        ano = s["data_atendimento"].year
        originais = [s[c] for c in TEXTO_SOAP]
        for c in TEXTO_SOAP:
            s[c] = anon.anonimiza(s[c], pac, d, ano)
        for c in DATAS_SOAP:
            if s[c] is not None:
                s[c] = s[c] + d
        v = [s[c] for c in cols_s]
        saida_s.append(v[:1] + [paciente_id.get(s["_cidadao"])] + v[1:]
                       + [rotulo(s["_unidade"]), idade_saida(s["_idade"])])
        verif_s.append((s["atendimento_prof_id"], None,
                        " ||| ".join(o or "" for o in originais),
                        " ||| ".join(s[c] or "" for c in TEXTO_SOAP), pac))
    grava(pasta / "06_soap.csv",
          cols_s[:1] + ["paciente_id"] + cols_s[1:] + ["unidade_saude", "idade_anos"], saida_s)
    grava(pasta / "06_soap_verificacao.csv",
          ["atendimento_prof_id", "textos_originais (S ||| O ||| A ||| P ||| notas)",
           "textos_pseudoanonimizados (S ||| O ||| A ||| P ||| notas)"],
          [(v[0], v[2], v[3]) for v in verif_s])
    cont_soap = anon.contagem - cont_receitas - cont_atest

    print(f"receitas: {len(saida_r)} | atestados: {len(saida_a)} | atendimentos com SOAP: {len(saida_s)}"
          f" | pacientes: {len(paciente_id)}")
    print("trocas nas receitas:", dict(cont_receitas))
    print("trocas nos atestados:", dict(cont_atest))
    print("trocas no SOAP:", dict(cont_soap))
    residuo(verif, anon, pasta / "05_atestados_residuo.txt", "atestados")
    residuo(verif_s, anon, pasta / "06_soap_residuo.txt", "atendimentos (SOAP)")


def residuo(verif, anon, arquivo: Path, rotulo: str) -> None:
    """Procura no texto pseudo-anonimizado o que deveria ter saído."""
    sobra = Counter()
    exemplos = []
    reais = anon.lex.nomes_completos
    falsos = {normalizar(t) for fic in anon.mapa_nome.values() for t in fic}
    para_tokens = lambda s: re.findall(r"[a-z']+", normalizar(re.sub(r"<[^>]*>|&[a-z]+;", " ", s)))
    for aid, _, orig, pseudo, pac in verif:
        if not pseudo:
            continue
        tok = para_tokens(pseudo)
        no_original = " " + " ".join(para_tokens(orig)) + " "
        achou = set()
        # nome completo cadastrado (>= 2 palavras) que ficou; só conta se já
        # estava no original (senão é combinação de nomes fictícios)
        for n in range(7, 1, -1):
            for i in range(len(tok) - n + 1):
                g = " ".join(tok[i:i + n])
                if g in reais and g not in anon.ficticios and f" {g} " in no_original:
                    achou.add("nome_base")
        # duas palavras seguidas do nome cadastrado do paciente que ficaram
        # (par feito só de palavras usadas como substituto não conta)
        for nome, _ in pac.nomes:
            reg = [t for t in normalizar(nome).split() if t not in PARTICULAS and len(t) > 2]
            sem_part = [t for t in tok if t not in PARTICULAS]
            do_reg = lambda t: any(parecido(t, r) for r in reg)
            if any(do_reg(a) and do_reg(b) and not (a in falsos and b in falsos)
                   for a, b in zip(sem_part, sem_part[1:])):
                achou.add("nome_paciente")
        for m in CPF_RE.finditer(pseudo):
            dig = re.sub(r"\D", "", m.group())
            if cpf_valido(dig) and dig not in anon.mapa_doc.values():
                achou.add("cpf")
        for m in CNS_RE.finditer(pseudo):
            if cns_valido(m.group()) and m.group() not in anon.mapa_doc.values():
                achou.add("cns")
        if re.search(r"severiano|ild[eo]mar|cristalino|nogueira neta", normalizar(pseudo)):
            achou.add("unidade/municipio")
        for k in achou:
            sobra[k] += 1
        if achou and len(exemplos) < 400:
            exemplos.append((aid, sorted(achou)))
    print(f"{rotulo} com possível resíduo:", dict(sobra))
    arquivo.write_text("\n".join(f"{a}\t{', '.join(k)}" for a, k in exemplos), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
