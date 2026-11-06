"""Mechanismus mit den Molekülen des Nutzers (Etappe B, docs/mechanismus-substrate-design.md).

Netzfrei: alle Eingaben sind SMILES. Erwartete Produkte stehen als eigene SMILES hier
(zweite Formulierung), Stereochemie wird per CIP geprüft, nicht am SVG.
"""

import pytest
from rdkit import Chem
from rdkit.Chem import rdCIPLabeler

from chemdraw_tool.mechanism import CurvedArrow
from chemdraw_tool.mechanism_substrate import NU, C, UnsupportedSubstrates, build_steps
from tests.mechanism_matrix import MATRIX


def _plain(smiles: str) -> str:
    """Gemapptes Schritt-SMILES → kanonisches SMILES ohne Maps."""
    mol = Chem.MolFromSmiles(smiles)
    assert mol is not None, smiles
    for a in mol.GetAtoms():
        a.SetAtomMapNum(0)
    return Chem.MolToSmiles(Chem.MolFromSmiles(Chem.MolToSmiles(mol)))


def _canon(smiles: str) -> str:
    return Chem.MolToSmiles(Chem.MolFromSmiles(smiles))


def _maps(step) -> set[int]:
    found = set()
    for smi in step.molecules:
        mol = Chem.MolFromSmiles(smi, sanitize=False)
        found |= {a.GetAtomMapNum() for a in mol.GetAtoms()}
    return found


def _arrows_point_at_drawn_atoms(steps):
    for step in steps:
        maps = _maps(step)
        for arrow in step.arrows:
            assert arrow.source[0] in maps and arrow.target[0] in maps, (step.label, arrow)


# --- SN2 ----------------------------------------------------------------------


def test_sn2_2_brombutan_cyanid_invertiert_das_stereozentrum():
    steps = build_steps("sn2", ["C[C@@H](Br)CC", "[C-]#N"])  # (R)-2-Brombutan
    assert len(steps) == 3
    produkt = next(s for s in steps[-1].molecules if "N" in s)
    mol = Chem.MolFromSmiles(_plain(produkt))
    assert _canon("CCC(C)C#N") == Chem.MolToSmiles(Chem.MolFromSmiles(_plain(produkt)), isomericSmiles=False)
    rdCIPLabeler.AssignCIPLabels(mol)
    codes = [a.GetProp("_CIPCode") for a in mol.GetAtoms() if a.HasProp("_CIPCode")]
    assert codes == ["S"], "SN2 muss (R)-2-Brombutan zu (S)-2-Methylbutannitril invertieren"
    assert _canon("[Br-]") in [_plain(s) for s in steps[-1].molecules]


def test_sn2_zeichnet_das_ganze_substrat_in_jedem_schritt():
    steps = build_steps("sn2", ["CCCCBr", "[I-]"])
    edukte = sorted(_plain(s) for s in steps[0].molecules)
    assert edukte == sorted([_canon("CCCCBr"), _canon("[I-]")])
    assert sorted(_plain(s) for s in steps[-1].molecules) == sorted([_canon("CCCCI"), _canon("[Br-]")])
    ts = steps[1]
    assert ts.is_transition_state and len(ts.molecules) == 3
    assert set(ts.partial_bonds) == {(3, 1), (1, 2)}
    _arrows_point_at_drawn_atoms(steps)


def test_sn2_pfeile_stehen_an_den_edukten_nicht_im_uebergangszustand():
    """Clayden Kap. 15: die Pfeile zeigen, was die Edukte tun; der Übergangszustand ist das
    Ergebnis dieser Bewegung und trägt Teilbindungen, keine Pfeile (Gutachter GELB, Etappe E)."""
    steps = build_steps("sn2", ["CCBr", "[I-]"])
    edukte, ts = steps[0], steps[1]
    assert {(a.source, a.target) for a in edukte.arrows} == {
        ((3, "lone_pair"), (1, "atom")), ((1, "bond_to", 2), (2, "atom"))}
    assert ts.is_transition_state and ts.arrows == []
    assert set(ts.partial_bonds) == {(3, 1), (1, 2)}


