import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class LogParser:
    """
    Parses SLAM runtime logs to extract detailed tracking events, optimization timings,
    warnings, errors, and system behavior.
    """

    def __init__(self) -> None:
        # Regex definitions for system behavior
        self.p_keyframe = re.compile(r"keyframe added|new keyframe", re.IGNORECASE)
        self.p_edge = re.compile(r"added.+factor|added.+edge|edge added", re.IGNORECASE)
        self.p_ba_run = re.compile(r"local ba ran|local bundle adjustment", re.IGNORECASE)
        self.p_ba_skip = re.compile(r"local ba skipped", re.IGNORECASE)
        
        self.p_vo_reject = re.compile(r"VO REJECT:\s*(.+)", re.IGNORECASE)
        self.p_track_lost = re.compile(r"TRACKING LOST", re.IGNORECASE)
        self.p_track_weak = re.compile(r"TRACKING WEAK", re.IGNORECASE)
        self.p_track_rec = re.compile(r"TRACKING RECOVERED", re.IGNORECASE)
        
        self.p_loop = re.compile(r"loop closure accepted", re.IGNORECASE)
        self.p_vins_fail = re.compile(r"vins scale failure", re.IGNORECASE)
        self.p_vins_scale = re.compile(r"VINS Initialization Scale:\s*([\d\.]+)", re.IGNORECASE)
        self.p_vins_status = re.compile(r"VINS Init Status:\s*(.+)", re.IGNORECASE)

    def parse_log(self, log_filepath: str) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {
            "keyframes": 0,
            "edges": 0,
            "ba_runs": 0,
            "ba_skips": 0,
            "vo_reject_reasons": {},
            "vo_rejects_total": 0,
            "tracking_lost": 0,
            "tracking_weak": 0,
            "tracking_recoveries": 0,
            "loop_closures": 0,
            "vins_scale_failures": 0,
            "vins_init_scale": None,
            "vins_init_status": "Not reached",
            "warnings_unique": {},
            "errors_unique": {}
        }

        try:
            with open(log_filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Capture unique warnings and errors
                    if "[WARN]" in line:
                        metrics["warnings_unique"][line] = metrics["warnings_unique"].get(line, 0) + 1
                    elif "[ERROR]" in line:
                        metrics["errors_unique"][line] = metrics["errors_unique"].get(line, 0) + 1

                    # System Behaviour
                    if self.p_keyframe.search(line): metrics["keyframes"] += 1
                    if self.p_edge.search(line): metrics["edges"] += 1
                    if self.p_ba_run.search(line): metrics["ba_runs"] += 1
                    if self.p_ba_skip.search(line): metrics["ba_skips"] += 1
                    
                    if self.p_track_lost.search(line): metrics["tracking_lost"] += 1
                    if self.p_track_weak.search(line): metrics["tracking_weak"] += 1
                    if self.p_track_rec.search(line): metrics["tracking_recoveries"] += 1
                    
                    if self.p_loop.search(line): metrics["loop_closures"] += 1
                    if self.p_vins_fail.search(line): metrics["vins_scale_failures"] += 1

                    reject_match = self.p_vo_reject.search(line)
                    if reject_match:
                        reason = reject_match.group(1).strip()
                        metrics["vo_reject_reasons"][reason] = metrics["vo_reject_reasons"].get(reason, 0) + 1
                        metrics["vo_rejects_total"] += 1
                        
                    scale_match = self.p_vins_scale.search(line)
                    if scale_match:
                        metrics["vins_init_scale"] = float(scale_match.group(1))
                        
                    status_match = self.p_vins_status.search(line)
                    if status_match:
                        metrics["vins_init_status"] = status_match.group(1).strip()

        except FileNotFoundError:
            logger.error(f"Log file not found: {log_filepath}")
        except Exception as e:
            logger.error(f"Error parsing log file: {e}")

        return metrics
