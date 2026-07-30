import polars as pl
try:
    from src.comparador import (
        comparar_custos, gerar_faturas_sinteticas, slippage_por_volume,
        vwap_execucao, spread_indiferenca_wire,
    )
except ImportError:
    import sys
    sys.path.insert(0, ".")
    from src.comparador import (
        comparar_custos, gerar_faturas_sinteticas, slippage_por_volume,
        vwap_execucao, spread_indiferenca_wire,
    )


# --- #3 (ADR-0011): VWAP no order book real, matemática pura ---

def test_vwap_um_nivel_suficiente():
    # book: 10.000 USDT a 5,00. Comprar R$ 25.000 = 5.000 USDT, tudo no 1º nível -> VWAP 5,00
    asks = [[5.00, 10_000.0]]
    assert vwap_execucao(asks, 25_000) == 5.00


def test_vwap_atravessa_niveis_encarece():
    # 1.000 USDT a 5,00 (=R$5k) esgota; resto vem a 5,10. VWAP fica entre 5,00 e 5,10
    asks = [[5.00, 1_000.0], [5.10, 10_000.0]]
    vwap = vwap_execucao(asks, 20_000)
    assert 5.00 < vwap < 5.10


def test_vwap_book_raso_retorna_none():
    # book só tem R$5k de profundidade, mas pedimos R$50k -> None (dispara fallback)
    asks = [[5.00, 1_000.0]]
    assert vwap_execucao(asks, 50_000) is None


def test_slippage_execucao_cai_no_fallback_sem_book(monkeypatch):
    # se o order book vier vazio, usa a heurística por faixa (fallback documentado)
    import src.comparador as cmp
    monkeypatch.setattr(cmp, "order_book_usdt_brl", lambda *a, **k: None)
    assert cmp.slippage_execucao(5_000_000) == slippage_por_volume(5_000_000)


# --- Achado #9 (auditoria 2026-07-30): slippage do USDC no book errado (USDT) ---

def test_slippage_execucao_usdc_usa_book_proprio_nao_o_do_usdt(monkeypatch):
    import src.comparador as cmp
    # books com profundidades bem diferentes: USDT líquido, USDC raso
    monkeypatch.setattr(cmp, "order_book_usdt_brl", lambda *a, **k: {
        "bids": [[5.00, 1_000_000.0]], "asks": [[5.00, 1_000_000.0]],
    })
    monkeypatch.setattr(cmp, "order_book_usdc_brl", lambda *a, **k: {
        "bids": [[5.00, 100.0]], "asks": [[5.00, 100.0]],
    })
    slip_usdt = cmp.slippage_execucao(400_000, moeda="usdt")
    slip_usdc = cmp.slippage_execucao(400_000, moeda="usdc")
    assert slip_usdt == 0.0          # book fundo, sem atrito
    assert slip_usdc > slip_usdt     # book raso do USDC não cobre o volume -> cai no fallback por faixa


# --- Achado #8 (auditoria 2026-07-30): prêmio de on-ramp mistura FX (PTAX D-1) com
# liquidez (preço cripto tempo real). Não dá pra "resolver" sem FX intradiário pago —
# a correção honesta é EXPOR a defasagem, não escondê-la (mesmo princípio do ADR-0011 §6).

def test_defasagem_ptax_binance_calcula_divergencia_relativa():
    from src.comparador import _defasagem_pct
    assert abs(_defasagem_pct(mid=5.75, ptax=5.70) - ((5.75 - 5.70) / 5.70 * 100)) < 1e-9


def test_defasagem_ptax_binance_none_sem_mid():
    from src.comparador import _defasagem_pct
    assert _defasagem_pct(mid=None, ptax=5.70) is None


