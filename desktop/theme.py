"""Dark theme (Qt stylesheet) matching the RailVision web dashboard palette."""

from __future__ import annotations

# Alert palette (hex) shared with widgets for painting.
ALERT_COLORS = {
    "safe": "#22c55e",
    "low": "#14b8a6",
    "medium": "#f59e0b",
    "high": "#f97316",
    "critical": "#ef4444",
}

BG = "#0b1220"
CARD = "#111a2e"
BORDER = "#1f2b45"
FG = "#e6edf7"
MUTED = "#8aa0c0"
PRIMARY = "#3b82f6"

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    color: {FG};
}}
QMainWindow, QWidget#Root {{ background: {BG}; }}

QFrame#Card {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QLabel#CardTitle {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
}}
QLabel#StatValue {{ font-size: 26px; font-weight: 700; }}
QLabel#StatLabel {{ color: {MUTED}; font-size: 11px; letter-spacing: 1px; }}
QLabel#H1 {{ font-size: 20px; font-weight: 800; }}
QLabel#Sub {{ color: {MUTED}; font-size: 11px; }}

QPushButton {{
    background: {PRIMARY};
    border: none; border-radius: 8px;
    padding: 8px 14px; font-weight: 600;
}}
QPushButton:hover {{ background: #2f6fe0; }}
QPushButton:disabled {{ background: #24406e; color: {MUTED}; }}
QPushButton#Ghost {{ background: transparent; border: 1px solid {BORDER}; }}
QPushButton#Ghost:hover {{ background: {BORDER}; }}

QComboBox, QLineEdit {{
    background: {BG}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 6px 10px;
}}
QComboBox QAbstractItemView {{
    background: {CARD}; border: 1px solid {BORDER}; selection-background-color: {PRIMARY};
}}
QCheckBox {{ spacing: 8px; }}

QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {PRIMARY}; width: 14px; margin: -6px 0; border-radius: 7px;
}}

QTableWidget {{
    background: {CARD}; border: none; gridline-color: {BORDER};
    selection-background-color: #1c2c4d;
}}
QHeaderView::section {{
    background: {CARD}; color: {MUTED}; border: none;
    border-bottom: 1px solid {BORDER}; padding: 6px; font-weight: 600;
}}
QScrollBar:vertical {{ background: {BG}; width: 10px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; }}
"""
