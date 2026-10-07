"""Experimento 04 - figuras dos resultados e decisões (para reunião e texto).

Lê os JSON mais recentes de `00_quase_identificadores`, `02_varredura_k` e
`03_varredura_epsilon` e grava PDF + PNG em `figuras/`. Só agregado: nenhuma
figura toca o banco.

Estilo: serifa no estilo LaTeX como as demais figuras do projeto; cores da
paleta de referência do guia de visualização (azul, laranja, verde-água,
amarelo, magenta, nessa ordem fixa, validada para daltonismo entre séries
vizinhas até 5 séries); tons claros abaixo de 3:1 de contraste sempre vêm com
legenda e rótulo direto; texto nunca na cor da série; grade fina e sólida.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from _conexao import ler

AQUI = Path(__file__).resolve().parent
FIGURAS = AQUI / "figuras"

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
NEUTRO = "#b9b8b2"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"
GRADE = "#e4e3df"
DESTAQUE = SERIES[0]

ROTULOS_QI = {
    "sexo": "sexo", "nasc_mes": "mês/ano de nascimento", "equipe": "equipe",
    "tercil": "tercil de distância", "raca_cor": "raça/cor", "mun_nasc": "município de nascimento",
    "mun_resid": "município de residência", "escolaridade": "escolaridade", "ocupacao": "ocupação",
    "estado_civil": "estado civil", "nacionalidade": "nacionalidade",
    "orient_sexual": "orientação sexual", "ident_genero": "identidade de gênero",
}


def estilo() -> None:
    plt.rcParams.update({
        "font.family": "serif", "mathtext.fontset": "cm", "font.size": 9,
        "axes.edgecolor": GRADE, "axes.linewidth": 0.8, "axes.labelcolor": TEXTO_2,
        "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlecolor": TEXTO,
        "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRADE, "grid.linewidth": 0.6, "grid.linestyle": "-",
        "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "legend.frameon": False,
        "legend.fontsize": 8.5, "lines.linewidth": 2, "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round", "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.dpi": 300, "savefig.bbox": "tight", "figure.dpi": 150,
    })


def salvar(fig, nome: str) -> None:
    FIGURAS.mkdir(exist_ok=True)
    fig.savefig(FIGURAS / f"{nome}.pdf")
    fig.savefig(FIGURAS / f"{nome}.png")
    plt.close(fig)
    print(f"  {nome}")


def pct(ax, eixo="x") -> None:
    f = FuncFormatter(lambda v, _: f"{v:.0f}%")
    (ax.xaxis if eixo == "x" else ax.yaxis).set_major_formatter(f)



def legenda(ax, **kw) -> None:
    """Chave da legenda com linha sólida e marcador sem a borda branca (a borda,
    útil no gráfico, cortava a linha da chave e ela parecia tracejada)."""
    from matplotlib.lines import Line2D
    linhas, rotulos = ax.get_legend_handles_labels()
    chaves = [Line2D([], [], color=h.get_color(), lw=2, marker="o", ms=5, mew=0) for h in linhas]
    ax.legend(chaves, rotulos, **kw)


def linha_k(ax, k=5, rotulo="k = 5 (adotado)") -> None:
    ax.axvline(k, color=TEXTO_2, lw=0.8, zorder=0)
    ax.text(k, 1.0, f" {rotulo}", transform=ax.get_xaxis_transform(), fontsize=8, color=TEXTO_2,
            va="top", ha="left")


def barras_h(ax, rotulos, valores, cores, fmt="{:.1f}%") -> None:
    y = range(len(rotulos))
    ax.barh(list(y), valores, height=0.55, color=cores, zorder=2)
    for yi, v in zip(y, valores):
        ax.text(v, yi, f" {fmt.format(v)}", va="center", ha="left", fontsize=8, color=TEXTO)
    ax.set_yticks(list(y), rotulos)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)


# ------------------------------------------------------------ 00
def fig_escada(d00: dict) -> None:
    esc = d00["escada"]
    rot = [ROTULOS_QI[e["acrescenta"]] if i == 0 else "+ " + ROTULOS_QI[e["acrescenta"]]
           for i, e in enumerate(esc)]
    vals = [e["pct_k1"] for e in esc]
    cores = [DESTAQUE if e["acrescenta"] == "raca_cor" else NEUTRO for e in esc]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    barras_h(ax, rot, vals, cores)
    ax.set_xlim(0, 112)
    pct(ax)
    ax.set_xlabel("cidadãos únicos (classe de tamanho 1)")
    ax.set_title("Quem é reidentificável na base sem tratamento", pad=10)
    salvar(fig, "01_escada_quase_identificadores")


def fig_tira_um(d00: dict) -> None:
    tira = d00["tira_um"]
    itens = sorted(tira.items(), key=lambda kv: kv[1]["pct_k1"])
    rot = ["todos os 13"] + [f"sem {ROTULOS_QI[q]}" for q, _ in itens]
    vals = [d00["completo"]["pct_k1"]] + [v["pct_k1"] for _, v in itens]
    cores = [NEUTRO] + [DESTAQUE if q == "nasc_mes" else NEUTRO for q, _ in itens]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    barras_h(ax, rot, vals, cores)
    ax.set_xlim(0, 112)
    pct(ax)
    ax.set_xlabel("cidadãos únicos com os demais quase-identificadores")
    ax.set_title("O nascimento é o quase-identificador que mais pesa", pad=10)
    salvar(fig, "02_sem_cada_quase_identificador")


def fig_generalizacao(d00: dict) -> None:
    g = d00["generalizacao_nascimento"]["cenarios"]
    rot = list(g)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    x = range(len(rot))
    for i, (chave, nome) in enumerate((("pct_k1", "únicos (k = 1)"), ("pct_k_menor_20", "em classe < 20"))):
        ys = [g[r][chave] for r in rot]
        ax.plot(list(x), ys, color=SERIES[i], marker="o", ms=6, mec="white", mew=1.5, label=nome, zorder=3)
        ax.text(len(rot) - 1 + 0.08, ys[-1], f"{ys[-1]:.1f}%", va="center", fontsize=8, color=TEXTO)
    ax.set_xticks(list(x), [r.replace(" (", "\n(") for r in rot], fontsize=8)
    ax.set_ylim(0, 105)
    pct(ax, "y")
    ax.set_ylabel("cidadãos")
    legenda(ax, loc="upper right")
    ax.set_title("Engrossar só a data não basta", pad=10)
    salvar(fig, "03_generalizacao_nascimento")


# ------------------------------------------------------------ 02
def _variante(d02, nome="ciclo, m=1"):
    return [(r["k"], r["nucleo"][nome]) for r in d02["resultados"]]


def fig_supressao(d02: dict) -> None:
    dados = _variante(d02)
    ks = [k for k, _ in dados]
    attrs = [("estado_civil", "estado civil"), ("escolaridade_nivel", "escolaridade"),
             ("raca_cor", "raça/cor"), ("tercil", "tercil de distância")]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for i, (a, nome) in enumerate(attrs):
        ys = [n["pct_suprimido"][a] for _, n in dados]
        ax.plot(ks, ys, color=SERIES[i], marker="o", ms=5, mec="white", mew=1.2, label=nome, zorder=3)
    linha_k(ax)
    ax.set_xticks(ks)
    ax.set_ylim(0, 105)
    pct(ax, "y")
    ax.set_xlabel("k")
    ax.set_ylabel("dos preenchidos, suprimidos")
    legenda(ax, loc="lower right", ncols=2)
    ax.set_title("Custo do k em atributos suprimidos", pad=10)
    salvar(fig, "04_supressao_por_k")


def fig_deslocamento(d02: dict) -> None:
    dados = _variante(d02)
    ks = [k for k, _ in dados]
    faixas = ["<2", "2-9", "10-19", "20-59", "60+"]
    nomes = {"<2": "menos de 2 anos", "2-9": "2 a 9", "10-19": "10 a 19", "20-59": "20 a 59", "60+": "60 ou mais"}
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for i, f in enumerate(faixas):
        ys = [n["desloc"][f]["mediana"] / 30.4 for _, n in dados]
        ax.plot(ks, ys, color=SERIES[i], marker="o", ms=5, mec="white", mew=1.2, label=nomes[f], zorder=3)
    linha_k(ax)
    ax.set_xticks(ks)
    ax.set_xlabel("k")
    ax.set_ylabel("deslocamento mediano (meses)")
    legenda(ax, loc="upper left", bbox_to_anchor=(1.01, 1.0), title="idade", title_fontsize=8.5,
            alignment="left")
    ax.set_title("Custo do k na data de nascimento", pad=10)
    salvar(fig, "05_deslocamento_nascimento_por_k")


def fig_variantes(d02: dict) -> None:
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for i, (nome, rot) in enumerate((("ciclo, m=1", "com corte por ciclo de vida (adotada)"),
                                     ("sem ciclo, m=1", "sem corte por ciclo"))):
        dados = _variante(d02, nome)
        xs = [n["pct_suprimido"]["tercil"] for _, n in dados]
        ys = [n["desloc"]["<2"]["mediana"] / 30.4 for _, n in dados]
        ax.plot(xs, ys, color=SERIES[i], marker="o", ms=6, mec="white", mew=1.5, label=rot, zorder=3)
        for k, x, y in zip([k for k, _ in dados], xs, ys):
            if k in (3, 5, 10, 20):
                ax.annotate(f"k={k}", (x, y), textcoords="offset points", xytext=(5, 4), fontsize=7.5,
                            color=TEXTO_2)
    ax.set_xlim(0, 105)
    pct(ax)
    ax.set_xlabel("tercil de distância suprimido (dos que têm)")
    ax.set_ylabel("deslocamento mediano, < 2 anos (meses)")
    legenda(ax, loc="upper right")
    ax.set_title("A fronteira entre as duas variantes do núcleo", pad=10)
    salvar(fig, "06_variantes_do_nucleo")


def fig_diagnosticos(d02: dict) -> None:
    ks = [r["k"] for r in d02["resultados"]]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for i, (chave, nome) in enumerate((("pct_pessoas_afetadas", "pessoas com algum diagnóstico generalizado"),
                                       ("pct_pares_generalizados", "pares pessoa-diagnóstico generalizados"))):
        ys = [r["diagnosticos"]["global"][chave] for r in d02["resultados"]]
        ax.plot(ks, ys, color=SERIES[i], marker="o", ms=5, mec="white", mew=1.2, label=nome, zorder=3)
    linha_k(ax)
    ax.set_xticks(ks)
    ax.set_ylim(0, 60)
    pct(ax, "y")
    ax.set_xlabel("k")
    legenda(ax, loc="center right", bbox_to_anchor=(1.0, 0.3))
    ax.set_title("Doenças raras: muitos códigos, poucas ocorrências", pad=10)
    salvar(fig, "07_diagnosticos_por_k")


# ------------------------------------------------------------ 03
def fig_epsilon(d03: dict) -> None:
    res = d03["resultados"]
    eps = [r["epsilon"] for r in res]
    series = [
        ("sexoxidade5xequipe", "idade × sexo × equipe"),
        ("diagnostico", "pessoas por código de diagnóstico"),
        ("pesoxsexoxidade5", "peso × sexo × idade"),
        ("sexoxidade5xracaxescol", "raça × escolaridade × sexo × idade"),
    ]
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    for i, (chave, nome) in enumerate(series):
        ax.plot(eps, [r["marginais"][chave]["tvd"] for r in res], color=SERIES[i], marker="o", ms=5,
                mec="white", mew=1.2, label=nome, zorder=3)
    modelo = [sum(r["fidelidade_fora_do_modelo_tvd"].values()) / len(r["fidelidade_fora_do_modelo_tvd"])
              for r in res]
    ax.plot(eps, modelo, color=SERIES[4], marker="o", ms=5, mec="white", mew=1.2,
            label="modelo: combinações não medidas (média)", zorder=3)
    ax.set_xscale("log")
    ax.set_xticks(eps, [f"{e:g}" for e in eps])
    ax.minorticks_off()
    ax.axvline(5, color=TEXTO_2, lw=0.8, zorder=0)
    ax.text(5, 1.0, " ε = 5 (recomendado)", transform=ax.get_xaxis_transform(), fontsize=8,
            color=TEXTO_2, va="top")
    ax.set_ylim(0, 0.95)
    ax.set_xlabel("ε (δ = 10⁻⁶)")
    ax.set_ylabel("distância de variação total")
    legenda(ax, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8, title="marginal",
            title_fontsize=8.5, alignment="left")
    ax.set_title("Erro do kit DP em função de ε", pad=10)
    salvar(fig, "08_kit_dp_erro_por_epsilon")


def fig_ruido_raras(d03: dict) -> None:
    res = d03["resultados"]
    eps = [r["epsilon"] for r in res]
    sig = [r["marginais"]["diagnostico"]["sigma"] for r in res]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.axhspan(1, 4, color=SERIES[1], alpha=0.12, lw=0, zorder=0)
    ax.text(eps[0], 2.5, "  doença rara: 1 a 4 pessoas", va="center", fontsize=8, color=TEXTO_2)
    ax.plot(eps, sig, color=SERIES[0], marker="o", ms=5, mec="white", mew=1.2, zorder=3)
    for e, s in zip(eps, sig):
        if e in (1, 5, 20):
            ax.annotate(f"σ ≈ {s:.0f}", (e, s), textcoords="offset points", xytext=(6, 4), fontsize=8,
                        color=TEXTO)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks(eps, [f"{e:g}" for e in eps])
    ax.minorticks_off()
    ax.set_xlabel("ε (δ = 10⁻⁶)")
    ax.set_ylabel("desvio-padrão do ruído (pessoas)")
    ax.set_title("Ruído na contagem de pessoas por código de diagnóstico", pad=10)
    salvar(fig, "09_kit_dp_ruido_doencas_raras")


# ------------------------------------------------------------ metodologia
def fig_metodologia() -> None:
    """Fluxo do Trilho A: pipeline, experimentos que definem os parâmetros e
    kit DP, da base original às populações sintéticas. Não depende de dados."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

    fig, ax = plt.subplots(figsize=(15.5, 7.6))
    ax.set_xlim(0, 130)
    ax.set_ylim(0, 64)
    ax.axis("off")
    fundo = "#f3f2ee"

    def caixa(x, y, w, h, titulo, corpo="", tag="", cor=None, preenchida=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                    fc=fundo if preenchida else "white", ec=GRADE, lw=1, zorder=2))
        if cor:
            ax.add_patch(Rectangle((x, y + 0.6), 0.7, h - 1.2, fc=cor, ec="none", zorder=3))
        ax.text(x + w / 2, y + h - 2.0, titulo, ha="center", va="top", fontsize=8.6, weight="bold",
                color=TEXTO, zorder=4, linespacing=1.15)
        if corpo:
            ax.text(x + w / 2, y + h - 2.0 - 2.6 * (titulo.count("\n") + 1), corpo, ha="center", va="top",
                    fontsize=7.3, color=TEXTO_2, zorder=4, linespacing=1.25)
        if tag:
            ax.text(x + w / 2, y + 1.3, tag, ha="center", va="bottom", fontsize=7, color=TEXTO_2,
                    style="italic", zorder=4)

    def seta(x1, y1, x2, y2, tracejada=False, rotulo="", rx=0.0, ry=0.0):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9,
                                     lw=1.1, color=TEXTO_2 if tracejada else "#8d8c86",
                                     linestyle=(0, (3, 2)) if tracejada else "-", zorder=1,
                                     shrinkA=0, shrinkB=0))
        if rotulo:
            ax.text((x1 + x2) / 2 + rx, (y1 + y2) / 2 + ry, rotulo, fontsize=7.6, color=TEXTO,
                    ha="center", va="center", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))

    def faixa(y, texto, cor):
        ax.add_patch(Rectangle((15, y), 1.2, 1.2, fc=cor, ec="none"))
        ax.text(17, y + 0.6, texto, fontsize=8.6, color=TEXTO, va="center", weight="bold")

    azul, laranja = SERIES[0], SERIES[1]
    # entrada e saída
    caixa(1, 4, 11, 54, "Base\noriginal", "e-SUS APS/PEC,\n12,4 mil\npessoas\n\napagada no fim\ndo prazo de\nretenção", preenchida=True)
    caixa(117, 4, 12, 54, "Populações\nsintéticas", "estrutura da base\nanonimizada +\nresolução fina\ndo kit DP", preenchida=True)

    # faixa A: pipeline
    faixa(59.8, "Pipeline de migrations: a base que fica", azul)
    ya, ha = 41, 17
    etapas = [
        ("Identificadores\ndiretos", "nomes, CPF, CNS, INE,\ne-mail, documentos,\nblobs, logs", "01–05, 07, 09–13"),
        ("Endereço e\nterritório", "endereço suprimido;\nequipe + tercil de\ndistância (k ≥ 20)", "06, 14"),
        ("Núcleo de quase-\nidentificadores", "sexo, nascimento,\nequipe, tercil, raça,\nescolaridade,\nestado civil", "15"),
        ("Antropometria", "corte de extremos +\nmicroagregação\npor valor", "08"),
        ("Doenças raras", "CID → categoria →\nsupressão; CIAP raro\nsuprimido", "16"),
    ]
    xs = [15, 32, 49, 66, 83]
    for x, (t, c, tag) in zip(xs, etapas):
        caixa(x, ya, 15, ha, t, c, tag, cor=azul)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        seta(x0 + 15, ya + ha / 2, x1, ya + ha / 2)
    caixa(100, ya, 13, ha, "Base\nanonimizada", "versões v00–v16\n(dump por etapa)", preenchida=True)
    seta(98, ya + ha / 2, 100, ya + ha / 2)
    seta(113, ya + ha / 2, 117, ya + ha / 2)

    # faixa B: experimentos
    faixa(36.3, "Experimentos na base original", "#8d8c86")
    yb, hb = 21, 13.5
    experimentos = [
        ("Medição dos quase-\nidentificadores", "81% únicos pelo\nque um vizinho sabe", "00"),
        ("Referência\nde utilidade", "estatísticas para\ncomparar as versões", "01"),
        ("Varredura de k", "k = 2 … 30;\nfronteira risco ×\nsupressão × data", "02"),
        ("Varredura de ε", "ε = 0,1 … 20;\nerro das marginais\ne do modelo", "03"),
    ]
    xb = [15, 32, 49, 66]
    for x, (t, c, tag) in zip(xb, experimentos):
        caixa(x, yb, 15, hb, t, c, tag)
    for x0, x1 in zip(xb[:-1], xb[1:]):
        seta(x0 + 15, yb + hb / 2, x1, yb + hb / 2)

    # parâmetros: k sobe para 15, 08 e 16; ε desce para o kit
    seta(56.5, yb + hb, 56.5, ya, tracejada=True, rotulo="k = 5", ry=1.2)
    seta(58, yb + hb, 72, ya, tracejada=True)
    seta(59.5, yb + hb, 89, ya, tracejada=True)

    # faixa C: kit DP
    faixa(16.3, "Kit de differential privacy (guardado à parte)", laranja)
    yc, hc = 4, 12
    caixa(15, yc, 32, hc, "Marginais da base original",
          "pessoas (sexo, idade, equipe, tercil, raça,\nescolaridade, estado civil), diagnósticos\npor código e capítulo, peso, altura, IMC",
          cor=laranja)
    caixa(51, yc, 30, hc, "Ruído gaussiano discreto",
          "OpenDP; orçamento em zCDP convertido\npara (ε, δ = 10⁻⁶); contribuição\nlimitada por pessoa", cor=laranja)
    seta(47, yc + hc / 2, 51, yc + hc / 2)
    caixa(100, yc, 13, hc, "Kit DP", "um único kit\ncom o ε escolhido", preenchida=True)
    seta(81, yc + hc / 2, 100, yc + hc / 2)
    seta(113, yc + hc / 2, 117, yc + hc / 2)
    seta(73.5, yb, 70, yc + hc, tracejada=True, rotulo="ε", rx=1.6)

    # base original alimenta as três faixas
    for y in (ya + ha / 2, yb + hb / 2, yc + hc / 2):
        seta(12, y, 15, y)

    ax.set_title("Metodologia do Trilho A: k-anonimato evoluído + kit DP", loc="left", pad=6)
    salvar(fig, "00_metodologia_trilho_a")


def main() -> None:
    estilo()
    print(f"Figuras em {FIGURAS}")
    d00 = ler("00_quase_identificadores")
    d02 = ler("02_varredura_k")
    d03 = ler("03_varredura_epsilon")
    fig_metodologia()
    fig_escada(d00)
    fig_tira_um(d00)
    fig_generalizacao(d00)
    fig_supressao(d02)
    fig_deslocamento(d02)
    fig_variantes(d02)
    fig_diagnosticos(d02)
    fig_epsilon(d03)
    fig_ruido_raras(d03)


if __name__ == "__main__":
    main()
