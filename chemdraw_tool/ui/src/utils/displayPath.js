// Dateipfade im Panel kürzen: das Home-Verzeichnis wird zu „~“. Der volle Pfad bleibt
// als title-Attribut erhalten; lang und mitten im Wort umbrechend half niemandem beim Finden.
export function displayPath(path) {
  if (!path) return "";
  return path
    .replace(/^\/(?:Users|home)\/[^/]+\//, "~/")
    .replace(/^[A-Za-z]:\\Users\\[^\\]+\\/, "~\\");
}
