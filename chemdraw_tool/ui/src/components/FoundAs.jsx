import React from "react";

// Schreibweise, unter der der Server den Namen gefunden hat, wenn es nicht die
// Eingabe war ("Dexamethason" → "Dexamethasone"). Macht einen Umweg sichtbar,
// damit ein falscher Treffer auffaellt; bei woertlichem Treffer nichts.
export default function FoundAs({ value }) {
  if (!value) return null;
  return <p data-testid="found-as" className="panel-record">Found as “{value}”</p>;
}