def test_sn2_gegenion_faellt_weg():
    steps = build_steps("sn2", ["CCBr", "[Na+].[C-]#N"])
    assert _canon("CCC#N") in [_plain(s) for s in steps[-1].molecules]
    assert not any("Na" in s for st in steps for s in st.molecules)


@pytest.mark.parametrize("nuc, produkt", [
    ("[OH-]", "CCO"), ("CC[O-]", "CCOCC"), ("[N-]=[N+]=[N-]", "CCN=[N+]=[N-]"),
    ("C[S-]", "CCSC"), ("[SH-]", "CCS"), ("[Br-]", "CCBr"),
])
def test_sn2_jedes_nucleophil_der_liste(nuc, produkt):
    steps = build_steps("sn2", ["CCI", nuc])
    assert _canon(produkt) in [_plain(s) for s in steps[-1].molecules]


@pytest.mark.parametrize("smiles, grund", [
    (["CC(C)(C)Br", "[OH-]"], "tertiary"),
    (["CCBr", "O"], "anionic nucleophile"),
    (["CCBr", "N"], "anionic nucleophile"),
    (["CCF", "[OH-]"], "fluoride"),
    (["BrCCBr", "[OH-]"], "more than one"),
    (["Brc1ccccc1", "[OH-]"], "alkyl halide"),
    (["CCBr"], "nucleophile"),
])
def test_sn2_grenze_mit_grund(smiles, grund):
    with pytest.raises(UnsupportedSubstrates, match=grund):
        build_steps("sn2", smiles)


def test_sn2_tertiaer_verweist_auf_sn1():
    with pytest.raises(UnsupportedSubstrates, match="sn1"):
        build_steps("sn2", ["CC(C)(C)Br", "[OH-]"])


# --- SN1 ----------------------------------------------------------------------


def test_sn1_tert_butylchlorid_wasser():
    """Neutrales Nucleophil: Angriff gibt das Oxonium-Ion, erst die Deprotonierung das Produkt
    (Clayden Kap. 15; OpenStax 11.4) — sechs Stationen, Sichtung 05.11.2026 (R4).
    Das Proton nimmt ein zweites Wassermolekül auf, kein freies H⁺ (Gutachter GELB, Etappe E2)."""
    from chemdraw_tool.mechanism_substrate import BASE, H_LEAVING

    steps = build_steps("sn1", ["CC(C)(C)Cl", "O"])
    assert [s.label for s in steps] == [
        "Reactants", "Leaving group departs", "Carbocation (intermediate)", "Nucleophilic attack",
        "Oxonium ion: deprotonation by the solvent", "Products",
    ]
    assert _canon("C[C+](C)C") in [_plain(s) for s in steps[2].molecules]
    assert _canon("[Cl-]") in [_plain(s) for s in steps[2].molecules]
    assert sorted(_plain(s) for s in steps[4].molecules) == sorted(
        [_canon("CC(C)(C)[OH2+]"), _canon("O"), _canon("[Cl-]")])
    assert steps[4].arrows == [
        CurvedArrow(source=(BASE, "lone_pair"), target=(H_LEAVING, "atom"), style="full"),
        CurvedArrow(source=(H_LEAVING, "bond_to", NU), target=(NU, "atom"), style="full"),
    ]
    assert sorted(_plain(s) for s in steps[-1].molecules) == sorted(
        [_canon("CC(C)(C)O"), _canon("[Cl-]"), _canon("[OH3+]")])
    _arrows_point_at_drawn_atoms(steps)


def test_sn1_alkohol_gibt_das_alkyloxonium_ion():
    steps = build_steps("sn1", ["CC(C)(C)Br", "CO"])
    assert len(steps) == 6
    assert _canon("C[OH+]C(C)(C)C") in [_plain(s) for s in steps[4].molecules]
    assert _canon("COC(C)(C)C") in [_plain(s) for s in steps[-1].molecules]
    assert _canon("C[OH2+]") in [_plain(s) for s in steps[-1].molecules]  # protoniertes Methanol


