import XCTest

// Gemeinsame Bausteine beider Stufen. Der Test-Runner läuft in der Sandbox: Ergebnisse verlassen
// ihn nur als XCTAttachment (run.sh exportiert sie), der Zustand zwischen Stufe A und B liegt im
// Container des Runners.

let claudeID = "com.anthropic.claudefordesktop"
let toolNamen = [
  "generate_molecule", "compare_molecules", "batch_generate", "generate_reaction",
  "generate_mechanism", "generate_3d", "generate_protein_or_antibody", "lookup_molecule_data",
  "generate_spectrum", "generate_tlc", "generate_titration_curve",
  "generate_species_distribution", "export_anki_deck",
  "lookup", "predict_spectrum", "calculate_ph", "save_png", "load_panel_part",
] + pharmaTools
/// Tools, die nur der zweite Konnektor `chempane-pharma` liefert (Profil pharma, seit 16.11.2026).
let pharmaTools = [
  "generate_scope_table", "generate_calibration_curve", "generate_pk_curve", "generate_dose_response",
  "calculate_solution", "calculate_content", "calculate_pharmacokinetics",
]

func ladeJSON(_ name: String) -> [String: Any] {
  let b = Bundle(for: ProbeFall.self)
  guard let url = b.url(forResource: name, withExtension: "json"),
        let data = try? Data(contentsOf: url),
        let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return [:] }
  return obj
}

enum Zustand {
  static var pfad: String { NSHomeDirectory() + "/desktop-probe-zustand.json" }
  static func lesen() -> [String: [String: String]] {
    guard let d = FileManager.default.contents(atPath: pfad),
          let o = try? JSONSerialization.jsonObject(with: d) as? [String: [String: String]] else { return [:] }
    return o
  }
  static func merken(_ tool: String, _ werte: [String: String]) {
    var z = lesen(); z[tool] = werte
    if let d = try? JSONSerialization.data(withJSONObject: z, options: [.prettyPrinted, .sortedKeys]) {
      FileManager.default.createFile(atPath: pfad, contents: d)
    }
  }
}

class ProbeFall: XCTestCase {
  let app = XCUIApplication(bundleIdentifier: claudeID)
  var tool = ""
  var zeilen: [[String: Any]] = []
  var start = Date()

  override func setUp() {
    continueAfterFailure = true
    start = Date()
    zeilen = []
  }

  override func tearDown() {
    // Fehler, die XCTest außerhalb eines Checkpoints meldet (z. B. ein abgebrochener Klick), dürfen im
    // Bericht nicht fehlen: sonst wäre die Tabelle grün und der Test rot.
    let rote = zeilen.filter { ($0["status"] as? String) == "rot" }.count
    let gemeldet = testRun?.totalFailureCount ?? 0
    if gemeldet > rote {
      zeilen.append(["name": "Abbruch außerhalb eines Checkpoints", "status": "rot", "info": "\(gemeldet - rote) Fehler, siehe xcodebuild.log", "s": 0.0])
    }
    // Eine Ergebnisdatei je Testmethode; run.sh baut daraus die Tabelle.
    let bericht: [String: Any] = ["tool": tool, "test": name, "dauer_s": rund(Date().timeIntervalSince(start)), "checkpoints": zeilen]
    if let d = try? JSONSerialization.data(withJSONObject: bericht, options: [.prettyPrinted, .sortedKeys]) {
      let a = XCTAttachment(data: d, uniformTypeIdentifier: "public.json")
      a.name = "ergebnis-\(stufe)-\(tool).json"; a.lifetime = .keepAlways; add(a)
    }
  }

  var stufe: String { "x" }
  func rund(_ x: Double) -> Double { (x * 10).rounded() / 10 }

