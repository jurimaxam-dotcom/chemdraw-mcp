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
