from datetime import date

import pytest

from bot import birthdays as b


@pytest.mark.parametrize("entrada,esperado", [
    ("1990-03-21", (21, 3, 1990)),
    ("21/03/1990", (21, 3, 1990)),
    ("1/3/1990", (1, 3, 1990)),
    ("21-03-1990", (21, 3, 1990)),
    ("21/03", (21, 3, None)),
    ("--03-21", (21, 3, None)),
    ("29/02", (29, 2, None)),
    ("1990-03-21 00:00:00", (21, 3, 1990)),
    (" 2000-02-29 ", (29, 2, 2000)),
])
def test_parse_data_ok(entrada, esperado):
    assert b.parse_data(entrada) == esperado


@pytest.mark.parametrize("entrada", ["", "abc", "31/02/1990", "2001-02-29", "13/13", "21/03/1800", None])
def test_parse_data_invalida(entrada):
    with pytest.raises(ValueError):
        b.parse_data(entrada)


def test_bissexto_vira_28_de_fevereiro():
    a = b.Aniversario("Leap", 29, 2, 2000)
    assert a.proxima_data(date(2027, 2, 1)) == date(2027, 2, 28)
    assert a.proxima_data(date(2028, 2, 1)) == date(2028, 2, 29)


def test_virada_de_ano():
    a = b.Aniversario("Ano Novo", 1, 1, 1990)
    hoje = date(2026, 12, 31)
    assert a.dias_ate(hoje) == 1
    assert a.idade_na_proxima(hoje) == 37


def test_carregar_ignora_inativos_vazios_e_reporta_invalidos():
    registros = [
        {"Nome ": "Ana", "Data": "1990-11-04"},
        {"nome": "Bia", "data": "05/11", "ativo": "não"},
        {"nome": "", "data": ""},
        {"nome": "Caio", "data": "xx"},
    ]
    lista, avisos = b.carregar(registros)
    assert [a.nome for a in lista] == ["Ana"]
    assert len(avisos) == 1 and "Linha 5" in avisos[0]


def test_mensagem_lembretes_agrupa_hoje_e_amanha():
    hoje = date(2026, 11, 4)
    lista = [b.Aniversario("Ana", 4, 11, 1990), b.Aniversario("Bruno", 5, 11), b.Aniversario("Zé", 20, 12)]
    grupos = b.proximos(lista, hoje, [0, 1])
    msg = b.mensagem_lembretes(grupos, hoje)
    assert "Hoje" in msg and "Ana — 36 anos" in msg
    assert "Amanhã" in msg and "• Bruno" in msg
    assert "Zé" not in msg


def test_sem_aniversarios_nao_gera_mensagem():
    assert b.mensagem_lembretes({}, date(2026, 1, 1)) is None


def test_resumo_ordena_por_proximidade():
    hoje = date(2026, 11, 4)
    lista = [b.Aniversario("C", 30, 11), b.Aniversario("A", 4, 11), b.Aniversario("B", 10, 11), b.Aniversario("X", 1, 1)]
    nomes = [a.nome for a in b.ate(lista, hoje, 30)]
    assert nomes == ["A", "B", "C"]