  /// Ein Checkpoint = eine Aktivität im Testbericht + eine Zeile grün/rot. Wirft nie; ein roter
  /// Checkpoint hält die folgenden nicht auf (außer der Aufrufer bricht bei `false` selbst ab).
  @discardableResult
  func checkpoint(_ titel: String, befund: Bool = false, _ block: () -> (Bool, String)) -> Bool {
    let t0 = Date()
    let (ok, info) = XCTContext.runActivity(named: titel) { _ in block() }
    let status = ok ? "gruen" : (befund ? "befund" : "rot")
    zeilen.append(["name": titel, "status": status, "info": info, "s": rund(Date().timeIntervalSince(t0))])
    print("CHECKPOINT \(stufe) \(tool) | \(status) | \(titel) | \(info)")
    if !ok {
      haengeBaumAn("rot-\(zeilen.count)")
      if !befund { XCTFail("\(titel): \(info)") }
    }
    return ok
  }

  func haengeBaumAn(_ marke: String) {
    let a = XCTAttachment(string: app.debugDescription)
    a.name = "baum-\(stufe)-\(tool)-\(marke).txt"; a.lifetime = .keepAlways; add(a)
  }

  /// Sichtbarer Bereich des Chats im Fenster: oben liegt die Kopfzeile, unten das Antwortfeld.
  var sichtbar: (oben: CGFloat, unten: CGFloat) {
    let f = app.windows.firstMatch.frame
    return (f.minY + 70, f.maxY - 170)
  }

  /// Rollt den Chat, bis `y` (Bildschirmkoordinate eines Punkts im Panel) auf `ziel` liegt.
  func rolle(_ el: XCUIElement, _ punkt: @escaping (CGRect) -> CGFloat, auf ziel: CGFloat) {
    let mitte = app.windows.firstMatch.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
    var still = 0, runden = 0
    while runden < 30 {
      let vorher = punkt(el.frame)
      let abstand = vorher - ziel
      if abs(abstand) < 12 { break }
      mitte.scroll(byDeltaX: 0, deltaY: max(-400, min(400, -abstand)))
      runden += 1; Thread.sleep(forTimeInterval: 0.35)
      still = abs(punkt(el.frame) - vorher) < 2 ? still + 1 : 0
      if still >= 3 { break }
    }
  }

  /// Bild nur vom Panel (ohne Seitenleiste mit privaten Chat-Titeln) – das ist das Material für draußen.
  /// Ein Bildschirmfoto zeigt nur, was im Fenster liegt (12 von 40 Bildern am 14.11.2026 waren
  /// abgeschnitten): deshalb erst das Panel in den sichtbaren Bereich rollen; ist es höher als der
  /// Bereich, entstehen zwei Bilder (`-oben`, `-unten`), die zusammen das ganze Panel zeigen.
  func panelBild(_ marke: String, _ el: XCUIElement? = nil) {
    let ziel = el ?? panel
    guard ziel.exists else { return }
    func foto(_ zusatz: String) {
      let a = XCTAttachment(screenshot: ziel.screenshot())
      a.name = "panel-\(tool)-\(marke)\(zusatz).png"; a.lifetime = .keepAlways; add(a)
    }
    let (oben, unten) = sichtbar
    if ziel.frame.height <= unten - oben {
      if ziel.frame.minY < oben || ziel.frame.maxY > unten { rolle(ziel, { $0.midY }, auf: (oben + unten) / 2) }
      foto("")
    } else {
      rolle(ziel, { $0.minY }, auf: oben); foto("-oben")
      rolle(ziel, { $0.maxY }, auf: unten); foto("-unten")
    }
  }