@pytest.mark.parametrize("cid, rt, subs, _cip", MATRIX, ids=[m[0] for m in MATRIX])
def test_gezeichnetes_h_heisst_alle_h_gezeichnet(cid, rt, subs, _cip):
    """Trägt ein Atom ein H als eigenes Atom (Pfeilziel), stehen dort alle seine H als Atome — sonst
    zeigt das Bild „OH⁺“ plus ein loses „H“ am selben O (Gutachter GELB, Etappe E2)."""
    for step in build_steps(rt, subs):
        for smi in step.molecules:
            for atom in _sanitized(smi).GetAtoms():
                drawn = sum(1 for n in atom.GetNeighbors() if n.GetAtomicNum() == 1)
                if atom.GetAtomicNum() != 1 and drawn:
                    assert atom.GetTotalNumHs() == 0, (cid, step.label, smi, atom.GetSymbol())


def test_sn1_anion_behaelt_fuenf_schritte():
    steps = build_steps("sn1", ["CC(C)(C)Cl", "[Na+].[N-]=[N+]=[N-]"])
    assert [s.label for s in steps][3:] == ["Nucleophilic attack", "Product"]


def test_sn1_mit_anion_und_alkohol():
    assert _canon("CC(C)(C)OCC") in [_plain(s) for s in build_steps("sn1", ["CC(C)(C)Br", "CCO"])[-1].molecules]
    azid = build_steps("sn1", ["CC(C)(C)Cl", "[Na+].[N-]=[N+]=[N-]"])  # Azid-Abfang des Kations
    assert _canon("CC(C)(C)N=[N+]=[N-]") in [_plain(s) for s in azid[-1].molecules]


def test_sn1_benzylisch_stereogen_heisst_racemisch():
    steps = build_steps("sn1", ["C[C@@H](Br)c1ccccc1", "O"])
    assert _canon("CC(O)c1ccccc1") in [_plain(s) for s in steps[-1].molecules]
    assert "racemic" in steps[-1].label
    # Produkt ohne Stereodeskriptor: Angriff von beiden Seiten
    assert all("@" not in s for s in steps[-1].molecules)


@pytest.mark.parametrize("smiles", [
    ["C=CC(C)(C)Br", "O"],   # tertiär UND allylisch — allylisch schlägt tertiär
    ["C=CC(C)Cl", "O"],      # sekundär allylisch
])
def test_sn1_allylisch_wird_mit_grund_abgelehnt(smiles):
    # Gutachter-Befund Runde 3 (05.11.2026): das Allylkation ist mesomer, Wasser greift an beiden
    # Enden an — zwei Produkte (OpenStax 11.5; Clayden Kap. 15). Nur eines zu zeichnen ist falsch.
    with pytest.raises(UnsupportedSubstrates, match="allylic") as err:
        build_steps("sn1", smiles)
    assert "two products" in str(err.value) and "generate_reaction" in str(err.value)


@pytest.mark.parametrize("smiles, grund", [
    (["CCCCBr", "O"], "sn2"),
    (["CC(C)Br", "O"], "sn2"),
    (["CC(C)(C)Br", "CC(=O)C"], "nucleophile"),
])
def test_sn1_grenze_mit_grund(smiles, grund):
    with pytest.raises(UnsupportedSubstrates, match=grund):
        build_steps("sn1", smiles)


# --- Fischer ------------------------------------------------------------------


def _sanitized(smiles: str) -> Chem.Mol:
    """Schritt-SMILES mit expliziten, gemappten H (sanitize=False behält sie), dann voll geprüft."""
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    Chem.SanitizeMol(mol)
    return mol


def _charge_at(step, map_id: int) -> int:
    for smi in step.molecules:
        for a in _sanitized(smi).GetAtoms():
            if a.GetAtomMapNum() == map_id:
                return a.GetFormalCharge()
    raise AssertionError(f"Map {map_id} fehlt in {step.label}")


def test_fischer_propionsaeure_ethanol():
    steps = build_steps("fischer_ester", ["CCC(=O)O", "CCO"])
    assert len(steps) == 8
    # Das Katalysator-Proton kommt beim Alkohol (Lösungsmittel) an: protoniertes Ethanol
    assert sorted(_plain(s) for s in steps[-1].molecules) == sorted(
        [_canon("CCC(=O)OCC"), _canon("O"), _canon("CC[OH2+]")])
    _arrows_point_at_drawn_atoms(steps)


