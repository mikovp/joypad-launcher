"""Main loop context shared across input handling."""

from dataclasses import dataclass

RESCAN_INTERVAL = 120


@dataclass
class LoopContext:
    axis_held: int = 0
    trig_page_arm_lt: bool = True
    trig_page_arm_rt: bool = True
    frames_since_rescan: int = 0
