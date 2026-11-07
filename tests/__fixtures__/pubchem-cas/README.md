# CAS selection evidence (2026-11-07)

`ibuprofen-synonyms.json` and `ibuprofen-cas.json` are the responses recorded from:

- https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/3672/synonyms/JSON
- https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/3672/JSON?heading=CAS

The first synonym is 58560-75-1. The dedicated CAS section instead identifies
15687-27-1, including its CAS Common Chemistry reference:
https://commonchemistry.cas.org/detail?cas_rn=15687-27-1 . Both numbers pass the
[CAS check digit rule](https://www.cas.org/ja/training/documentation/chemical-substances/checkdig),
so checksum validation alone does not select the preferred identifier.

Selection uses the exact CID returned with the synonyms. Within the current
CAS section, values attributed to CAS Common Chemistry take priority. If that
source supplies multiple values, the value supported by the most distinct named
sources wins among those values. Without that source, compare all valid CAS
values. Repeated entries and multiple references from the same source count
once. A tie returns no identifier. Deprecated CAS sections and a mismatching
record CID cannot supply a value. If the CAS request fails, the synonyms may
supply a fallback only when there is exactly one distinct checksum-valid CAS;
an ambiguous list never falls back to its first entry. This is a source-selection
policy, not a claim that a checksum proves substance identity.

`identity-cas.json` records all 25 concrete inputs in `tests/identity/stoffe.json`,
deduplicated by InChIKey to 19 compounds. The six inputs expecting an error have
no resolved compound and therefore no CAS to compare. Requests used
`/rest/pug/compound/inchikey/{key}/synonyms/JSON`, followed by
`/rest/pug_view/data/compound/{cid}/JSON?heading=CAS`.
The fixture keeps the first 30 synonyms (the original selection window), the
CAS section and its references, and the measured before/after values. Tests
replay both selections against the same recorded responses with no network.

Result: **1 of 19 compounds (1 of 25 inputs) changes**, Ibuprofen
58560-75-1 → 15687-27-1. No previously populated CAS becomes empty.

The three compounds with multiple CAS Common Chemistry values retain:

| Compound | CAS | Recorded PubChem source |
|---|---|---|
| Citric acid | 77-92-9 | https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/311/JSON?heading=CAS |
| Urea | 57-13-6 | https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/1176/JSON?heading=CAS |
| Sodium chloride | 7647-14-5 | https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/5234/JSON?heading=CAS |

Their CAS Common Chemistry references, plus distinct supporting sources, are
preserved in the fixture; alternative values are not silently discarded from
the evidence. Raw live responses and execution logs from this run are local at
`/tmp/chemdraw-desktop-test/2026-11-07/cas-audit/`.
