"""
Haseen Kids - shared kid-friendly theme.

One palette for every window (child app, parent panel, setup wizard) so the
program feels like a single playful, friendly product. Bright colours, big clear
type, soft rounded corners, and readable hover/tooltip popups that explain every
control in plain Arabic.
"""

# --- Palette ---------------------------------------------------------------
VIOLET = "#7C5CFF"
VIOLET_DARK = "#6244E8"
PINK = "#FF6B9D"
TEAL = "#22C1A8"
YELLOW = "#FFD166"
ORANGE = "#FF9F1C"
SKY = "#3AB7F5"

BG_A = "#F4F1FF"
BG_B = "#E9F7FF"
CARD = "#FFFFFF"
INK = "#2B2350"
MUTED = "#6B6390"
LINE = "#E6E0FF"
DANGER = "#FF5C7A"
# Darker shades for gradients / hover states
TEAL_DARK = "#17A991"
RED = "#FF5C7A"
RED_DARK = "#E8455F"

# Emoji fonts are listed explicitly: Qt does not always fall back to them, and a
# missing fallback turns every emoji into a "tofu" box.
FONT_STACK = ("'IBM Plex Sans Arabic', 'Segoe UI', 'Segoe UI Emoji', "
              "'Segoe UI Symbol', Tahoma, Arial, sans-serif")

# Emoji mascots used across the UI (no image assets needed)
MASCOT = "🦉"