def test_fischer_folgt_clayden_mit_protonentransfer():
    """Design (g)9, Clayden Kap. 10: Wasser verlässt das Molekül als OH₂⁺, nicht als neutrales OH.
    Reihenfolge: Protonierung → Angriff → Deprotonierung → Protonierung des OH → Wasserabspaltung
    → Deprotonierung. Der Protonentransfer läuft in zwei Schritten über ein Alkoholmolekül
    (Lösungsmittel), nicht intramolekular (Gutachter GELB, Etappe E2)."""
    from chemdraw_tool.mechanism_substrate import (
        BASE,
        C_ACID,
        H_MOVING,
        O_ALCOHOL,
        O_CARBONYL,
        O_HYDROXY,
    )

    steps = build_steps("fischer_ester", ["CC(=O)O", "CCO"])
    assert [s.label for s in steps] == [
        "Reactants",
        "Protonation of the carbonyl group",
        "Nucleophilic attack of the alcohol",
        "Deprotonation by the alcohol",
        "Protonation of an OH group",
        "Loss of water",
        "Deprotonation (catalyst regenerated)",
        "Products (ROH₂⁺ = catalyst H⁺)",
    ]
    for step in steps:
        for smi in step.molecules:
            _sanitized(smi)  # Valenz und Ladung jedes Zwischenprodukts gültig
    # Ladung wandert: Oxonium am Alkohol-O → Alkohol (ROH₂⁺) → OH₂⁺ → protonierter Ester → ROH₂⁺
    assert _charge_at(steps[3], O_ALCOHOL) == +1
    assert _charge_at(steps[4], O_ALCOHOL) == 0 and _charge_at(steps[4], BASE) == +1
    assert _charge_at(steps[5], O_HYDROXY) == +1 and _charge_at(steps[5], BASE) == 0
    assert _charge_at(steps[6], O_CARBONYL) == +1
    assert _charge_at(steps[7], BASE) == +1  # Katalysator-Proton zurück, am Lösungsmittel
    # Zwei Pfeilpaare: Alkohol holt das H vom Oxonium, das OH holt es vom ROH₂⁺
    assert {(a.source, a.target) for a in steps[3].arrows} == {
        ((BASE, "lone_pair"), (H_MOVING, "atom")), ((H_MOVING, "bond_to", O_ALCOHOL), (O_ALCOHOL, "atom"))}
    assert {(a.source, a.target) for a in steps[4].arrows} == {
        ((O_HYDROXY, "lone_pair"), (H_MOVING, "atom")), ((H_MOVING, "bond_to", BASE), (BASE, "atom"))}
    loss = steps[5].arrows
    assert any(a.source == (C_ACID, "bond_to", O_HYDROXY) and a.target == (O_HYDROXY, "atom") for a in loss)
    assert any(a.source == (O_CARBONYL, "lone_pair") and a.target == (C_ACID, "bond_to", O_CARBONYL) for a in loss)
    assert any(a.target == (O_CARBONYL, "atom") for a in steps[6].arrows)
    assert any(a.source == (BASE, "lone_pair") for a in steps[6].arrows)


def test_vorlage_und_substratweg_sagen_dasselbe():
    """Die festen Lehrbuchbeispiele SIND der Substratweg mit den Beispiel-Substraten."""
    from chemdraw_tool.templates import get_template

    beispiele = {"sn2": ["CBr", "[OH-]"], "sn1": ["CC(C)(C)Br", "O"], "fischer_ester": ["CC(=O)O", "CO"]}
    for rt, smiles in beispiele.items():
        vorlage = get_template(rt).steps
        weg = build_steps(rt, smiles)
        assert [(s.label, s.molecules, s.arrows) for s in vorlage] == [(s.label, s.molecules, s.arrows) for s in weg], rt


def test_fischer_sekundaerer_alkohol_und_reihenfolge_egal():
    steps = build_steps("fischer_ester", ["CC(C)O", "c1ccccc1C(=O)O"])
    assert _canon("CC(C)OC(=O)c1ccccc1") in [_plain(s) for s in steps[-1].molecules]


