import sys
import os
import threading
import asyncio
import ctypes
from datetime import datetime

# Enable custom taskbar icon in Windows 7 / 10 / 11
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("saip.haseen.kids.v1")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QTabWidget,
    QProgressBar, QSpinBox, QTimeEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QFormLayout, QComboBox,
    QCheckBox, QGroupBox, QStackedWidget, QSystemTrayIcon, QMenu,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont, QIcon, QPixmap, QFontDatabase

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from core.security import SecurityManager
from youtube.engine import YouTubeEngine
from core.approvals import ApprovalManager
from core.updater import SecureGitHubUpdater
from core.reports import WeeklyReportGenerator

# Child-friendly shared theme (colours, rounding, fonts, tooltips)
from ui.theme import STYLESHEET as STYLE_SHEET_DARK, tip as add_tip


class ResetPasswordDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.security = SecurityManager(self.db)
        self.approvals = ApprovalManager(self.db)
        self.setWindowTitle("استرجاع كلمة مرور ولي الأمر 🛡️")
        self.setFixedSize(430, 380)
        self.setStyleSheet(STYLE_SHEET_DARK)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout(self)
        title = QLabel("إعادة تعيين كلمة المرور عبر البريد:")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #7C5CFF;")
        layout.addWidget(title)

        parent_email = self.db.get_setting("parent_email", "")
        if parent_email:
            # Mask email e.g. o***@gmail.com
            parts = parent_email.split("@")
            masked = parts[0][0] + "***@" + parts[1] if len(parts) == 2 else parent_email
            lbl_info = QLabel(f"سيتم إرسال رمز تحقق مؤقت (OTP) إلى بريدك المسجل:\n<b>{masked}</b>")
        else:
            lbl_info = QLabel("لم يتم تسجيل بريد إلكتروني لولي الأمر في الإعدادات مسبقاً.")
            lbl_info.setStyleSheet("color: #FF5C7A;")
        lbl_info.setStyleSheet("color: #2B2350; line-height: 1.4;")
        layout.addWidget(lbl_info)

        self.btn_send_otp = QPushButton("📨 إرسال رمز التحقق إلى بريدي الآن")
        self.btn_send_otp.setStyleSheet("background-color: #7C5CFF; color: white; padding: 8px; border-radius: 6px; font-weight: bold;")
        self.btn_send_otp.clicked.connect(self.send_otp)
        layout.addWidget(self.btn_send_otp)

        self.in_otp = QLineEdit()
        self.in_otp.setPlaceholderText("أدخل رمز التحقق (6 أرقام)")
        self.in_otp.setMaxLength(6)

        self.in_new_p1 = QLineEdit()
        self.in_new_p1.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_new_p1.setPlaceholderText("كلمة المرور الجديدة")

        self.in_new_p2 = QLineEdit()
        self.in_new_p2.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_new_p2.setPlaceholderText("تأكيد كلمة المرور الجديدة")

        self.chk_show = QCheckBox("👁️ إظهار كلمة المرور للتأكد")
        self.chk_show.setStyleSheet("color: #7C5CFF;")
        self.chk_show.toggled.connect(self.toggle_show)

        layout.addWidget(self.in_otp)
        layout.addWidget(self.in_new_p1)
        layout.addWidget(self.in_new_p2)
        layout.addWidget(self.chk_show)

        btn_box = QHBoxLayout()
        self.btn_confirm = QPushButton("تأكيد وتغيير كلمة المرور ✅")
        self.btn_confirm.setObjectName("actionBtn")
        self.btn_confirm.clicked.connect(self.confirm_reset)
        btn_close = QPushButton("إلغاء ❌")
        btn_close.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_confirm)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def toggle_show(self, checked):
        m = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.in_new_p1.setEchoMode(m)
        self.in_new_p2.setEchoMode(m)

    def send_otp(self):
        parent_email = self.db.get_setting("parent_email", "")
        if not parent_email:
            QMessageBox.warning(self, "خطأ", "لا يوجد بريد مسجل لولي الأمر في البرنامج.\nيرجى التواصل مع مسؤول الجهاز.")
            return

        otp = self.security.generate_reset_otp()
        self.btn_send_otp.setEnabled(False)
        self.btn_send_otp.setText("جاري إرسال الرمز للبريد... ⏳")
        QApplication.processEvents()

        ok, msg = self.approvals.send_password_reset_email(parent_email, otp)
        self.btn_send_otp.setEnabled(True)
        self.btn_send_otp.setText("إعادة إرسال رمز التحقق 🔄")
        if ok:
            QMessageBox.information(self, "تم الإرسال", f"{msg}\nيرجى مراجعة صندوق الوارد والبريد غير الهام (Spam).")
        else:
            QMessageBox.critical(self, "فشل الإرسال", f"{msg}\nتأكد من اتصال الإنترنت وصحة إعدادات SMTP.")

    def confirm_reset(self):
        otp = self.in_otp.text().strip()
        p1 = self.in_new_p1.text().strip()
        p2 = self.in_new_p2.text().strip()

        if not otp:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال رمز التحقق المرسل إلى بريدك.")
            return

        ok, msg = self.security.verify_reset_otp(otp)
        if not ok:
            QMessageBox.warning(self, "رمز غير صحيح", msg)
            return

        if len(p1) < 4:
            QMessageBox.warning(self, "تنبيه", "يجب أن تكون كلمة المرور 4 أحرف أو أرقام على الأقل.")
            return

        if p1 != p2:
            QMessageBox.warning(self, "عدم تطابق", "كلمتا المرور غير متطابقتين! يرجى إعادة التحقق.")
            return

        self.security.set_admin_password(p1)
        self.security.clear_reset_otp()
        QMessageBox.information(self, "تم النجاح", "تم تعيين كلمة مرور جديدة بنجاح! سيتم فتح لوحة التحكم الآن ✅")
        self.accept()