def test_comparar_custos_expoe_defasagem_ptax_binance(monkeypatch):
    # PTAX (D-1) = 5,70; Binance mid = 5,80 -> defasagem ~1,75%, acima do limiar de ruído.
    import src.comparador as cmp
    monkeypatch.setattr(cmp, "ptax_venda", lambda: 5.70)
    monkeypatch.setattr(cmp, "order_book_usdt_brl", lambda *a, **k: {
        "bids": [[5.79, 1_000_000.0]], "asks": [[5.81, 1_000_000.0]],
    })
    monkeypatch.setattr(cmp, "order_book_usdc_brl", lambda *a, **k: {
        "bids": [[5.70, 1_000_000.0]], "asks": [[5.70, 1_000_000.0]],
    })
    df = cmp.comparar_custos(50_000, caso_uso="cross_border")
    usdt = df.filter(pl.col("trilho") == "USDT (Polygon)")
    usdc = df.filter(pl.col("trilho") == "USDC (Polygon)")
    assert usdt["defasagem_ptax_binance_pct"][0] > cmp.LIMIAR_DEFASAGEM_PTAX_PERCENT
    assert abs(usdc["defasagem_ptax_binance_pct"][0]) < 1e-6  # sem divergência: mid == ptax


def test_comparar_custos_busca_order_book_uma_vez_por_moeda(monkeypatch):
    # antes do fix, cada um dos 4 trilhos stablecoin (USDT-ERC20/Polygon, USDC-ERC20/Polygon)
    # chamava slippage_execucao -> 4 chamadas de rede pro MESMO valor_brl, quando só existem
    # 2 books distintos (USDT e USDC) a consultar.
    import src.comparador as cmp
    chamadas = {"usdt": 0, "usdc": 0}

    def _book_usdt(*a, **k):
        chamadas["usdt"] += 1
        return {"bids": [[5.00, 1_000_000.0]], "asks": [[5.00, 1_000_000.0]]}

    def _book_usdc(*a, **k):
        chamadas["usdc"] += 1
        return {"bids": [[5.00, 1_000_000.0]], "asks": [[5.00, 1_000_000.0]]}

    monkeypatch.setattr(cmp, "order_book_usdt_brl", _book_usdt)
    monkeypatch.setattr(cmp, "order_book_usdc_brl", _book_usdc)
    cmp.comparar_custos(50_000, caso_uso="cross_border")
    assert chamadas["usdt"] == 1
    assert chamadas["usdc"] == 1


# --- ponto C (ADR-0010): slippage por volume, aproximação documentada ---

def test_slippage_zero_para_volume_pequeno():
    assert slippage_por_volume(50_000) == 0.0


def test_slippage_monotonico_com_volume():
    # propriedade econômica: converter mais nunca sofre MENOS atrito proporcional
    volumes = [50_000, 500_000, 5_000_000, 50_000_000]
    slips = [slippage_por_volume(v) for v in volumes]
    assert slips == sorted(slips)
    assert slips[-1] > slips[0]


def test_slippage_encarece_custo_percentual_do_trilho_stablecoin():
    pequeno = comparar_custos(50_000, caso_uso="cross_border")
    grande = comparar_custos(50_000_000, caso_uso="cross_border")
    pct_peq = pequeno.filter(pl.col("trilho") == "USDT (Polygon)")["custo_percent"][0]
    pct_gra = grande.filter(pl.col("trilho") == "USDT (Polygon)")["custo_percent"][0]
    assert pct_gra > pct_peq  # volume grande paga mais % de conversão


# --- estrutura básica (caso_uso cross_border é o default) ---

def test_comparador_retorna_dataframe():
    df = comparar_custos(50000, caso_uso="cross_border")
    assert isinstance(df, pl.DataFrame)
    # cross_border: Wire + USDT(erc20/poly) + USDC(erc20/poly) = 5 trilhos
    assert len(df) == 5


def test_comparador_tem_colunas_esperadas():
    df = comparar_custos(50000)
    cols = ["trilho", "moeda", "spread_brl", "tarifa_brl", "iof_brl", "gas_brl", "custo_total_brl", "custo_percent"]
    for c in cols:
        assert c in df.columns


def test_comparador_ordenado_por_custo():
    df = comparar_custos(50000)
    custos = df["custo_total_brl"].to_list()
    assert custos == sorted(custos)