@pytest.mark.parametrize("smiles, grund", [
    (["CC(=O)O", "CC(C)(C)O"], "tertiary"),
    (["CC(=O)O", "Oc1ccccc1"], "phenol"),
    (["OC(=O)CCC(=O)O", "CO"], "more than one"),
    (["CC(O)C(=O)O"], "two separate"),
    (["CCBr", "CO"], "carboxylic acid"),
])
def test_fischer_grenze_mit_grund(smiles, grund):
    with pytest.raises(UnsupportedSubstrates, match=grund):
        build_steps("fischer_ester", smiles)


# --- Lehrbuchbeispiele bleiben gültige Eingaben ------------------------------


@pytest.mark.parametrize("rt, smiles, n", [
    ("sn2", ["CBr", "[OH-]"], 3),
    ("sn1", ["CC(C)(C)Br", "O"], 6),
    ("fischer_ester", ["CC(=O)O", "CO"], 8),
])
def test_lehrbuchbeispiele_laufen_ueber_den_substratweg(rt, smiles, n):
    assert len(build_steps(rt, smiles)) == n


# --- CIP-Deskriptor des Produktzentrums im Schritt-Label (Desktop-Abnahme 05.11.2026) ----------


def _product_cip(steps) -> str:
    """CIP-Code am Produktzentrum (Map 1), berechnet auf dem UNGEMAPPTEN Produkt."""
    smi = next(s for s in steps[-1].molecules if f":{1}]" in s)
    mapped = Chem.MolFromSmiles(smi)
    idx = next(a.GetIdx() for a in mapped.GetAtoms() if a.GetAtomMapNum() == 1)
    for a in mapped.GetAtoms():
        a.SetAtomMapNum(0)  # Maps ändern CIP-Ränge — Indizes bleiben dabei gleich
    rdCIPLabeler.AssignCIPLabels(mapped)
    atom = mapped.GetAtomWithIdx(idx)
    return atom.GetProp("_CIPCode") if atom.HasProp("_CIPCode") else ""


def test_sn2_label_nennt_das_s_produkt():
    steps = build_steps("sn2", ["C[C@@H](Br)CC", "[C-]#N"])  # (R)-2-Brombutan
    assert steps[-1].label == "Products, (S)"
    assert _product_cip(steps) == "S"


def test_sn2_label_nennt_das_r_produkt():
    steps = build_steps("sn2", ["C[C@H](Br)CC", "[C-]#N"])  # (S)-2-Brombutan
    assert steps[-1].label == "Products, (R)"
    assert _product_cip(steps) == "R"


def test_sn2_achirales_substrat_ohne_deskriptor():
    steps = build_steps("sn2", ["CCBr", "[OH-]"])
    assert steps[-1].label == "Products"


def test_sn2_unbestimmtes_stereozentrum_bekommt_keinen_deskriptor():
    """Entscheid 05.11.: ohne Konfiguration in der Eingabe steht kein (R)/(S) und kein „racemic" —
    über die Herkunft der Eingabe (Racemat oder unbekannt) sagt ein SMILES ohne @ nichts."""
    steps = build_steps("sn2", ["CCC(C)Br", "[C-]#N"])
    assert steps[-1].label == "Products"



@pytest.mark.parametrize("case_id, family, substrates, expected", MATRIX, ids=[m[0] for m in MATRIX])
def test_matrix_produktlabel_traegt_den_deskriptor(case_id, family, substrates, expected):
    steps = build_steps(family, substrates)
    label = steps[-1].label
    if expected in ("R", "S"):
        assert f"({expected})" in label, label
        assert _product_cip(steps) == expected
    elif expected == "racemic":
        assert "racemic" in label, label
    else:
        assert "(R)" not in label and "(S)" not in label and "racemic" not in label, label


# --- Ring am Reaktionszentrum (Kontaktbogen 05.11.2026) ---------------------------------


