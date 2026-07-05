import yaml
from pathlib import Path

_IOF_CACHE = None


def carregar_iof(caminho: str | None = None) -> dict:
    global _IOF_CACHE
    if _IOF_CACHE is not None:
        return _IOF_CACHE
    if caminho is None:
        caminho = Path(__file__).parents[1] / "data" / "raw" / "iof_aliquotas.yaml"
    with open(caminho, encoding="utf-8") as f:
        dados = yaml.safe_load(f)
    _IOF_CACHE = {op["tipo"]: op for op in dados["operacoes"]}
    return _IOF_CACHE


def aliquota_iof(tipo_operacao: str) -> float:
    tabela = carregar_iof()
    if tipo_operacao not in tabela:
        return 0.0
    return tabela[tipo_operacao]["aliquota_percent"]