# --- Achado #1 (auditoria 2026-07-30): manchete de "~90% de economia" depende de duas
# constantes (IOF + SPREAD_WIRE_PERCENT fixo em 2,5%, spread de varejo). Tesouraria
# corporativa negocia spread bem menor — o spread precisa ser parâmetro, e a fronteira
# onde a conclusão inverte precisa ser calculável, não escondida.

def test_spread_wire_e_configuravel():
    caro = comparar_custos(1_000_000, spread_wire_percent=2.5)
    barato = comparar_custos(1_000_000, spread_wire_percent=0.5)
    wire_caro = caro.filter(pl.col("trilho") == "Wire (SWIFT)")["custo_total_brl"][0]
    wire_barato = barato.filter(pl.col("trilho") == "Wire (SWIFT)")["custo_total_brl"][0]
    assert wire_barato < wire_caro


def test_fronteira_indiferenca_bate_no_ponto_exato(monkeypatch):
    # no spread de indiferença, Wire e o melhor trilho stablecoin custam (quase) o mesmo.
    # Determinístico (sem rede) — CoinGecko/Binance ao vivo têm rate-limit e variam entre
    # as duas chamadas (cálculo da fronteira + verificação), o que quebraria a igualdade.
    import src.comparador as cmp
    monkeypatch.setattr(cmp, "preco_stablecoin", lambda moeda: None)
    monkeypatch.setattr(cmp, "ptax_venda", lambda: 5.70)
    monkeypatch.setattr(cmp, "order_book_usdt_brl", lambda *a, **k: None)
    monkeypatch.setattr(cmp, "order_book_usdc_brl", lambda *a, **k: None)
    monkeypatch.setattr(cmp, "gas_fee_eth", lambda: {"avg_gwei": 20})
    monkeypatch.setattr(cmp, "gas_fee_polygon", lambda: {"avg_gwei": 50})
    monkeypatch.setattr(cmp, "preco_eth", lambda: 1800.0)
    monkeypatch.setattr(cmp, "preco_matic", lambda: 0.50)

    valor = 1_000_000
    tipo = "remessa_internacional_terceiros"
    spread_indif = spread_indiferenca_wire(valor, tipo)
    assert spread_indif is not None

    df = comparar_custos(valor, tipo, caso_uso="cross_border", spread_wire_percent=spread_indif)
    wire_total = df.filter(pl.col("trilho") == "Wire (SWIFT)")["custo_total_brl"][0]
    melhor_stablecoin = df.filter(pl.col("trilho") != "Wire (SWIFT)")["custo_total_brl"].min()
    assert abs(wire_total - melhor_stablecoin) < 1.0  # tolerância de arredondamento (R$1)


def test_fronteira_indiferenca_importacao_bens_alcancavel_remessa_estrutural(monkeypatch):
    # IOF isento (ADR-0011 §1, importacao_bens): a folga de IOF que sustenta a manchete
    # desaparece, então a fronteira de indiferença fica num spread de Wire POSITIVO e
    # realista de se negociar (achado #1 do review: com spread ~0,5%, stablecoin já perde
    # aqui). Já em remessa a terceiros (IOF 3,5%), a fronteira é profundamente NEGATIVA —
    # nenhum spread real de Wire (sempre ≥0%) alcança; a arbitragem é estrutural, não
    # depende do spread negociado. Isola o efeito do IOF fixando o resto determinístico —
    # CoinGecko/Binance ao vivo têm rate-limit e variam entre as duas chamadas.
    import src.comparador as cmp
    monkeypatch.setattr(cmp, "preco_stablecoin", lambda moeda: None)  # força fallback fixo
    monkeypatch.setattr(cmp, "ptax_venda", lambda: 5.70)
    monkeypatch.setattr(cmp, "order_book_usdt_brl", lambda *a, **k: None)
    monkeypatch.setattr(cmp, "order_book_usdc_brl", lambda *a, **k: None)
    monkeypatch.setattr(cmp, "gas_fee_eth", lambda: {"avg_gwei": 20})
    monkeypatch.setattr(cmp, "gas_fee_polygon", lambda: {"avg_gwei": 50})
    monkeypatch.setattr(cmp, "preco_eth", lambda: 1800.0)
    monkeypatch.setattr(cmp, "preco_matic", lambda: 0.50)

    spread_bens = spread_indiferenca_wire(1_000_000, "importacao_bens")
    spread_remessa = spread_indiferenca_wire(1_000_000, "remessa_internacional_terceiros")
    assert 0 < spread_bens < 5        # realista de negociar -> a conclusão PODE inverter
    assert spread_remessa < 0         # nenhum spread real de Wire alcança -> ganha sempre
    assert spread_bens > spread_remessa


