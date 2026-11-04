"""Regras de negócio puras (sem I/O), fáceis de testar."""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
VALORES_FALSOS = {"não", "nao", "n", "false", "falso", "0", "no", "inativo"}


@dataclass(frozen=True)
class Aniversario:
    nome: str
    dia: int
    mes: int
    ano: int | None = None
    obs: str = ""

    def proxima_data(self, hoje: date) -> date:
        """Próxima ocorrência do aniversário a partir de `hoje` (inclusive)."""
        ocorrencia = data_no_ano(self.dia, self.mes, hoje.year)
        if ocorrencia < hoje:
            ocorrencia = data_no_ano(self.dia, self.mes, hoje.year + 1)
        return ocorrencia

    def dias_ate(self, hoje: date) -> int:
        return (self.proxima_data(hoje) - hoje).days

    def idade_na_proxima(self, hoje: date) -> int | None:
        if self.ano is None:
            return None
        return self.proxima_data(hoje).year - self.ano


def data_no_ano(dia: int, mes: int, ano: int) -> date:
    """29/02 vira 28/02 em anos não bissextos (ninguém fica sem aniversário)."""
    if mes == 2 and dia == 29 and not calendar.isleap(ano):
        return date(ano, 2, 28)
    return date(ano, mes, dia)


_FORMATOS = [
    # (regex, ordem dos grupos)
    (re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$"), ("ano", "mes", "dia")),   # 1990-03-21
    (re.compile(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$"), ("dia", "mes", "ano")),  # 21/03/1990
    (re.compile(r"^(\d{1,2})[/.-](\d{1,2})$"), ("dia", "mes")),             # 21/03 (sem ano)
    (re.compile(r"^--(\d{1,2})-(\d{1,2})$"), ("mes", "dia")),              # --03-21 (ISO sem ano)
]


def parse_data(valor: object) -> tuple[int, int, int | None]:
    """Converte o texto da planilha em (dia, mes, ano|None). Lança ValueError se inválido."""
    texto = str(valor or "").strip()
    # Datas do Sheets às vezes chegam com hora ("1990-03-21 00:00:00")
    texto = texto.split(" ")[0].split("T")[0]
    for regex, ordem in _FORMATOS:
        m = regex.match(texto)
        if not m:
            continue
        partes = dict(zip(ordem, (int(g) for g in m.groups())))
        dia, mes, ano = partes["dia"], partes["mes"], partes.get("ano")
        # valida usando ano bissexto para aceitar 29/02 sem ano
        date(ano if ano else 2000, mes, dia)
        if ano is not None and not (1900 <= ano <= 2100):
            raise ValueError(f"ano fora do intervalo: {texto!r}")
        return dia, mes, ano
    raise ValueError(f"data em formato desconhecido: {texto!r}")


def ativo(valor: object) -> bool:
    texto = str(valor if valor is not None else "").strip().lower()
    return texto not in VALORES_FALSOS


def carregar(registros: Iterable[dict]) -> tuple[list[Aniversario], list[str]]:
    """Converte linhas da planilha. Retorna (aniversários válidos, avisos)."""
    aniversarios: list[Aniversario] = []
    avisos: list[str] = []
    for i, bruto in enumerate(registros, start=2):  # linha 1 = cabeçalho
        linha = {str(k).strip().lower(): v for k, v in bruto.items()}
        nome = str(linha.get("nome", "")).strip()
        if not nome and not str(linha.get("data", "")).strip():
            continue  # linha vazia
        if not ativo(linha.get("ativo", "")):
            continue
        try:
            dia, mes, ano = parse_data(linha.get("data"))
        except ValueError as e:
            avisos.append(f"Linha {i} ({nome or 'sem nome'}): {e}")
            continue
        if not nome:
            avisos.append(f"Linha {i}: sem nome")
            continue
        aniversarios.append(Aniversario(nome, dia, mes, ano, str(linha.get("obs", "")).strip()))
    return aniversarios, avisos


def proximos(aniversarios: Iterable[Aniversario], hoje: date, dias: Iterable[int]) -> dict[int, list[Aniversario]]:
    """Agrupa por antecedência (ex.: {0: [...hoje], 1: [...amanhã]}) apenas para os `dias` pedidos."""
    alvo = set(dias)
    grupos: dict[int, list[Aniversario]] = {d: [] for d in sorted(alvo)}
    for a in aniversarios:
        d = a.dias_ate(hoje)
        if d in alvo:
            grupos[d].append(a)
    for lista in grupos.values():
        lista.sort(key=lambda a: a.nome.lower())
    return {d: lst for d, lst in grupos.items() if lst}


def ate(aniversarios: Iterable[Aniversario], hoje: date, janela: int) -> list[Aniversario]:
    """Todos os aniversários dos próximos `janela` dias (inclusive hoje), em ordem."""
    return sorted(
        (a for a in aniversarios if a.dias_ate(hoje) <= janela),
        key=lambda a: (a.dias_ate(hoje), a.nome.lower()),
    )


# ------------------------------------------------------------------ mensagens

def _rotulo(dias: int, hoje: date) -> str:
    if dias == 0:
        return "🎉 Hoje"
    if dias == 1:
        return "🔔 Amanhã"
    alvo = hoje + timedelta(days=dias)
    return f"📅 Em {dias} dias ({alvo:%d/%m}, {DIAS_SEMANA[alvo.weekday()]})"


def _item(a: Aniversario, hoje: date) -> str:
    extra = []
    idade = a.idade_na_proxima(hoje)
    if idade is not None and idade > 0:
        extra.append(f"{idade} anos")
    if a.obs:
        extra.append(a.obs)
    return f"• {a.nome}" + (f" — {' · '.join(extra)}" if extra else "")


def mensagem_lembretes(grupos: dict[int, list[Aniversario]], hoje: date) -> str | None:
    if not grupos:
        return None
    partes = ["🎂 Lembretes de aniversário"]
    for dias, lista in grupos.items():
        partes.append("")
        partes.append(_rotulo(dias, hoje))
        partes.extend(_item(a, hoje) for a in lista)
    if 0 in grupos:
        partes += ["", "Não esqueça de dar os parabéns! 🥳"]
    return "\n".join(partes)


def mensagem_resumo(lista: list[Aniversario], hoje: date, janela: int) -> str:
    if not lista:
        return f"📆 Nenhum aniversário nos próximos {janela} dias."
    partes = [f"📆 Aniversários dos próximos {janela} dias", ""]
    for a in lista:
        d = a.proxima_data(hoje)
        quando = "hoje" if d == hoje else "amanhã" if a.dias_ate(hoje) == 1 else DIAS_SEMANA[d.weekday()]
        partes.append(f"{d:%d/%m} ({quando}) {_item(a, hoje)[2:]}")
    return "\n".join(partes)
