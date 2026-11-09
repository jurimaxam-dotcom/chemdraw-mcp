"""Peptide aus Drei- und Einbuchstabencode — offline über RDKits HELM-Leser.

PubChem kennt nur Peptide, die jemand eingetragen hat: "Gly-Ala" ja,
"Ala-Trp-Lys-Ser-Gly" nicht (09.11.2026: not_found). Die Kette ist aber
eindeutig aufgeschrieben, also baut dieses Modul sie selbst.

Warum HELM und nicht `Chem.MolFromSequence`: MolFromSequence liest "gly" still
als Gly-Leu-Tyr, Kleinbuchstaben still als L-Form, zerreißt bei Leerzeichen
und kennt keine Termini. `Chem.MolFromHELM` (RDKit 2026.09) kennt D-Reste
([dA]), N-Acetyl ([ac]), C-Amid ([am]) und Ringschlüsse. Gemessen am
09.11.2026 — und was dabei NICHT ging, steht unten bei _UNSUPPORTED:
  - [Nal] verliert still den Rest (Bruchstück-Mol), [seC] ist Selenomethionin,
    nicht Selenocystein — beide bewusst nicht aufgenommen.
  - Aib, Hyp, Pyr/pGlu, Cit, Phg, Cha, Dab, Dap, Hcy, Hse parsen nicht.
  - γ-/ε-Isopeptide (Glutathion) und Phosphorylierung gibt es hier nicht.

Zwei Wege, beide streng:
  - three_letter_smiles("Ala-Gly-Ser") — Teil der Namenskaskade. Gibt None,
    wenn die Eingabe keine reine Sequenz ist (dann fragt die alte Kaskade),
    und wirft PeptideSequenceError, wenn sie wie eine Sequenz aussieht, aber
    einen Rest enthält, den es nicht bauen kann ("Val-Cit": Cit). Der
    Resolver fragt in diesem Fall ERST die alte Kaskade (PubChem kennt
    Val-Cit) und zeigt die Meldung nur, wenn die nichts findet.
  - one_letter_smiles("AGS") — nur hinter dem ausdrücklichen Präfix
    "peptide:", weil "AGS" als Name ATPγS ist und "CCC" als SMILES Propan.
    Kleinbuchstabe = D-Rest (übliche Konvention), nie still L.
"""

from __future__ import annotations

import re

from rdkit import Chem

# Ab 21 Resten wird die Strichformel bei 1000×800 px unlesbar: gemessen am
# 09.11.2026 mit CoordGen-Layout — Atombeschriftung 20 Reste 10,2 px,
# 30 Reste 8,3 px (Bindung 17 → 14 px). Darüber hilft kein Bild mehr.
MAX_RESIDUES = 20

_PROTEINOGENIC = {
    "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
    "Gln": "Q", "Glu": "E", "Gly": "G", "His": "H", "Ile": "I",
    "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
    "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
}  # fmt: skip
# Nichtproteinogene Reste, die RDKits HELM-Bibliothek richtig baut (je ein
# InChIKey-Test in tests/test_peptide.py). Nur als L-/achirale Form.
_EXTRA = {"Orn": "[Orn]", "Nle": "[Nle]", "Nva": "[Nva]", "Sar": "[Sar]", "Abu": "[Abu]"}

THREE_LETTER: dict[str, str] = {**_PROTEINOGENIC, **_EXTRA}
_BY_FOLD = {code.casefold(): code for code in THREE_LETTER}
_ONE_LETTER = {letter: code for code, letter in _PROTEINOGENIC.items()}
_ACHIRAL = {"Gly", "Sar"}

_UNSUPPORTED = {
    "aib": "α-aminoisobutyric acid",
    "hyp": "hydroxyproline",
    "pyr": "pyroglutamic acid",
    "glp": "pyroglutamic acid",
    "cit": "citrulline",
    "phg": "phenylglycine",
    "cha": "cyclohexylalanine",
    "dab": "2,4-diaminobutyric acid",
    "dap": "2,3-diaminopropionic acid",
    "hcy": "homocysteine",
    "hse": "homoserine",
    "sec": "selenocysteine",
    "nal": "naphthylalanine",
    "pyl": "pyrrolysine",
}

_SUPPORTED = (
    "Buildable: the 20 standard codes plus Orn, Nle, Nva, Sar, Abu; D-residues "
    "as D-Ala; termini H-/Ac- and -OH/-NH2 (default: free H-…-OH); cyclo(…) "
    "for a head-to-tail ring. Not available: disulfide bridges, side-chain "
    "(γ/ε) links, phosphorylation."
)

PREFIX = "peptide:"
_CYCLO = re.compile(r"cyclo\s*\((.*)\)", re.IGNORECASE | re.DOTALL)


class PeptideSequenceError(ValueError):
    """Sieht aus wie eine Sequenz, lässt sich aber nicht bauen — englischer Text."""


def _build(monomers: list[str], cyclic: bool) -> str:
    """HELM → kanonisches SMILES. Bruchstücke (stiller Monomer-Verlust) sind ein Fehler."""
    links = f"PEPTIDE1,PEPTIDE1,{len(monomers)}:R2-1:R1" if cyclic else ""
    helm = "PEPTIDE1{" + ".".join(monomers) + "}$" + links + "$$$"
    mol = Chem.MolFromHELM(helm)
    if mol is None or len(Chem.GetMolFrags(mol)) != 1:
        raise PeptideSequenceError(f"RDKit could not build the chain {helm}.")
    return Chem.MolToSmiles(mol)