@pytest.mark.parametrize(("cid", "rt", "subs"), [(c, r, s) for c, r, s, _ in MATRIX], ids=[m[0] for m in MATRIX])
def test_ringe_bleiben_regelmaessig_in_jedem_schritt(cid, rt, subs):
    """Cyclohexylbromid + I⁻: im Übergangszustand lagen beide Ring-Nachbarn des Zentrums auf 90°/270°
    (180° auseinander) — der Ring wurde zum gefalteten Bicyclus. Jede Ringbindung in jedem Schritt
    hat die normale Bindungslänge (± 15 %), jeder Ringwinkel ist ein Polygonwinkel (± 20°)."""
    import math

    from chemdraw_tool.mechanism_coords import BOND, layout_anchored

    steps = build_steps(rt, subs)
    fehler = []
    for step, mols in zip(steps, layout_anchored(steps)):
        for mol in mols:
            conf = mol.GetConformer()
            ri = mol.GetRingInfo()
            for ring in ri.AtomRings():
                n = len(ring)
                soll = 180.0 * (n - 2) / n
                for k, i in enumerate(ring):
                    a, b, c = ring[k - 1], i, ring[(k + 1) % n]
                    pa, pb, pc = (conf.GetAtomPosition(x) for x in (a, b, c))
                    laenge = (pb - pc).Length()
                    if abs(laenge - BOND) > 0.15 * BOND:
                        fehler.append(f"{step.label}: Ringbindung {laenge / BOND:.2f} Bindungslängen")
                    u, v = pa - pb, pc - pb
                    winkel = math.degrees(math.acos(max(-1.0, min(1.0, u.DotProduct(v) / u.Length() / v.Length()))))
                    if abs(winkel - soll) > 20:
                        fehler.append(f"{step.label}: Ringwinkel {winkel:.0f}° statt {soll:.0f}°")
    assert not fehler, f"{cid}:\n" + "\n".join(fehler)


def test_sn1_anion_bindung_laeuft_nicht_durch_die_ladung():
    """Kontaktbogen 05.11.2026: im SN1-Angriff lag die C≡N-Bindung waagrecht rechts vom C⁻ — RDKit
    setzt das „⁻“ oben rechts, die Bindung lief hindurch. Der Nachbar des angreifenden Atoms liegt
    deshalb schräg unterhalb."""
    from chemdraw_tool.mechanism_substrate import NU

    steps = build_steps("sn1", ["CC(C)(C)Br", "[Na+].[C-]#N"])
    angriff = steps[3]
    nuc_anker = angriff.anchors[1]
    (nu_x, nu_y) = nuc_anker[NU]
    nachbar = next(p for m, p in nuc_anker.items() if m != NU)
    assert nachbar[1] < nu_y - 0.3, f"Nachbar {nachbar} liegt nicht unterhalb von {nu_x, nu_y}"


def test_matrix_zeigt_kein_sn1_mit_cyanid():
    """Sichtung 05.11.2026 (R3): tertiäres Halogenid + Cyanid ist kein Lehrbuch-SN1 — E2 überwiegt,
    am Kation entsteht eher das Isonitril (Kornblum). Die Fähigkeit bleibt im Code, die Matrix
    (Kontaktbögen, Gutachter) zeigt stattdessen den Azid-Abfang."""
    from tests.mechanism_matrix import MATRIX

    sn1 = [(cid, subs) for cid, rt, subs, _ in MATRIX if rt == "sn1"]
    assert not [cid for cid, subs in sn1 if any("C-]#N" in s for s in subs)]
    assert any("[N-]=[N+]=[N-]" in s for _, subs in sn1 for s in subs), "Azid-Abfang fehlt in der Matrix"


def _winkel_am_kation(step) -> list[float]:
    """Winkel (°) zwischen den Schweratom-Nachbarn des Kation-C im fertigen Layout, sortiert."""
    import math

    from chemdraw_tool.mechanism_coords import layout_anchored

    mol = layout_anchored([step])[0][0]
    conf = mol.GetConformer()
    c = next(a for a in mol.GetAtoms() if a.GetAtomMapNum() == C)
    p = conf.GetAtomPosition(c.GetIdx())
    dirs = sorted(math.degrees(math.atan2(conf.GetAtomPosition(n.GetIdx()).y - p.y,
                                          conf.GetAtomPosition(n.GetIdx()).x - p.x)) % 360
                  for n in c.GetNeighbors())
    return sorted(((dirs[(i + 1) % len(dirs)] - dirs[i]) % 360) for i in range(len(dirs)))


