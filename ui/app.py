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
    QCheckBox, QGroupBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont, QIcon, QPixmap

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from core.security import SecurityManager
from youtube.engine import YouTubeEngine
from core.approvals import ApprovalManager
from core.updater import SecureGitHubUpdater
from core.reports import WeeklyReportGenerator

STYLE_SHEET_DARK = """
QMainWindow, QDialog {
    background-color: #0f172a;
    color: #f8fafc;
}
QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 14px;
}
QGroupBox {
    border: 1px solid #334155;
    border-radius: 10px;
    margin-top: 15px;
    padding-top: 15px;
    font-weight: bold;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 0 10px;
}
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 8px;
    background: #1e293b;
}
QTabBar::tab {
    background: #0f172a;
    color: #94a3b8;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #1e293b;
    color: #38bdf8;
    border-bottom: 2px solid #38bdf8;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton#actionBtn {
    background-color: #10b981;
}
QPushButton#actionBtn:hover {
    background-color: #059669;
}
QPushButton#dangerBtn {
    background-color: #e11d48;
}
QPushButton#dangerBtn:hover {
    background-color: #be123c;
}
QLineEdit, QTextEdit, QComboBox, QTimeEdit, QSpinBox {
    background-color: #0f172a;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 8px;
    color: white;
}
QProgressBar {
    border: 1px solid #334155;
    border-radius: 8px;
    text-align: center;
    background-color: #0f172a;
    color: white;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 7px;
}
QTableWidget {
    background-color: #0f172a;
    border: 1px solid #334155;
    gridline-color: #1e293b;
    color: white;
}
QHeaderView::section {
    background-color: #1e293b;
    color: #38bdf8;
    padding: 6px;
    border: 1px solid #334155;
    font-weight: bold;
}
"""

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
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(title)

        parent_email = self.db.get_setting("parent_email", "")
        if parent_email:
            # Mask email e.g. o***@gmail.com
            parts = parent_email.split("@")
            masked = parts[0][0] + "***@" + parts[1] if len(parts) == 2 else parent_email
            lbl_info = QLabel(f"سيتم إرسال رمز تحقق مؤقت (OTP) إلى بريدك المسجل:\n<b>{masked}</b>")
        else:
            lbl_info = QLabel("لم يتم تسجيل بريد إلكتروني لولي الأمر في الإعدادات مسبقاً.")
            lbl_info.setStyleSheet("color: #ef4444;")
        lbl_info.setStyleSheet("color: #cbd5e1; line-height: 1.4;")
        layout.addWidget(lbl_info)

        self.btn_send_otp = QPushButton("📨 إرسال رمز التحقق إلى بريدي الآن")
        self.btn_send_otp.setStyleSheet("background-color: #0284c7; color: white; padding: 8px; border-radius: 6px; font-weight: bold;")
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
        self.chk_show.setStyleSheet("color: #38bdf8;")
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
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db or DBManager()
        self.setWindowTitle("دخول لوحة التحكم الأبوية | Parent Login")
        self.setFixedSize(380, 240)
        self.setStyleSheet(STYLE_SHEET_DARK)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout(self)
        lbl = QLabel("أدخل كلمة مرور ولي الأمر للوصول للإعدادات:")
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(lbl)

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setPlaceholderText("كلمة المرور")
        layout.addWidget(self.pwd_input)

        self.chk_show = QCheckBox("👁️ إظهار كلمة المرور للتأكد")
        self.chk_show.setStyleSheet("color: #94a3b8;")
        self.chk_show.toggled.connect(lambda c: self.pwd_input.setEchoMode(QLineEdit.EchoMode.Normal if c else QLineEdit.EchoMode.Password))
        layout.addWidget(self.chk_show)

        self.btn_forgot = QPushButton("🔗 نسيت كلمة المرور؟ (استرجاع عبر البريد)")
        self.btn_forgot.setStyleSheet("color: #38bdf8; background: none; border: none; text-align: right; text-decoration: underline; font-size: 12px; cursor: pointer;")
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

        self.init_ui()

        # Ensure proxy and tracker are active even if service daemon was not started separately
        self._ensure_embedded_services()

        # Update timer for live counters
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_usage_gauges)
        self.timer.start(3000)

    def _ensure_embedded_services(self):
        import socket
        import time
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("127.0.0.1", 8089))
        sock.close()
        if result != 0:
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
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: bold; color: #38bdf8;")
        self.lbl_sub = QLabel("حماية تصفح ذكية • مشغل يوتيوب معزول بدون إعلانات • إدارة الوقت")
        self.lbl_sub.setStyleSheet("font-size: 13px; color: #94a3b8;")
        title_box.addWidget(self.lbl_title)
        title_box.addWidget(self.lbl_sub)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        self.lang_btn = QPushButton("🌐 English / عربي")
        self.lang_btn.clicked.connect(self.toggle_language)
        top_bar.addWidget(self.lang_btn)

        self.admin_btn = QPushButton("⚙️ لوحة ولي الأمر")
        self.admin_btn.setObjectName("actionBtn")
        self.admin_btn.clicked.connect(self.open_parent_panel)
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
        layout = QVBoxLayout(self.tab_child)
        layout.setSpacing(18)

        # Time gauges
        grp_time = QGroupBox("مؤشرات الوقت المتبقي لليوم:")
        v_time = QVBoxLayout(grp_time)

        # Entertainment
        self.lbl_ent = QLabel("🎮 وقت الترفيه والألعاب:")
        self.bar_ent = QProgressBar()
        v_time.addWidget(self.lbl_ent)
        v_time.addWidget(self.bar_ent)

        # General Browsing
        self.lbl_gen = QLabel("🌐 وقت التصفح العام:")
        self.bar_gen = QProgressBar()
        v_time.addWidget(self.lbl_gen)
        v_time.addWidget(self.bar_gen)

        # School Platforms Status
        lbl_sch = QLabel("📚 منصات المدرسة والتعليم (مدرستي، بنك المعرفة، خان أكاديمي): مفتوحة دائماً بلا حدود ✅")
        lbl_sch.setStyleSheet("color: #10b981; font-weight: bold; margin-top: 8px;")
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
        lbl_tips.setStyleSheet("line-height: 1.6; color: #cbd5e1;")
        v_tips.addWidget(lbl_tips)
        layout.addWidget(grp_tips)

        layout.addStretch()

    # --- YouTube Clean Tab ---
    def setup_youtube_tab(self):
        layout = QVBoxLayout(self.tab_youtube)
        layout.setSpacing(14)

        info_lbl = QLabel("مشغل يوتيوب النظيف: تشغيل فوري بدون أي إعلانات وبدون سحب الصفحة الثقيلة")
        info_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")
        layout.addWidget(info_lbl)

        h_search = QHBoxLayout()
        self.yt_input = QLineEdit()
        self.yt_input.setPlaceholderText("الصق رابط الفيديو من يوتيوب (مثال: https://www.youtube.com/watch?v=...)")
        self.yt_play_btn = QPushButton("تشغيل الفيديو فوراً 🎬")
        self.yt_play_btn.setObjectName("actionBtn")
        self.yt_play_btn.clicked.connect(self.play_clean_youtube)

        h_search.addWidget(self.yt_input)
        h_search.addWidget(self.yt_play_btn)
        layout.addLayout(h_search)

        self.yt_status = QLabel("جاهز للتشغيل")
        self.yt_status.setStyleSheet("color: #94a3b8;")
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
    def refresh_usage_gauges(self):
        today_usage = self.db.get_today_usage()
        today_sched = self.db.get_today_schedule()

        ent_limit = today_sched["entertainment_limit_mins"] * 60
        gen_limit = today_sched["general_limit_mins"] * 60

        ent_used = today_usage["entertainment_seconds"]
        gen_used = today_usage["general_seconds"]

        ent_rem_min = max(0, (ent_limit - ent_used) // 60)
        gen_rem_min = max(0, (gen_limit - gen_used) // 60)

        self.lbl_ent.setText(f"🎮 وقت الترفيه والألعاب: متبقي {ent_rem_min} دقيقة (من أصل {today_sched['entertainment_limit_mins']} دقيقة)")
        pct_ent = min(100, int((ent_used / ent_limit) * 100)) if ent_limit > 0 else 100
        self.bar_ent.setValue(100 - pct_ent)

        self.lbl_gen.setText(f"🌐 وقت التصفح العام: متبقي {gen_rem_min} دقيقة (من أصل {today_sched['general_limit_mins']} دقيقة)")
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = HaseenMainWindow()
    win.show()
    sys.exit(app.exec())
