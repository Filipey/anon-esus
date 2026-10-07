"""Carga das tabelas por pessoa usadas pelos experimentos de k-anonimato.

Três recortes, todos lidos de um banco (a original ou uma versão anonimizada,
para comparar):

- `pessoas`: um cidadão por linha (`tb_cidadao`), com os quase-identificadores
  e o tercil de distância do domicílio calculado pela migration 06;
- `diagnosticos`: pares (cidadão, código) de CID-10 e CIAP-2 registrados como
  problema/condição nos atendimentos (DW, que já liga cada problema ao cidadão);
- `medicoes`: medições antropométricas de `tb_medicao`, com o cidadão e a data.

Tudo é agregado em memória pelos scripts; nenhum valor sai para arquivo.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date

import numpy as np
import pandas as pd

from _conexao import RAIZ, consulta

VARIAVEIS_ANTRO = {
    "peso": "nu_medicao_peso",
    "altura": "nu_medicao_altura",
    "imc": "nu_medicao_imc",
    "perimetro_cefalico": "nu_medicao_perimetro_cefalico",
    "circ_abdominal": "nu_medicao_circunf_abdominal",
    "altura_uterina": "nu_medicao_altura_uterina",
    "panturrilha": "nu_perimetro_panturrilha",
}


def _sql(conn, sql: str, params=None) -> list[tuple]:
    r = consulta(conn, sql, params)
    if isinstance(r, dict):
        raise SystemExit(f"consulta falhou: {r['erro']}")
    return r


def migration(arquivo: str):
    """Importa uma migration de scripts/ (nome começa com dígito)."""
    scripts = RAIZ / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    nome = "_exp_" + arquivo.removesuffix(".py")
    spec = importlib.util.spec_from_file_location(nome, scripts / arquivo)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


def faixas_idade(idade: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "faixa5": (idade // 5 * 5).astype("Int64"),
        "faixa10": (idade // 10 * 10).astype("Int64"),
        "ciclo": pd.cut(
            idade, bins=[-1, 1, 9, 19, 59, 200],
            labels=["0-1", "2-9", "10-19", "20-59", "60+"],
        ).astype(str),
    })


def pessoas(conn, referencia: date, apenas_ativos: bool = True) -> pd.DataFrame:
    filtro = "WHERE st_ativo = 1 AND st_faleceu = 0" if apenas_ativos else ""
    df = pd.DataFrame(
        _sql(
            conn,
            f"""
            SELECT co_seq_cidadao, no_sexo, dt_nascimento, co_raca_cor, co_localidade,
                   co_localidade_endereco, co_escolaridade, co_cbo, co_nacionalidade,
                   co_estado_civil, tp_orientacao_sexual, tp_identidade_genero
            FROM tb_cidadao {filtro}
            """,
        ),
        columns=["id", "sexo", "dt_nasc", "raca_cor", "mun_nasc", "mun_resid", "escolaridade",
                 "ocupacao", "nacionalidade", "estado_civil", "orient_sexual", "ident_genero"],
    )
    equipe = pd.DataFrame(
        _sql(conn, "SELECT co_cidadao, max(nu_ine) FROM tb_cidadao_vinculacao_equipe GROUP BY 1"),
        columns=["id", "equipe"],
    )
    # cidadão -> domicílio pelo DW; o território de família mais recente vence.
    domicilio = pd.DataFrame(
        _sql(
            conn,
            """
            SELECT DISTINCT ON (p.co_cidadao) p.co_cidadao, d.co_seq_cds_domicilio
            FROM tb_fat_cidadao_pec p
            JOIN tb_fat_cidadao_territorio ct ON ct.co_fat_cidadao_pec = p.co_seq_fat_cidadao_pec
            JOIN tb_fat_familia_territorio ft
              ON ft.co_seq_fat_familia_territorio = ct.co_fat_familia_territorio
            JOIN tb_fat_cad_domiciliar fd ON fd.co_seq_fat_cad_domiciliar = ft.co_fat_cad_domiciliar
            JOIN tb_cds_cad_domiciliar cd ON cd.co_unico_ficha::text = fd.nu_uuid_ficha::text
            JOIN tb_cds_domicilio d ON d.co_unico_domicilio = cd.co_unico_domicilio
            ORDER BY p.co_cidadao, ft.co_seq_fat_familia_territorio DESC
            """,
        ),
        columns=["id", "domicilio"],
    )
    m06 = migration("06_anon_endereco.py")
    linhas = _sql(
        conn,
        "SELECT co_seq_cds_domicilio, nu_latitude::float8, nu_longitude::float8, "
        "nu_ine::text, nu_cnes::text FROM tb_cds_domicilio",
    )
    tercis = m06.calcular_tercis(linhas, m06.carregar_unidades())
    domicilio["tercil"] = domicilio["domicilio"].map(tercis)

    df = df.merge(equipe, on="id", how="left").merge(domicilio, on="id", how="left")
    nasc = pd.to_datetime(df["dt_nasc"])
    df["dt_nasc"] = nasc
    df["idade"] = (pd.Timestamp(referencia) - nasc).dt.days // 365.25
    df["nasc_dia"] = nasc.dt.strftime("%Y-%m-%d")
    df["nasc_mes"] = nasc.dt.strftime("%Y-%m")
    df["nasc_ano"] = nasc.dt.year
    return pd.concat([df, faixas_idade(df["idade"])], axis=1)


def diagnosticos(conn) -> pd.DataFrame:
    """(id do cidadão, sistema, código) distintos dos problemas avaliados nos
    atendimentos individuais e odontológicos e no consolidado do DW."""
    partes = []
    for tabela in ("tb_fat_atd_ind_problemas", "tb_fat_atend_odonto_problemas"):
        for sistema, dim, num in (("CID", "tb_dim_cid", "nu_cid"), ("CIAP", "tb_dim_ciap", "nu_ciap")):
            col = "co_dim_cid" if sistema == "CID" else "co_dim_ciap"
            partes.append(pd.DataFrame(
                _sql(
                    conn,
                    f"""
                    SELECT DISTINCT p.co_cidadao, d.{num}
                    FROM {tabela} f
                    JOIN tb_fat_cidadao_pec p ON p.co_seq_fat_cidadao_pec = f.co_fat_cidadao_pec
                    JOIN {dim} d ON d.co_seq_{dim[3:]} = f.{col}
                    WHERE d.{num} IS NOT NULL AND d.{num} NOT IN ('-', '')
                    """,
                ),
                columns=["id", "codigo"],
            ).assign(sistema=sistema))
    out = pd.concat(partes, ignore_index=True).drop_duplicates()
    out["codigo"] = out["codigo"].str.strip().str.upper()
    return out


def _numero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def medicoes(conn) -> pd.DataFrame:
    cols = ", ".join(f"m.{c}" for c in VARIAVEIS_ANTRO.values())
    df = pd.DataFrame(
        _sql(
            conn,
            f"""
            SELECT m.co_seq_medicao, p.co_cidadao, m.dt_medicao, {cols}
            FROM tb_medicao m
            JOIN tb_atend_prof ap ON ap.co_seq_atend_prof = m.co_atend_prof
            JOIN tb_atend a ON a.co_seq_atend = ap.co_atend
            JOIN tb_prontuario p ON p.co_seq_prontuario = a.co_prontuario
            """,
        ),
        columns=["medicao", "id", "dt_medicao", *VARIAVEIS_ANTRO],
    )
    for var in VARIAVEIS_ANTRO:
        df[var] = _numero(df[var])
    df["dt_medicao"] = pd.to_datetime(df["dt_medicao"], utc=True).dt.tz_localize(None)
    return df


def idade_na_data(nasc: pd.Series, data: pd.Series) -> pd.Series:
    return ((data - nasc).dt.days / 365.25).astype(float).apply(np.floor)
