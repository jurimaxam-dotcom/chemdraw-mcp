// Aufnahmeauflösung und Click-Log sind unabhängig; das Standardlayout bleibt gleich.
// Nur der Medienschnitt: 350 ms nach dem Druck und 150 ms vor dem Ergebnis behalten.
// Die ungeschnittene Aufnahme und das Click-Log bleiben für Shorts erhalten.
export function demoEditFilter(clickMs, readyMs) {
  if (clickMs == null || readyMs == null || readyMs - clickMs <= 500) return "null";
  const start = (clickMs + 350) / 1000;
  const end = (readyMs - 150) / 1000;
  return `select='not(between(t,${start.toFixed(3)},${end.toFixed(3)}))',setpts='PTS-if(gte(T,${end.toFixed(3)}),${(end - start).toFixed(3)},0)/TB'`;
}

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
