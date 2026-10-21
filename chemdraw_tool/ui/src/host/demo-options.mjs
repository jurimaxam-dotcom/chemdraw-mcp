// Aufnahmeauflösung und Click-Log sind unabhängig; das Standardlayout bleibt gleich.
export function recordingOptions(args) {
  const mitKlicks = args.includes("--clicks");
  const szenen = args.filter((arg) => arg !== "--clicks" && arg !== "--hires");
  return {
    mitKlicks,
    zoom: mitKlicks || args.includes("--hires") ? 2 : 1,
    width: 720,
    height: mitKlicks ? 720 : 560,
    szenen: szenen.length ? szenen : ["molecule"],
  };
}
