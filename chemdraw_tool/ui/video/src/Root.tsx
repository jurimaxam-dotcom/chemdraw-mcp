import React from "react";
import { Composition } from "remotion";
import { Short, type ShortProps } from "./Short.tsx";
import { EMPTY_LOG } from "./lib/click-log.ts";
import { FPS, SIZE, totalSeconds } from "./lib/timeline.ts";

// Props kommen aus scripts/demo-short.sh (--props): Aufnahme in public/ + ihr Click-Log
const defaults: ShortProps = { video: "molecule.mp4", log: { ...EMPTY_LOG, viewport: { width: 1440, height: 1440 } } };

export const Root: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    width={SIZE.width}
    height={SIZE.height}
    fps={FPS}
    durationInFrames={Math.ceil(totalSeconds(defaults.log) * FPS)}
    defaultProps={defaults}
    calculateMetadata={({ props }) => ({ durationInFrames: Math.ceil(totalSeconds(props.log) * FPS) })}
  />
);
