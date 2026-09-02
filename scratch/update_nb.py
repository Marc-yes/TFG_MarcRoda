import nbformat
import os

NOTEBOOK_PATH = "Codi_Projecte/ai/baselines.ipynb"

with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

for cell in nb.cells:
    if cell.cell_type == "markdown" and "cv-markdown-header-001" in cell.get("id", ""):
        cell.source = (
            "## Validació Encreuada (Cross-Validation)\n\n"
            "A continuació implementem una validació encreuada de 4 folds (`StratifiedKFold`) amb llindar d'Estadi 1 a 0.55, "
            "exactament amb el mateix protocol que la validació exterior (*Outer Loop*) del model final V3 (`trainIA_V3.ipynb`), "
            "permetent una comparativa directa i 100% controlada (*apples-to-apples*)."
        )
    if cell.cell_type == "code":
        src = cell.source
        if "StratifiedKFold(n_splits=5" in src:
            src = src.replace("StratifiedKFold(n_splits=5", "StratifiedKFold(n_splits=4")
        if "y1_pred = (y1_prob >= 0.70).astype(int)" in src:
            src = src.replace("y1_pred = (y1_prob >= 0.70).astype(int)", "y1_pred = (y1_prob >= 0.55).astype(int)")
        cell.source = src

with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print("Notebook baselines.ipynb actualitzat correctament!")
