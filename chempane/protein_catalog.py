"""Welcher Proteineintrag? — eine Stelle für Meldung, Datenblatt und Bild (E8).

Die Protein-Erkennung aus E6 nimmt bei mehreren Organismen den Menschen. Für
Laborenzyme ist das falsch: „Lysozym" ist im Labor Hühnereiweiß-Lysozym,
„Trypsin" meist Rindertrypsin. Darum in dieser Reihenfolge:

1. Kuratierte Laborstandards (Tabelle unten, ohne Netz) — mit festem UniProt-
   und PDB-Eintrag samt Ketten. Organismuswörter in der Eingabe („human
   lysozyme", „Rindertrypsin") wählen eine andere Zeile oder gehen als Filter
   an UniProt.
2. Antikörper: Tabelle INN → PDB-Eintrag; jeder andere Antikörpername (auch
   „IgG", „Antikörper", „anti-GFP") bekommt das IgG-Schema und die intakte
   IgG-Struktur 1HZH als Anschauung — ausdrücklich nicht „der" Antikörper.
3. Bakterielle Gen-/Proteinkürzel („RecA", „LipA", „GroEL", Form
   [a-zA-Z][a-z]{2}[A-Z][A-Z0-9]?) über UniProts Genfeld; was danach steht
   („RecA Bacillus subtilis", „RecA from B. subtilis") ist der Organismus.
4. Sonst UniProt nach Namen (databases.uniprot_protein, Mensch zuerst).

Jede Zeile der Tabellen ist am 10.11.2026 nachgemessen: UniProt-REST (Name,
Organismus, reife Kette aus den Merkmalen Chain/Peptide, Masse aus der
Sequenz mit mittleren Restmassen + H₂O je Kette) und RCSB-GraphQL (Titel des
Eintrags, Ketten mit Organismus und UniProt-Zuordnung, Mutationen).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- Organismuswörter ---------------------------------------------------------
# (Wörter in der Eingabe, wissenschaftlicher Name für UniProt, Anzeige)
_ORGANISMS = [
    (("hen egg-white", "hen egg white", "egg-white", "egg white", "hen", "chicken",
      "hühnereiweiß", "huehnereiweiss", "hühnereiweiss", "hühner", "huehner", "huhn",
      "gallus gallus"), "Gallus gallus", "chicken"),
    (("bovine", "bos taurus", "beef", "cow", "rinder", "rind", "bovin"), "Bos taurus", "bovine"),
    (("human", "homo sapiens", "humanes", "humane", "mensch", "menschliches", "human-"),
     "Homo sapiens", "human"),
    (("porcine", "pig", "swine", "sus scrofa", "schweine", "schwein"), "Sus scrofa", "porcine"),
    (("horse liver", "horse heart", "horse", "equine", "equus caballus", "pferdeleber",
      "pferdeherz", "pferde", "pferd"), "Equus caballus", "horse"),
    (("baker's yeast", "yeast", "saccharomyces cerevisiae", "hefe"),
     "Saccharomyces cerevisiae", "yeast"),
    (("sperm whale", "physeter", "pottwal"), "Physeter macrocephalus", "sperm whale"),
    (("mouse", "murine", "mus musculus", "maus"), "Mus musculus", "mouse"),
    (("rat", "rattus norvegicus", "ratte"), "Rattus norvegicus", "rat"),
]
_ORGANISM_WORDS = sorted(
    ((w, sci) for words, sci, _ in _ORGANISMS for w in words), key=lambda x: -len(x[0])
)
_TISSUE = ("liver", "heart", "serum", "leber", "herz")
# Nur deutsche Vorsilben bilden Komposita ("Rindertrypsin") — englische Wörter
# nicht: "horseradish peroxidase" ist kein Pferdeprotein.
_GERMAN_PREFIXES = {
    "rinder", "schweine", "hühnereiweiß", "hühnereiweiss", "huehnereiweiss", "hühner",
    "huehner", "pferdeleber", "pferdeherz", "pferde", "hefe",
}


# --- Tabellen -----------------------------------------------------------------


@dataclass(frozen=True)
class Curated:
    key: str
    names: tuple[str, ...]  # casefold, auch deutsch und Abkürzungen
    title: str  # empfohlener UniProt-Name bzw. Laborname
    organism: str  # wissenschaftlich (für den Vergleich mit Eingabewörtern)
    organism_label: str  # Anzeige, z. B. "Gallus gallus (hen egg white)"
    uniprot: tuple[str, ...]
    pdb: str
    chains: tuple[str, ...]
    chain_labels: tuple[tuple[str, str], ...] = ()
    mature_length: int = 0  # reife Kette(n) laut UniProt-Merkmal
    mass_da: int = 0
    default: bool = True  # Standard, wenn die Eingabe keinen Organismus nennt
    structure_note: str = ""
    alternatives: str = ""
    other_reading: str = ""


# Belege je Zeile (gemessen 10.11.2026): RCSB-Titel bzw. Entität | UniProt-Merkmal.
CURATED: tuple[Curated, ...] = (
    # 1LYZ "Real-space refinement of the structure of hen egg-white lysozyme",
    # Kette A, Gallus gallus, P00698 | Chain 19–147
    Curated("lysozyme", ("lysozyme", "lysozym", "lysozyme c", "muramidase", "hewl"),
            "Lysozyme C", "Gallus gallus", "Gallus gallus (hen egg white)",
            ("P00698",), "1LYZ", ("A",), mature_length=129, mass_da=14313,
            alternatives="human lysozyme (UniProt P61626) — ask for 'human lysozyme'"),
    # 2PTN Trypsin, Bos taurus, Kette A, P00760 | Chain 24–246 (Serine protease 1)
    Curated("trypsin", ("trypsin", "cationic trypsin", "beta-trypsin", "β-trypsin"),
            "Trypsin (cationic, serine protease 1)", "Bos taurus", "Bos taurus (bovine pancreas)",
            ("P00760",), "2PTN", ("A",), mature_length=223, mass_da=23305,
            alternatives="porcine trypsin; human trypsin-1 (UniProt P07477) — ask for 'human trypsin'"),
    # 4CHA "Structure of alpha-chymotrypsin refined at 1.68 Å", Ketten A/B/C
    # (13 + 131 + 97 aa) und E/F/G (zweite Kopie), P00766 | Chains 1–13, 16–146, 149–245
    Curated("chymotrypsin", ("chymotrypsin", "alpha-chymotrypsin", "α-chymotrypsin",
                             "chymotrypsin a", "chymotrypsinogen a"),
            "α-Chymotrypsin A", "Bos taurus", "Bos taurus (bovine pancreas)",
            ("P00766",), "4CHA", ("A", "B", "C"),
            (("A", "chain A"), ("B", "chain B"), ("C", "chain C")),
            mature_length=241, mass_da=25244,
            structure_note="one of two copies in the crystal"),
    # 7RSA "Structure of phosphate-free ribonuclease A", Kette A, P61823 | Chain 27–150
    Curated("rnase a", ("rnase a", "ribonuclease a", "rnase", "ribonuclease",
                        "ribonuklease a", "ribonuklease", "pancreatic ribonuclease",
                        "ribonuclease pancreatic", "bovine pancreatic ribonuclease"),
            "Ribonuclease A (pancreatic ribonuclease)", "Bos taurus", "Bos taurus (bovine pancreas)",
            ("P61823",), "7RSA", ("A",), mature_length=124, mass_da=13690),
    # 4F5S "Crystal Structure of Bovine Serum Albumin", Ketten A/B, P02769 | Chain 25–607
    Curated("bsa", ("bsa", "bovine serum albumin", "rinderserumalbumin", "serum albumin bovine"),
            "Serum albumin (BSA)", "Bos taurus", "Bos taurus (bovine serum)",
            ("P02769",), "4F5S", ("A",), mature_length=583, mass_da=66433,
            structure_note="one of two copies in the crystal",
            alternatives="human serum albumin (UniProt P02768) — ask for 'human serum albumin'",
            other_reading=(
                "In organic chemistry BSA also means N,O-bis(trimethylsilyl)acetamide, a "
                "silylation reagent — pass that name to draw it"
            )),
    # 8CAT "The NADPH binding site on beef liver catalase", Ketten A/B, P00432 | Chain 2–527
    Curated("catalase", ("catalase", "katalase", "beef liver catalase"),
            "Catalase", "Bos taurus", "Bos taurus (beef liver)",
            ("P00432",), "8CAT", ("A",), mature_length=526, mass_da=59784,
            structure_note="one subunit of the tetramer",
            alternatives="human catalase (UniProt P04040); Aspergillus niger catalase"),
    # 1ATJ "Recombinant horseradish peroxidase C1A", Ketten A–F, P00433 | Chain 31–338
    Curated("hrp", ("horseradish peroxidase", "hrp", "meerrettichperoxidase",
                    "meerrettich-peroxidase", "peroxidase c1a"),
            "Peroxidase C1A (horseradish peroxidase)", "Armoracia rusticana",
            "Armoracia rusticana (horseradish)", ("P00433",), "1ATJ", ("A",),
            mature_length=308, mass_da=33918,
            structure_note="recombinant, not glycosylated; one of six copies in the crystal"),
    # 1GFL "Structure of green fluorescent protein", Ketten A/B, P42212, Mutation
    # Q80R (die verbreitete Klon-Variante) | Chain 1–238
    Curated("gfp", ("gfp", "green fluorescent protein", "avgfp", "wild-type gfp",
                    "grün fluoreszierendes protein", "gruen fluoreszierendes protein"),
            "Green fluorescent protein", "Aequorea victoria", "Aequorea victoria (jellyfish)",
            ("P42212",), "1GFL", ("A",), mature_length=238, mass_da=26886,
            structure_note="Q80R, the common cloned variant; one of two copies in the crystal",
            alternatives="EGFP and other variants differ by point mutations (e.g. PDB 1EMA = S65T)"),
    # 2PRK Proteinase K, Engyodontium album, Kette A, P06873 | Chain 106–384
    Curated("proteinase k", ("proteinase k", "protease k", "endopeptidase k"),
            "Proteinase K", "Parengyodontium album", "Parengyodontium album (fungus)",
            ("P06873",), "2PRK", ("A",), mature_length=279, mass_da=28907),
    # 1STP "Structural origins of high-affinity biotin binding to streptavidin",
    # Kette A, P22629 | Chain 25–183
    Curated("streptavidin", ("streptavidin",),
            "Streptavidin", "Streptomyces avidinii", "Streptomyces avidinii (bacterium)",
            ("P22629",), "1STP", ("A",), mature_length=159, mass_da=16491,
            structure_note="one subunit of the tetramer, with biotin bound"),
    # 1TAU "Taq polymerase/DNA/β-octylglucoside complex", Kette A (832 aa, ohne
    # Mutation — 1TAQ trägt S575C–S577C), DNA-Ketten P/T weggelassen, P19821
    Curated("taq", ("taq polymerase", "taq dna polymerase", "taq-polymerase", "taq"),
            "Taq DNA polymerase (DNA polymerase I, thermostable)", "Thermus aquaticus",
            "Thermus aquaticus (bacterium)", ("P19821",), "1TAU", ("A",), mature_length=832, mass_da=93910,
            structure_note="the bound DNA is not shown"),
    # 3I40 "Human insulin", Ketten A (21) und B (30), P01308 | Peptide B 25–54, A 90–110
    Curated("insulin", ("insulin", "humaninsulin", "insulin human"),
            "Insulin", "Homo sapiens", "Homo sapiens (human)",
            ("P01308",), "3I40", ("A", "B"), (("A", "A chain"), ("B", "B chain")),
            mature_length=51, mass_da=5814,
            alternatives="porcine insulin (PDB 4INS, UniProt P01315) — ask for 'porcine insulin'"),
    # 4INS "The structure of 2Zn pig insulin crystals", Ketten A/B (+ C/D), P01315
    Curated("insulin", ("insulin", "schweineinsulin"),
            "Insulin", "Sus scrofa", "Sus scrofa (pig)",
            ("P01315",), "4INS", ("A", "B"), (("A", "A chain"), ("B", "B chain")),
            mature_length=51, mass_da=5784, default=False,
            structure_note="one of two insulin molecules in the crystal"),
    # 2HHB "Human deoxyhaemoglobin at 1.74 Å", α: A/C (P69905), β: B/D (P68871)
    Curated("hemoglobin", ("hemoglobin", "haemoglobin", "hämoglobin", "haemoglobin a",
                           "hemoglobin a", "hba", "deoxyhemoglobin", "adult hemoglobin"),
            "Hemoglobin A (α₂β₂ tetramer)", "Homo sapiens", "Homo sapiens (human)",
            ("P69905", "P68871"), "2HHB", ("A", "B", "C", "D"),
            (("A", "α1"), ("B", "β1"), ("C", "α2"), ("D", "β2")),
            mature_length=574, mass_da=61986,
            structure_note="deoxy form, with its four hemes"),
    # 1WLA "Myoglobin (horse heart) recombinant wild-type", Kette A, P68082 | Chain 2–154
    Curated("myoglobin", ("myoglobin", "myoglobin horse heart"),
            "Myoglobin", "Equus caballus", "Equus caballus (horse heart)",
            ("P68082",), "1WLA", ("A",), mature_length=153, mass_da=16951,
            alternatives="sperm whale myoglobin (PDB 1A6M, UniProt P02185) — ask for 'sperm whale myoglobin'"),
    # 1A6M "Oxy-myoglobin, atomic resolution", Physeter catodon, Kette A, P02185
    Curated("myoglobin", ("myoglobin",),
            "Myoglobin", "Physeter macrocephalus", "Physeter macrocephalus (sperm whale)",
            ("P02185",), "1A6M", ("A",), mature_length=153, mass_da=17200, default=False),
    # 3KS3 "High resolution structure of human carbonic anhydrase II at 0.9 Å",
    # Kette A, P00918 | Chain 2–260
    Curated("carbonic anhydrase ii", ("carbonic anhydrase ii", "carbonic anhydrase 2",
                                      "carbonic anhydrase", "carboanhydrase ii",
                                      "carboanhydrase", "ca ii", "hcaii"),
            "Carbonic anhydrase II", "Homo sapiens", "Homo sapiens (human)",
            ("P00918",), "3KS3", ("A",), mature_length=259, mass_da=29115,
            alternatives="bovine erythrocyte carbonic anhydrase II (UniProt P00921)"),
    # 4W6Z "Yeast alcohol dehydrogenase I", Ketten A–D, P00330 | Chain 2–348
    Curated("adh", ("alcohol dehydrogenase", "alkoholdehydrogenase", "adh", "yeast adh",
                    "alcohol dehydrogenase 1", "adh1"),
            "Alcohol dehydrogenase 1", "Saccharomyces cerevisiae", "Saccharomyces cerevisiae (yeast)",
            ("P00330",), "4W6Z", ("A",), mature_length=347, mass_da=36718,
            structure_note="one subunit of the tetramer",
            alternatives="horse liver ADH (PDB 8ADH, UniProt P00327) — ask for 'horse liver alcohol dehydrogenase'"),
    # 8ADH "Interdomain motion in liver alcohol dehydrogenase", Equus caballus,
    # Kette A, P00327 | Chain 2–375
    Curated("adh", ("alcohol dehydrogenase", "alkoholdehydrogenase", "adh",
                    "liver alcohol dehydrogenase", "lador"),
            "Alcohol dehydrogenase E chain", "Equus caballus", "Equus caballus (horse liver)",
            ("P00327",), "8ADH", ("A",), mature_length=374, mass_da=39804, default=False,
            structure_note="apo form, one subunit of the dimer"),
    # 1LCI "Firefly luciferase", Photinus pyralis, Kette A, P08659 | Chain 1–550
    Curated("luciferase", ("luciferase", "firefly luciferase", "luziferase",
                           "glühwürmchen-luciferase", "luciferin 4-monooxygenase"),
            "Firefly luciferase (luciferin 4-monooxygenase)", "Photinus pyralis",
            "Photinus pyralis (firefly)", ("P08659",), "1LCI", ("A",),
            mature_length=550, mass_da=60745,
            alternatives="Renilla luciferase and bacterial luciferases are unrelated proteins"),
    # 4PEP "Monoclinic porcine pepsin refined at 1.8 Å", Kette A, P00791 | Chain 60–385
    Curated("pepsin", ("pepsin", "pepsin a"),
            "Pepsin A", "Sus scrofa", "Sus scrofa (porcine stomach)",
            ("P00791",), "4PEP", ("A",), mature_length=326, mass_da=34510,
            alternatives="human pepsin A (UniProt P0DJD7)"),
    # 9PAP "Structure of papain refined at 1.65 Å", Kette A, P00784 | Chain 134–345
    Curated("papain", ("papain",),
            "Papain", "Carica papaya", "Carica papaya (papaya latex)",
            ("P00784",), "9PAP", ("A",), mature_length=212, mass_da=23428),
    # 1PPB "Human α-thrombin … with D-Phe-Pro-Arg chloromethylketone",
    # Ketten H (259) und L (36 aufgelöst), P00734 | Chains 315–363 + 364–622
    Curated("thrombin", ("thrombin", "alpha-thrombin", "α-thrombin", "factor iia", "faktor iia"),
            "α-Thrombin", "Homo sapiens", "Homo sapiens (human)",
            ("P00734",), "1PPB", ("H", "L"), (("H", "heavy chain"), ("L", "light chain")),
            mature_length=308, mass_da=35372,
            structure_note="with the inhibitor PPACK bound",
            alternatives="bovine thrombin (UniProt P00735)"),
    # 1UZE: menschliches Hoden-ACE mit gebundenem Inhibitor, Kette A (589 aa), P12821
    # | somatisches ACE: Chain 30–1306 (1277 aa)
    Curated("ace", ("angiotensin-converting enzyme", "angiotensin converting enzyme",
                    "angiotensin i-converting enzyme", "angiotensin i converting enzyme",
                    "angiotensin-konvertierendes enzym", "ace", "kininase ii"),
            "Angiotensin-converting enzyme", "Homo sapiens", "Homo sapiens (human)",
            ("P12821",), "1UZE", ("A",), mature_length=1277, mass_da=146829,
            structure_note=(
                "testis ACE (the C-domain isoform, 589 residues) with a bound ACE "
                "inhibitor — somatic ACE has two such domains"
            ),
            alternatives="the same testis ACE with lisinopril: PDB 1O86"),
)


@dataclass(frozen=True)
class Antibody:
    inn: str
    pdb: str
    chains: tuple[str, ...]
    chain_labels: tuple[tuple[str, str], ...]
    what: str  # "Fab fragment" | "intact IgG4"
    antigen: str
    note: str = ""


# Belege (RCSB-Titel, 10.11.2026); Ketten per Entitätsbeschreibung, bei
# mehreren Kopien gepaart über Cα-Kontakte (4NYL: H–L 39, die anderen Paare kleiner).
ANTIBODIES: tuple[Antibody, ...] = (
    # 1N8Z "Extracellular domain of human HER2 complexed with Herceptin Fab";
    # A = light, B = heavy, C = HER2 (weggelassen)
    Antibody("trastuzumab", "1N8Z", ("A", "B"), (("A", "light chain"), ("B", "heavy chain")),
             "Fab fragment", "HER2", "from the complex with HER2; the antigen is not shown"),
    # 4KAQ "Structure of rituximab Fab"; H, L
    Antibody("rituximab", "4KAQ", ("L", "H"), (("L", "light chain"), ("H", "heavy chain")),
             "Fab fragment", "CD20"),
    # 4NYL "Crystal structure of adalimumab FAB fragment"; Paar H/L von vier Kopien
    Antibody("adalimumab", "4NYL", ("L", "H"), (("L", "light chain"), ("H", "heavy chain")),
             "Fab fragment", "TNF-α", "one of four copies in the crystal"),
    # 1YY9 "EGFR extracellular domain in complex with the Fab fragment of
    # cetuximab"; C = light, D = heavy, A = EGFR (weggelassen)
    Antibody("cetuximab", "1YY9", ("C", "D"), (("C", "light chain"), ("D", "heavy chain")),
             "Fab fragment", "EGFR", "from the complex with EGFR; the antigen is not shown"),
    # 5DK3 "Crystal Structure of Pembrolizumab, a full length IgG4 antibody";
    # light A/F, heavy B/G
    Antibody("pembrolizumab", "5DK3", ("A", "B", "F", "G"),
             (("A", "light chain 1"), ("B", "heavy chain 1"), ("F", "light chain 2"),
              ("G", "heavy chain 2")),
             "intact IgG4", "PD-1"),
    # 5WT9 "Complex structure of PD-1 and nivolumab-Fab"; H, L, G = PD-1 (weggelassen)
    Antibody("nivolumab", "5WT9", ("L", "H"), (("L", "light chain"), ("H", "heavy chain")),
             "Fab fragment", "PD-1", "from the complex with PD-1; the antigen is not shown"),
    # 4G3Y "TNF-alpha in complex with Infliximab Fab fragment"; H, L, C = TNF (weggelassen)
    Antibody("infliximab", "4G3Y", ("L", "H"), (("L", "light chain"), ("H", "heavy chain")),
             "Fab fragment", "TNF-α", "from the complex with TNF-α; the antigen is not shown"),
    # 2XA8 "Crystal structure of the Fab domain of omalizumab at 2.41 Å"; L, H
    Antibody("omalizumab", "2XA8", ("L", "H"), (("L", "light chain"), ("H", "heavy chain")),
             "Fab fragment", "IgE"),
    # 3GIZ "Crystal structure of the Fab fragment of anti-CD20 antibody Ofatumumab"; L, H
    Antibody("ofatumumab", "3GIZ", ("L", "H"), (("L", "light chain"), ("H", "heavy chain")),
             "Fab fragment", "CD20"),
)
# Bewusst nicht in der Tabelle: bevacizumab (1BJ1 nennt den Antikörper nicht,
# 6BFT ist eine Mutante), adalimumab 6CR1 (künstliches EFab).

# 1HZH "Crystal structure of the intact human IgG b12 …": H/K schwer, L/M leicht
INTACT_IGG = Antibody(
    "IgG1 b12", "1HZH", ("H", "L", "K", "M"),
    (("H", "heavy chain 1"), ("L", "light chain 1"), ("K", "heavy chain 2"),
     ("M", "light chain 2")),
    "intact IgG1", "HIV-1 gp120",
)

_GENERIC_ANTIBODY = re.compile(
    r"(?:monoclonal\s+)?(?:antibod(?:y|ies)|antikörper|antikoerper|immunoglobulin(?:\s+g)?|"
    r"immunglobulin(?:\s+g)?|igg[1-4]?|mabs?)",
    re.IGNORECASE,
)
_ANTI_X = re.compile(r"anti-[\w-]+(?:\s+(?:antibody|antikörper|igg))?", re.IGNORECASE)
_INN_MAB = re.compile(r"[a-z]{3,}mab", re.IGNORECASE)

# Bakterielles Gen-/Proteinkürzel: drei Buchstaben, dann ein Großbuchstabe und
# höchstens ein weiteres Zeichen ("RecA", "LipA", "GroEL", "recA"). Kurznamen
# kleiner Moleküle stehen in Großbuchstaben (ATP, NADH, DMSO, EDTA, THF, PABA)
# oder haben die Großbuchstaben an anderer Stelle (NaCl, EtOH, AcOH, cAMP).
GENE_SYMBOL = re.compile(r"[a-zA-Z][a-z]{2}[A-Z][A-Z0-9]?")
_ORGANISM_LEAD = re.compile(r"^(?:from|aus|in|of|von|des)\s+", re.IGNORECASE)


# --- Auswahl ------------------------------------------------------------------


@dataclass
class StructureRef:
    source: str  # "pdb" | "alphafold" | "best" (PDBe sucht die beste Kette)
    pdb: str = ""
    chains: tuple[str, ...] = ()
    chain_labels: dict[str, str] = field(default_factory=dict)
    note: str = ""


@dataclass
class ProteinChoice:
    kind: str  # "curated" | "antibody" | "antibody_generic" | "gene" | "uniprot"
    query: str
    title: str
    organism: str = ""  # Anzeige
    accession: tuple[str, ...] = ()
    reviewed: bool = True
    gene: str = ""
    length: int | None = None
    mass_da: int | None = None
    precursor: bool = False
    structure: StructureRef | None = None
    alternatives: str = ""
    other_reading: str = ""
    family: bool = False
    others: list[dict] = field(default_factory=list)
    scheme: bool = False  # IgG-Schema dazu
    antibody_what: str = ""
    # Genkürzel mit Organismus, aber ohne Eintrag unter dem Gennamen: der Treffer
    # kam über den Proteinnamen, den die übrigen Einträge des Gens tragen.
    by_name_for: str = ""

    @property
    def headline(self) -> str:
        """Titel für Bild, Panel und Meldung — Organismus und Quelle immer dabei."""
        name = self.title
        if self.gene and self.gene.casefold() not in name.casefold():
            name += f" ({self.gene[:1].upper() + self.gene[1:]})"
        parts = [name]
        if self.organism:
            parts.append(self.organism)
        head = ", ".join(parts)
        return f"{head} — {self.source_label}" if self.source_label else head

    @property
    def figure_title(self) -> str:
        """Bildtitel ohne Quelle (die steht in der Unterzeile) — sonst bricht er um."""
        name = self.title
        if self.gene and self.gene.casefold() not in name.casefold():
            name += f" ({self.gene[:1].upper() + self.gene[1:]})"
        return f"{name}, {self.organism}" if self.organism else name

    @property
    def source_label(self) -> str:
        s = self.structure
        if s is None:
            return ""
        if s.source == "alphafold":
            return "AlphaFold model, predicted"
        if s.pdb:
            chains = "/".join(s.chains)
            return f"PDB {s.pdb}, chain{'s' if len(s.chains) > 1 else ''} {chains}"
        return ""


def _norm(text: str) -> str:
    text = text.replace("‐", "-").replace("‑", "-")
    return " ".join(text.replace('"', " ").split()).strip(" .").casefold()


_ANY_ORGANISM = re.compile("|".join(re.escape(w) for w, _ in _ORGANISM_WORDS))


def _split_organism(text: str) -> tuple[str, str]:
    """(Rest, wissenschaftlicher Name) — Organismuswörter vorn, hinten oder als Vorsilbe."""
    t = _norm(text)
    if not _ANY_ORGANISM.search(t):
        return t, ""  # schneller Weg: der Resolver fragt das für jeden Namen
    for word, sci in _ORGANISM_WORDS:
        for pattern in (rf"^{re.escape(word)}[\s-]+(.+)$", rf"^(.+?)[\s,]+(?:from\s+|aus\s+)?{re.escape(word)}$"):
            if m := re.match(pattern, t):
                return _strip_tissue(m.group(1)), sci
        # deutsche Komposita: "Rindertrypsin", "Schweineinsulin", "Hühnereiweißlysozym"
        if word in _GERMAN_PREFIXES and t.startswith(word) and len(t) > len(word) + 3:
            return _strip_tissue(t[len(word):].lstrip("-")), sci
    return t, ""


def _strip_tissue(text: str) -> str:
    words = [w for w in text.split() if w not in _TISSUE]
    return " ".join(words) or text


def _curated_rows(base: str) -> list[Curated]:
    return [c for c in CURATED if base in c.names]


def _from_curated(row: Curated, query: str) -> ProteinChoice:
    return ProteinChoice(
        kind="curated",
        query=query,
        title=row.title,
        organism=row.organism_label,
        accession=row.uniprot,
        length=row.mature_length or None,
        mass_da=row.mass_da or None,
        structure=StructureRef("pdb", row.pdb, row.chains, dict(row.chain_labels), row.structure_note),
        alternatives=row.alternatives,
        other_reading=row.other_reading,
    )


def antibody_choice(name: str) -> ProteinChoice | None:
    """Antikörper aus der Tabelle, sonst der allgemeine Bauplan — oder None."""
    t = _norm(name)
    for ab in ANTIBODIES:
        if t == ab.inn:
            note = ab.note
            return ProteinChoice(
                kind="antibody",
                query=name,
                title=f"{ab.inn.capitalize()} {ab.what}",
                organism=f"therapeutic antibody against {ab.antigen}",
                structure=StructureRef("pdb", ab.pdb, ab.chains, dict(ab.chain_labels), note),
                scheme=True,
                antibody_what=ab.what,
            )
    if _INN_MAB.fullmatch(t) or _GENERIC_ANTIBODY.fullmatch(t) or _ANTI_X.fullmatch(t):
        shown = name.strip()
        # Bei "IgG"/"antibody" ist der Bauplan die Antwort; bei einem bestimmten
        # Antikörper ohne Tabelleneintrag steht ausdrücklich, dass er es nicht ist.
        title = (
            "Architecture of an intact IgG antibody"
            if _GENERIC_ANTIBODY.fullmatch(t)
            else f"Architecture of an intact IgG, not {shown}"
        )
        return ProteinChoice(
            kind="antibody_generic",
            query=name,
            title=title,
            organism="human IgG1 b12 as the example",
            structure=StructureRef(
                "pdb", INTACT_IGG.pdb, INTACT_IGG.chains, dict(INTACT_IGG.chain_labels),
                "general architecture shared by IgG antibodies",
            ),
            scheme=True,
            antibody_what="intact IgG1",
        )
    return None


def curated_choice(name: str) -> ProteinChoice | None:
    """Laborstandard oder Antikörper ohne Netz — None, wenn keiner passt.

    Nennt die Eingabe einen Organismus, für den die Tabelle keine Zeile hat
    („human lysozyme"), ist das hier None: dann entscheidet UniProt mit
    Organismusfilter (organism_hint).
    """
    if ab := antibody_choice(name):
        return ab
    t = _norm(name)
    rows = _curated_rows(t)
    if rows:
        default = next((r for r in rows if r.default), rows[0])
        return _from_curated(default, name)
    base, organism = _split_organism(name)
    rows = _curated_rows(base)
    if rows and organism:
        match = next((r for r in rows if r.organism == organism), None)
        return _from_curated(match, name) if match else None
    return None


def organism_hint(name: str) -> tuple[str, str]:
    """(Proteinname, Organismus) für die UniProt-Suche — Organismus "" ohne Angabe."""
    base, organism = _split_organism(name)
    return (base, organism) if organism else (name.strip(), "")


def is_gene_symbol(name: str) -> bool:
    """Genkürzel-Form, auch mit Organismus dahinter ("RecA Bacillus subtilis")."""
    head = name.strip().split(maxsplit=1)
    return bool(head) and bool(GENE_SYMBOL.fullmatch(head[0]))


def split_gene_symbol(name: str) -> tuple[str, str]:
    """("RecA", "Bacillus subtilis") — alles nach dem Kürzel ist der Organismus.

    Kurzformen wie "B. subtilis" fragen UniProt nach dem Artnamen allein; der
    gleicht in Kombination mit dem Gen nur bakterielle Treffer.
    """
    parts = name.strip().split(maxsplit=1)
    symbol = parts[0]
    organism = _ORGANISM_LEAD.sub("", parts[1].strip()) if len(parts) > 1 else ""
    organism = organism.strip(" ()")
    if m := re.fullmatch(r"[A-Z]\.\s*([a-z]+)(?:\s.*)?", organism):
        organism = m.group(1)
    return symbol, organism


def from_gene_record(record: dict, query: str) -> ProteinChoice:
    domain = f" ({record['domain']})" if record.get("domain") else ""
    organism = record.get("organism", "").split(" (strain")[0]
    review = "" if record.get("reviewed", True) else " — UniProt unreviewed (TrEMBL)"
    by_name = record.get("found_by") == "name"
    return ProteinChoice(
        kind="gene",
        query=query,
        title=record.get("name") or record.get("gene", ""),
        organism=f"{organism}{domain}{review}",
        accession=(record["accession"],),
        reviewed=record.get("reviewed", True),
        gene="" if by_name else record.get("gene", ""),
        length=record.get("length"),
        mass_da=record.get("mass"),
        structure=StructureRef("best"),
        others=[{"name": o, "accession": ""} for o in record.get("others", [])],
        by_name_for=record.get("gene", "") if by_name else "",
    )


def from_uniprot_record(record: dict, query: str) -> ProteinChoice:
    return ProteinChoice(
        kind="uniprot",
        query=query,
        title=record.get("name") or record.get("matched", query),
        organism=record.get("organism", ""),
        accession=(record["accession"],),
        length=record.get("length"),
        mass_da=record.get("mass"),
        precursor=bool(record.get("precursor")),
        structure=StructureRef("best"),
        family=bool(record.get("family")),
        others=list(record.get("others", [])),
    )