@pytest.mark.parametrize("halogenid", ["CC(C)(C)Cl", "CC1(Br)CCCCC1", "ClC(c1ccccc1)(c1ccccc1)c1ccccc1"])
def test_sn1_carbokation_ist_trigonal_planar(halogenid):
    """sp²-Kation mit 120° zwischen den Substituenten, nicht T-förmig 90/90/180 (Gutachter GELB,
    Etappe E) — im Kationschritt und beim Angriff des Nucleophils."""
    steps = build_steps("sn1", [halogenid, "O"])
    for label in ("Carbocation (intermediate)", "Nucleophilic attack"):
        step = next(s for s in steps if s.label == label)
        assert _winkel_am_kation(step) == pytest.approx([120, 120, 120], abs=3), label


# --- Konkurrenz durch Eliminierung (Gutachter GELB, Etappe E2) -------------------------------


@pytest.mark.parametrize("rt, smiles, erwartet", [
    ("sn2", ["CC(C)I", "[OH-]"], "E2"),                  # sekundär + starke Base [OS-11.12]
    ("sn2", ["CC(C)Br", "CC[O-]"], "E2"),                # sekundär + Alkoxid
    ("sn2", ["CCBr", "CC(C)(C)[O-]"], "E2"),             # primär + sperriges tert-Alkoxid
    ("sn1", ["CC(C)(C)I", "CC(C)O"], "E1"),              # tertiäres Kation mit β-H
    ("sn1", ["CC(C)(C)Cl", "[N-]=[N+]=[N-]"], "E1"),
    ("sn1", ["C[C@@H](Br)c1ccccc1", "O"], "E1"),         # Methyl-H am 1-Phenylethyl-Kation
])
def test_eliminierung_als_konkurrenz_wird_genannt(rt, smiles, erwartet):
    """OpenStax 11.12 (Zusammenfassung SN1/SN2/E1/E2): sekundäre Halogenide mit starker Base
    eliminieren nach E2; tertiäre Kationen verlieren nach E1 ein β-H. Clayden Kap. 17."""
    from chemdraw_tool.mechanism_substrate import competition_notes

    notes = competition_notes(rt, smiles)
    assert len(notes) == 1 and erwartet in notes[0], notes


@pytest.mark.parametrize("rt, smiles", [
    ("sn2", ["CI", "[OH-]"]),                            # Methyl: kein β-H
    ("sn2", ["CC(C)I", "[I-]"]),                         # sekundär, aber schwach basisch
    ("sn2", ["CCCCCl", "[N-]=[N+]=[N-]"]),               # primär + Azid
    ("sn1", ["ClC(c1ccccc1)(c1ccccc1)c1ccccc1", "O"]),   # Trityl: kein β-H
    ("sn1", ["ClC(c1ccccc1)c1ccccc1", "CO"]),            # Benzhydryl: kein β-H
    ("fischer_ester", ["CC(=O)O", "CCO"]),
])
def test_ohne_konkurrenz_kein_hinweis(rt, smiles):
    from chemdraw_tool.mechanism_substrate import competition_notes

    assert competition_notes(rt, smiles) == []


def test_sn1_angriffsschritt_behaelt_das_halogenid():
    """Gutachter E2: in „Nucleophilic attack“ fehlte X⁻ — das Bild trug +1, alle anderen 0."""
    steps = build_steps("sn1", ["CC(C)(C)Cl", "O"])
    angriff = next(s for s in steps if s.label == "Nucleophilic attack")
    assert _canon("[Cl-]") in [_plain(s) for s in angriff.molecules]


def test_fischer_produkt_nennt_das_katalysator_proton():
    """Gutachter E2: ROH₂⁺ am Ende ist das zurückgebildete H⁺ — das Label sagt es."""
    assert build_steps("fischer_ester", ["CC(=O)O", "CCO"])[-1].label == "Products (ROH₂⁺ = catalyst H⁺)"


def test_e2_hinweis_nennt_e2_als_hauptweg():
    from chemdraw_tool.mechanism_substrate import competition_notes

    assert "often the main pathway" in competition_notes("sn2", ["CC(C)I", "[OH-]"])[0]
