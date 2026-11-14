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

  /// Bild nur vom Panel (ohne Seitenleiste mit privaten Chat-Titeln) – das ist das Material für draußen.
  func panelBild(_ marke: String, _ el: XCUIElement? = nil) {
    let ziel = el ?? panel
    guard ziel.exists else { return }
    let a = XCTAttachment(screenshot: ziel.screenshot())
    a.name = "panel-\(tool)-\(marke).png"; a.lifetime = .keepAlways; add(a)
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
  var server: String {
    let g = chat.groups.containing(.webView, identifier: "MCP-UI Proxy").allElementsBoundByIndex.last
    return g?.title ?? ""
  }

  func irgendwo(_ root: XCUIElement, _ typ: XCUIElement.ElementType = .any, _ format: String, _ args: Any...) -> XCUIElement {
    root.descendants(matching: typ).matching(NSPredicate(format: format, argumentArray: args)).firstMatch
  }

  var chatTitel: String {
    let b = irgendwo(app, .button, "title ENDSWITH ', rename session'")
    guard b.exists else { return "" }
    return b.title.replacingOccurrences(of: ", rename session", with: "")
  }
}
