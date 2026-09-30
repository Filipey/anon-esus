"""Testes da migration 06 (supressão de endereço + tercil de distância)."""

from __future__ import annotations

import pytest
from _helpers import load_migration
from sqlalchemy import text

m = load_migration("06_anon_endereco.py")
fake_cnes = load_migration("02_anon_unidade_saude.py")._fake_cnes

CNES_REAL = "2380692"
UNIDADE = (-6.0, -38.0)


def _csv(tmp_path, monkeypatch, cnes=CNES_REAL):
    path = tmp_path / "unidades.csv"
    path.write_text(
        "# comentário ignorado\n"
        "co_unidade,nu_cnes,nome_referencia,endereco_referencia,latitude,longitude\n"
        f"{cnes},{cnes},UBS Teste,\"RUA X, 1\",{UNIDADE[0]},{UNIDADE[1]}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(m, "CSV_UNIDADES", path)


def _seed(engine, domicilios):
    """domicilios: lista de (lat, lng, ine, cnes)."""
    with engine.begin() as c:
        c.execute(
            text(
                "CREATE TABLE public.tb_cds_domicilio ("
                "co_seq_cds_domicilio serial PRIMARY KEY, "
                "nu_latitude double precision, nu_longitude double precision, "
                "nu_ine text, nu_cnes text, ds_ponto_referencia varchar(255), "
                "no_bairro text, no_logradouro text, ds_cep text, nu_domicilio text)"
            )
        )
        for lat, lng, ine, cnes in domicilios:
            c.execute(
                text(
                    "INSERT INTO public.tb_cds_domicilio "
                    "(nu_latitude, nu_longitude, nu_ine, nu_cnes, ds_ponto_referencia, "
                    " no_bairro, no_logradouro, ds_cep, nu_domicilio) "
                    "VALUES (:lat, :lng, :ine, :cnes, 'perto da padaria', "
                    " 'Centro', 'Rua A', '59910-000', '10')"
                ),
                {"lat": lat, "lng": lng, "ine": ine, "cnes": cnes},
            )
        c.execute(
            text(
                "CREATE TABLE public.tb_cidadao (co_seq serial PRIMARY KEY, no_cidadao text, "
                "ds_logradouro text, no_bairro text, ds_cep text, nu_numero text, "
                "ds_ponto_referencia text)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_cidadao (no_cidadao, ds_logradouro, no_bairro, ds_cep, "
                "nu_numero, ds_ponto_referencia) VALUES "
                "('Fulano', 'Rua B', 'Norte', '59910-001', '20', 'ao lado da escola')"
            )
        )
        c.execute(
            text(
                "CREATE TABLE public.tb_unidade_saude (co_seq serial PRIMARY KEY, "
                "ds_logradouro text, no_bairro text, ds_cep text)"
            )
        )
        c.execute(
            text(
                "INSERT INTO public.tb_unidade_saude (ds_logradouro, no_bairro, ds_cep) "
                "VALUES ('Rua Princesa Isabel', 'Centro', '59910-000')"
            )
        )


def _equipe(n, ine, cnes, passo=0.001):
    """n domicílios da equipe `ine`, cada um ~111 m mais longe da unidade."""
    return [(UNIDADE[0] + passo * (i + 1), UNIDADE[1], ine, cnes) for i in range(n)]


def _domicilios(engine):
    with engine.connect() as c:
        return c.execute(
            text(
                "SELECT nu_latitude, nu_longitude, ds_ponto_referencia, no_bairro, "
                "no_logradouro, ds_cep, nu_domicilio, nu_ine, nu_cnes "
                "FROM public.tb_cds_domicilio ORDER BY co_seq_cds_domicilio"
            )
        ).all()


def _tercil(valor):
    return None if valor is None else int(valor.split("tercil ")[1].split(" ")[0])


def test_tercis_seguem_a_regra_do_experimento():
    # 9 distâncias crescentes: cortes em ds[2] e ds[5] -> faixas 2/3/4.
    faixas = m.tercis_por_grupo(["A"] * 9, list(range(9)))
    assert faixas == [0, 0, 1, 1, 1, 2, 2, 2, 2]


def test_suprime_endereco_e_coordenada_do_domicilio(pg_engine, tmp_path, monkeypatch):
    _csv(tmp_path, monkeypatch)
    _seed(pg_engine, _equipe(9, "INE1", CNES_REAL))
    m.run(pg_engine)
    for lat, lng, _, bairro, logr, cep, num, ine, cnes in _domicilios(pg_engine):
        assert (lat, lng, bairro, logr, cep, num) == (None,) * 6
        assert ine == "INE1" and cnes == CNES_REAL  # equipe e unidade ficam


def test_suprime_endereco_de_cidadao_e_preserva_unidade(pg_engine, tmp_path, monkeypatch):
    _csv(tmp_path, monkeypatch)
    _seed(pg_engine, _equipe(3, "INE1", CNES_REAL))
    m.run(pg_engine)
    with pg_engine.connect() as c:
        cid = c.execute(
            text("SELECT no_cidadao, ds_logradouro, no_bairro, ds_cep, nu_numero, "
                 "ds_ponto_referencia FROM public.tb_cidadao")
        ).one()
        un = c.execute(text("SELECT ds_logradouro, no_bairro, ds_cep FROM public.tb_unidade_saude")).one()
    assert cid == ("Fulano", None, None, None, None, None)
    assert tuple(un) == ("Rua Princesa Isabel", "Centro", "59910-000")


def test_tercil_por_equipe_com_k_minimo(pg_engine, tmp_path, monkeypatch):
    """Equipe com 9 domicílios -> classes 2/3/4; com k=3 a primeira classe
    (2 domicílios) não recebe tercil. Equipe com 2 domicílios -> nenhuma."""
    _csv(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "K_MIN", 3)
    _seed(pg_engine, _equipe(9, "INE1", CNES_REAL) + _equipe(2, "INE2", CNES_REAL))
    m.run(pg_engine)
    tercis = [_tercil(r.ds_ponto_referencia) for r in _domicilios(pg_engine)]
    assert tercis[:9] == [None, None, 2, 2, 2, 3, 3, 3, 3]
    assert tercis[9:] == [None, None]


def test_casa_unidade_pelo_cnes_ficticio_da_02(pg_engine, tmp_path, monkeypatch):
    """Na pipeline a 02 já trocou o CNES; o CSV continua com o real."""
    _csv(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "K_MIN", 1)
    _seed(pg_engine, _equipe(6, "INE1", fake_cnes(CNES_REAL)))
    m.run(pg_engine)
    assert all(r.ds_ponto_referencia for r in _domicilios(pg_engine))


def test_sem_coordenada_equipe_ou_unidade_fica_sem_tercil(pg_engine, tmp_path, monkeypatch):
    _csv(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "K_MIN", 1)
    _seed(
        pg_engine,
        _equipe(3, "INE1", CNES_REAL)
        + [
            (None, None, "INE1", CNES_REAL),          # sem coordenada
            (UNIDADE[0] + 0.01, UNIDADE[1], None, CNES_REAL),  # sem equipe
            (UNIDADE[0] + 0.01, UNIDADE[1], "INE1", "9999999"),  # unidade sem coordenada
            (0.0, 0.0, "INE1", CNES_REAL),            # fora do Brasil
        ],
    )
    m.run(pg_engine)
    refs = [r.ds_ponto_referencia for r in _domicilios(pg_engine)]
    assert all(refs[:3]) and refs[3:] == [None] * 4


def test_sem_csv_so_suprime(pg_engine, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "CSV_UNIDADES", tmp_path / "nao_existe.csv")
    _seed(pg_engine, _equipe(9, "INE1", CNES_REAL))
    m.run(pg_engine)
    assert all(r.ds_ponto_referencia is None and r.nu_latitude is None for r in _domicilios(pg_engine))


def test_tabelas_ausentes_sao_puladas(pg_engine):
    m.run(pg_engine)  # banco vazio: nada a fazer, sem erro


def test_recusa_suprimir_tabela_institucional(pg_engine, monkeypatch):
    monkeypatch.setattr(
        m, "ADDRESS_TABLES", m.ADDRESS_TABLES + [m.AddressTable("public", "tb_unidade_saude", ("no_bairro",))]
    )
    with pytest.raises(RuntimeError, match="institucional"):
        m.run(pg_engine)


def test_atomicidade_rollback_em_falha(pg_engine, tmp_path, monkeypatch):
    _csv(tmp_path, monkeypatch)
    _seed(pg_engine, _equipe(3, "INE1", CNES_REAL))
    with pg_engine.begin() as c:
        c.execute(text("CREATE TABLE public.tb_poison (co_seq serial PRIMARY KEY, no_bairro text)"))
        c.execute(text("INSERT INTO public.tb_poison (no_bairro) VALUES ('X')"))
        c.execute(text("CREATE FUNCTION boom() RETURNS trigger AS "
                       "$$ BEGIN RAISE EXCEPTION 'boom'; END $$ LANGUAGE plpgsql"))
        c.execute(text("CREATE TRIGGER trg BEFORE UPDATE ON public.tb_poison "
                       "FOR EACH ROW EXECUTE FUNCTION boom()"))
    monkeypatch.setattr(
        m, "ADDRESS_TABLES", m.ADDRESS_TABLES + [m.AddressTable("public", "tb_poison", ("no_bairro",))]
    )
    with pytest.raises(Exception):
        m.run(pg_engine)
    assert all(r.no_bairro == "Centro" and r.nu_latitude is not None for r in _domicilios(pg_engine))
