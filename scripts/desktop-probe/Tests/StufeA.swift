import XCTest

// Stufe A: je Panel-Tool ein neuer Chat mit dem Prompt aus evals/panel-beispiele.json.
// Prüft, was nur Desktop zeigt: ruft das Modell das Tool, kommt ein Rechte-Dialog, erscheint das Panel.
final class StufeA: ProbeFall {
  override var stufe: String { "A" }

  var modell = ""

  /// Liest das Modell des neuen Chats; mit PROBE_MODELL (run.sh --modell "Fable 5.2") stellt es um.
  /// Der Knopf heißt "Model: <Name> <Aufwand>", die Wahl bleibt für folgende neue Chats stehen.
  func waehleModell() -> String {
    let knopf = app.popUpButtons.matching(NSPredicate(format: "title BEGINSWITH 'Model: '")).firstMatch
    guard knopf.waitForExistence(timeout: 5) else { return "" }
    let wunsch = ProcessInfo.processInfo.environment["PROBE_MODELL"] ?? ""
    if !wunsch.isEmpty && !knopf.title.localizedCaseInsensitiveContains(wunsch) {
      // Über die Koordinate klicken: click() auf einem PopUpButton wartet auf die Meldung eines
      // nativen Menüs, die ein Web-Menü nie schickt, und bricht dann den Test ab.
      knopf.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).click()
      Thread.sleep(forTimeInterval: 0.8)
      haengeBaumAn("modellmenue")
      let eintrag = app.descendants(matching: .any).matching(NSPredicate(format: "(title CONTAINS[c] %@ OR label CONTAINS[c] %@) AND NOT (title BEGINSWITH 'Model: ')", wunsch, wunsch)).firstMatch
      if eintrag.waitForExistence(timeout: 5) { eintrag.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)).click() } else { app.typeKey(.escape, modifierFlags: []) }
      Thread.sleep(forTimeInterval: 0.8)
    }
    return knopf.title.replacingOccurrences(of: "Model: ", with: "")
  }

  func lauf(_ name: String) {
    tool = name
    let faelle = ladeJSON("panel-beispiele"), extra = ladeJSON("checkpoints")
    let prompt = ((faelle[name] as? [String: Any])?["prompt"] as? String)
      ?? ((extra[name] as? [String: Any])?["prompt"] as? String) ?? ""
    guard checkpoint("Prompt vorhanden", { (!prompt.isEmpty, prompt.isEmpty ? "kein Prompt für \(name)" : "\(prompt.count) Zeichen") }) else { return }
    guard checkpoint("Desktop im Vordergrund", { (nachVorn(), "") }) else { return }

    let gesendet = checkpoint("Neuer Chat, Prompt getippt und gesendet") {
      // Über das Menü, nicht über die Seitenleiste: deren Knopf "New" kann weggescrollt oder verdeckt
      // sein, und das Antwortfeld eines offenen Chats trägt denselben Namen wie das Feld im neuen.
      app.menuBars.menuBarItems["File"].firstMatch.click()
      let eintrag = app.menuItems["New Chat"].firstMatch
      guard eintrag.waitForExistence(timeout: 5) else { return (false, "Menü File > New Chat fehlt") }
      eintrag.click()
      guard chat.waitForNonExistence(timeout: 10) else { return (false, "alter Chat noch offen – kein neuer Chat") }
      let feld = app.textViews["Write your prompt to Claude"].firstMatch
      guard feld.waitForExistence(timeout: 10) else { return (false, "Eingabefeld fehlt") }
      modell = waehleModell()
      feld.click()
      feld.typeText(prompt)
      feld.typeKey(.return, modifierFlags: [])
      return (true, "")
    }
    guard gesendet else { return }
    let wunsch = ProcessInfo.processInfo.environment["PROBE_MODELL"] ?? ""
    checkpoint("Modell") { (wunsch.isEmpty || modell.localizedCaseInsensitiveContains(wunsch), wunsch.isEmpty ? modell : "gewünscht \(wunsch), gewählt \(modell)") }

    checkpoint("Prompt unverändert im Chat") {
      let meiner = irgendwo(app, .staticText, "value == %@", prompt)
      let ok = meiner.waitForExistence(timeout: 15)
      if ok { return (true, "") }
      let ist = irgendwo(app, .staticText, "title BEGINSWITH 'You said: '")
      return (false, "angekommen: \(ist.exists ? ist.title : "nichts")")
    }

    // Auf den Tool-Kopf warten; nebenbei einen Rechte-Dialog bedienen und das Antwortende erkennen.
    var gerufen = "", dialog = "kein Dialog"
    let erwartetDa = checkpoint("Modell ruft ein Tool") {
      // Exakte Titel, und nur im Dialog selbst: `CONTAINS 'once'` traf am 14.11.2026 den Seitenleisten-Chat
      // „Phenytoin plasma concentration …“ — der Dialog blieb offen und der Lauf meldete „kein Tool-Aufruf“.
      let anfrage = app.groups.matching(NSPredicate(format: "title BEGINSWITH 'Permission request'")).firstMatch
      let kopf = chat.staticTexts.matching(NSPredicate(format: "value IN %@", toolNamen))
      let strom = chat.groups["Currently streaming message"].firstMatch
      let antwort = chat.groups.matching(NSPredicate(format: "title BEGINSWITH 'Message 2 of'"))
      let ende = Date().addingTimeInterval(180)
      var fertigSeit: Date? = nil, dialogSeit: Date? = nil
      while Date() < ende {
        if anfrage.exists {
          // „Claude wants to use <Tool> from <Konnektor>“ — sagt, welcher Konnektor fragt.
          let wer = anfrage.buttons.matching(NSPredicate(format: "title BEGINSWITH 'Claude wants to use'")).firstMatch
          dialog = "Dialog: \(wer.exists ? wer.title : anfrage.title)"
          let once = anfrage.buttons.matching(NSPredicate(format: "title ==[c] 'Allow once'")).firstMatch
          // Nur die einmalige Freigabe: „Always allow“ würde Jays Konnektor-Rechte ändern.
          // Der Dialog baut sich beim Erscheinen einmal neu auf (Klick im ersten Moment: „No matches found“,
          // 14.11.2026): erst klicken, wenn er eine Runde später noch steht und treffbar ist.
          if dialogSeit == nil { dialogSeit = Date() }
          else if Date().timeIntervalSince(dialogSeit!) > 1.5, once.exists, once.isHittable {
            once.click(); dialogSeit = nil; fertigSeit = nil
          }
          Thread.sleep(forTimeInterval: 1.0); continue
        } else { dialogSeit = nil }
        if kopf.count > 0 { gerufen = (kopf.firstMatch.value as? String) ?? ""; return (true, gerufen) }
        // Antwort da, Streaming-Gruppe weg und 6 s lang kein Tool-Kopf: das Modell hat kein Tool gerufen.
        if antwort.count > 0 && !strom.exists {
          if fertigSeit == nil { fertigSeit = Date() }
          else if Date().timeIntervalSince(fertigSeit!) > 6 { return (false, "Antwort ohne Tool-Aufruf") }
        }
        Thread.sleep(forTimeInterval: 1.0)
      }
      return (false, "180 s ohne Tool-Kopf")
    }
    checkpoint("Rechte-Dialog", befund: true) { (dialog == "kein Dialog", dialog) }
    guard erwartetDa else { Zustand.merken(name, ["titel": chatTitel, "gerufen": ""]); return }
    checkpoint("Es ist das erwartete Tool", befund: true) { (gerufen == name, "erwartet \(name), gerufen \(gerufen)") }

    let da = checkpoint("Panel eingebettet") {
      let ok = panel.waitForExistence(timeout: 45)
      return (ok, ok ? server : "keine WebView MCP-UI Proxy im Chat")
    }
    if da {
      checkpoint("Panel hat Inhalt") {
        let ok = panelInhalt.waitForExistence(timeout: 30)
        guard ok else { return (false, "WebView Chem-MCP fehlt") }
        // Auf den ersten echten Inhalt warten (Text oder Bild), nicht nur auf den Rahmen.
        let inhalt = panelInhalt.descendants(matching: .any).matching(NSPredicate(format: "elementType IN %@", [XCUIElement.ElementType.staticText.rawValue, XCUIElement.ElementType.image.rawValue]))
        let bis = Date().addingTimeInterval(30)
        while inhalt.count < 2 && Date() < bis { Thread.sleep(forTimeInterval: 0.5) }
        return (inhalt.count >= 2, "\(inhalt.count) Text-/Bildelemente")
      }
      Thread.sleep(forTimeInterval: 1.5)
      let a = XCTAttachment(string: panel.debugDescription)
      a.name = "baum-A-\(name)-panel.txt"; a.lifetime = .keepAlways; add(a)
      panelBild("A")
    }
    // Titel vergibt das Modell kurz nach der ersten Antwort; Stufe B findet den Chat darüber.
    var titel = chatTitel
    let bis = Date().addingTimeInterval(20)
    while (titel.isEmpty || titel == "New session") && Date() < bis { Thread.sleep(forTimeInterval: 1); titel = chatTitel }
    Zustand.merken(name, ["titel": titel, "gerufen": gerufen])
    checkpoint("Chat-Titel für Stufe B gemerkt") { (!titel.isEmpty, titel) }
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
}
