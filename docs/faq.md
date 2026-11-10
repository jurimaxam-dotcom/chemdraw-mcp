# FAQ

Questions that came up in real use and in the hand tests in Claude Desktop,
with the answer and what to do.

## Installation and Claude Desktop

**The model sees every tool twice.**
Two registrations are active: either the extension and `chemdraw-install`
were both installed, or both connectors (`chemdraw` and `chemdraw-pharma`)
are switched on in the same chat. Keep one installation route and enable one
connector per chat.

**I installed or updated it and nothing changed, or the panel is missing.**
Claude Desktop keeps the old server process. Quit Claude Desktop completely
(Cmd-Q on macOS) and start it again.

**Claude never calls a tool, or says it has no such tool.**
Open Settings → Connectors → `chemdraw` and look at the tool permissions. A
tool set to blocked is not offered to the model at all; newly added tools can
start out blocked. A tool that needs approval shows a dialog in the chat
("Claude wants to use … from chemdraw") and waits for your click.

**Claude answers from memory instead of using the tool.**
Claude Desktop often does that for knowledge questions (solubility, expected
IR bands, a pH value): 0 of 3 chats each called a tool in a measurement on
3 November 2026. Drawing requests are not affected. Adding "use ChemDraw" to
the prompt made Desktop call the tool in 2 of 2 chats each.

**The extension fails on its very first start right after a new release.**
In one test the first start about a minute after the upload failed with "no
version of chemdraw-mcp==…", and a start a minute later worked. Restart Claude
Desktop.

**`chemdraw-doctor` reports `[NOTE]` for the Claude Desktop config.**
That is expected with the extension: extensions are managed by Claude Desktop
and do not appear in its config file.

**Does it run on Windows?** The extension declares macOS and Linux only.
Windows is untested.

**Do I need ChemDraw?** No. CDXML is an optional output format for people who
want to keep editing in ChemDraw.

## Structures and names

**My SMILES is drawn, but there is no name or CAS number.**
PubChem has no record for its InChIKey. By default the SMILES itself is not
sent ([Privacy](privacy.md)); formula and molar mass are computed locally.

**"Draw glucose" shows a choice instead of a structure.**
"glucose", "xylene", "cresol", "toluidine" and "butanol" name several
compounds. Click the one you mean, or name it ("beta-D-glucose", "p-xylene").

**The Fischer view of glucose shows an open chain.**
A ring sugar has no Fischer projection of its own. For "D-glucose",
"beta-D-glucose" or "D-fructose" the Fischer view draws the open-chain form and
says so ("open-chain form"). Glycosides have no Fischer view.

**"Lysozyme" is the hen enzyme, not the human one.**
Lab standards come first: lysozyme means hen egg-white lysozyme. Add the
organism ("human lysozyme"); the message names the common alternatives.

**A gene symbol is not recognised as a protein.**
Gene symbols are recognised in the style `RecA`, `LacZ`, `GroEL`, `HemA`. In
capitals ("RECA", like "ATP") the input is read as a compound name.

**The "Apply coefficients" button does not appear.**
It appears only when the drawn equation is not balanced and whole-number
coefficients exist. Claude may balance the equation itself and pass the
coefficients (seen in a hand test with H₂ + O₂); then the scheme is balanced
from the start and there is nothing to apply.

**Where is the file of my mechanism or my chair drawing?**
Mechanisms and the extra views (All H, Fischer, Haworth, Chair) exist only in
the panel. **Export PNG** saves what you see to `~/ChemDraw-Output/png/`.

## Limits

If something here does not match what you see, check the installed version:
`chemdraw-doctor` prints it in its first line.
