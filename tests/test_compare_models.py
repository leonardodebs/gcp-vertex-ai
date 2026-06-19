"""Testes da lógica determinística de compare_models (qualidade e custo)."""
import compare_models as cm


# ----- Heurística de qualidade (1-5) -----

def test_qualidade_resposta_vazia_e_minima():
    """Resposta vazia recebe a nota mínima 1."""
    assert cm._qualidade("", ["nat", "internet gateway"]) == 1


def test_qualidade_cobertura_total_da_nota_maxima():
    """Cobrir todas as palavras-chave deve dar nota 5."""
    esperado = ["nat", "internet gateway", "privada"]
    resposta = "O NAT permite saída de subrede privada; o Internet Gateway é público."
    assert cm._qualidade(resposta, esperado) == 5


def test_qualidade_e_case_insensitive():
    """A checagem de palavras-chave ignora maiúsculas/minúsculas."""
    nota = cm._qualidade("RTO e RPO definem recuperação", ["rto", "rpo", "recuperação"])
    assert nota == 5


def test_qualidade_dentro_do_intervalo_1_a_5():
    """Qualquer combinação fica sempre no intervalo fechado [1, 5]."""
    esperado = ["a", "b", "c", "d"]
    for resposta in ["", "a", "a b", "a b c", "a b c d", "nada disso"]:
        nota = cm._qualidade(resposta, esperado)
        assert 1 <= nota <= 5


# ----- Cálculo de custo -----

def test_custo_gemini_flash_por_milhao():
    """1M de tokens de entrada + 1M de saída do Gemini Flash = 0,075 + 0,30."""
    custo = cm._custo("gemini-1.5-flash", 1_000_000, 1_000_000)
    assert round(custo, 4) == round(0.075 + 0.30, 4)


def test_custo_haiku_mais_caro_que_flash():
    """Para o mesmo workload, o Claude 3 Haiku custa mais que o Gemini Flash."""
    flash = cm._custo("gemini-1.5-flash", 500, 500)
    haiku = cm._custo("claude-3-haiku", 500, 500)
    assert haiku > flash


def test_custo_zero_tokens():
    assert cm._custo("gemini-1.5-flash", 0, 0) == 0.0


# ----- Estrutura de constantes -----

def test_cinco_prompts_e_esperados_alinhados():
    """Há 5 prompts e cada um tem sua lista de palavras-chave esperadas."""
    assert len(cm.PROMPTS) == 5
    assert len(cm.ESPERADO) == len(cm.PROMPTS)