def _split_cyclo(text: str) -> tuple[str, bool]:
    match = _CYCLO.fullmatch(text)
    if match:
        # Schreibweise mit Bindestrichen am Rand: cyclo(-Arg-Gly-Asp-)
        return match.group(1).strip().strip("-"), True
    return text, False


def _check_length(count: int, name: str) -> None:
    if count > MAX_RESIDUES:
        raise PeptideSequenceError(
            f"'{name}' has {count} residues; a skeletal formula above "
            f"{MAX_RESIDUES} residues is no longer legible (atom labels shrink "
            f"below 10 px). Draw a shorter fragment."
        )


def three_letter_smiles(name: str) -> str | None:
    """SMILES für "Ala-Gly-Ser" & Co. — None, wenn `name` keine reine Sequenz ist.

    Reine Sequenz: Segmente mit "-" getrennt, jedes ein Dreibuchstabencode
    (Groß-/Kleinschreibung egal) oder D-/L- davor, optional H-/Ac- vorn und
    -OH/-NH2 hinten oder cyclo(…) außen, mindestens zwei Reste und mindestens
    ein bekannter Code. Alles andere ("Met-enkephalin", "Fmoc-Gly-OH",
    "Ala") geht unverändert an die Kaskade.
    """
    text, cyclic = _split_cyclo(name.strip())
    if not text or any(ch.isspace() for ch in text):
        return None
    segments = text.split("-")
    if any(not segment for segment in segments):
        return None

    n_cap = c_cap = ""
    if not cyclic:
        first, last = segments[0].casefold(), segments[-1].casefold()
        if first in ("h", "ac"):
            n_cap = "[ac]" if first == "ac" else ""
            segments = segments[1:]
        if segments and last in ("oh", "nh2"):
            c_cap = "[am]" if last == "nh2" else ""
            segments = segments[:-1]

    residues: list[tuple[str, str]] = []  # (Konfiguration "", "d", "l"; Segment)
    config = ""
    for segment in segments:
        folded = segment.casefold()
        if folded in ("d", "l") and not config:
            config = folded
            continue
        if not (len(segment) == 3 and segment.isascii() and segment.isalpha()):
            return None
        residues.append((config, segment))
        config = ""
    if config or len(residues) < 2:
        return None
    if not any(segment.casefold() in _BY_FOLD for _, segment in residues):
        return None

    faults, monomers = [], []
    for config, segment in residues:
        folded = segment.casefold()
        code = _BY_FOLD.get(folded)
        if code is None:
            if folded in _UNSUPPORTED:
                faults.append(f"'{segment}' ({_UNSUPPORTED[folded]}) is not supported")
            else:
                faults.append(f"'{segment}' is not a residue code")
        elif config and code in _ACHIRAL:
            faults.append(f"'{config.upper()}-{segment}': {code} is achiral")
        elif config == "d" and code not in _PROTEINOGENIC:
            faults.append(
                f"'D-{segment}': D-forms exist here only for the 19 chiral standard residues"
            )
        elif config == "d":
            monomers.append(f"[d{_PROTEINOGENIC[code]}]")
        else:
            monomers.append(THREE_LETTER[code])
    if faults:
        raise PeptideSequenceError(
            f"'{name.strip()}' reads as a three-letter peptide sequence, but "
            f"{'; '.join(faults)}. {_SUPPORTED}"
        )
    _check_length(len(monomers), name.strip())
    return _build([m for m in (n_cap, *monomers, c_cap) if m], cyclic)


def one_letter_sequence(name: str) -> str | None:
    """Der Teil hinter "peptide:" — None ohne Präfix."""
    text = name.strip()
    if text.casefold().startswith(PREFIX):
        return text[len(PREFIX):].strip()
    return None


def one_letter_smiles(sequence: str) -> str:
    """SMILES für "AGS" (L), "aG" (D-Ala-Gly), "Ac-AG-NH2", "cyclo(RGDfV)"."""
    text, cyclic = _split_cyclo(sequence.strip())
    n_cap = c_cap = ""
    if not cyclic:
        lowered = text.casefold()
        if lowered.startswith(("ac-", "h-")):
            n_cap = "[ac]" if lowered.startswith("ac-") else ""
            text = text[text.index("-") + 1 :]
        lowered = text.casefold()
        if lowered.endswith(("-nh2", "-oh")):
            c_cap = "[am]" if lowered.endswith("-nh2") else ""
            text = text[: text.rindex("-")]

    faults, monomers = [], []
    for char in text:
        upper = char.upper()
        if upper not in _ONE_LETTER or not char.isascii():
            faults.append(f"'{char}' is not a one-letter residue code")
        elif char == "g":
            faults.append("'g': glycine has no D-form, write G")
        elif char.islower():
            monomers.append(f"[d{upper}]")
        else:
            monomers.append(upper)
    label = f"{PREFIX}{sequence.strip()}"
    if faults:
        raise PeptideSequenceError(
            f"Could not build peptide '{label}': {'; '.join(faults)}. One-letter "
            f"code: uppercase = L residue, lowercase = D residue (e.g. "
            f"peptide:aGS); optional Ac-/-NH2 or cyclo(…). {_SUPPORTED}"
        )
    if len(monomers) < 2:
        raise PeptideSequenceError(
            f"Could not build peptide '{label}': a peptide needs at least two "
            f"residues. For a single amino acid pass its name (e.g. 'alanine')."
        )
    _check_length(len(monomers), label)
    return _build([m for m in (n_cap, *monomers, c_cap) if m], cyclic)
