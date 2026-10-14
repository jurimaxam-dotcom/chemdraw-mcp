import React from "react";

export default function NavTabs({ tabs, activeTab, onTabChange }) {
  return <div className="source-tabs" role="group" aria-label="Data sources">
    {tabs.map((tab) => <button key={tab} type="button" aria-pressed={tab === activeTab} onClick={() => onTabChange(tab)}>{tab}</button>)}
  </div>;
}
