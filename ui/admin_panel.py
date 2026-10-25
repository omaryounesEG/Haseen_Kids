import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFormLayout, QComboBox,
    QCheckBox, QGroupBox, QSpinBox, QTimeEdit, QWidget
)
from PyQt6.QtCore import Qt, QTime, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager
from core.security import SecurityManager
from core.updater import SecureGitHubUpdater
from core.reports import WeeklyReportGenerator
from core.approvals import ApprovalManager
from proxy.filter_engine import SmartFilterEngine

STYLE_ADMIN = """
QDialog { background-color: #0f172a; color: #f8fafc; }
QWidget { font-family: 'Segoe UI', Tahoma, Arial, sans-serif; font-size: 13px; color: #f8fafc; }
QGroupBox { border: 1px solid #334155; border-radius: 8px; margin-top: 15px; padding-top: 15px; font-weight: bold; color: #38bdf8; }
QTabWidget::pane { border: 1px solid #334155; background: #1e293b; }
QTabBar::tab { background: #0f172a; color: #94a3b8; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
QTabBar::tab:selected { background: #1e293b; color: #38bdf8; border-bottom: 2px solid #38bdf8; }
QPushButton { background-color: #2563eb; color: white; border: none; border-radius: 6px; padding: 8px 14px; font-weight: bold; }
QPushButton:hover { background-color: #1d4ed8; }
QPushButton#saveBtn { background-color: #10b981; }
QPushButton#saveBtn:hover { background-color: #059669; }
QPushButton#dangerBtn { background-color: #e11d48; }
QPushButton#dangerBtn:hover { background-color: #be123c; }
QLineEdit, QComboBox, QTimeEdit, QSpinBox { background-color: #0f172a; border: 1px solid #475569; border-radius: 4px; padding: 6px; color: white; }
QTableWidget { background-color: #0f172a; border: 1px solid #334155; gridline-color: #1e293b; color: white; }
QHeaderView::section { background-color: #1e293b; color: #38bdf8; padding: 4px; border: 1px solid #334155; font-weight: bold; }
"""

class ParentAdminDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ لوحة تحكم ولي الأمر | Parent Control Console")
        self.resize(900, 650)
        self.setStyleSheet(STYLE_ADMIN)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.db = DBManager()
        self.security = SecurityManager(self.db)
        self.updater = SecureGitHubUpdater()
        self.reports = WeeklyReportGenerator(self.db)

        layout = QVBoxLayout(self)

        header = QLabel("⚙️ لوحة الإدارة الأبوية الشاملة - حصين | Haseen Kids")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8; margin-bottom: 5px;")
        layout.addWidget(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.setup_schedule_tab()
        self.setup_domains_tab()
        self.setup_ai_security_tab()
        self.setup_updates_tab()

    # --- 1. Schedule Tab ---
    def setup_schedule_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        lbl = QLabel("تحديد الحصص اليومية (بالدقائق) لكل يوم من أيام الأسبوع:")
        lbl.setStyleSheet("font-weight: bold; color: #94a3b8;")
        v.addWidget(lbl)

        self.spin_boxes = {}
        day_names_ar = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]

        # Fetch current schedule from DB
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT day_of_week, entertainment_limit_mins, general_limit_mins, bedtime_start, bedtime_end FROM time_schedule ORDER BY day_of_week")
            rows = c.fetchall()

        grid_layout = QVBoxLayout()
        for i, row in enumerate(rows):
            dow, ent, gen, b_start, b_end = row
            h = QHBoxLayout()
            l_day = QLabel(f"📅 {day_names_ar[dow]}:")
            l_day.setFixedWidth(90)

            l_ent = QLabel("ترفيه:")
            sp_ent = QSpinBox()
            sp_ent.setRange(0, 600)
            sp_ent.setValue(ent)
            sp_ent.setSuffix(" دقيقة")

            l_gen = QLabel("تصفح عام:")
            sp_gen = QSpinBox()
            sp_gen.setRange(0, 1000)
            sp_gen.setValue(gen)
            sp_gen.setSuffix(" دقيقة")

            self.spin_boxes[dow] = (sp_ent, sp_gen)

            h.addWidget(l_day)
            h.addWidget(l_ent)
            h.addWidget(sp_ent)
            h.addWidget(l_gen)
            h.addWidget(sp_gen)
            grid_layout.addLayout(h)

        v.addLayout(grid_layout)

        # Bedtime box
        grp_bed = QGroupBox("وقت النوم وإغلاق التصفح (Bedtime):")
        h_bed = QHBoxLayout(grp_bed)
        h_bed.addWidget(QLabel("يبدأ وقت النوم من:"))
        self.time_bed_start = QTimeEdit()
        self.time_bed_start.setDisplayFormat("HH:mm")
        self.time_bed_start.setTime(QTime.fromString(rows[0][3] if rows else "21:00", "HH:mm"))
        h_bed.addWidget(self.time_bed_start)

        h_bed.addWidget(QLabel("وحتى الساعة:"))
        self.time_bed_end = QTimeEdit()
        self.time_bed_end.setDisplayFormat("HH:mm")
        self.time_bed_end.setTime(QTime.fromString(rows[0][4] if rows else "07:00", "HH:mm"))
        h_bed.addWidget(self.time_bed_end)
        v.addWidget(grp_bed)

        h_btns = QHBoxLayout()
        btn_save = QPushButton("حفظ الجدول الزمني 💾")
        btn_save.setObjectName("saveBtn")
        btn_save.clicked.connect(self.save_schedule)
        h_btns.addWidget(btn_save)

        btn_reset_today = QPushButton("🔄 تصفير استخدام اليوم يدوياً")
        btn_reset_today.clicked.connect(self.reset_today_usage)
        h_btns.addWidget(btn_reset_today)
        v.addLayout(h_btns)

        v.addStretch()
        self.tabs.addTab(tab, "⏱️ جدول الأوقات")

    def save_schedule(self):
        b_start = self.time_bed_start.time().toString("HH:mm")
        b_end = self.time_bed_end.time().toString("HH:mm")
        with self.db.get_connection() as conn:
            c = conn.cursor()
            for dow, (sp_ent, sp_gen) in self.spin_boxes.items():
                c.execute('''
                    UPDATE time_schedule SET
                        entertainment_limit_mins = ?,
                        general_limit_mins = ?,
                        bedtime_start = ?,
                        bedtime_end = ?
                    WHERE day_of_week = ?
                ''', (sp_ent.value(), sp_gen.value(), b_start, b_end, dow))
            conn.commit()
        QMessageBox.information(self, "نجاح", "تم حفظ الجدول الزمني بنجاح ✅")

    def reset_today_usage(self):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE daily_usage SET entertainment_used_seconds = 0, general_used_seconds = 0, school_used_seconds = 0 WHERE usage_date = date('now')")
            conn.commit()
        QMessageBox.information(self, "نجاح", "تم تصفير استهلاك اليوم لجميع الفئات ✅")

    # --- 2. Domains Tab ---
    def setup_domains_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        # Quick Add
        grp_add = QGroupBox("إضافة قاعدة موقع مخصصة:")
        f_add = QHBoxLayout(grp_add)

        self.in_domain = QLineEdit()
        self.in_domain.setPlaceholderText("اسم النطاق (مثال: roblox.com)")
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(["SAFE", "EDU", "SCHOOL", "GAMING", "ADULT", "VIOLENCE"])
        self.cmb_act = QComboBox()
        self.cmb_act.addItems(["ALLOW", "BLOCK"])
        btn_add = QPushButton("إضافة القاعدة ➕")
        btn_add.setObjectName("saveBtn")
        btn_add.clicked.connect(self.add_domain_rule)

        f_add.addWidget(self.in_domain)
        f_add.addWidget(QLabel("التصنيف:"))
        f_add.addWidget(self.cmb_cat)
        f_add.addWidget(QLabel("الإجراء:"))
        f_add.addWidget(self.cmb_act)
        f_add.addWidget(btn_add)
        v.addWidget(grp_add)

        # Table
        self.table_domains = QTableWidget()
        self.table_domains.setColumnCount(4)
        self.table_domains.setHorizontalHeaderLabels(["النطاق (Domain)", "التصنيف", "الإجراء", "المصدر"])
        self.table_domains.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        v.addWidget(self.table_domains)

        h_ctrl = QHBoxLayout()
        btn_refresh = QPushButton("تحديث القائمة 🔄")
        btn_refresh.clicked.connect(self.load_domains_table)
        btn_del = QPushButton("حذف القاعدة المحددة 🗑️")
        btn_del.setObjectName("dangerBtn")
        btn_del.clicked.connect(self.delete_selected_domain)
        h_ctrl.addWidget(btn_refresh)
        h_ctrl.addWidget(btn_del)
        v.addLayout(h_ctrl)

        self.tabs.addTab(tab, "🛡️ القوائم والقواعد")
        self.load_domains_table()

    def load_domains_table(self):
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT domain, category, action, source FROM domains ORDER BY last_evaluated DESC LIMIT 150")
            rows = c.fetchall()

        self.table_domains.setRowCount(len(rows))
        for r_idx, (d, cat, act, src) in enumerate(rows):
            self.table_domains.setItem(r_idx, 0, QTableWidgetItem(d))
            self.table_domains.setItem(r_idx, 1, QTableWidgetItem(cat))
            act_item = QTableWidgetItem("سماح ✅" if act == "ALLOW" else "حجب ⛔")
            act_item.setForeground(Qt.GlobalColor.green if act == "ALLOW" else Qt.GlobalColor.red)
            self.table_domains.setItem(r_idx, 2, act_item)
            self.table_domains.setItem(r_idx, 3, QTableWidgetItem(src))

    def add_domain_rule(self):
        d = self.in_domain.text().strip().lower()
        if not d:
            return
        cat = self.cmb_cat.currentText()
        act = self.cmb_act.currentText()
        self.db.save_domain_decision(d, act, cat, "PARENT_RULE")
        self.in_domain.clear()
        self.load_domains_table()
        QMessageBox.information(self, "نجاح", f"تم حفظ قاعدة الموقع {d} بنجاح.")

    def delete_selected_domain(self):
        cur = self.table_domains.currentRow()
        if cur < 0:
            return
        d = self.table_domains.item(cur, 0).text()
        with self.db.get_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM domains WHERE domain = ?", (d,))
            conn.commit()
        self.load_domains_table()

    # --- 3. AI & Security Tab ---
    def setup_ai_security_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        settings = self.db.get_all_settings()

        grp_prot = QGroupBox("خيارات الحماية والنظام:")
        v_prot = QVBoxLayout(grp_prot)

        self.chk_lockdown = QCheckBox("قفل المتصفحات غير المعتمدة والبروكسيات المحمولة (Process Whitelisting)")
        self.chk_lockdown.setChecked(settings.get("process_lockdown") == "1")
        v_prot.addWidget(self.chk_lockdown)

        self.chk_yt_clean = QCheckBox("تفعيل الوضع المعزول لليوتيوب (استخراج البث بدون إعلانات نهائياً)")
        self.chk_yt_clean.setChecked(settings.get("youtube_clean_mode", "1") == "1")
        v_prot.addWidget(self.chk_yt_clean)

        btn_apply_reg = QPushButton("تطبيق سياسات سجل ويندوز الإجبارية للمتصفحات (Chrome / Edge Policies) 🔒")
        btn_apply_reg.clicked.connect(self.apply_policies)
        v_prot.addWidget(btn_apply_reg)

        v.addWidget(grp_prot)

        # AI Settings
        grp_ai = QGroupBox("محرك الذكاء الاصطناعي لفحص المواقع غير المعروفة (Micro-Prompting):")
        f_ai = QFormLayout(grp_ai)

        self.cmb_ai = QComboBox()
        self.cmb_ai.addItem("Google Gemini (مجاني 15 طلب/دقيقة)", "gemini")
        self.cmb_ai.addItem("Groq - فائقة السرعة (مجاني 30 طلب/دقيقة)", "groq")
        self.cmb_ai.addItem("OpenRouter (نماذج مجانية متعددة)", "openrouter")
        self.cmb_ai.addItem("DeepSeek V3 (اقتصادي)", "deepseek")

        # Set current selection
        cur_prov = settings.get("ai_provider", "gemini")
        idx = self.cmb_ai.findData(cur_prov)
        if idx >= 0:
            self.cmb_ai.setCurrentIndex(idx)

        f_ai.addRow("المزود المختار:", self.cmb_ai)

        # Provider Key links
        h_links = QHBoxLayout()
        btn_gemini_link = QPushButton("🔗 مفتاح Gemini مجاني")
        btn_gemini_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #0284c7;")
        btn_gemini_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/apikey")))

        btn_groq_link = QPushButton("🔗 مفتاح Groq مجاني")
        btn_groq_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #059669;")
        btn_groq_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.groq.com/keys")))

        btn_or_link = QPushButton("🔗 مفتاح OpenRouter مجاني")
        btn_or_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #7c3aed;")
        btn_or_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://openrouter.ai/keys")))

        btn_ds_link = QPushButton("🔗 مفتاح DeepSeek")
        btn_ds_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #334155;")
        btn_ds_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://platform.deepseek.com/api_keys")))

        h_links.addWidget(btn_gemini_link)
        h_links.addWidget(btn_groq_link)
        h_links.addWidget(btn_or_link)
        h_links.addWidget(btn_ds_link)
        f_ai.addRow("استخراج مفاتيح مجانية:", h_links)

        self.in_gemini = QLineEdit(settings.get("gemini_api_key", ""))
        self.in_gemini.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_groq = QLineEdit(settings.get("groq_api_key", ""))
        self.in_groq.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_openrouter = QLineEdit(settings.get("openrouter_api_key", ""))
        self.in_openrouter.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_deepseek = QLineEdit(settings.get("deepseek_api_key", ""))
        self.in_deepseek.setEchoMode(QLineEdit.EchoMode.Password)

        f_ai.addRow("Gemini API Key:", self.in_gemini)
        f_ai.addRow("Groq API Key:", self.in_groq)
        f_ai.addRow("OpenRouter API Key:", self.in_openrouter)
        f_ai.addRow("DeepSeek API Key:", self.in_deepseek)

        # AI Test Row
        h_ai_test = QHBoxLayout()
        btn_test_ai = QPushButton("🧪 اختبار اتصال ونشاط الـ API")
        btn_test_ai.clicked.connect(self.test_ai_connection)
        self.lbl_ai_led = QLabel("⚪ لم يتم اختبار اتصال الـ AI بعد")
        self.lbl_ai_led.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold;")
        h_ai_test.addWidget(btn_test_ai)
        h_ai_test.addWidget(self.lbl_ai_led)
        h_ai_test.addStretch()
        f_ai.addRow("", h_ai_test)

        v.addWidget(grp_ai)

        # Email & SMTP Settings
        grp_mail = QGroupBox("إعدادات بريد الموافقات والتقارير الأسبوعية (Gmail SMTP):")
        f_mail = QFormLayout(grp_mail)

        self.in_parent_email = QLineEdit(settings.get("parent_email", ""))
        self.in_smtp_user = QLineEdit(settings.get("smtp_user", ""))
        self.in_smtp_pass = QLineEdit(settings.get("smtp_app_password", ""))
        self.in_smtp_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_smtp_server = QLineEdit(settings.get("smtp_server", "smtp.gmail.com"))

        btn_app_pwd_link = QPushButton("🔗 استخراج كلمة مرور التطبيق من Google مباشرة (Google App Passwords)")
        btn_app_pwd_link.setStyleSheet("background-color: #0284c7; color: white; padding: 6px 12px; font-weight: bold;")
        btn_app_pwd_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://myaccount.google.com/apppasswords")))
        f_mail.addRow("خطوة سريعة:", btn_app_pwd_link)

        lbl_hint_pwd = QLabel("ملاحظة: اختر اسم 'Haseen Kids' وأنشئ كلمة مرور التطبيق وانسخ الـ 16 حرفاً هنا.")
        lbl_hint_pwd.setStyleSheet("color: #94a3b8; font-size: 11px;")
        f_mail.addRow("", lbl_hint_pwd)

        f_mail.addRow("بريد ولي الأمر المستلم:", self.in_parent_email)
        f_mail.addRow("بريد الإرسال (Gmail):", self.in_smtp_user)
        f_mail.addRow("كلمة مرور التطبيق (16 حرفاً):", self.in_smtp_pass)
        f_mail.addRow("سيرفر SMTP:", self.in_smtp_server)

        # Mail Test & LED Row
        h_mail_test = QHBoxLayout()
        btn_test_smtp = QPushButton("🧪 فحص اتصال بريد Gmail")
        btn_test_smtp.clicked.connect(self.test_smtp_mail)
        self.lbl_mail_led = QLabel("⚪ لم يتم فحص الاتصال بعد")
        self.lbl_mail_led.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold;")
        h_mail_test.addWidget(btn_test_smtp)
        h_mail_test.addWidget(self.lbl_mail_led)
        h_mail_test.addStretch()
        f_mail.addRow("", h_mail_test)

        btn_test_rep = QPushButton("إرسال تقرير أسبوعي تجريبي عبر البريد الآن 📊")
        btn_test_rep.clicked.connect(self.send_test_report)
        f_mail.addRow("", btn_test_rep)

        v.addWidget(grp_mail)

        btn_save_all = QPushButton("حفظ جميع الإعدادات 💾")
        btn_save_all.setObjectName("saveBtn")
        btn_save_all.clicked.connect(self.save_security_settings)
        v.addWidget(btn_save_all)

        v.addStretch()
        self.tabs.addTab(tab, "⚙️ الحماية والـ AI")

    def apply_policies(self):
        ok, msg = self.security.apply_browser_registry_policies()
        if ok:
            QMessageBox.information(self, "سياسات ويندوز", msg)
        else:
            QMessageBox.warning(self, "تنبيه", msg)

    def test_ai_connection(self):
        prov = self.cmb_ai.currentData() or "gemini"
        key_map = {
            "gemini": self.in_gemini.text().strip(),
            "groq": self.in_groq.text().strip(),
            "openrouter": self.in_openrouter.text().strip(),
            "deepseek": self.in_deepseek.text().strip()
        }
        api_key = key_map.get(prov, "")
        if not api_key:
            self.lbl_ai_led.setText("🔴 يرجى إدخال مفتاح الـ API أولاً")
            self.lbl_ai_led.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold;")
            return

        self.lbl_ai_led.setText("⏳ جاري اختبار الاتصال...")
        self.lbl_ai_led.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: bold;")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        ok, msg = SmartFilterEngine.test_ai_provider(prov, api_key)
        if ok:
            self.lbl_ai_led.setText(f"🟢 {msg}")
            self.lbl_ai_led.setStyleSheet("color: #34d399; font-size: 12px; font-weight: bold; background: rgba(16, 185, 129, 0.15); padding: 4px 8px; border-radius: 4px;")
            QMessageBox.information(self, "نجاح فحص الـ API", msg)
        else:
            self.lbl_ai_led.setText(f"🔴 {msg[:60]}")
            self.lbl_ai_led.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold;")
            QMessageBox.critical(self, "فشل فحص الـ API", msg)

    def test_smtp_mail(self):
        user = self.in_smtp_user.text().strip()
        pwd = self.in_smtp_pass.text().strip()
        srv = self.in_smtp_server.text().strip() or "smtp.gmail.com"

        if not user or not pwd:
            self.lbl_mail_led.setText("🔴 أدخل بريد الإرسال وكلمة مرور التطبيق أولاً")
            self.lbl_mail_led.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold;")
            return

        self.lbl_mail_led.setText("⏳ جاري فحص الاتصال بسيرفر Google...")
        self.lbl_mail_led.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: bold;")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        ok, msg = ApprovalManager.test_smtp_connection(user, pwd, srv)
        if ok:
            self.lbl_mail_led.setText("🟢 متصل بنجاح وجاهز للإرسال والاستقبال ✅")
            self.lbl_mail_led.setStyleSheet("color: #34d399; font-size: 12px; font-weight: bold; background: rgba(16, 185, 129, 0.15); padding: 4px 8px; border-radius: 4px;")
            QMessageBox.information(self, "نجاح الاتصال بالبريد", msg)
        else:
            self.lbl_mail_led.setText("🔴 فشل الاتصال - راجع كلمة المرور")
            self.lbl_mail_led.setStyleSheet("color: #ef4444; font-size: 12px; font-weight: bold;")
            QMessageBox.critical(self, "فشل الاتصال بالبريد", msg)

    def save_security_settings(self):
        self.db.set_setting("process_lockdown", "1" if self.chk_lockdown.isChecked() else "0")
        self.db.set_setting("youtube_clean_mode", "1" if self.chk_yt_clean.isChecked() else "0")
        self.db.set_setting("ai_provider", self.cmb_ai.currentData() or "gemini")
        self.db.set_setting("gemini_api_key", self.in_gemini.text().strip())
        self.db.set_setting("groq_api_key", self.in_groq.text().strip())
        self.db.set_setting("openrouter_api_key", self.in_openrouter.text().strip())
        self.db.set_setting("deepseek_api_key", self.in_deepseek.text().strip())
        self.db.set_setting("parent_email", self.in_parent_email.text().strip())
        self.db.set_setting("smtp_user", self.in_smtp_user.text().strip())
        self.db.set_setting("smtp_app_password", self.in_smtp_pass.text().strip())
        self.db.set_setting("smtp_server", self.in_smtp_server.text().strip())
        QMessageBox.information(self, "نجاح", "تم حفظ كافة إعدادات الحماية ومفاتيح الـ AI والبريد بنجاح ✅")

    def send_test_report(self):
        self.save_security_settings()
        ok, msg = self.reports.send_weekly_digest()
        if ok:
            QMessageBox.information(self, "نجاح الإرسال", msg)
        else:
            QMessageBox.critical(self, "فشل الإرسال", msg)

    # --- 4. Updates Tab ---
    def setup_updates_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)

        grp_up = QGroupBox("التحديثات الآمنة والترقية المباشرة (GitHub Updates):")
        v_up = QVBoxLayout(grp_up)

        lbl_desc = QLabel("يمكنك فحص وتنزيل أحدث التحديثات والتحسينات مباشرة من GitHub دون فقد أي من إعداداتك أو كلمات المرور:")
        lbl_desc.setStyleSheet("color: #94a3b8; line-height: 1.5;")
        v_up.addWidget(lbl_desc)

        # Big One-Click Update Button
        self.btn_direct_update = QPushButton("🚀 تحديث البرنامج فورا لآخر إصدار من GitHub (بضغطة واحدة)")
        self.btn_direct_update.setStyleSheet("background-color: #10b981; color: white; padding: 12px 20px; font-size: 14px; font-weight: bold; border-radius: 8px;")
        self.btn_direct_update.clicked.connect(self.run_direct_update)
        v_up.addWidget(self.btn_direct_update)

        self.lbl_update_progress = QLabel("")
        self.lbl_update_progress.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px;")
        v_up.addWidget(self.lbl_update_progress)

        h_checks = QHBoxLayout()
        btn_chk = QPushButton("فحص التحديثات من GitHub 🔍")
        btn_chk.clicked.connect(self.check_github_updates)
        h_checks.addWidget(btn_chk)

        btn_ytdlp = QPushButton("🎬 تحديث محرك اليوتيوب yt-dlp فقط")
        btn_ytdlp.clicked.connect(self.update_ytdlp)
        btn_lists = QPushButton("🛡️ تحديث قوائم المواقع المحجوبة فقط")
        btn_lists.clicked.connect(self.update_lists)
        h_checks.addWidget(btn_ytdlp)
        h_checks.addWidget(btn_lists)
        v_up.addLayout(h_checks)

        v.addWidget(grp_up)

        # Change Admin Password
        grp_pwd = QGroupBox("تغيير كلمة مرور ولي الأمر:")
        f_pwd = QFormLayout(grp_pwd)
        self.in_new_pwd = QLineEdit()
        self.in_new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_new_pwd.setPlaceholderText("كلمة المرور الجديدة")
        btn_ch_pwd = QPushButton("تغيير كلمة المرور 🔑")
        btn_ch_pwd.setObjectName("actionBtn")
        btn_ch_pwd.clicked.connect(self.change_password)
        f_pwd.addRow("كلمة المرور الجديدة:", self.in_new_pwd)
        f_pwd.addRow("", btn_ch_pwd)
        v.addWidget(grp_pwd)

        v.addStretch()
        self.tabs.addTab(tab, "🔄 التحديثات والصيانة")

    def run_direct_update(self):
        reply = QMessageBox.question(
            self,
            "تحديث البرنامج",
            "هل ترغب في تحديث كافة ملفات البرنامج الآن من GitHub؟\n(سيتم الحفاظ على كافة إعداداتك وكلمات المرور)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_direct_update.setEnabled(False)
        self.lbl_update_progress.setText("جاري التحديث من GitHub...")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        ok, msg = self.updater.update_from_github_direct(progress_callback=self.lbl_update_progress.setText)
        self.btn_direct_update.setEnabled(True)
        if ok:
            self.lbl_update_progress.setText("اكتمل التحديث بنجاح! ✅")
            QMessageBox.information(self, "نجاح التحديث", f"{msg}\n\nيرجى إعادة فتح البرنامج لتفعيل التعديلات الجديدة.")
        else:
            self.lbl_update_progress.setText("فشل التحديث ❌")
            QMessageBox.critical(self, "فشل التحديث", msg)

    def check_github_updates(self):
        has_up, r_ver, info, err = self.updater.check_for_updates()
        if err:
            QMessageBox.information(self, "فحص التحديثات", err)
        elif has_up:
            reply = QMessageBox.question(
                self,
                "تحديث متوفر!",
                f"يتوفر إصدار رسمي جديد v{r_ver} على GitHub!\nالتفاصيل: {info.get('notes', '')}\n\nهل ترغب في تطبيق التحديث الآن مباشرة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.run_direct_update()
        else:
            QMessageBox.information(self, "فحص التحديثات", f"البرنامج محدث لآخر إصدار ({self.updater.current_version}).")

    def update_ytdlp(self):
        ok, msg = self.updater.update_ytdlp_micro()
        if ok:
            QMessageBox.information(self, "محرك اليوتيوب", msg)
        else:
            QMessageBox.warning(self, "تنبيه", msg)

    def update_lists(self):
        ok, msg = self.updater.update_filter_lists_micro()
        if ok:
            QMessageBox.information(self, "قوائم الحجب", msg)
        else:
            QMessageBox.warning(self, "تنبيه", msg)

    def change_password(self):
        p = self.in_new_pwd.text().strip()
        if len(p) < 4:
            QMessageBox.warning(self, "تنبيه", "يجب أن تكون كلمة المرور 4 أحرف على الأقل")
            return
        self.security.set_admin_password(p)
        self.in_new_pwd.clear()
        QMessageBox.information(self, "نجاح", "تم تغيير كلمة مرور ولي الأمر بنجاح ✅")
