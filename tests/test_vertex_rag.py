"""Testes do carregamento/chunking de runbooks do vertex_rag (sem chamar a nuvem)."""
import vertex_rag as vr


def test_carregar_chunks_le_os_oito_runbooks():
    """Os 8 runbooks reaproveitados devem ser carregados."""
    chunks = vr.carregar_chunks()
    arquivos = {c["file"] for c in chunks}
    assert len(arquivos) == 8
    assert "alb-502-errors.md" in arquivos


def test_chunks_tem_formato_e_tamanho_minimo():
    """Cada chunk tem as chaves file/text e respeita o piso de 40 caracteres."""
    chunks = vr.carregar_chunks()
    assert len(chunks) > 0
    for c in chunks:
        assert set(c.keys()) == {"file", "text"}
        assert len(c["text"]) >= 40


def test_modelos_configurados():
    """O modelo de geração é o Gemini Flash e o de embeddings vem de env/default."""
    assert vr.MODELO_GEN == "gemini-1.5-flash"
    assert "embedding" in vr.MODELO_EMBED or "gecko" in vr.MODELO_EMBED
