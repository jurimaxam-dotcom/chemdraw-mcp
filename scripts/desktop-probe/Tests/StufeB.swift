import XCTest

// Stufe B: kein neuer Prompt. Öffnet den Chat, den Stufe A für das Tool hinterlassen hat, und geht
// die Checkpoints aus checkpoints.json durch. Prüft damit auch, dass Desktop ein Panel beim
// Wiederöffnen eines Chats neu aufbaut.
final class StufeB: ProbeFall {
  override var stufe: String { "B" }

  let typen: [String: XCUIElement.ElementType] = [
    "tab": .tab, "button": .button, "checkBox": .checkBox, "staticText": .staticText, "image": .image,
    "group": .group, "radioButton": .radioButton, "link": .link, "slider": .slider, "any": .any,
    "popUpButton": .popUpButton, "table": .table, "cell": .cell, "textField": .textField,
  ]

  /// Sucht im Panel nach Bedienungshilfen-Namen: "titel" (genau), "beginnt", "enthaelt" – jeweils gegen
  /// title, label und value.
  func finde(_ s: [String: Any]) -> XCUIElement {
    let typ = typen[(s["typ"] as? String) ?? "any"] ?? .any
    var format = "", wert = ""
    if let t = s["titel"] as? String { format = "title == %@ OR label == %@ OR value == %@"; wert = t }
    else if let t = s["beginnt"] as? String { format = "title BEGINSWITH %@ OR label BEGINSWITH %@ OR value BEGINSWITH %@"; wert = t }
    else if let t = s["enthaelt"] as? String { format = "title CONTAINS[c] %@ OR label CONTAINS[c] %@ OR value CONTAINS[c] %@"; wert = t }
    let q = panel.descendants(matching: typ)
    if format.isEmpty { return q.firstMatch }
    return q.matching(NSPredicate(format: format, wert, wert, wert)).firstMatch
  }

  /// Bilder, die ein Schritt mit "merke" abgelegt hat – Vergleichsgrundlage für "gleichWie".
  var gemerkt: [String: XCUIScreenshot] = [:]

