"""Neue Banden müssen die unabhängige IR-Abdeckungsmessung tatsächlich erreichen."""

import argparse

from scripts import masse_eval


def test_ir_report_counts_supported_groups_but_keeps_real_gaps(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(masse_eval, "EVIDENZ", tmp_path)
    # Der Produktivbericht verlangt einen Pfad relativ zum Repo.
    monkeypatch.setattr(masse_eval, "REPO", tmp_path)
    probes = {
        "fluoromethane": "CF",
        "chlorobenzene": "Clc1ccccc1",
        "methyl bromide": "CBr",
        "methanesulfonamide": "CS(=O)(=O)N",
        "dimethyl sulfone": "CS(=O)(=O)C",
        "dimethyl sulfoxide": "CS(=O)C",
        "thioacetamide": "CC(=S)N",
        "methyl azide": "CN=[N+]=[N-]",
        "trimethyl phosphate": "COP(=O)(OC)OC",
        "charged phosphate ester": "COP(=O)([O-])[O-]",
        "ethylidene methylamine": "CC=NC",
        "methyl carbamate": "COC(N)=O",
        "guanidine": "NC(=N)N",
    }
    monkeypatch.setattr(masse_eval, "_ir_stoffe", lambda: [
        {"eingabe": name, "smiles_referenz": smiles} for name, smiles in probes.items()
    ])
    assert masse_eval.ir_abdeckung(argparse.Namespace()) == 0
    report = (tmp_path / "ir-abdeckung.md").read_text()
    for group in [
        "Fluor (aliphatisch, C–F)", "Halogenaryl (C–F/Cl/Br/I)",
        "Alkylchlorid/-bromid/-iodid", "Sulfonamid", "Sulfon", "Sulfoxid",
        "Thiocarbonyl (Thioamid/-harnstoff)", "Azid",
    ]:
        row = next(line for line in report.splitlines()
                   if line.startswith(f"| {group} | ja |"))
        assert "| 1 | 1 |" in row, row
    # Eine P–O-Esterbande deckt keine fehlende P=O-Regel für das Ion ab.
    assert "| Phosphat/Phosphonat | ja | 2 | 1 |" in report
    # Die neue einfache Imin-Regel darf Guanidin nicht als Erfolg verstecken.
    assert "| Imin/Amidin/Guanidin (C=N, nicht aromatisch) | ja | 2 | 1 |" in report
    assert "| Carbamat | ja | 1 | 0 |" in report
    assert "Gruppen mit Lücken" in capsys.readouterr().out


_DETERMINISMUS_SKRIPT = """
import argparse, pathlib, sys
from scripts import masse_eval
ziel = pathlib.Path(sys.argv[1])
masse_eval.EVIDENZ = ziel
masse_eval.REPO = ziel
probes = {"methyl carbamate": "COC(N)=O", "guanidine": "NC(=N)N",
          "charged phosphate ester": "COP(=O)([O-])[O-]"}
masse_eval._ir_stoffe = lambda: [
    {"eingabe": n, "smiles_referenz": s} for n, s in probes.items()
]
masse_eval.ir_abdeckung(argparse.Namespace())
"""


def test_ir_report_is_byte_identical_across_hash_seeds(tmp_path):
    """Gleichstand in „häufigste gemeldete Gruppen“ darf nicht von der Set-Reihenfolge abhängen."""
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parents[1]
    berichte = []
    for seed in ["0", "1", "2", "3", "4", "5"]:
        ziel = tmp_path / seed
        ziel.mkdir()
        env = {**os.environ, "PYTHONHASHSEED": seed}
        subprocess.run([sys.executable, "-c", _DETERMINISMUS_SKRIPT, str(ziel)],
                       cwd=repo, env=env, check=True, capture_output=True)
        berichte.append((ziel / "ir-abdeckung.md").read_bytes())
    erste = set(berichte[0].decode().splitlines())
    abweichend = sorted({z for b in berichte[1:] for z in b.decode().splitlines()} ^ erste)
    assert all(b == berichte[0] for b in berichte[1:]), abweichend
