"""Configuração compartilhada de testes.

Coloca a raiz do projeto e `src/` no sys.path para que os módulos possam ser
importados como `import compare_models`, etc. Os testes exercitam apenas a lógica
determinística que NÃO depende de credenciais GCP/AWS (os imports de nuvem ficam
dentro das funções dos scripts, então a importação dos módulos é segura).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
for caminho in (str(ROOT), str(SRC)):
    if caminho not in sys.path:
        sys.path.insert(0, caminho)
