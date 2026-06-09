import React from "react";

export default function NavTabs({ tabs, activeTab, onTabChange }) {
  return (
    <div
      style={{
        display: "flex",
        background: "var(--bg-alt)",
        borderRadius: "var(--radius-md)",
        padding: 2,
        gap: 2,
        marginBottom: 12,
      }}
    >
      {tabs.map((tab) => {
        const isActive = tab === activeTab;
        return (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            style={{
              flex: 1,
              padding: "5px 10px",
              fontSize: 11,
              fontFamily: "var(--font)",
              borderRadius: "var(--radius-sm)",
              border: "none",
              cursor: "pointer",
              background: isActive ? "var(--bg-alt)" : "transparent",
              boxShadow: isActive ? "var(--shadow-card)" : "none",
              color: isActive ? "var(--fg)" : "var(--fg-muted)",
              transition: "background 0.15s, color 0.15s",
            }}
          >
            {tab}
          </button>
        );
      })}
    </div>
  );
}
