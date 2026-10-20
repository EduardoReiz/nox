from datetime import UTC, datetime, timedelta

from nox.domain.mercado import Vela, limpar_serie, validar_serie

T0 = datetime(2026, 10, 1, tzinfo=UTC)
HORA = timedelta(hours=1)


def vela(i: int, **mudar) -> Vela:
    dados = dict(ativo="BTCUSDT", intervalo="1h", instante=T0 + i * HORA, abertura=100.0,
                 maxima=110.0, minima=95.0, fechamento=105.0, volume=3.0, fonte="binance")
    dados.update(mudar)
    return Vela(**dados)


def test_serie_correta_e_integra():
    assert validar_serie([vela(i) for i in range(5)]).integra


def test_acha_duplicada_fora_de_ordem_e_lacuna():
    serie = [vela(0), vela(1), vela(1), vela(4), vela(3)]
    rel = validar_serie(serie)
    assert rel.duplicadas == [T0 + HORA]
    assert rel.lacunas == [(T0 + HORA, T0 + 4 * HORA)]
    assert rel.fora_de_ordem == [T0 + 3 * HORA]


def test_acha_vela_invalida():
    rel = validar_serie([vela(0, minima=120.0), vela(1, volume=-1.0), vela(2, abertura=0.0)])
    # Uma vela pode quebrar mais de uma regra; o que importa é que as três apareçam.
    for i in range(3):
        assert any((T0 + i * HORA).isoformat() in erro for erro in rel.invalidas)
    assert any("volume negativo" in erro for erro in rel.invalidas)
    assert any("preço menor ou igual a zero" in erro for erro in rel.invalidas)


def test_instante_sem_fuso_e_invalido():
    rel = validar_serie([vela(0, instante=datetime(2026, 10, 1))])
    assert "instante sem fuso horário" in rel.invalidas[0]


def test_limpar_ordena_tira_duplicada_e_invalida():
    limpa = limpar_serie([vela(2), vela(0), vela(0), vela(1, maxima=1.0)])
    assert [v.instante for v in limpa] == [T0, T0 + 2 * HORA]