  /// Mittlerer Helligkeitsunterschied zweier Bilder (0–255), beide auf 64×64 Graustufen gebracht.
  /// Für „hat sich das Bild geändert“ und „ist es wieder das alte“ – nicht für feine Vergleiche.
  func bildabstand(_ a: XCUIScreenshot, _ b: XCUIScreenshot) -> Double {
    func grau(_ s: XCUIScreenshot) -> [UInt8]? {
      guard let cg = s.image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return nil }
      var px = [UInt8](repeating: 0, count: 64 * 64)
      let ok = px.withUnsafeMutableBytes { roh -> Bool in
        guard let ctx = CGContext(data: roh.baseAddress, width: 64, height: 64, bitsPerComponent: 8, bytesPerRow: 64,
                                  space: CGColorSpaceCreateDeviceGray(), bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return false }
        ctx.interpolationQuality = .medium
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: 64, height: 64)); return true
      }
      return ok ? px : nil
    }
    guard let x = grau(a), let y = grau(b) else { return -1 }
    var summe = 0
    for i in 0..<x.count { summe += abs(Int(x[i]) - Int(y[i])) }
    return Double(summe) / Double(x.count)
  }

  /// Welcher Konnektor muss antworten? Seit 16.11.2026 liefert `chempane` die 18 Standard-Tools und
  /// `chempane-pharma` nur die Zusatz-Tools (bis 0.11.3: chemdraw/chemdraw-pharma); das installierte Bündel darf
  /// in einem Probe-Lauf gar nicht antworten – es bringt einen älteren Stand mit.
  func konnektorCheckpoint() {
    checkpoint("Antwort kommt vom richtigen Konnektor") {
      let titel = server
      let soll = pharmaTools.contains(tool) ? "chempane-pharma" : "chempane"
      // Die Gruppe heißt "<konnektor> embed" oder "<konnektor>: <Titel>".
      let ist = titel.components(separatedBy: CharacterSet(charactersIn: " :")).first ?? ""
      return (ist == soll, "soll \(soll), Gruppe „\(titel)“")
    }
  }

  func nachVorn() -> Bool {
    app.activate()
    return app.wait(for: .runningForeground, timeout: 10)
  }

  var chat: XCUIElement { app.groups["Chat messages"].firstMatch }
  /// Das Panel ist die WebView "MCP-UI Proxy" (Desktops Sandbox-Rahmen um unser iframe "Chem-MCP").
  /// Die Gruppe darum taugt nicht als Anker: sie heißt mal "<server> embed", mal "<server>: <Titel>".
  var panel: XCUIElement { chat.webViews["MCP-UI Proxy"].firstMatch }
  var panelInhalt: XCUIElement { panel.webViews["Chem-MCP"].firstMatch }
  /// Name des Konnektors, der geantwortet hat (steht im Tool-Kopf vor dem Toolnamen).
  /// Bevorzugt die Gruppe um unser iframe „Chem-MCP“, damit ein zusätzliches Host-Widget (z. B. visualize)
  /// im selben Chat nicht als Konnektor unseres Panels gelesen wird.
  var server: String {
    let mitInhalt = chat.groups.containing(.webView, identifier: "Chem-MCP").allElementsBoundByIndex
      .last { !$0.title.isEmpty && !$0.title.hasPrefix("Message ") }
    if let t = mitInhalt?.title { return t }
    let g = chat.groups.containing(.webView, identifier: "MCP-UI Proxy").allElementsBoundByIndex
      .last { !$0.title.isEmpty && !$0.title.hasPrefix("Message ") }
    return g?.title ?? ""
  }

  func irgendwo(_ root: XCUIElement, _ typ: XCUIElement.ElementType = .any, _ format: String, _ args: Any...) -> XCUIElement {
    root.descendants(matching: typ).matching(NSPredicate(format: format, argumentArray: args)).firstMatch
  }

  /// Steht Desktop an der Nutzungsgrenze? Dann antwortet das Modell nicht, und jeder rote Checkpoint
  /// danach wäre keine Messung (16.11.2026: 14 Fälle „Eingabefeld fehlt“, 3 Fälle „180 s ohne Tool-Kopf“).
  var nutzungsgrenze: Bool {
    irgendwo(app, .staticText, "value BEGINSWITH[c] %@ OR value CONTAINS[c] %@ OR title == %@", "You’ve reached you", "usage limit", "Need more usage?").exists
  }

  var chatTitel: String {
    let b = irgendwo(app, .button, "title ENDSWITH ', rename session'")
    guard b.exists else { return "" }
    return b.title.replacingOccurrences(of: ", rename session", with: "")
  }
}
