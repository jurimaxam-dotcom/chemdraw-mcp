"""pH-Rechnungen: exakte Ladungsbilanz, Lehrbuchnäherung daneben.

Gerechnet wird über `ph_plots.exact_ph` — dieselbe Bilanz, die auch die
Titrationskurve zeichnet. Das ist Absicht: Bild und Zahl im selben Protokoll
dürfen sich nicht widersprechen.

Die Näherung wird trotzdem mitgeliefert, denn sie ist die Formel, die in der
Klausur verlangt wird. Interessant ist die Differenz: Wo beide auseinander
laufen, hat die Näherung ihre Voraussetzung verloren (kaum dissoziiert,
Autoprotolyse vernachlässigbar) — und genau das ist der Lerninhalt.

Einheiten: Konzentration in mol/L, pKs/pKb dimensionslos, T = 25 °C (pKw 14).
"""

from __future__ import annotations

import math

from chemdraw_tool.ph_plots import exact_ph

PKW = 14.0

# Ab dieser Abweichung zwischen exaktem Wert und Näherung ist die Näherung
# nicht mehr brauchbar. 0,1 pH-Einheiten sind etwa die Ablesegenauigkeit
# eines pH-Meters — darunter wäre die Warnung Pedanterie.
APPROXIMATION_TOLERANCE = 0.1

# Ausserhalb pKs ± 1 ist das Verhältnis steiler als 1:10 und die Kapazität
# bricht weg; ausserhalb ± 2 ist es kein Puffer mehr, sondern eine Lösung mit
# etwas Fremdstoff darin.
BUFFER_GOOD_RANGE = 1.0
BUFFER_MAX_RANGE = 2.0


def _require_positive(value: float, name: str) -> float:
    if value is None or value <= 0:
        raise ValueError(f"{name} must be greater than zero — got {value!r}.")
    return value


def weak_acid_ph(
    concentration: float,
    pka: float | None = None,
    pka_values: list[float] | None = None,
) -> dict:
    """pH einer schwachen (auch mehrprotonigen) Säure."""
    _require_positive(concentration, "concentration")
    pkas = list(pka_values) if pka_values else ([pka] if pka is not None else [])
    if not pkas:
        raise ValueError(
            "A weak acid needs a pka (or pka_values for a polyprotic acid). "
            "Without it the calculation is not defined."
        )

    ph = exact_ph(pkas, c_acid=concentration, c_na=0.0)

    # Näherung nur für die erste Stufe: pH = ½ (pKs − log c)
    ph_approx = 0.5 * (pkas[0] - math.log10(concentration))
    valid = abs(ph - ph_approx) <= APPROXIMATION_TOLERANCE

    notes = []
    if not valid:
        notes.append(
            f"The textbook approximation gives pH {ph_approx:.2f}, the exact "
            f"charge balance pH {ph:.2f}. The approximation assumes the acid is "
            "barely dissociated and water contributes nothing — at this "
            "concentration and pKa that no longer holds. Use the exact value."
        )
    if len(pkas) > 1:
        notes.append(
            "For a polyprotic acid only the first protolysis step matters here; "
            "the exact value accounts for all of them anyway."
        )

    return {
        "ph": ph,
        "ph_approx": ph_approx,
        "approximation_valid": valid,
        "approx_formula": "pH = ½ · (pKa − log c)",
        "approx_substitution": (
            f"pH = ½ · ({pkas[0]:g} − log {concentration:g})"
        ),
        "pka_values": pkas,
        "concentration": concentration,
        "poh": PKW - ph,
        "notes": notes,
    }


