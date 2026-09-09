"""Experimento 04 - gera os graficos dos experimentos em PDF (e PNG).

Le os JSON mais recentes de `resultados/` e produz as figuras que sustentam
a decisao de geografia da fase 1. **Nao acessa o banco**: tudo que precisa
ja esta agregado nos resultados dos experimentos 01-03, entao roda offline
e a qualquer momento.

Reaproveita o estilo visual de `scripts/plots/_common.py` (serif, mathtext
Computer Modern) para as figuras sairem coerentes com as ja existentes no
projeto.

Figuras geradas:

  k_por_nivel          k mediano da classe por nivel geografico candidato
  distancia            distribuicao da distancia domicilio -> unidade
  esquemas_de_faixa    supressao por esquema de faixa e agrupamento
  sensibilidade_k      supressao em funcao de k, por configuracao
  agrupamentos         compacidade contra supressao, por agrupamento candidato
  iloss_por_k          supressao E perda de informacao em funcao de k

`sensibilidade_k` e a que responde "por que k=20": ela mostra que a escolha
entre k=2 e k=20 nao muda o resultado na configuracao recomendada, e onde
fica o joelho da curva.

`iloss_por_k` e o par dela no eixo de utilidade. A curva de supressao conta
*quantos registros* se perde ao exigir k; a de ILoss conta *quanta
informacao*, somando o que a generalizacao ja custava antes de suprimir
qualquer coisa. As duas juntas mostram a inversao que sustenta a decisao: o
agrupamento de menor ILoss enquanto k e frouxo e o de maior ILoss assim que
k aperta, porque a perda migra de generalizacao para supressao.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PALETA_AGRUPAMENTO = {
    "equipe (INE)": ("#2E4057", "-", "o"),
    "par (equipe, micro-área)": ("#F18F01", "--", "s"),
    "micro-área só": ("#9E2A2B", ":", "d"),
    "MDAV k=20": ("#2A9D8F", "-.", "^"),
    "MDAV k=20 estratificado": ("#7E57C2", (0, (3, 1, 1, 1)), "v"),
}

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
RESULTADOS = AQUI / "resultados"
SAIDA = AQUI / "figuras"

sys.path.insert(0, str(RAIZ / "scripts" / "plots"))
try:
    from _common import COLOR_PRIMARY, COLOR_RISK, COLOR_SECONDARY, set_latex_style
except Exception:  # noqa: BLE001 - o modulo puxa sqlalchemy/seaborn; se faltar, segue
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_RISK = "#2E4057", "#F18F01", "#9E2A2B"

    def set_latex_style() -> None:
        plt.rcParams.update(
            {
                "font.family": "serif",
                "mathtext.fontset": "cm",
                "axes.edgecolor": "0.3",
                "axes.linewidth": 0.8,
                "grid.linewidth": 0.5,
                "grid.alpha": 0.4,
                "figure.dpi": 150,
                "savefig.dpi": 300,
                "savefig.bbox": "tight",
            }
        )


def ultimo(prefixo: str) -> dict | None:
    arquivos = sorted(RESULTADOS.glob(f"{prefixo}_*.json"))
    if not arquivos:
        print(f"  AUSENTE: nenhum {prefixo}_*.json em resultados/ - figura pulada")
        return None
    print(f"  lendo {arquivos[-1].name}")
    return json.loads(arquivos[-1].read_text(encoding="utf-8"))


def salvar(fig, stem: str) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    caminho = SAIDA / f"{stem}.pdf"
    fig.savefig(caminho)
    fig.savefig(caminho.with_suffix(".png"))
    plt.close(fig)
    print(f"  -> {caminho.relative_to(RAIZ)}  (+ .png)")


def limiares_de(entrada: dict) -> list[int]:
    """Descobre os limiares de k presentes no resultado.

    O conjunto mudou ao longo dos experimentos (de 5 para 11 valores), entao
    a figura se adapta ao que o JSON tiver em vez de assumir uma lista fixa.
    """
    ks = []
    for chave in entrada:
        if chave.startswith("linhas_k_menor_"):
            ks.append(int(chave.rsplit("_", 1)[1]))
    return sorted(ks)


# ---------------------------------------------------------------- figura 1
def fig_k_por_nivel(dados: dict) -> None:
    niveis = dados.get("niveis", {})
    ordem = [
        ("área / equipe", "area / equipe"),
        ("unidade", "unidade"),
        ("micro-área", "micro-area (territorio)"),
        ("bairro", "bairro (normalizado)"),
        ("município", "municipio"),
    ]
    rotulos, medianas, suprimir, passa = [], [], [], []
    for rotulo, chave in ordem:
        e = niveis.get(chave, {}).get("isolado")
        if not e or "mediana" not in e:
            continue
        rotulos.append(rotulo)
        medianas.append(max(1, int(e["mediana"])))
        n20 = int(e.get("linhas_k_menor_20", 0))
        suprimir.append(n20)
        passa.append(int(e["mediana"]) >= 20)

    if not rotulos:
        print("  sem niveis utilizaveis no exp. 02 - figura pulada")
        return

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    y = np.arange(len(rotulos))[::-1]
    cores = [COLOR_PRIMARY if p else COLOR_RISK for p in passa]
    ax.barh(y, medianas, height=0.6, color=cores)
    ax.set_xscale("log")
    ax.set_xlim(1, max(medianas) * 3)
    ax.set_yticks(y, rotulos)
    ax.axvline(20, color=COLOR_RISK, ls="--", lw=1.1, alpha=0.8)
    ax.text(20, len(rotulos) - 0.35, " k = 20", color=COLOR_RISK, fontsize=9, va="bottom")

    for yi, m, s in zip(y, medianas, suprimir):
        txt = f"{m:,}".replace(",", ".")
        if s:
            txt += f"   ({s} linha{'s' if s > 1 else ''} abaixo do mínimo)"
        ax.text(m * 1.15, yi, txt, va="center", fontsize=8.5, color="0.25")

    ax.set_xlabel("tamanho mediano da classe de equivalência (escala log)")
    ax.set_title("k por nível geográfico candidato, isoladamente", loc="left", fontsize=11)
    ax.grid(axis="y", visible=False)
    salvar(fig, "k_por_nivel")


# ---------------------------------------------------------------- figura 2
def fig_distancia(dados: dict) -> None:
    d = dados.get("distancia_m")
    if not d:
        print("  sem distancia no exp. 03 - figura pulada")
        return

    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    caixa = {
        "med": d["mediana"],
        "q1": d["p25"],
        "q3": d["p75"],
        "whislo": d["min"],
        "whishi": d["p95"],
        "fliers": [d["max"]],
        "label": "",
    }
    bp = ax.bxp(
        [caixa], orientation="horizontal", showfliers=True,
        widths=0.45, patch_artist=True,
    )
    for p in bp["boxes"]:
        p.set(facecolor=COLOR_PRIMARY, alpha=0.25, edgecolor=COLOR_PRIMARY, lw=1.2)
    for p in bp["medians"]:
        p.set(color=COLOR_PRIMARY, lw=2.2)
    for p in bp["whiskers"] + bp["caps"]:
        p.set(color="0.45", lw=1)
    for p in bp["fliers"]:
        p.set(marker="o", markerfacecolor=COLOR_RISK, markeredgecolor="none", markersize=5)

    ax.set_xscale("log")
    ax.set_xlabel("distância domicílio → unidade de vínculo (m, escala log)")
    razao = d["p75"] / d["p25"] if d["p25"] else 0
    milhar = f"{d['n']:,}".replace(",", ".")
    ax.set_title(
        f"Do 1º ao 3º quartil a distância cresce {razao:.0f}× (n = {milhar})",
        loc="left",
        fontsize=11,
    )
    for chave, rotulo, dy in (
        ("p25", "p25", 0.34), ("mediana", "mediana", -0.40), ("p75", "p75", 0.34),
        ("p95", "p95", -0.40), ("max", "máx.", 0.34),
    ):
        v = d[chave]
        texto = f"{v/1000:.0f} km" if v >= 1000 else f"{v:.0f} m"
        ax.annotate(
            f"{rotulo} {texto}", xy=(v, 1), xytext=(v, 1 + dy),
            ha="center", fontsize=8, color=COLOR_RISK if chave == "max" else "0.3",
        )
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    salvar(fig, "distancia")


# ---------------------------------------------------------------- figura 3
def fig_esquemas(dados: dict) -> None:
    esquemas = dados.get("esquemas")
    if not esquemas:
        print("  sem esquemas no exp. 03 (rode a versao nova) - figura pulada")
        return

    n = dados["domicilios_usados"] - dados.get("fora_do_limite", {}).get("n", 0)
    larguras = dados.get("larguras", {})
    buckets = list(esquemas)

    # Ordem deliberada: primeiro a largura fixa (o termo de comparacao), depois
    # os esquemas de numero limitado de faixas, do mais grosso ao mais fino.
    # Sem a largura fixa na figura o resultado central - que o formato importa
    # mais que a largura - fica invisivel.
    COLUNAS = [
        ("1 km fixo", None),
        ("6 fixas", "6 faixas fixas (250/500/1k/2.5k/5k)"),
        ("4 fixas", "4 faixas fixas (500/1.5k/5k)"),
        ("quartis", "quartis por bucket"),
        ("tercis", "tercis por bucket"),
    ]
    rotulo_bucket = {
        "nu_micro_area": "micro-área", "nu_ine": "equipe (INE)",
        "no_bairro_filtro": "bairro",
    }

    fig, axes = plt.subplots(1, len(buckets), figsize=(8.0, 3.2), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, b in zip(axes, buckets):
        vals = []
        for _, chave in COLUNAS:
            if chave is None:
                e = larguras.get(b, {}).get("1000m", {}).get("sem_outliers")
            else:
                e = esquemas.get(b, {}).get(chave)
            vals.append(100 * e["linhas_k_menor_20"] / n if e else float("nan"))

        cores = [COLOR_PRIMARY if v < 0.2 else COLOR_RISK for v in vals]
        x = np.arange(len(COLUNAS))
        ax.bar(x, vals, width=0.62, color=cores)
        ax.set_xticks(x, [c for c, _ in COLUNAS], rotation=45, ha="right", fontsize=8)
        ax.set_title(rotulo_bucket.get(b, b), fontsize=10)
        for xi, v in zip(x, vals):
            if v != v:
                continue
            ax.text(xi, v + 0.5, f"{v:.1f}", ha="center", fontsize=8,
                    color=COLOR_PRIMARY if v < 0.2 else COLOR_RISK)
        ax.axvline(0.5, color="0.75", ls=":", lw=1)
        ax.grid(axis="x", visible=False)

    axes[0].set_ylabel("% de domicílios a suprimir")
    milhar = f"{n:,}".replace(",", ".")
    fig.suptitle(
        f"Supressão necessária para k ≥ 20, por esquema de faixa (n = {milhar})",
        x=0.02, ha="left", fontsize=11,
    )
    fig.text(
        0.02, 0.005,
        "À esquerda da linha pontilhada, largura fixa; à direita, número fixo de faixas.",
        fontsize=8, color="0.35",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    salvar(fig, "esquemas_de_faixa")


# ---------------------------------------------------------------- figura 4
def fig_sensibilidade_k(dados: dict) -> None:
    esquemas = dados.get("esquemas")
    if not esquemas:
        print("  sem esquemas no exp. 03 - figura de sensibilidade pulada")
        return

    n = dados["domicilios_usados"] - dados.get("fora_do_limite", {}).get("n", 0)
    interesse = [
        ("nu_micro_area", "tercis por bucket", "micro-área + tercis", COLOR_PRIMARY, "-", "o"),
        ("nu_micro_area", "quartis por bucket", "micro-área + quartis", COLOR_PRIMARY, "--", "s"),
        ("nu_ine", "quartis por bucket", "equipe + quartis", COLOR_SECONDARY, "-", "^"),
        ("no_bairro_filtro", "tercis por bucket", "bairro + tercis", COLOR_RISK, ":", "d"),
    ]

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    plotou = False
    for bucket, esq, rotulo, cor, ls, mk in interesse:
        e = esquemas.get(bucket, {}).get(esq)
        if not e:
            continue
        ks = limiares_de(e)
        if not ks:
            continue
        ys = [100 * e[f"linhas_k_menor_{k}"] / n for k in ks]
        ax.plot(ks, ys, ls, marker=mk, ms=4.5, lw=1.6, color=cor, label=rotulo)
        plotou = True

    if not plotou:
        print("  sem limiares no JSON - figura de sensibilidade pulada")
        plt.close(fig)
        return

    ax.axvline(20, color="0.45", ls="--", lw=1)
    topo = ax.get_ylim()[1]
    ax.annotate(
        "k = 20 (valor adotado)", xy=(21, topo * 0.45),
        fontsize=8, color="0.35", ha="left", rotation=90, va="center",
    )
    ax.set_xlabel("k exigido")
    ax.set_ylabel("% de domicílios a suprimir")
    ax.set_title(
        "Custo de utilidade em função de k, por configuração", loc="left", fontsize=11
    )
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    salvar(fig, "sensibilidade_k")


# ---------------------------------------------------------------- figura 5
def fig_agrupamentos(dados: dict) -> None:
    """Espaco de trade-off: compacidade contra supressao do par.

    Uma figura so, porque o argumento e a relacao entre as duas coisas -
    o agrupamento mais compacto e justamente o que mais falha no par, e
    e tambem o que revela mais localizacao para o mesmo k.
    """
    ag = dados.get("agrupamentos")
    if not ag or not dados.get("com_tercil"):
        print("  exp. 06 sem tercil - figura de agrupamentos pulada")
        return

    n = dados["domicilios"]
    pts = []
    for nome, m in ag.items():
        if m.get("compacidade_mediana_m") is None:
            continue
        pts.append((
            nome,
            m["compacidade_mediana_m"],
            100 * m["par_linhas_k_menor_20"] / n,
            m["par_n_classes"],
            m["par_k_min"],
        ))
    if not pts:
        return

    # Deslocamento por ponto, escolhido a mao: com cinco marcadores em duas
    # regioes apertadas, a formula automatica sobrepoe os rotulos.
    OFFSETS = {
        "MDAV k=20": (72, 6, "left"),
        "MDAV k=20 estratificado": (60, -32, "left"),
        "par (equipe, micro-área)": (0, 26, "center"),
        "micro-área só": (-14, -4, "right"),
        "equipe (INE)": (0, 26, "center"),
    }

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    for nome, comp, sup, classes, kmin in pts:
        passa = kmin >= 20
        cor = COLOR_PRIMARY if passa else COLOR_RISK
        ax.scatter(
            comp, sup, s=30 + classes * 2.2, color=cor,
            alpha=0.75, edgecolor="white", linewidth=1.2, zorder=3,
        )
        dx, dy, ha = OFFSETS.get(nome, (0, 22, "center"))
        ax.annotate(
            f"{nome}\n{classes} classes · k mín {kmin}",
            xy=(comp, sup), xytext=(dx, dy), textcoords="offset points",
            ha=ha, fontsize=8, color=cor, zorder=4,
        )

    ax.axhline(0, color="0.6", lw=1, ls="--")
    ax.set_xscale("log")
    ax.set_xlabel("compacidade do agrupamento — distância mediana ao centro (m, escala log)")
    ax.set_ylabel("% a suprimir no par (agrupamento, tercil)")
    ax.set_ylim(-14, 104)
    ax.set_xlim(35, 9000)
    ax.set_title(
        "Só um agrupamento passa — e não é o mais compacto", loc="left", fontsize=11
    )
    ax.text(
        0.5, -0.30,
        "Área do marcador ∝ nº de classes publicadas. Quanto mais à esquerda, mais precisa a "
        "localização revelada\npara o mesmo k — o que torna o agrupamento mais compacto também "
        "o de maior exposição locacional.",
        transform=ax.transAxes, ha="center", fontsize=8, color="0.35",
    )
    fig.tight_layout()
    salvar(fig, "agrupamentos")


# ---------------------------------------------------------------- figura 6
def fig_iloss_por_k(dados: dict) -> None:
    """Supressao e perda de informacao no MESMO eixo de k.

    Painel de cima: quantos domicilios o k exigido obriga a suprimir.
    Painel de baixo: ILoss do par publicado ja contando essa supressao.

    Sao duas leituras do mesmo custo. A de baixo e a que mostra o preco que a
    de cima esconde: um agrupamento pode suprimir pouco e ainda assim custar
    caro, porque generalizou muito antes de chegar ao k - e vice-versa.
    """
    ag = dados.get("agrupamentos")
    if not ag or not dados.get("com_tercil"):
        print("  exp. 06 sem tercil - figura de ILoss pulada")
        return
    if not any(f"par_iloss_k_" in c for m in ag.values() for c in m):
        print("  exp. 06 sem ILoss por k (rode a versao nova) - figura pulada")
        return

    n = dados["domicilios"]
    fig, (ax_sup, ax_il) = plt.subplots(
        2, 1, figsize=(7.2, 5.8), sharex=True,
        gridspec_kw={"height_ratios": [1, 1.15], "hspace": 0.12},
    )

    for nome, (cor, ls, mk) in PALETA_AGRUPAMENTO.items():
        m = ag.get(nome)
        if not m:
            continue
        ks = limiares_de({c.replace("par_", "", 1): 0 for c in m if c.startswith("par_linhas_k_menor_")})
        ks = [k for k in ks if f"par_iloss_k_{k}" in m]
        if not ks:
            continue
        ax_sup.plot(
            ks, [100 * m[f"par_linhas_k_menor_{k}"] / n for k in ks],
            linestyle=ls, marker=mk, ms=4, lw=1.6, color=cor, label=nome,
        )
        ax_il.plot(
            ks, [m[f"par_iloss_k_{k}"] for k in ks],
            linestyle=ls, marker=mk, ms=4, lw=1.6, color=cor, label=nome,
        )

    for ax in (ax_sup, ax_il):
        ax.axvline(20, color="0.45", ls="--", lw=1, zorder=0)
        ax.grid(True, axis="y", lw=0.5, alpha=0.4)

    ax_sup.set_ylabel("% de domicílios a suprimir")
    ax_sup.set_ylim(-4, 104)
    ax_sup.set_title(
        "O mesmo k, dois custos: registros perdidos e informação perdida",
        loc="left", fontsize=11,
    )
    ax_sup.legend(frameon=False, fontsize=8.5, loc="center right", ncol=1)

    ax_il.set_ylabel("ILoss do par publicado")
    ax_il.set_ylim(-0.04, 1.04)
    ax_il.set_xlabel("k exigido")
    ax_il.axhline(1.0, color="0.6", lw=0.9, ls=":")
    # O rotulo do k adotado vai no painel de baixo: e onde a faixa ao lado da
    # linha esta livre em qualquer das cinco curvas.
    ax_il.annotate(
        "k = 20 (valor adotado)", xy=(20.8, 0.40), xycoords=("data", "axes fraction"),
        fontsize=8, color="0.35", ha="left", rotation=90, va="center",
    )
    ax_il.annotate(
        "supressão total", xy=(2.5, 0.955), fontsize=8, color="0.45", va="top",
    )

    ax_il.text(
        0.5, -0.40,
        "ILoss aqui já inclui a supressão: classe abaixo de k sobe à raiz da hierarquia e paga o custo "
        "máximo.\nPor isso o agrupamento mais fino — de menor ILoss com k frouxo — é o que primeiro "
        "dispara a curva quando k aperta.",
        transform=ax_il.transAxes, ha="center", fontsize=8, color="0.35",
    )
    salvar(fig, "iloss_por_k")


def main() -> None:
    set_latex_style()
    print(f"Lendo resultados de {RESULTADOS.relative_to(RAIZ)}\n")

    exp02 = ultimo("02_k_por_nivel")
    if exp02:
        fig_k_por_nivel(exp02)

    exp03 = ultimo("03_faixa_de_distancia")
    if exp03:
        fig_distancia(exp03)
        fig_esquemas(exp03)
        fig_sensibilidade_k(exp03)

    exp06 = ultimo("06_agrupamentos")
    if exp06:
        fig_agrupamentos(exp06)
        fig_iloss_por_k(exp06)

    print(f"\nFiguras em {SAIDA.relative_to(RAIZ)}/ (.pdf para o texto, .png para slides)")
    print(f"gerado em {datetime.now():%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    main()