  func schritt(_ s: [String: Any]) {
    let name = (s["name"] as? String) ?? "?"
    let warte = (s["timeout"] as? Double) ?? 8
    // "befund": true – ein Rot hier ist meldenswert, aber kein Fehler des Produkts, den dieser Schritt
    // belegen könnte (z. B. ein Zug, den XCUIAutomation in Desktops WebView nicht ausgelöst bekommt).
    checkpoint(name, befund: (s["befund"] as? Bool) == true) {
      let el = finde(s)
      // "fehlt": true – das Element darf nicht (mehr) da sein, z. B. Reiter in einer Übersicht.
      if (s["fehlt"] as? Bool) == true {
        let weg = el.waitForNonExistence(timeout: warte)
        if weg, let marke = s["bild"] as? String { panelBild(marke) }
        return (weg, weg ? "fehlt wie erwartet" : "ist noch da")
      }
      guard el.waitForExistence(timeout: warte) else { return (false, "nicht gefunden") }
      var info = ""
      // "merke": Bild des Elements ablegen. "ziehen": mit der Maus über das Element ziehen und belegen,
      // dass sich sein Bild dabei ändert (ein Checkpoint „drehbar“ muss drehen, nicht nur die Fläche
      // finden). "gleichWie": das Bild muss wieder dem gemerkten entsprechen (z. B. nach „Reset view“).
      if s["merke"] != nil || s["ziehen"] != nil || s["gleichWie"] != nil {
        let (oben, unten) = sichtbar
        if el.frame.minY < oben || el.frame.maxY > unten { rolle(el, { $0.midY }, auf: (oben + unten) / 2) }
        Thread.sleep(forTimeInterval: 0.5)
      }
      if let m = s["merke"] as? String { gemerkt[m] = el.screenshot() }
      if (s["ziehen"] as? Bool) == true {
        let vorher = el.screenshot()
        // Langsam ziehen und am Ende kurz halten: ein schneller Zug kommt in der WebView als
        // Drücken und Loslassen ohne Bewegung dazwischen an (16.11.2026: Bildabstand 0,00).
        // Koordinaten über das Fenster, aus dem Rahmen des Elements im Moment des Ziehens: die
        // elementbezogene Koordinate eines Web-Bildes traf nach dem Rollen nicht (Bildabstand 0,00).
        let f = el.frame, w = app.windows.firstMatch, wf = w.frame
        func punkt(_ dx: CGFloat, _ dy: CGFloat) -> XCUICoordinate {
          w.coordinate(withNormalizedOffset: .zero).withOffset(CGVector(dx: f.minX + f.width * dx - wf.minX, dy: f.minY + f.height * dy - wf.minY))
        }
        punkt(0.4, 0.45).press(forDuration: 0.3, thenDragTo: punkt(0.6, 0.6), withVelocity: .slow, thenHoldForDuration: 0.3)
        Thread.sleep(forTimeInterval: 0.8)
        let d = bildabstand(vorher, el.screenshot())
        if let marke = s["bild"] as? String { panelBild(marke) }
        // Schwelle 1,0 von 255: ein unbewegtes Bild liegt bei 0, ein gedrehtes Modell bei mehreren Einheiten.
        return (d >= 1.0, String(format: "Bildabstand nach dem Ziehen %.2f (Schwelle 1,0), Fläche %.0f×%.0f bei %.0f/%.0f", d, f.width, f.height, f.minX, f.minY))
      }
      if let m = s["gleichWie"] as? String {
        guard let alt = gemerkt[m] else { return (false, "kein gemerktes Bild „\(m)“") }
        let d = bildabstand(alt, el.screenshot())
        if let marke = s["bild"] as? String { panelBild(marke) }
        return (d >= 0 && d < 0.5, String(format: "Bildabstand zum gemerkten Bild %.2f (Schwelle 0,5)", d))
      }
      // Schalter, die schon im Zielzustand stehen (Chat war noch offen), nicht umlegen.
      let schonDa = (s["wert"] as? String).map { $0 == "\(el.value ?? "")" } ?? false
      if schonDa && (s["aktion"] as? String) == "klick" && s["dann"] == nil { info = "stand schon so" }
      else if (s["aktion"] as? String) == "klick" {
        // Ein Klick auf ein nicht treffbares Element bricht den ganzen Test ab (XCTest wirft dann),
        // statt nur diesen Checkpoint rot zu machen. Also erst in den sichtbaren Bereich rollen.
        // Ziel ist die Fenstermitte, nicht bloß "treffbar": oben liegt die Kopfzeile, unten das
        // Antwortfeld über dem Chat, und ein Klick am Rand trifft dann das Falsche.
        let fenster = app.windows.firstMatch.frame
        let mitte = app.windows.firstMatch.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
        var runden = 0, still = 0, ruettler = 0
        while runden < 25 {
          let vorher = el.frame.midY
          let abstand = vorher - fenster.midY
          let mittig = abs(abstand) < fenster.height * 0.22
          if mittig && el.isHittable { break }
          // Mittig und trotzdem nicht treffbar (gemessen 17.11.2026, Batch-Detail): nach einem Höhenwechsel
          // des Panels meldet Desktop für den Chat-Text darunter noch die alten Rahmen, der Treffertest
          // landet dann in einer Tabellenzeile, die im Bild 300 px tiefer steht. Ein spürbarer Rollschritt
          // lässt den Baum neu melden; höchstens viermal, abwechselnd hin und zurück.
          if mittig { if ruettler >= 4 { break }; ruettler += 1 }
          let schritt: CGFloat = mittig ? (ruettler % 2 == 1 ? -160 : 160) : max(-400, min(400, -abstand))
          mitte.scroll(byDeltaX: 0, deltaY: schritt)
          runden += 1; Thread.sleep(forTimeInterval: 0.4)
          // Am Anfang oder Ende des Chats bewegt sich nichts mehr: dann reicht "treffbar". Erst nach
          // drei Runden ohne Bewegung aufgeben – direkt nach dem Rollen ist der Rahmen oft noch der alte.
          still = abs(el.frame.midY - vorher) < 2 ? still + 1 : 0
          if still >= 3 { break }
        }
        guard el.isHittable else { return (false, "nicht klickbar (verdeckt oder außerhalb des Fensters)") }
        el.click()
        info = runden > 0 ? "geklickt nach \(runden)× Rollen" : "geklickt"
      }
      if let w = s["wert"] as? String {
        // Zustand nach dem Klick, z. B. value "1" bei einem gewählten Tab.
        let bis = Date().addingTimeInterval(5)
        var ist = "\(el.value ?? "")"
        while ist != w && Date() < bis { Thread.sleep(forTimeInterval: 0.3); ist = "\(el.value ?? "")" }
        if ist != w { return (false, "value \(ist), erwartet \(w)") }
      }
      if let d = s["dann"] as? [String: Any] {
        let folge = finde(d)
        let ok = folge.waitForExistence(timeout: (d["timeout"] as? Double) ?? 20)
        if !ok { return (false, "\(info) – Folge fehlt: \(d)") }
      }
      if let w = s["pause"] as? Double { Thread.sleep(forTimeInterval: w) }
      if let marke = s["bild"] as? String { panelBild(marke) }
      return (true, info)
    }
  }