def test_wire_tem_spread_e_iof_positivos():
    df = comparar_custos(100000, "remessa_internacional_terceiros")
    wire = df.filter(pl.col("trilho") == "Wire (SWIFT)")
    assert wire["spread_brl"][0] > 0
    assert wire["iof_brl"][0] > 0
    assert wire["tarifa_brl"][0] > 0


# --- F2: segmentação por caso de uso ---

def test_cross_border_nao_inclui_pix():
    # PIX é doméstico BRL — não disputa pagamento cross-border (F2)
    df = comparar_custos(50000, caso_uso="cross_border")
    assert "PIX" not in df["trilho"].to_list()
    assert "Wire (SWIFT)" in df["trilho"].to_list()


def test_domestico_so_tem_pix():
    df = comparar_custos(50000, caso_uso="domestico")
    trilhos = df["trilho"].to_list()
    assert trilhos == ["PIX"]


def test_domestico_pix_custo_zero():
    df = comparar_custos(50000, caso_uso="domestico")
    pix = df.filter(pl.col("trilho") == "PIX")
    assert pix["custo_total_brl"][0] == 0.0


# --- F1: custo do trilho stablecoin inclui spread de conversão ---

def test_stablecoin_tem_spread_de_conversao_positivo():
    # antes do F1 o custo era só gas (spread_brl == 0). Agora on/off-ramp entra.
    df = comparar_custos(50000, caso_uso="cross_border")
    stables = df.filter(pl.col("moeda").str.contains("USD") & (pl.col("trilho") != "Wire (SWIFT)"))
    assert len(stables) == 4
    for s in stables["spread_brl"].to_list():
        assert s > 0  # off-ramp fixo (0,3%) garante spread > 0 mesmo se prêmio on-ramp = 0


def test_stablecoin_custo_total_inclui_spread_mais_gas():
    df = comparar_custos(50000, caso_uso="cross_border")
    usdt = df.filter(pl.col("trilho") == "USDT (Polygon)")
    linha = usdt.row(0, named=True)
    esperado = linha["spread_brl"] + linha["tarifa_brl"] + linha["iof_brl"] + linha["gas_brl"]
    assert abs(linha["custo_total_brl"] - esperado) < 0.01


# --- F7: religação do filtro legal BCB 561 (eFX remove stablecoin) ---

def test_efx_remove_stablecoin_da_comparacao():
    df = comparar_custos(50000, caso_uso="cross_border", eletronico_cambio=True)
    trilhos = df["trilho"].to_list()
    assert "Wire (SWIFT)" in trilhos
    assert not any("USDT" in t or "USDC" in t for t in trilhos)


# --- IOF ---

def test_iof_35_para_remessa():
    df = comparar_custos(100000, "remessa_internacional_terceiros")
    wire = df.filter(pl.col("trilho") == "Wire (SWIFT)")
    iof_esperado = (100000 / 5.7) * 0.035 * 5.7
    assert abs(wire["iof_brl"][0] - iof_esperado) < 1.0


# --- perfis sintéticos (rodam em cross_border, onde a escolha importa) ---

def test_faturas_sinteticas_4_perfis():
    df = gerar_faturas_sinteticas()
    assert len(df) == 4
    assert "perfil" in df.columns


def test_faturas_sinteticas_melhor_nao_e_sempre_pix():
    # o bug F2 fazia PIX vencer sempre; em cross_border PIX nem entra
    df = gerar_faturas_sinteticas()
    assert "PIX" not in df["melhor_trilho"].to_list()