class PasswordDialog(QDialog):
    def __init__(self, db=None, parent=None, title=None, prompt=None):
        super().__init__(parent)
        self.db = db or DBManager()
        self.setWindowTitle(title or "دخول لوحة التحكم الأبوية | Parent Login")
        self.setFixedSize(380, 240)
        self.setStyleSheet(STYLE_SHEET_DARK)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout(self)
        lbl = QLabel(prompt or "أدخل كلمة مرور ولي الأمر للوصول للإعدادات:")
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #7C5CFF;")
        layout.addWidget(lbl)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("كلمة المرور")
        layout.addWidget(self.pwd_input)

        self.chk_show = QCheckBox("👁️ إظهار كلمة المرور للتأكد")
        self.chk_show.setStyleSheet("color: #6B6390;")
        self.chk_show.toggled.connect(lambda c: self.pwd_input.setEchoMode(QLineEdit.EchoMode.Normal if c else QLineEdit.EchoMode.Password))
        layout.addWidget(self.chk_show)

        self.btn_forgot = QPushButton("🔗 نسيت كلمة المرور؟ (استرجاع عبر البريد)")
        self.btn_forgot.setStyleSheet("color: #7C5CFF; background: none; border: none; text-align: right; text-decoration: underline; font-size: 12px;")
        self.btn_forgot.clicked.connect(self.open_password_reset)
        layout.addWidget(self.btn_forgot)

        btn_box = QHBoxLayout()
        self.login_btn = QPushButton("دخول ✅")
        self.login_btn.setObjectName("actionBtn")
        self.login_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("إلغاء ❌")
        self.cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(self.login_btn)
        btn_box.addWidget(self.cancel_btn)
        layout.addLayout(btn_box)

    def open_password_reset(self):
        dlg = ResetPasswordDialog(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.reset_successful = True
            self.accept()

    def get_password(self):
        return self.pwd_input.text().strip()

class HaseenMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("حَصِين للأطفال | Haseen Kids - الحماية الأسرية الذكية")
        self.resize(1000, 700)
        self.setStyleSheet(STYLE_SHEET_DARK)
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.db = DBManager()
        self.security = SecurityManager(self.db)
        self.youtube = YouTubeEngine()
        self.approvals = ApprovalManager(self.db)
        self.updater = SecureGitHubUpdater()

        self.current_lang = self.db.get_setting("language", "ar")
        self.apply_layout_direction()

        self._force_exit = False
        # These must exist before init_ui(): it renders the gauges once.
        self._gauges_busy = False
        self._gauges_last = None
        self.init_ui()
        self.setup_system_tray()

        # Ensure proxy and tracker are active even if service daemon was not started separately
        self._ensure_embedded_services()

        # Update timer for live counters.
        # 5s (not 3s) and never re-entrant: a slow query used to queue timers
        # up and starve the event loop -- the window looked frozen.
        # Freeze watchdog: the child window owns the heartbeat; if the GUI
        # thread stops answering for 8s we dump every stack to
        # logs/haseen_freeze.log so the hang can be diagnosed instead of guessed.
        try:
            from core.crashguard import install_freeze_watchdog, beat
            install_freeze_watchdog(threshold=8.0)
            self._beat_timer = QTimer(self)
            self._beat_timer.timeout.connect(beat)
            self._beat_timer.start(1000)
        except Exception:
            pass

        self._gauges_busy = False
        self._gauges_last = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick_gauges)
        self.timer.start(5000)

    def _ensure_embedded_services(self):
        import time
        # Short timeout: a bare connect_ex() to a filtered port blocks the GUI
        # thread for ~2s on Windows (measured), which delays the first paint.
        from core.uiutils import port_is_open
        if not port_is_open("127.0.0.1", 8089, timeout=0.3):
            from proxy.local_proxy import LocalProxyServer
            def run_proxy():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    srv = LocalProxyServer(port=8089)
                    loop.run_until_complete(srv.start())
                except Exception:
                    pass
            t = threading.Thread(target=run_proxy, daemon=True)
            t.start()

        from core.tracker import ActiveWindowTracker
        def run_tracker():
            tracker = ActiveWindowTracker(self.db, poll_interval=3)
            while True:
                try:
                    tracker.tick()
                    time.sleep(3)
                except Exception:
                    time.sleep(3)
        t_tr = threading.Thread(target=run_tracker, daemon=True)
        t_tr.start()

        # Passive biweekly update check (1-second query once every 14 days, zero continuous overhead)
        def run_update_check():
            try:
                self.updater.check_biweekly_background_update(callback_on_update=self.on_biweekly_update_found)
            except Exception:
                pass
        threading.Thread(target=run_update_check, daemon=True).start()

    def on_biweekly_update_found(self, new_ver):
        print(f"[Haseen Updater] New release available on GitHub: v{new_ver}")

    def apply_layout_direction(self):
        if self.current_lang == "ar":
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

    def keyPressEvent(self, event):
        """Ctrl+Shift+F12 = write a diagnostic report (useful when it feels stuck)."""
        try:
            mods = event.modifiers()
            if (event.key() == Qt.Key.Key_F12
                    and mods & Qt.KeyboardModifier.ControlModifier
                    and mods & Qt.KeyboardModifier.ShiftModifier):
                from core.crashguard import dump_all_stacks
                path = dump_all_stacks("requested by Ctrl+Shift+F12")
                QMessageBox.information(self, "تقرير التشخيص",
                                        "تم حفظ تقرير التشخيص في:" + chr(10) + path)
                return
        except Exception:
            pass
        super().keyPressEvent(event)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Top Bar
        top_bar = QHBoxLayout()
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            lbl_icon = QLabel()
            pix = QPixmap(icon_path).scaled(46, 46, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_icon.setPixmap(pix)
            top_bar.addWidget(lbl_icon)

        title_box = QVBoxLayout()
        self.lbl_title = QLabel("حَصِين للأطفال | Haseen Kids")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #7C5CFF;")
        self.lbl_sub = QLabel("حماية تصفح ذكية • مشغل يوتيوب معزول بدون إعلانات • إدارة الوقت")
        self.lbl_sub.setStyleSheet("font-size: 13px; color: #6B6390;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_sub)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.lang_btn = QPushButton("🌐 English / عربي")
        self.lang_btn.clicked.connect(self.toggle_language)
        add_tip(self.lang_btn, "تغيير لغة واجهة البرنامج بين العربية والإنجليزية.")
        # Pause control next to the language switch: the same action as the
        # tray icon, so a parent finds it without knowing about right-click.
        self.btn_pause = QPushButton("⏸️ إيقاف مؤقت")
        self.btn_pause.clicked.connect(self.open_pause_chooser)
        add_tip(self.btn_pause,
                "يوقف الحجب والجدول مؤقتاً لمدة تختارها بكلمة مرور ولي الأمر، "
                "ثم يعود كل شيء تلقائياً.")
        top_bar.addWidget(self.btn_pause)

        top_bar.addWidget(self.lang_btn)

        self.admin_btn = QPushButton("⚙️ لوحة ولي الأمر")
        self.admin_btn.setObjectName("actionBtn")
        self.admin_btn.clicked.connect(self.open_parent_panel)
        add_tip(self.admin_btn, "تفتح لوحة التحكم الكاملة (المواقع، الوقت، التقارير، التحديث).<br>"
                               "محمية بكلمة مرور ولي الأمر حتى لا يدخلها الطفل.")
        top_bar.addWidget(self.admin_btn)

        main_layout.addLayout(top_bar)

        # Main Navigation Tabs
        self.tabs = QTabWidget()
        self.tab_child = QWidget()
        self.tab_youtube = QWidget()
        self.tab_requests = QWidget()

        self.setup_child_tab()
        self.setup_youtube_tab()
        self.setup_requests_tab()

        self.tabs.addTab(self.tab_child, "📊 رصيد الوقت والنشاط")
        self.tabs.addTab(self.tab_youtube, "🎬 يوتيوب النظيف (بدون إعلانات)")
        self.tabs.addTab(self.tab_requests, "✉️ طلب استثناء / تفعيل رمز")

        main_layout.addWidget(self.tabs)

        self.refresh_usage_gauges()

    # --- Child Dashboard Tab ---
    def setup_child_tab(self):
        # Everything lives inside a scroll area: on a small screen the parent
        # no longer has to maximise the window to reach the lower buttons, and
        # a resize never has to squeeze the cards below their readable size.
        outer = QVBoxLayout(self.tab_child)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(18)
        layout.setContentsMargins(18, 18, 18, 18)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # Hero greeting card - gives the dashboard a friendly face
        hero = QGroupBox()
        hero.setStyleSheet(
            "QGroupBox { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #F4F1FF, stop:1 #E9F7FF); border:2px solid #E6E0FF;"
            "border-radius:22px; padding:16px; }"
        )
        h_hero = QHBoxLayout(hero)
        mascot = QLabel("🦉")
        mascot.setStyleSheet("font-size:52px;")
        h_hero.addWidget(mascot)
        h_hero_txt = QVBoxLayout()
        self.lbl_hero = QLabel("أهلاً يا بطل! 👋")
        self.lbl_hero.setStyleSheet("font-size:22px; font-weight:800; color:#7C5CFF;")
        self.lbl_hero_sub = QLabel("حَصِين يحميك وأنت تتعلم وتلعب بأمان — اختر ما تريد فعله اليوم.")
        self.lbl_hero_sub.setStyleSheet("font-size:14px; color:#6B6390;")
        h_hero_txt.addWidget(self.lbl_hero)
        h_hero_txt.addWidget(self.lbl_hero_sub)
        h_hero.addLayout(h_hero_txt)
        h_hero.addStretch()
        layout.addWidget(hero)

        # Big friendly action tiles
        tiles = QHBoxLayout()
        tiles.setSpacing(14)

        def tile(icon, title, subtitle, color, on_click, tip_text):
            card = QGroupBox()
            card.setStyleSheet(
                f"QGroupBox {{ background:{color}; border:none; border-radius:20px; padding:18px; }}"
            )
            v = QVBoxLayout(card)
            v.setSpacing(6)
            i = QLabel(icon)
            i.setStyleSheet("font-size:38px; background:transparent;")
            t = QLabel(title)
            t.setStyleSheet("font-size:17px; font-weight:800; color:#FFFFFF; background:transparent;")
            st = QLabel(subtitle)
            st.setWordWrap(True)
            st.setStyleSheet("font-size:13px; color:rgba(255,255,255,0.92); background:transparent;")
            b = QPushButton("ابدأ الآن")
            b.setStyleSheet("background:rgba(255,255,255,0.22); color:#FFFFFF; border-radius:12px; padding:9px;")
            b.clicked.connect(on_click)
            v.addWidget(i)
            v.addWidget(t)
            v.addWidget(st)
            v.addWidget(b)
            add_tip(card, tip_text)
            return card

        tiles.addWidget(tile("🎬", "فيديو نظيف", "شاهد أي فيديو بدون إعلانات",
                             "#7C5CFF", lambda: self.tabs.setCurrentIndex(1),
                             "يفتح تبويب يوتيوب النظيف: تلصق الرابط فيعمل بدون إعلانات ولا مقترحات."))
        tiles.addWidget(tile("📊", "رصيدي اليوم", "اعرف كم بقي من وقتك",
                             "#22C1A8", lambda: self.tabs.setCurrentIndex(0),
                             "يرجعك لمؤشرات الوقت: كم استهلكت وكم بقي لك اليوم."))
        tiles.addWidget(tile("✉️", "اطلب موقعاً", "أرسل طلباً لوالدك بضغطة",
                             "#FF6B9D", lambda: self.tabs.setCurrentIndex(2),
                             "لو احتجت موقعاً محجوباً لدرسك، اطلبه من هنا وسيصل لوالدك."))
        layout.addLayout(tiles)

        # Time gauges
        grp_time = QGroupBox("مؤشرات الوقت المتبقي لليوم:")
        v_time = QVBoxLayout(grp_time)

        # Entertainment
        self.lbl_ent = QLabel("🎮 وقت الترفيه والألعاب:")
        self.bar_ent = QProgressBar()
        self.bar_ent.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        add_tip(self.bar_ent, "الشريط يوضح كم استهلكت من وقت الألعاب والترفيه اليوم.<br>"
                              "عندما يكتمل الشريط تتوقف الألعاب حتى الغد (أو حتى يزيدها والدك).")
        v_time.addWidget(self.lbl_ent)
        v_time.addWidget(self.bar_ent)

        # General Browsing
        self.lbl_gen = QLabel("🌐 وقت التصفح العام:")
        self.bar_gen = QProgressBar()
        self.bar_gen.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        add_tip(self.bar_gen, "وقت التصفح العادي للمواقع المسموحة.<br>"
                              "منصات المدرسة والتعليم لا تُحسب من هذا الوقت إطلاقاً.")
        v_time.addWidget(self.lbl_gen)
        v_time.addWidget(self.bar_gen)

        # School Platforms Status
        lbl_sch = QLabel("📚 منصات المدرسة والتعليم (مدرستي، بنك المعرفة، خان أكاديمي): مفتوحة دائماً بلا حدود ✅")
        lbl_sch.setStyleSheet("color: #22C1A8; font-weight: bold; margin-top: 8px;")
        v_time.addWidget(lbl_sch)

        layout.addWidget(grp_time)

        # Safe Tips
        grp_tips = QGroupBox("إرشادات أمان للأبطال:")
        v_tips = QVBoxLayout(grp_tips)
        tips_text = (
            "• استمتع بوقتك في التعلم والاستكشاف المفيد.<br>"
            "• إذا صادفت موقعاً محجوباً تحتاجه لدراستك، يمكنك إرسال طلب لوالدك بضغطة زر.<br>"
            "• عند اقتراب وقت النوم، سيتم إغلاق التصفح تلقائياً لمساعدتك على أخذ قسط كافٍ من النوم."
        )
        lbl_tips = QLabel(tips_text)
        lbl_tips.setTextFormat(Qt.TextFormat.RichText)
        lbl_tips.setStyleSheet("line-height: 1.6; color: #2B2350;")
        v_tips.addWidget(lbl_tips)
        from PyQt6.QtWidgets import QSizePolicy
        grp_tips.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout.addWidget(grp_tips)

        layout.addStretch()

    # --- YouTube Clean Tab ---
    def setup_youtube_tab(self):
        layout = QVBoxLayout(self.tab_youtube)
        layout.setSpacing(14)

        info_lbl = QLabel("مشغل يوتيوب النظيف: تشغيل فوري بدون أي إعلانات وبدون سحب الصفحة الثقيلة")
        info_lbl.setStyleSheet("color: #7C5CFF; font-weight: bold;")
        layout.addWidget(info_lbl)

        h_search = QHBoxLayout()
        self.yt_input = QLineEdit()
        self.yt_input.setPlaceholderText("الصق رابط الفيديو من يوتيوب (مثال: https://www.youtube.com/watch?v=...)")
        add_tip(self.yt_input, "الصق رابط أي فيديو من يوتيوب هنا.<br>"
                               "سيُفتح في مشغل حَصِين النظيف: بدون إعلانات وبدون تعليقات ولا فيديوهات مقترحة.")
        self.yt_play_btn = QPushButton("تشغيل الفيديو فوراً 🎬")
        self.yt_play_btn.setObjectName("actionBtn")
        self.yt_play_btn.clicked.connect(self.play_clean_youtube)
        add_tip(self.yt_play_btn, "يبدأ تشغيل الفيديو فوراً في المشغل النظيف المعزول.")

        h_search.addWidget(self.yt_input)
        h_search.addWidget(self.yt_play_btn)
        layout.addLayout(h_search)

        self.yt_status = QLabel("جاهز للتشغيل")
        self.yt_status.setStyleSheet("color: #6B6390;")
        layout.addWidget(self.yt_status)

        # Safe Recommendations list
        grp_rec = QGroupBox("قنوات ومقاطع مقترحة مفيدة:")
        v_rec = QVBoxLayout(grp_rec)

        samples = [
            ("حيوانات صديقة على غير العادة (National Geographic)", "https://www.youtube.com/watch?v=wi_ig8NYTvY"),
            ("عوالم الجليد القطبيّة - الكوكب المعادي (National Geographic)", "https://www.youtube.com/watch?v=TqcrhAljNDI"),
            ("ناشونال جيوغرافيك كيدز - المساهمون الصغار", "https://www.youtube.com/watch?v=yiC-MPRffVY")
        ]

        for title, link in samples:
            h_row = QHBoxLayout()
            l = QLabel(title)
            btn = QPushButton("تشغيل ▶")
            btn.setFixedWidth(100)
            btn.clicked.connect(lambda ch, u=link: self.play_url(u))
            h_row.addWidget(l)
            h_row.addWidget(btn)
            v_rec.addLayout(h_row)

        layout.addWidget(grp_rec)
        layout.addStretch()

    # --- Requests Tab ---
    def setup_requests_tab(self):
        layout = QVBoxLayout(self.tab_requests)

        grp_req = QGroupBox("إرسال طلب استثناء لموقع محجوب:")
        f_req = QFormLayout(grp_req)
        self.req_domain = QLineEdit()
        self.req_domain.setPlaceholderText("اسم الموقع أو الرابط (مثال: example.com)")
        self.req_reason = QTextEdit()
        self.req_reason.setPlaceholderText("اكتب سبب رغبتك في فتح الموقع...")
        self.req_reason.setFixedHeight(70)

        self.req_btn = QPushButton("إرسال الطلب لوالدي 📧")
        self.req_btn.clicked.connect(self.submit_child_request)

        f_req.addRow("الموقع المطلوب:", self.req_domain)
        f_req.addRow("السبب:", self.req_reason)
        f_req.addRow("", self.req_btn)
        layout.addWidget(grp_req)

        grp_code = QGroupBox("تفعيل رمز الموافقة المستلم من ولي الأمر:")
        f_code = QFormLayout(grp_code)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("أدخل رمز الموافقة (مثال: 102948)")
        self.code_btn = QPushButton("تأكيد وفتح الموقع ✅")
        self.code_btn.setObjectName("actionBtn")
        self.code_btn.clicked.connect(self.submit_approval_code)

        f_code.addRow("رمز الموافقة:", self.code_input)
        f_code.addRow("", self.code_btn)
        layout.addWidget(grp_code)

        layout.addStretch()

    # --- Action Handlers ---
    def _tick_gauges(self):
        """Timer slot: keep the GUI thread free and skip useless repaints."""
        if self._gauges_busy:
            return
        self._gauges_busy = True
        try:
            self.refresh_usage_gauges()
        finally:
            self._gauges_busy = False

    def refresh_usage_gauges(self):
        today_usage = self.db.get_today_usage()
        today_sched = self.db.get_today_schedule()

        ent_limit = today_sched["entertainment_limit_mins"] * 60
        gen_limit = today_sched["general_limit_mins"] * 60

        ent_used = today_usage["entertainment_seconds"]
        gen_used = today_usage["general_seconds"]

        ent_rem_min = max(0, (ent_limit - ent_used) // 60)
        gen_rem_min = max(0, (gen_limit - gen_used) // 60)

        ent_text = f"🎮 وقت الترفيه والألعاب: متبقي {ent_rem_min} دقيقة (من أصل {today_sched['entertainment_limit_mins']} دقيقة)"
        if self._gauges_last != ent_text:
            self.lbl_ent.setText(ent_text)
        pct_ent = min(100, int((ent_used / ent_limit) * 100)) if ent_limit > 0 else 100
        self.bar_ent.setValue(100 - pct_ent)

        gen_text = f"🌐 وقت التصفح العام: متبقي {gen_rem_min} دقيقة (من أصل {today_sched['general_limit_mins']} دقيقة)"
        if self._gauges_last != (ent_text, gen_text):
            self.lbl_gen.setText(gen_text)
            self._gauges_last = (ent_text, gen_text)
        pct_gen = min(100, int((gen_used / gen_limit) * 100)) if gen_limit > 0 else 100
        self.bar_gen.setValue(100 - pct_gen)

    def play_clean_youtube(self):
        url = self.yt_input.text().strip()
        if not url:
            QMessageBox.warning(self, "تنبيه", "يرجى لصق رابط فيديو يوتيوب أولاً")
            return
        self.play_url(url)

    def play_url(self, url):
        self.yt_status.setText("جاري استخراج البث بدون إعلانات وتشغيل المشغل...")
        QApplication.processEvents()
        ok, msg = self.youtube.play_video(url)
        if ok:
            self.yt_status.setText(f"تم التشغيل بنجاح ✅ ({msg})")
        else:
            self.yt_status.setText(f"تعذر التشغيل: {msg}")
            QMessageBox.critical(self, "خطأ في التشغيل", msg)

    def submit_child_request(self):
        domain = self.req_domain.text().strip()
        reason = self.req_reason.toPlainText().strip()
        if not domain or not reason:
            QMessageBox.warning(self, "بيانات ناقصة", "يرجى إدخال اسم الموقع وسبب الطلب")
            return
        success, msg, perm_code, temp_code = self.approvals.create_and_send_request(domain, f"https://{domain}", reason)
        QMessageBox.information(self, "طلب استثناء", msg)
        self.req_domain.clear()
        self.req_reason.clear()

    def submit_approval_code(self):
        code = self.code_input.text().strip()
        if not code:
            return
        success, msg, typ, domain = self.db.verify_and_apply_code(code)
        if success:
            QMessageBox.information(self, "نجاح التفعيل", msg)
            self.code_input.clear()
        else:
            QMessageBox.critical(self, "خطأ", msg)

    def toggle_language(self):
        self.current_lang = "en" if self.current_lang == "ar" else "ar"
        self.db.set_setting("language", self.current_lang)
        self.apply_layout_direction()
        QMessageBox.information(self, "اللغة / Language", "يرجى إعادة تشغيل الواجهة لتطبيق التغيير الكامل للغة")

    def setup_system_tray(self):
        """Configures System Tray icon beside the Windows clock."""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setToolTip("حَصِين للأطفال | نظام الحماية الأسرية نشط 🛡️")

        tray_menu = QMenu()
        tray_menu.setStyleSheet("QMenu { background-color: #FFFFFF; color: #2B2350; font-family: 'IBM Plex Sans Arabic', sans-serif; font-size: 13px; } QMenu::item:selected { background-color: #2563eb; }")

        act_show = tray_menu.addAction("عرض الواجهة الرئيسية 🛡️")
        act_show.triggered.connect(self.show_main_window)

        act_admin = tray_menu.addAction("لوحة تحكم ولي الأمر ⚙️")
        act_admin.triggered.connect(self.open_parent_panel)

        tray_menu.addSeparator()

        # --- Pause / resume the whole protection (parent password) ----------
        self.menu_pause = tray_menu.addMenu("⏸️ إيقاف الحماية مؤقتاً")
        self.menu_pause.setToolTip("يتوقف الحجب والجدول مؤقتاً لمدة تختارها، مع رمز ولي الأمر، ثم يرجع تلقائياً.")
        self.pause_actions = {}
        for mins, label in ((15, "15 دقيقة"), (30, "30 دقيقة"), (60, "ساعة واحدة"), (240, "4 ساعات")):
            act = self.menu_pause.addAction(f"⏸️ إيقاف لمدة {label}")
            act.triggered.connect(lambda _checked=False, m=mins: self.pause_protection(m))
            self.pause_actions[mins] = act

        self.act_resume = tray_menu.addAction("▶️ استئناف الحماية الآن")
        self.act_resume.triggered.connect(self.resume_protection)
        self.act_pause_status = tray_menu.addAction("الحالة: الحماية نشطة ✅")
        self.act_pause_status.setEnabled(False)

        tray_menu.addSeparator()

        act_exit = tray_menu.addAction("إغلاق البرنامج وإنهاء الحماية ❌")
        act_exit.triggered.connect(self.exit_app_parent_authenticated)

        self.tray_menu = tray_menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

        # Refresh the remaining time on the tray every 30 seconds
        self._tray_timer = QTimer(self)
        self._tray_timer.timeout.connect(self.refresh_pause_state)
        self._tray_timer.start(30000)
        self.refresh_pause_state()

        # Tell the parent once that the tray icon is where the controls live.
        try:
            if self.db.get_setting("tray_hint_shown") != "1":
                self.tray_icon.showMessage(
                    "حَصِين للأطفال 🛡️",
                    "الأيقونة بجوار الساعة: بالزر الأيمن يمكنك إيقاف الحماية مؤقتاً "
                    "(15/30 دقيقة، ساعة، 4 ساعات) أو إغلاق البرنامج بكلمة المرور.",
                    QSystemTrayIcon.MessageIcon.Information, 9000)
                self.db.set_setting("tray_hint_shown", "1")
        except Exception:
            pass

    # --- pause / resume ---------------------------------------------------
    @staticmethod
    def _fmt_minutes(seconds):
        mins = int(round(seconds / 60.0))
        if mins >= 60:
            h, m = divmod(mins, 60)
            return f"{h} ساعة" + (f" و{m} دقيقة" if m else "")
        return f"{mins} دقيقة"

    def refresh_pause_state(self):
        """Keeps the tray tooltip, the status line and the resume item honest."""
        try:
            left = self.db.get_pause_remaining()
        except Exception:
            left = 0
        paused = left > 0

        self.act_resume.setEnabled(paused)
        for mins, act in getattr(self, "pause_actions", {}).items():
            act.setEnabled(not paused)
        self.menu_pause.setEnabled(not paused)

        if paused:
            txt = f"⏸️ الحماية متوقفة مؤقتاً — باقٍ {self._fmt_minutes(left)}"
            self.act_pause_status.setText(txt)
            try:
                self.tray_icon.setToolTip("حَصِين للأطفال | " + txt)
            except Exception:
                pass
            if hasattr(self, "lbl_hero"):
                self.lbl_hero.setText("الحماية متوقفة مؤقتاً ⏸️")
                self.lbl_hero_sub.setText(f"ولي أمرك أوقف الحماية مؤقتاً — ستعود تلقائياً بعد {self._fmt_minutes(left)}.")
        else:
            self.act_pause_status.setText("الحالة: الحماية نشطة ✅")
            try:
                self.tray_icon.setToolTip("حَصِين للأطفال | نظام الحماية الأسرية نشط 🛡️")
            except Exception:
                pass
            if hasattr(self, "lbl_hero"):
                self.lbl_hero.setText("أهلاً يا بطل! 👋")
                self.lbl_hero_sub.setText("حَصِين يحميك وأنت تتعلم وتلعب بأمان — اختر ما تريد فعله اليوم.")

    def _ask_parent_password(self, title, prompt):
        """Shows the parent password dialog; True only when the password is right."""
        dlg = PasswordDialog(self.db, self, title=title, prompt=prompt)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return False
        pwd = dlg.get_password()
        if getattr(dlg, "reset_successful", False):
            return True
        return bool(self.security.verify_admin(pwd))

    @staticmethod
    def _pwd_dialog_accepts_titles():
        try:
            import inspect
            params = inspect.signature(PasswordDialog.__init__).parameters
            return "title" in params
        except Exception:
            return False

    def open_pause_chooser(self):
        """Small duration picker, then the parent password."""
        from PyQt6.QtWidgets import QInputDialog
        options = ["15 دقيقة", "30 دقيقة", "ساعة واحدة", "4 ساعات", "استئناف الحماية الآن"]
        current = 0 if not self.db.is_paused() else 4
        choice, ok = QInputDialog.getItem(
            self, "إيقاف الحماية مؤقتاً",
            "اختر المدة التي تريد فيها إيقاف الحماية (ستعود تلقائياً):",
            options, current, False)
        if not ok:
            return
        if choice == options[4]:
            self.resume_protection()
            return
        minutes = {0: 15, 1: 30, 2: 60, 3: 240}[options.index(choice)]
        self.pause_protection(minutes)

    def pause_protection(self, minutes):
        if not self._ask_parent_password("تأكيد إيقاف الحماية", f"أدخل كلمة مرور ولي الأمر لإيقاف الحماية مؤقتاً لمدة {minutes} دقيقة."):
            return
        self.db.set_pause(minutes)
        self.refresh_pause_state()
        self.tray_icon.showMessage(
            "حَصِين للأطفال ⏸️",
            f"تم إيقاف الحماية مؤقتاً لمدة {self._fmt_minutes(minutes * 60)}. ستعود تلقائياً."
            + chr(10) + "يمكنك الاستئناف في أي وقت من نفس القائمة.",
            QSystemTrayIcon.MessageIcon.Information, 5000)

    def resume_protection(self):
        self.db.clear_pause()
        self.refresh_pause_state()
        self.tray_icon.showMessage("حَصِين للأطفال ✅", "تم استئناف الحماية من جديد.",
                                   QSystemTrayIcon.MessageIcon.Information, 3000)

    def show_main_window(self):
        self.showNormal()
        self.activateWindow()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show_main_window()

    def closeEvent(self, event):
        """Intercepts window close: minimizes to system tray unless authenticated."""
        if self._force_exit:
            self.tray_icon.hide()
            event.accept()
        else:
            event.ignore()
            self.hide()
            if self.tray_icon.isSystemTrayAvailable():
                self.tray_icon.showMessage(
                    "حَصِين للأطفال 🛡️",
                    "البرنامج مستمر في العمل في الخلفية لحماية جهاز طفلك.\n(يمكنك الوصول إليه من أيقونات شريط المهام بجوار الساعة).",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )

    def exit_app_parent_authenticated(self):
        """Exits app only if parent password is authenticated."""
        dlg = PasswordDialog(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            pwd = dlg.get_password()
            if getattr(dlg, 'reset_successful', False) or self.security.verify_admin(pwd):
                self._force_exit = True
                self.tray_icon.hide()
                QApplication.quit()
            else:
                QMessageBox.critical(self, "ممنوع الإغلاق", "كلمة المرور غير صحيحة!\nلا يمكن إغلاق البرنامج إلا بإذن ولي الأمر.")

    def open_parent_panel(self):
        dlg = PasswordDialog(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            pwd = dlg.get_password()
            if getattr(dlg, 'reset_successful', False) or self.security.verify_admin(pwd):
                from ui.admin_panel import ParentAdminDialog
                admin = ParentAdminDialog(self)
                admin.exec()
            else:
                QMessageBox.critical(self, "خطأ", "كلمة المرور غير صحيحة!")

def setup_custom_fonts():
    font_dir = os.path.join(BASE_DIR, "assets", "fonts")
    for f in ["IBMPlexSansArabic-Regular.ttf", "IBMPlexSansArabic-Bold.ttf"]:
        fp = os.path.join(font_dir, f)
        if os.path.exists(fp):
            QFontDatabase.addApplicationFont(fp)

if __name__ == "__main__":
    # --- Never let an exception close the program -------------------------
    # Without this a single bad click aborts the whole process (PyQt calls
    # abort() on unhandled exceptions), which is exactly what a parent sees as
    # "it crashed and will not open again".
    try:
        from core.crashguard import install_exception_hooks, make_safe_application, read_last_error
        install_exception_hooks()
        AppClass = make_safe_application()
    except Exception:
        AppClass = QApplication

    app = AppClass(sys.argv)
    setup_custom_fonts()
    app.setFont(QFont("IBM Plex Sans Arabic", 11))
    app.setStyleSheet(STYLE_SHEET_DARK)   # one kid-friendly palette everywhere

    win = HaseenMainWindow()
    if "--minimized" not in sys.argv:
        win.show()
    sys.exit(app.exec())