  func lauf(_ name: String) {
    tool = name
    let plan = (ladeJSON("checkpoints")[name] as? [String: Any]) ?? [:]
    let merk = Zustand.lesen()[name] ?? [:]
    let titel = merk["titel"] ?? ""
    guard checkpoint("Chat aus Stufe A bekannt", { (!titel.isEmpty, titel.isEmpty ? "erst run.sh A \(name)" : titel) }) else { return }
    guard checkpoint("Desktop im Vordergrund", { (nachVorn(), "") }) else { return }

    let offen = checkpoint("Chat geöffnet") {
      if chatTitel == titel { return (true, "war schon offen") }
      // Öffnet ein Chat eine Dateivorschau, klappt Desktop die Seitenleiste ein.
      let zeigen = app.buttons["Show sidebar"].firstMatch
      if zeigen.exists { zeigen.click() }
      let eintrag = app.buttons.matching(NSPredicate(format: "title == %@ OR title == %@", titel, titel + " Unread response")).firstMatch
      guard eintrag.waitForExistence(timeout: 8) else { return (false, "kein Eintrag '\(titel)' in der Seitenleiste") }
      // Einträge unterhalb des sichtbaren Bereichs stehen mit 1 px Höhe im Baum; ein Klick ginge ins
      // Leere. Deshalb die Seitenleiste rollen, bis der Eintrag echte Höhe hat.
      let leiste = app.windows.firstMatch.coordinate(withNormalizedOffset: CGVector(dx: 0.05, dy: 0.6))
      var runden = 0
      while eintrag.frame.height < 10 && runden < 40 { leiste.scroll(byDeltaX: 0, deltaY: -300); runden += 1; Thread.sleep(forTimeInterval: 0.15) }
      guard eintrag.frame.height >= 10 else { return (false, "Eintrag bleibt außerhalb des sichtbaren Bereichs") }
      eintrag.click()
      let kopf = irgendwo(app, .button, "title == %@", titel + ", rename session")
      return (kopf.waitForExistence(timeout: 15), "über die Seitenleiste")
    }
    guard offen else { return }

    let da = checkpoint("Panel nach Wiederöffnen eingebettet") {
      // Öffnet der Chat neben einer Dateivorschau oder am Ende einer langen Antwort, liegt die
      // Einbettung oberhalb des sichtbaren Bereichs und steht nur als 1 px hohe Gruppe im Baum –
      // die WebView baut Desktop erst, wenn sie ins Bild rollt (Kalibriergerade, 16.11.2026).
      var ok = panel.waitForExistence(timeout: 8)
      let mitte = app.windows.firstMatch.coordinate(withNormalizedOffset: CGVector(dx: 0.4, dy: 0.5))
      var runden = 0
      while !ok && runden < 20 { mitte.scroll(byDeltaX: 0, deltaY: 300); runden += 1; ok = panel.waitForExistence(timeout: 1.5) }
      return (ok, ok ? server + (runden > 0 ? " (nach \(runden)× Hochrollen)" : "") : "keine WebView MCP-UI Proxy im Chat")
    }
    guard da else { return }
    konnektorCheckpoint()
    checkpoint("Panel hat Inhalt") {
      guard panelInhalt.waitForExistence(timeout: 30) else { return (false, "WebView Chem-MCP fehlt") }
      let inhalt = panelInhalt.descendants(matching: .any).matching(NSPredicate(format: "elementType IN %@", [XCUIElement.ElementType.staticText.rawValue, XCUIElement.ElementType.image.rawValue]))
      let bis = Date().addingTimeInterval(30)
      while inhalt.count < 2 && Date() < bis { Thread.sleep(forTimeInterval: 0.5) }
      return (inhalt.count >= 2, "\(inhalt.count) Text-/Bildelemente")
    }
    panelBild("B-start")
    gemerkt = [:]
    for s in (plan["schritte"] as? [[String: Any]]) ?? [] { schritt(s) }
    let a = XCTAttachment(string: panel.debugDescription)
    a.name = "baum-B-\(name)-panel.txt"; a.lifetime = .keepAlways; add(a)
  }

  func test_generate_molecule() { lauf("generate_molecule") }
  func test_compare_molecules() { lauf("compare_molecules") }
  func test_batch_generate() { lauf("batch_generate") }
  func test_generate_reaction() { lauf("generate_reaction") }
  func test_generate_mechanism() { lauf("generate_mechanism") }
  func test_generate_3d() { lauf("generate_3d") }
  func test_generate_protein_or_antibody() { lauf("generate_protein_or_antibody") }
  func test_lookup_molecule_data() { lauf("lookup_molecule_data") }
  func test_generate_spectrum() { lauf("generate_spectrum") }
  func test_generate_tlc() { lauf("generate_tlc") }
  func test_generate_titration_curve() { lauf("generate_titration_curve") }
  func test_generate_species_distribution() { lauf("generate_species_distribution") }
  func test_export_anki_deck() { lauf("export_anki_deck") }
  func test_generate_calibration_curve() { lauf("generate_calibration_curve") }
}
