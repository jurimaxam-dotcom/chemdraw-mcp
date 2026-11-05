"""Substrat-Matrix für generate_mechanism (Etappe E, 05.11.2026).

≥ 10 Fälle je Familie, nur SMILES (kein Netz im Gate). Randfälle: Stereozentrum, Aromat am
Zentrum, lange Kette, Salz mit Gegenion, Grenzfall sekundär/tertiär, Ringe.
Jeder Fall muss mit substrates_drawn=True ohne fallback_reason rendern
(tests/test_mechanism_geometry.py) und die Pfeil-Geometrie bestehen.
"""

from __future__ import annotations

# (id, reaction_type, substrates, CIP-Deskriptor des Produktzentrums oder "" / "racemic")
MATRIX: list[tuple[str, str, list[str], str]] = [
    # --- SN2: Methyl, primär, sekundär; Stereozentrum wird invertiert -----------------
    ("sn2-R-2-brombutan-cyanid", "sn2", ["C[C@@H](Br)CC", "[C-]#N"], "S"),
    ("sn2-S-2-brombutan-cyanid", "sn2", ["C[C@H](Br)CC", "[C-]#N"], "R"),
    ("sn2-methyliodid-hydroxid", "sn2", ["CI", "[OH-]"], ""),
    ("sn2-ethylbromid-natriumethanolat", "sn2", ["CCBr", "CC[O-].[Na+]"], ""),
    ("sn2-1-chlorbutan-azid", "sn2", ["CCCCCl", "[N-]=[N+]=[N-]"], ""),
    ("sn2-benzylbromid-cyanid-salz", "sn2", ["BrCc1ccccc1", "[K+].[C-]#N"], ""),
    ("sn2-1-bromoctan-iodid", "sn2", ["CCCCCCCCBr", "[I-]"], ""),
    ("sn2-R-2-chlorpentan-thiolat", "sn2", ["CCC[C@@H](C)Cl", "C[S-]"], "S"),
    ("sn2-isobutylbromid-hydrosulfid", "sn2", ["CC(C)CBr", "[SH-]"], ""),
    ("sn2-cyclohexylbromid-iodid", "sn2", ["BrC1CCCCC1", "[I-]"], ""),
    ("sn2-2-iodpropan-hydroxid", "sn2", ["CC(C)I", "[Na+].[OH-]"], ""),
    # --- SN1: tertiär, benzylisch (allylisch abgelehnt); Stereozentrum → racemic ----
    ("sn1-tbucl-wasser", "sn1", ["CC(C)(C)Cl", "O"], ""),
    ("sn1-tbubr-methanol", "sn1", ["CC(C)(C)Br", "CO"], ""),
    ("sn1-2-chlor-2-methylbutan-ethanol", "sn1", ["CCC(C)(C)Cl", "CCO"], ""),
    ("sn1-3-brom-3-methylhexan-wasser", "sn1", ["CCCC(C)(Br)CC", "O"], "racemic"),
    ("sn1-1-phenylethylbromid-wasser", "sn1", ["C[C@@H](Br)c1ccccc1", "O"], "racemic"),
    ("sn1-benzhydrylchlorid-methanol", "sn1", ["ClC(c1ccccc1)c1ccccc1", "CO"], ""),
    ("sn1-tritylchlorid-wasser", "sn1", ["ClC(c1ccccc1)(c1ccccc1)c1ccccc1", "O"], ""),
    ("sn1-1-methylcyclohexylbromid-wasser", "sn1", ["CC1(Br)CCCCC1", "O"], ""),
    ("sn1-2-brom-2-methylpentan-wasser", "sn1", ["CCCC(C)(C)Br", "O"], ""),
    # tert-Halogenid + Cyanid ist kein Lehrbuch-SN1 (E2 überwiegt, am Kation eher Isonitril,
    # Kornblum) — Sichtung 05.11.2026; der Azid-Abfang des Kations ist der klassische Fall
    ("sn1-tbucl-azid-salz", "sn1", ["CC(C)(C)Cl", "[Na+].[N-]=[N+]=[N-]"], ""),
    ("sn1-tbui-isopropanol", "sn1", ["CC(C)(C)I", "CC(C)O"], ""),
    # --- Fischer: eine COOH + primärer/sekundärer Alkohol -----------------------------
    ("fischer-essigsaeure-ethanol", "fischer_ester", ["CC(=O)O", "CCO"], ""),
    ("fischer-propionsaeure-ethanol", "fischer_ester", ["CCC(=O)O", "CCO"], ""),
    ("fischer-ameisensaeure-methanol", "fischer_ester", ["O=CO", "CO"], ""),
    ("fischer-benzoesaeure-methanol", "fischer_ester", ["OC(=O)c1ccccc1", "CO"], ""),
    ("fischer-essigsaeure-isopropanol", "fischer_ester", ["CC(=O)O", "CC(C)O"], ""),
    ("fischer-buttersaeure-1-butanol", "fischer_ester", ["CCCC(=O)O", "CCCCO"], ""),
    ("fischer-salicylsaeure-methanol", "fischer_ester", ["OC(=O)c1ccccc1O", "CO"], ""),
    ("fischer-essigsaeure-isoamylalkohol", "fischer_ester", ["CC(=O)O", "CC(C)CCO"], ""),
    ("fischer-stearinsaeure-methanol", "fischer_ester", ["CCCCCCCCCCCCCCCCCC(=O)O", "CO"], ""),
    ("fischer-essigsaeure-benzylalkohol", "fischer_ester", ["CC(=O)O", "OCc1ccccc1"], ""),
    ("fischer-essigsaeure-cyclohexanol", "fischer_ester", ["CC(=O)O", "OC1CCCCC1"], ""),
]
