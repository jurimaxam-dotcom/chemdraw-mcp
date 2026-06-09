import React from "react";

export default function FunctionalGroupList({
  groups,
  hoveredGroup,
  onHoverGroup,
}) {
  if (!groups || groups.length === 0) return null;

  return (
    <div>
      {groups.map((g, i) => {
        const active = hoveredGroup === g.name;
        return (
          <div
            key={i}
            onMouseEnter={() => onHoverGroup(g.name)}
            onMouseLeave={() => onHoverGroup(null)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "3px 4px",
              borderRadius: 4,
              cursor: "default",
              background: active ? `${g.color}18` : "transparent",
              transition: "background 0.15s",
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: g.color,
                flexShrink: 0,
                boxShadow: active ? `0 0 4px ${g.color}` : "none",
                transition: "box-shadow 0.15s",
              }}
            />
            <span style={{
              fontSize: 10,
              color: active ? "var(--fg)" : "var(--fg-muted)",
              fontWeight: active ? 600 : 400,
              transition: "color 0.15s",
            }}>
              {g.name}
            </span>
            <span style={{
              fontSize: 9,
              color: "var(--fg-muted)",
              marginLeft: "auto",
              opacity: 0.6,
            }}>
              {g.atomIndices.length}
            </span>
          </div>
        );
      })}
    </div>
  );
}