def build_stylesheet(scale=1.0):
    """Returns the full QSS for the whole app."""
    f = lambda px: f"{int(px * scale)}px"
    return f"""
/* ---------- Base ---------- */
QWidget {{
    font-family: {FONT_STACK};
    font-size: {f(15)};
    color: {INK};
}}
QMainWindow, QDialog, QWizard, QWizardPage {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {BG_A}, stop:1 {BG_B});
}}
QLabel {{ background: transparent; }}
QLabel#title {{ font-size: {f(26)}; font-weight: 800; color: {VIOLET}; }}
QLabel#subtitle {{ font-size: {f(14)}; color: {MUTED}; }}
QLabel#hint {{ font-size: {f(13)}; color: {MUTED}; }}
QLabel#ok {{ color: {TEAL}; font-weight: 700; }}
QLabel#bad {{ color: {DANGER}; font-weight: 700; }}

/* ---------- Cards ---------- */
QGroupBox {{
    background: {CARD};
    border: 2px solid {LINE};
    border-radius: {f(20)};
    margin-top: {f(22)};
    padding: {f(20)} {f(18)} {f(16)} {f(18)};
    font-weight: 700;
    font-size: {f(16)};
    color: {VIOLET};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top right;
    right: {f(18)};
    padding: 0 {f(8)};
    background: transparent;
}}

/* ---------- Tabs as playful pills ---------- */
QTabWidget::pane {{
    border: 2px solid {LINE};
    border-radius: {f(18)};
    background: {CARD};
    top: -2px;
}}
QTabBar::tab {{
    background: #EDE9FF;
    color: {MUTED};
    padding: {f(11)} {f(20)};
    margin-right: {f(6)};
    border-radius: {f(14)};
    font-weight: 700;
    font-size: {f(14)};
}}
QTabBar::tab:selected {{
    background: {VIOLET};
    color: #FFFFFF;
}}
QTabBar::tab:hover:!selected {{ background: #E1DBFF; color: {VIOLET}; }}

/* ---------- Buttons ---------- */
QPushButton {{
    background: {VIOLET};
    color: #FFFFFF;
    border: none;
    border-radius: {f(14)};
    padding: {f(12)} {f(22)};
    font-weight: 700;
    font-size: {f(15)};
}}
/* Semantic buttons: green = allow/confirm, red = deny/delete. Kids and
   parents read the colour before the words. */
QPushButton#btnSuccess {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {TEAL}, stop:1 {TEAL_DARK});
    border: none; color: #FFFFFF;
}}
QPushButton#btnSuccess:hover {{ background: {TEAL_DARK}; }}

QPushButton#btnDanger {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {RED}, stop:1 {RED_DARK});
    border: none; color: #FFFFFF;
}}
QPushButton#btnDanger:hover {{ background: {RED_DARK}; }}

QPushButton:hover {{ background: {VIOLET_DARK}; }}
QPushButton:pressed {{ background: #5334CC; }}
QPushButton:disabled {{ background: #CFC8EC; color: #F3F1FA; }}
QPushButton#actionBtn {{ background: {TEAL}; }}
QPushButton#actionBtn:hover {{ background: #17A791; }}
QPushButton#dangerBtn {{ background: {DANGER}; }}
QPushButton#dangerBtn:hover {{ background: #E44560; }}
QPushButton#ghostBtn {{
    background: #F0ECFF; color: {VIOLET};
}}
QPushButton#ghostBtn:hover {{ background: #E4DDFF; }}
QPushButton#bigBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {VIOLET}, stop:1 {PINK});
    padding: {f(16)} {f(26)};
    font-size: {f(17)};
    border-radius: {f(18)};
}}

/* ---------- Inputs ---------- */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QTimeEdit, QSpinBox, QDateEdit {{
    background: #FBFAFF;
    border: 2px solid {LINE};
    border-radius: {f(14)};
    padding: {f(10)} {f(14)};
    color: {INK};
    font-size: {f(15)};
    selection-background-color: {VIOLET};
    selection-color: #FFFFFF;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QTimeEdit:focus {{
    border: 2px solid {VIOLET};
    background: #FFFFFF;
}}
QLineEdit:disabled {{ background: #F2F0FA; color: #A9A2C4; }}
QComboBox::drop-down {{ border: none; width: {f(26)}; }}
QComboBox QAbstractItemView {{
    background: #FFFFFF; border: 2px solid {LINE}; border-radius: {f(12)};
    selection-background-color: {VIOLET}; selection-color: #FFFFFF; padding: {f(4)};
}}

/* ---------- Checkboxes / Radio ---------- */
QCheckBox, QRadioButton {{ spacing: {f(10)}; font-size: {f(15)}; color: {INK}; }}
/* Keep the native Windows tick mark: it is instantly recognisable for both
   children and parents, unlike a flat coloured square. */
QCheckBox::indicator, QRadioButton::indicator {{ width: {f(19)}; height: {f(19)}; }}

/* ---------- Progress ---------- */
QProgressBar {{
    border: 2px solid {LINE};
    border-radius: {f(13)};
    text-align: center;
    background: #F5F2FF;
    color: {INK};
    font-weight: 800;
    font-size: {f(13)};
    min-height: {f(26)};
}}
QProgressBar::chunk {{
    border-radius: {f(11)};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {TEAL}, stop:0.6 {SKY}, stop:1 {VIOLET});
}}

/* ---------- Tables ---------- */
QTableWidget, QTableWidget QTableCornerButton::section {{
    background: #FFFFFF;
    border: 2px solid {LINE};
    border-radius: {f(14)};
    gridline-color: #F0EDFF;
    color: {INK};
    font-size: {f(14)};
    alternate-background-color: #FBFAFF;
}}
QHeaderView::section {{
    background: #EFEBFF;
    color: {VIOLET};
    padding: {f(9)};
    border: none;
    border-bottom: 2px solid {LINE};
    font-weight: 800;
    font-size: {f(14)};
}}
QTableWidget::item:selected {{ background: #E6E0FF; color: {INK}; }}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {{ background: transparent; width: {f(12)}; margin: 0; }}
QScrollBar::handle:vertical {{ background: #D8D1F5; border-radius: {f(6)}; min-height: {f(30)}; }}
QScrollBar::handle:vertical:hover {{ background: {VIOLET}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: {f(12)}; }}
QScrollBar::handle:horizontal {{ background: #D8D1F5; border-radius: {f(6)}; min-width: {f(30)}; }}

/* ---------- Explanatory popups (tooltips) ---------- */
QToolTip {{
    background: #2B2350;
    color: #FFFFFF;
    border: 2px solid {VIOLET};
    border-radius: {f(12)};
    padding: {f(9)} {f(12)};
    font-family: {FONT_STACK};
    font-size: {f(14)};
    opacity: 240;
}}
QMessageBox {{ background: {CARD}; }}
QMenu {{
    background: #FFFFFF; border: 2px solid {LINE}; border-radius: {f(12)};
    padding: {f(6)};
}}
QMenu::item {{ padding: {f(9)} {f(20)}; border-radius: {f(9)}; font-size: {f(14)}; }}
QMenu::item:selected {{ background: #EFEBFF; color: {VIOLET}; }}
"""


STYLESHEET = build_stylesheet()


# --- Tooltip helper --------------------------------------------------------
def tip(widget, text, fmt="html"):
    """Attaches an explanatory popup to any widget ('comment popup')."""
    if fmt == "html":
        widget.setToolTip(
            f"<div style='font-family:{FONT_STACK}; font-size:13px; line-height:1.7;'>"
            f"<b style='color:{VIOLET};'>{MASCOT} شرح الخيار</b><br>{text}</div>"
        )
    else:
        widget.setToolTip(text)
    return widget


def apply(app_or_widget):
    """Applies the shared stylesheet to a QApplication or a widget."""
    app_or_widget.setStyleSheet(STYLESHEET)