def weak_base_ph(
    concentration: float,
    pkb: float | None = None,
    pka: float | None = None,
) -> dict:
    """pH einer schwachen Base — über den pKs der korrespondierenden Säure.

    Eine Base B in Wasser ist dasselbe System wie die vollständig
    deprotonierte Form ihrer korrespondierenden Säure BH+. Deshalb reicht
    dieselbe Ladungsbilanz, wenn man sie als „ganz neutralisiert" ansetzt.
    """
    _require_positive(concentration, "concentration")
    if pkb is None and pka is None:
        raise ValueError(
            "A weak base needs either pkb (of the base) or pka (of its "
            "conjugate acid). pKa + pKb = 14."
        )
    pka_conj = pka if pka is not None else PKW - pkb
    pkb_value = pkb if pkb is not None else PKW - pka

    ph = exact_ph([pka_conj], c_acid=concentration, c_na=concentration)

    poh_approx = 0.5 * (pkb_value - math.log10(concentration))
    ph_approx = PKW - poh_approx
    valid = abs(ph - ph_approx) <= APPROXIMATION_TOLERANCE

    notes = []
    if not valid:
        notes.append(
            f"The approximation gives pH {ph_approx:.2f}, the exact balance "
            f"pH {ph:.2f} — the assumption of little protonation fails here."
        )

    return {
        "ph": ph,
        "ph_approx": ph_approx,
        "approximation_valid": valid,
        "approx_formula": "pOH = ½ · (pKb − log c), pH = 14 − pOH",
        "approx_substitution": (
            f"pOH = ½ · ({pkb_value:g} − log {concentration:g}) = {poh_approx:.2f}"
        ),
        "pka_conjugate": pka_conj,
        "pkb": pkb_value,
        "concentration": concentration,
        "poh": PKW - ph,
        "notes": notes,
    }


def buffer_ph(
    acid_concentration: float,
    base_concentration: float,
    pka: float,
) -> dict:
    """pH eines Puffers aus Säure und korrespondierender Base."""
    _require_positive(acid_concentration, "acid_concentration")
    _require_positive(base_concentration, "base_concentration")
    if pka is None:
        raise ValueError("A buffer needs the pka of the acid/base pair.")

    total = acid_concentration + base_concentration
    ph = exact_ph([pka], c_acid=total, c_na=base_concentration)
    ratio = base_concentration / acid_concentration
    ph_hh = pka + math.log10(ratio)

    # Pufferkapazität nach van Slyke: β = 2,303 · C · α · (1 − α)
    alpha = base_concentration / total
    capacity = 2.303 * total * alpha * (1.0 - alpha)

    notes = []
    if abs(ph_hh - pka) > BUFFER_GOOD_RANGE:
        notes.append(
            f"The ratio base : acid is {ratio:.3g} : 1, which puts the pH "
            f"{abs(ph_hh - pka):.2f} units away from the pKa. Beyond one unit "
            "(ratio 10 : 1) the buffer range is left and the capacity drops "
            "sharply — pick a pair whose pKa is closer to the target pH."
        )
    if total < 0.01:
        notes.append(
            f"Total buffer concentration is only {total:.4g} mol/L. The pH is "
            "right, but such a dilute buffer is easily overwhelmed."
        )

    return {
        "ph": ph,
        "ph_henderson_hasselbalch": ph_hh,
        "formula": "pH = pKa + log([A⁻] / [HA])",
        "substitution": (
            f"pH = {pka:g} + log({base_concentration:g} / {acid_concentration:g})"
        ),
        "ratio": ratio,
        "capacity": capacity,
        "total_concentration": total,
        "pka": pka,
        "notes": notes,
    }


