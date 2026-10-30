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

# Shared kid-friendly theme
try:
    from ui.theme import STYLESHEET as STYLE_ADMIN, tip as add_tip
except Exception:
    from theme import STYLESHEET as STYLE_ADMIN, tip as add_tip


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
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #7C5CFF; margin-bottom: 5px;")
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
        lbl.setStyleSheet("font-weight: bold; color: #6B6390;")
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

        # Explainer: one whitelist for every browser
        lbl_note = QLabel(
            "💡 <b>قاعدة واحدة تكفي:</b> عند إضافة موقع للقائمة المسموحة يعمل تلقائياً في "
            "<b>كل المتصفحات</b> (Chrome, Edge, Brave, Firefox) ومع كل صفحاته الفرعية "
            "(مثل <code>app.classera.com</code>) وملفاته وصوره وفيديوهاته.<br>"
            "🎬 أي فيديو يوتيوب داخل صفحة مسموحة يعمل مباشرة في المشغل النظيف — "
            "<b>بدون حجب وبدون انتظار موافقة</b>."
        )
        lbl_note.setWordWrap(True)
        lbl_note.setTextFormat(Qt.TextFormat.RichText)
        lbl_note.setStyleSheet(
            "background:#F4F1FF; border:2px solid #E6E0FF; border-radius:14px;"
            "padding:12px; color:#2B2350; font-size:13px; line-height:1.7;"
        )
        v.addWidget(lbl_note)

        # Quick Add
        grp_add = QGroupBox("إضافة قاعدة موقع مخصصة:")
        f_add = QHBoxLayout(grp_add)

        self.in_domain = QLineEdit()
        self.in_domain.setPlaceholderText("اسم النطاق (مثال: classera.com)")
        add_tip(self.in_domain, "اكتب اسم الموقع فقط بدون https أو www.<br>"
                                "مثال: <b>classera.com</b> يفتح كل صفحات Classera وكل متصفح.")
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(["SAFE", "EDU", "SCHOOL", "GAMING", "ADULT", "VIOLENCE"])
        self.cmb_act = QComboBox()
        self.cmb_act.addItems(["ALLOW", "BLOCK"])
        add_tip(self.cmb_cat, "نوع الموقع: <b>EDU/SCHOOL</b> = تعليمي (مفتوح دائماً بلا حدود وقت)، "
                              "<b>SAFE</b> = عادي، <b>GAMING</b> = يُحسب من وقت الترفيه.")
        add_tip(self.cmb_act, "<b>ALLOW</b> = السماح بالفتح، <b>BLOCK</b> = الحجب.")
        btn_add = QPushButton("إضافة القاعدة ➕")
        btn_add.setObjectName("saveBtn")
        add_tip(btn_add, "يضيف الموقع للقائمة ويطبق فوراً على جميع المتصفحات.")
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
        btn_gemini_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #7C5CFF;")
        btn_gemini_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/apikey")))

        btn_groq_link = QPushButton("🔗 مفتاح Groq مجاني")
        btn_groq_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #059669;")
        btn_groq_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://console.groq.com/keys")))

        btn_or_link = QPushButton("🔗 مفتاح OpenRouter مجاني")
        btn_or_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #7c3aed;")
        btn_or_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://openrouter.ai/keys")))

        btn_ds_link = QPushButton("🔗 مفتاح DeepSeek")
        btn_ds_link.setStyleSheet("font-size: 11px; padding: 4px 8px; background: #E6E0FF;")
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
        self.lbl_ai_led.setStyleSheet("color: #6B6390; font-size: 12px; font-weight: bold;")
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
        btn_app_pwd_link.setStyleSheet("background-color: #7C5CFF; color: white; padding: 6px 12px; font-weight: bold;")
        btn_app_pwd_link.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://myaccount.google.com/apppasswords")))
        f_mail.addRow("خطوة سريعة:", btn_app_pwd_link)

        lbl_hint_pwd = QLabel("ملاحظة: اختر اسم 'Haseen Kids' وأنشئ كلمة مرور التطبيق وانسخ الـ 16 حرفاً هنا.")
        lbl_hint_pwd.setStyleSheet("color: #6B6390; font-size: 11px;")
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
        self.lbl_mail_led.setStyleSheet("color: #6B6390; font-size: 12px; font-weight: bold;")
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
            self.lbl_ai_led.setStyleSheet("color: #FF5C7A; font-size: 12px; font-weight: bold;")
            return

        self.lbl_ai_led.setText("⏳ جاري اختبار الاتصال...")
        self.lbl_ai_led.setStyleSheet("color: #7C5CFF; font-size: 12px; font-weight: bold;")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        ok, msg = SmartFilterEngine.test_ai_provider(prov, api_key)
        if ok:
            self.lbl_ai_led.setText(f"🟢 {msg}")
            self.lbl_ai_led.setStyleSheet("color: #34d399; font-size: 12px; font-weight: bold; background: rgba(16, 185, 129, 0.15); padding: 4px 8px; border-radius: 4px;")
            QMessageBox.information(self, "نجاح فحص الـ API", msg)
        else:
            self.lbl_ai_led.setText(f"🔴 {msg[:60]}")
            self.lbl_ai_led.setStyleSheet("color: #FF5C7A; font-size: 12px; font-weight: bold;")
            QMessageBox.critical(self, "فشل فحص الـ API", msg)

    def test_smtp_mail(self):
        user = self.in_smtp_user.text().strip()
        pwd = self.in_smtp_pass.text().strip()
        srv = self.in_smtp_server.text().strip() or "smtp.gmail.com"

        if not user or not pwd:
            self.lbl_mail_led.setText("🔴 أدخل بريد الإرسال وكلمة مرور التطبيق أولاً")
            self.lbl_mail_led.setStyleSheet("color: #FF5C7A; font-size: 12px; font-weight: bold;")
            return

        self.lbl_mail_led.setText("⏳ جاري فحص الاتصال بسيرفر Google...")
        self.lbl_mail_led.setStyleSheet("color: #7C5CFF; font-size: 12px; font-weight: bold;")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        ok, msg = ApprovalManager.test_smtp_connection(user, pwd, srv)
        if ok:
            self.lbl_mail_led.setText("🟢 متصل بنجاح وجاهز للإرسال والاستقبال ✅")
            self.lbl_mail_led.setStyleSheet("color: #34d399; font-size: 12px; font-weight: bold; background: rgba(16, 185, 129, 0.15); padding: 4px 8px; border-radius: 4px;")
            QMessageBox.information(self, "نجاح الاتصال بالبريد", msg)
        else:
            self.lbl_mail_led.setText("🔴 فشل الاتصال - راجع كلمة المرور")
            self.lbl_mail_led.setStyleSheet("color: #FF5C7A; font-size: 12px; font-weight: bold;")
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

        grp_up = QGroupBox("التحديثات والترقية المباشرة من GitHub:")
        v_up = QVBoxLayout(grp_up)

        # Version status card
        v_card = QHBoxLayout()
        self.lbl_cur_ver = QLabel(f"📌 الإصدار الحالي المثبت: <b style='color:#22C1A8;'>v{self.updater.current_version}</b>")
        self.lbl_rem_ver = QLabel("🌐 حالة مستودع GitHub: <span style='color:#7C5CFF;'>جاهز للفحص</span>")
        v_card.addWidget(self.lbl_cur_ver)
        v_card.addWidget(self.lbl_rem_ver)
        v_up.addLayout(v_card)

        lbl_desc = QLabel("يمكنك فحص وتنزيل أحدث التحديثات والتحسينات مباشرة من GitHub دون مساس بقاعدة البيانات أو كلمات المرور:")
        lbl_desc.setStyleSheet("color: #6B6390; line-height: 1.5;")
        v_up.addWidget(lbl_desc)

        # Big One-Click Update Button
        self.btn_direct_update = QPushButton("🚀 تحديث البرنامج فورا لآخر إصدار من GitHub (بضغطة واحدة)")
        self.btn_direct_update.setStyleSheet("background-color: #22C1A8; color: white; padding: 12px 20px; font-size: 14px; font-weight: bold; border-radius: 8px;")
        self.btn_direct_update.clicked.connect(self.run_direct_update)
        v_up.addWidget(self.btn_direct_update)

        self.lbl_update_progress = QLabel("")
        self.lbl_update_progress.setStyleSheet("color: #7C5CFF; font-weight: bold; font-size: 12px;")
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

        # --- Offline recovery & removal -------------------------------------
        grp_rec = QGroupBox("الاسترجاع والحذف النهائي (يعمل بدون إنترنت):")
        v_rec = QVBoxLayout(grp_rec)
        lbl_rec = QLabel(
            "لو نسيت كلمة المرور أو أردت إزالة البرنامج بالكامل دون إنترنت، استخدم إحدى "
            "الطرق الثلاث: <b>مفتاح الاسترجاع</b>، أو <b>صلاحيات Administrator</b> في ويندوز، "
            "أو <b>كلمة المرور</b>. افتح ملف <code>Haseen_Remove.bat</code> من مجلد البرنامج."
        )
        lbl_rec.setWordWrap(True)
        lbl_rec.setTextFormat(Qt.TextFormat.RichText)
        lbl_rec.setStyleSheet("color:#6B6390; font-size:13px; line-height:1.7;")
        v_rec.addWidget(lbl_rec)

        h_rec = QHBoxLayout()
        self.btn_show_key = QPushButton("🔑 عرض / توليد مفتاح استرجاع جديد")
        self.btn_show_key.clicked.connect(self.show_recovery_key)
        add_tip(self.btn_show_key, "يعرض مفتاح الاسترجاع الحالي إن وُجد، أو يولّد مفتاحاً جديداً.<br>"
                                   "احفظه في مكان آمن — بدونه ستحتاج صلاحيات المسؤول لإزالة البرنامج.")
        h_rec.addWidget(self.btn_show_key)

        self.btn_remove_app = QPushButton("🗑️ إزالة البرنامج نهائياً")
        self.btn_remove_app.setObjectName("dangerBtn")
        self.btn_remove_app.clicked.connect(self.remove_program)
        add_tip(self.btn_remove_app, "يوقف الحماية ويزيل قواعد المتصفحات وجدار الحماية والاختصارات.")
        h_rec.addWidget(self.btn_remove_app)
        v_rec.addLayout(h_rec)
        v.addWidget(grp_rec)

        # Change Admin Password
        grp_pwd = QGroupBox("تغيير كلمة مرور ولي الأمر:")
        f_pwd = QFormLayout(grp_pwd)
        
        self.in_new_pwd = QLineEdit()
        self.in_new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_new_pwd.setPlaceholderText("أدخل كلمة المرور الجديدة")
        
        self.in_confirm_pwd = QLineEdit()
        self.in_confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_confirm_pwd.setPlaceholderText("أعد إدخال كلمة المرور للتأكيد")
        
        self.chk_show_pwd = QCheckBox("👁️ إظهار كلمة المرور للتأكد قبل الحفظ")
        self.chk_show_pwd.setStyleSheet("color: #7C5CFF; font-weight: bold;")
        self.chk_show_pwd.toggled.connect(self.toggle_show_passwords)
        
        btn_ch_pwd = QPushButton("حفظ كلمة المرور الجديدة 🔑")
        btn_ch_pwd.setObjectName("actionBtn")
        btn_ch_pwd.clicked.connect(self.change_password)
        
        f_pwd.addRow("كلمة المرور الجديدة:", self.in_new_pwd)
        f_pwd.addRow("تأكيد كلمة المرور:", self.in_confirm_pwd)
        f_pwd.addRow("", self.chk_show_pwd)
        f_pwd.addRow("", btn_ch_pwd)
        v.addWidget(grp_pwd)

        v.addStretch()
        self.tabs.addTab(tab, "🔄 التحديثات والصيانة")

        self.create_requests_tab()

    # --- Child requests (approve/deny in one click) -----------------------
    def create_requests_tab(self):
        tab = QWidget()
        v = QVBoxLayout(tab)
        v.setSpacing(12)
        v.setContentsMargins(14, 14, 14, 14)

        info = QLabel(
            "هنا تصل طلبات طفلك لفتح مواقع. اضغط «موافقة» فيُفتح الموقع له "
            "تلقائياً في نفس اللحظة — بلا إعادة تحميل ولا انتظار."
        )
        info.setWordWrap(True)
        info.setStyleSheet("background:#F4F1FF; border:1px solid #E6E0FF;"
                           "border-radius:14px; padding:12px; color:#2B2350; font-size:14px;")
        v.addWidget(info)

        self.tbl_req = QTableWidget(0, 3)
        self.tbl_req.setHorizontalHeaderLabels(["الموقع المطلوب", "سبب الطفل", "الوقت"])
        self.tbl_req.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_req.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_req.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_req.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_req.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_req.verticalHeader().setDefaultSectionSize(38)
        v.addWidget(self.tbl_req, 1)

        row = QHBoxLayout()
        btn_perm = QPushButton("✅ موافقة دائمة")
        btn_perm.setObjectName("btnSuccess")
        add_tip(btn_perm, "يفتح الموقع لطفلك دائماً ويدخله القائمة البيضاء (كل المتصفحات وكل الصفحات الفرعية).")
        btn_perm.clicked.connect(lambda: self._decide_request(permanent=True))

        btn_temp = QPushButton("⏳ موافقة 30 دقيقة")
        add_tip(btn_temp, "يفتح الموقع لمدة نصف ساعة فقط ثم يعود محجوباً تلقائياً.")
        btn_temp.clicked.connect(lambda: self._decide_request(permanent=False))

        btn_rej = QPushButton("🚫 رفض")
        btn_rej.setObjectName("btnDanger")
        add_tip(btn_rej, "يرفض الطلب ويُبقي الموقع مغلقاً.")
        btn_rej.clicked.connect(self._reject_request)

        btn_ref = QPushButton("🔄 تحديث")
        add_tip(btn_ref, "يعيد قراءة الطلبات الجديدة من الطفل.")
        btn_ref.clicked.connect(self.load_requests)

        row.addWidget(btn_perm)
        row.addWidget(btn_temp)
        row.addWidget(btn_rej)
        row.addWidget(btn_ref)
        v.addLayout(row)

        self.tabs.addTab(tab, "📨 طلبات الطفل")
        self.load_requests()

    def load_requests(self):
        self.tbl_req.setRowCount(0)
        try:
            rows = self.db.list_exception_requests("PENDING")
        except Exception:
            rows = []
        for _id, domain, url, reason, status, created in rows:
            r = self.tbl_req.rowCount()
            self.tbl_req.insertRow(r)
            self.tbl_req.setItem(r, 0, QTableWidgetItem(domain or "(بدون نطاق)"))
            self.tbl_req.setItem(r, 1, QTableWidgetItem(reason or "-"))
            self.tbl_req.setItem(r, 2, QTableWidgetItem(str(created or "")))
        if not rows:
            self.tbl_req.insertRow(0)
            it = QTableWidgetItem("لا توجد طلبات جديدة الآن — كل شيء على ما يرام ✅")
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_req.setItem(0, 0, it)
            self.tbl_req.setSpan(0, 0, 1, 3)

    def _selected_request_domain(self):
        r = self.tbl_req.currentRow()
        if r < 0:
            QMessageBox.information(self, "تنبيه", "اختر الطلب من الجدول أولاً.")
            return None
        item = self.tbl_req.item(r, 0)
        if not item or item.text() in ("(بدون نطاق)", ""):
            QMessageBox.warning(self, "تنبيه", "هذا الطلب لم يسجّل اسم الموقع. اطلب من طفلك إعادة الطلب من صفحة الحجب.")
            return None
        return item.text().strip()

    def _decide_request(self, permanent=True):
        domain = self._selected_request_domain()
        if not domain:
            return
        self.db.grant_exception(domain, minutes=None if permanent else 30)
        self.load_requests()
        QMessageBox.information(
            self, "تم",
            f"تم السماح بموقع {domain} "
            + ("دائماً ✅" if permanent else "لمدة 30 دقيقة ⏳")
            + chr(10) + "سيفتح عند طفلك تلقائياً خلال ثوانٍ بدون أي إجراء منه."
        )

    def _reject_request(self):
        domain = self._selected_request_domain()
        if not domain:
            return
        self.db.reject_exception(domain)
        self.load_requests()
        QMessageBox.information(self, "تم", f"تم رفض طلب {domain}.")


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
        self.lbl_rem_ver.setText("جاري الفحص من GitHub... ⏳")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        has_up, rem_v, info, err = self.updater.check_for_updates()
        cur_v = self.updater.current_version
        if err:
            self.lbl_rem_ver.setText("<span style='color:#FF5C7A;'>فشل الاتصال</span>")
            QMessageBox.warning(self, "فحص التحديثات", f"تعذر التحقق من التحديثات:\n{err}")
        elif has_up:
            self.lbl_rem_ver.setText(f"🌐 يتوفر إصدار جديد: <b style='color:#7C5CFF;'>v{rem_v}</b>")
            reply = QMessageBox.question(
                self,
                "تحديث جديد متوفر!",
                f"يتوفر إصدار رسمي جديد: v{rem_v} على GitHub!\n"
                f"الإصدار الحالي المثبت لديك: v{cur_v}\n\n"
                f"تفاصيل التحديث:\n{info.get('notes', 'تحسينات أمنية واستقرار شامل')}\n\n"
                f"هل ترغب في تطبيق التحديث الآن مباشرة؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.run_direct_update()
        else:
            self.lbl_rem_ver.setText(f"🌐 مستودع GitHub: <b style='color:#22C1A8;'>v{rem_v} (محدث بالكامل)</b>")
            QMessageBox.information(
                self,
                "البرنامج محدث",
                f"أنت تعمل بالفعل على أحدث إصدار متوفر: v{cur_v} ✅\nلا توجد تحديثات جديدة حالياً."
            )

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


    # --- Recovery key & removal -------------------------------------------
    def show_recovery_key(self):
        import core.recovery as recovery_mod
        NL = chr(10)
        existing = self.db.get_setting("recovery_key_hash", "")
        key = recovery_mod.generate_recovery_key()
        if existing:
            txt = ("يوجد مفتاح محفوظ " + NL + NL
                   + "مفتاح جديد: " + key + NL + NL
                   + "هل تريد استبداله؟")
            if QMessageBox.question(self, "مفتاح الاسترجاع", txt) != QMessageBox.StandardButton.Yes:
                return
        recovery_mod.store_recovery_key(self.db, key)
        try:
            path = recovery_mod.write_recovery_note(key)
            extra = NL + NL + "حفظت نسخة في: " + str(path)
        except Exception:
            extra = ""
        QMessageBox.information(
            self, "مفتاح الاسترجاع",
            "مفتاح الاسترجاع الخاص بك: " + NL + NL + "   " + key + extra
        )

    def remove_program(self):
        NL = chr(10)
        ans = QMessageBox.warning(
            self, "تأكيد الإزالة",
            "سيتم إيقاف الحماية وإزالة قواعد المتصفحات وجدار الحماية والاختصارات." + NL + NL + "هل أنت متأكد؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        try:
            import core.recovery as recovery_mod
            summary = recovery_mod.full_remove(delete_folder=False)
            QMessageBox.information(
                self, "تمت الإزالة",
                "تم إيقاف الحماية واستعادة إعدادات الجهاز." + NL
                + "processes stopped: " + str(summary.get("processes", 0)) + NL
                + "browser policies removed: " + str(summary.get("policies", 0)) + NL
                + "firewall rules removed: " + str(summary.get("firewall", 0)) + NL
                + "autostart entries removed: " + str(summary.get("autostart", 0)) + NL + NL
                + "يمكنك الآن حذف مجلد البرنامج يدوياً."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def toggle_show_passwords(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.in_new_pwd.setEchoMode(mode)
        self.in_confirm_pwd.setEchoMode(mode)

    def change_password(self):
        p1 = self.in_new_pwd.text().strip()
        p2 = self.in_confirm_pwd.text().strip()
        
        if len(p1) < 4:
            QMessageBox.warning(self, "تنبيه", "يجب أن تكون كلمة المرور 4 أحرف أو أرقام على الأقل.")
            return
            
        if p1 != p2:
            QMessageBox.warning(self, "عدم تطابق", "كلمتا المرور غير متطابقتين!\nيرجى التأكد من كتابة نفس كلمة المرور في الحقلين.")
            return

        self.security.set_admin_password(p1)
        self.in_new_pwd.clear()
        self.in_confirm_pwd.clear()
        self.chk_show_pwd.setChecked(False)
        QMessageBox.information(self, "نجاح", "تم تغيير كلمة مرور ولي الأمر بنجاح وحفظها بأمان ✅")