def buffer_recipe(
    target_ph: float,
    pka: float,
    total_concentration: float,
    volume_ml: float,
    acid_molar_mass: float | None = None,
    base_molar_mass: float | None = None,
) -> dict:
    """Wie setze ich einen Puffer an? Verhältnis, Stoffmengen, Einwaagen."""
    _require_positive(total_concentration, "total_concentration")
    _require_positive(volume_ml, "volume_ml")
    if pka is None:
        raise ValueError("A buffer recipe needs the pka of the pair.")

    # Aus pH = pKa + log(base/acid) folgt base/acid = 10^(pH − pKa).
    ratio = 10.0 ** (target_ph - pka)
    base_fraction = ratio / (1.0 + ratio)
    base_concentration = total_concentration * base_fraction
    acid_concentration = total_concentration - base_concentration

    volume_l = volume_ml / 1000.0
    acid_mol = acid_concentration * volume_l
    base_mol = base_concentration * volume_l

    notes = []
    distance = abs(target_ph - pka)
    if distance > BUFFER_MAX_RANGE:
        notes.append(
            f"pH {target_ph:g} is {distance:.2f} units away from the pKa "
            f"{pka:g}. That is no longer a buffer — the ratio would be "
            f"{ratio:.4g} : 1. Choose a pair whose pKa is within one unit of "
            "the target pH."
        )
    elif distance > BUFFER_GOOD_RANGE:
        notes.append(
            f"pH {target_ph:g} is {distance:.2f} units from the pKa. It works, "
            "but the capacity is already poor on one side."
        )

    result = {
        "target_ph": target_ph,
        "pka": pka,
        "ratio": ratio,
        "acid_concentration": acid_concentration,
        "base_concentration": base_concentration,
        "acid_mol": acid_mol,
        "base_mol": base_mol,
        "volume_ml": volume_ml,
        "total_concentration": total_concentration,
        "notes": notes,
    }

    if acid_molar_mass:
        result["acid_mass_g"] = acid_mol * acid_molar_mass
    if base_molar_mass:
        result["base_mass_g"] = base_mol * base_molar_mass

    return result


def _with_water_autoprotolysis(concentration: float, acidic: bool) -> float:
    """[H+] aus der exakten quadratischen Bilanz inklusive Wasser.

    Für c ≫ 1e-6 identisch mit −log c; darunter rettet sie vor der klassischen
    Fangfrage, bei der 1e-8 M HCl scheinbar basisch wird.
    """
    kw = 10.0**-PKW
    # [H+]² − c·[H+] − Kw = 0 für die Säure (c = zugegebene Protonen),
    # bei der Base entsprechend für [OH−].
    added = concentration if acidic else -concentration
    h = (added + math.sqrt(added * added + 4.0 * kw)) / 2.0
    return h


def strong_acid_ph(concentration: float) -> dict:
    """pH einer starken Säure — vollständig dissoziiert."""
    _require_positive(concentration, "concentration")
    h = _with_water_autoprotolysis(concentration, acidic=True)
    ph = -math.log10(h)
    ph_naive = -math.log10(concentration)

    notes = []
    if abs(ph - ph_naive) > 0.01:
        notes.append(
            f"Simply taking −log c would give pH {ph_naive:.2f}. At this "
            "dilution water itself delivers more protons than the acid, so the "
            "autoprotolysis has to be included — an acid can never make a "
            "solution alkaline."
        )

    return {
        "ph": ph,
        "ph_naive": ph_naive,
        "formula": "pH = −log [H⁺], with [H⁺] from [H⁺]² − c·[H⁺] − Kw = 0",
        "substitution": f"c = {concentration:g} mol/L",
        "concentration": concentration,
        "poh": PKW - ph,
        "notes": notes,
    }


def strong_base_ph(concentration: float) -> dict:
    """pH einer starken Base — über pOH und das Ionenprodukt."""
    _require_positive(concentration, "concentration")
    h = _with_water_autoprotolysis(concentration, acidic=False)
    ph = -math.log10(h)
    ph_naive = PKW + math.log10(concentration)

    notes = []
    if abs(ph - ph_naive) > 0.01:
        notes.append(
            f"Simply taking 14 + log c would give pH {ph_naive:.2f}. At this "
            "dilution the autoprotolysis of water dominates — a base can never "
            "make a solution acidic."
        )

    return {
        "ph": ph,
        "ph_naive": ph_naive,
        "formula": "pOH = −log [OH⁻], pH = 14 − pOH",
        "substitution": f"c = {concentration:g} mol/L",
        "concentration": concentration,
        "poh": PKW - ph,
        "notes": notes,
    }
