import sys
import os
import platform
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import (
    QApplication, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QCheckBox, QLineEdit,
    QGroupBox, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap

from installer.preflight import SystemPreflightChecker
from core.security import SecurityManager

STYLE_WIZARD = """
QWizard, QWizardPage, QDialog {
    background-color: #0f172a;
    color: #f8fafc;
}
QWidget {
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 13px;
    color: #f8fafc;
    background-color: transparent;
}
QWizard QWidget#qt_wizard_page {
    background-color: #0f172a;
}
QLabel {
    color: #f8fafc;
}
QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 20px;
    padding-left: 10px;
    padding-right: 10px;
    padding-bottom: 10px;
    font-weight: bold;
    color: #38bdf8;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top right;
    padding: 2px 8px;
    color: #38bdf8;
}
QCheckBox {
    color: #f8fafc;
    spacing: 8px;
}
QPushButton {
    background-color: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QLineEdit {
    background-color: #0f172a;
    border: 1px solid #475569;
    border-radius: 4px;
    padding: 6px;
    color: white;
}
QProgressBar {
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    background: #0f172a;
    color: white;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #10b981;
    border-radius: 5px;
}
"""

# Worker for downloading Brave in background without freezing UI
class BraveDownloaderThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def run(self):
        checker = SystemPreflightChecker()
        ok, msg = checker.download_and_install_brave(progress_callback=self.progress_signal.emit)
        self.finished_signal.emit(ok, msg)

# Page 1: Welcome
class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("مرحباً بك في معالج تثبيت حَصِين للأطفال")
        layout = QVBoxLayout(self)

        top_h = QHBoxLayout()
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            lbl_ico = QLabel()
            pix = QPixmap(icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_ico.setPixmap(pix)
            top_h.addWidget(lbl_ico)

        lbl_head = QLabel("<h2>حَصِين للأطفال | Haseen Kids</h2><span style='color: #38bdf8;'>نظام الحماية والرقابة الأسرية الذكي</span>")
        lbl_head.setTextFormat(Qt.TextFormat.RichText)
        top_h.addWidget(lbl_head)
        top_h.addStretch()
        layout.addLayout(top_h)

        lbl = QLabel(
            "يقوم هذا المعالج بتثبيت برنامج <strong>حَصِين للأطفال | Haseen Kids</strong> على جهازك.<br><br>"
            "<strong>المميزات المضمنة:</strong><br>"
            "• محرك يوتيوب معزول بدون إعلانات نهائياً وبدون تحميل مسبق.<br>"
            "• فلترة ذكية ثلاثية المراحل بأقل استهلاك للموارد والتوكنز.<br>"
            "• إدارة ذكية للوقت والتفريق بين المنصات المدرسية والتصفح العام.<br>"
            "• متوافق مع كافة أنظمة ويندوز (Windows 7 / 10 / 11).<br><br>"
            "انقر فوق <strong>التالي (Next)</strong> لفحص متطلبات النظام والجهوزية."
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setStyleSheet("line-height: 1.6; font-size: 14px; color: #cbd5e1;")
        layout.addWidget(lbl)

# Page 2: Diagnostics & Pre-flight
class DiagnosticsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("فحص الجهوزية والأدوات والمتصفحات 🔍")
        self.checker = SystemPreflightChecker()
        layout = QVBoxLayout(self)

        self.grp_res = QGroupBox("مواصفات الجهاز والنظام:")
        v_res = QVBoxLayout(self.grp_res)
        self.lbl_res = QLabel("جاري فحص الموارد...")
        v_res.addWidget(self.lbl_res)
        layout.addWidget(self.grp_res)

        self.grp_browsers = QGroupBox("المتصفحات المكتشفة على الجهاز:")
        self.v_browsers = QVBoxLayout(self.grp_browsers)
        layout.addWidget(self.grp_browsers)

        # Brave auto download box
        self.grp_brave = QGroupBox("متصفح Brave الآمن للأطفال (موصى به):")
        v_brave = QVBoxLayout(self.grp_brave)
        self.chk_install_brave = QCheckBox("تحميل وتثبيت متصفح Brave الرسمي المعتمد تلقائياً")
        self.chk_install_brave.setChecked(True)
        self.lbl_brave_status = QLabel("يوفر Brave أفضل حماية تلقائية مدمجة ضد الإعلانات والمتعقبات.")
        self.lbl_brave_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        v_brave.addWidget(self.chk_install_brave)
        v_brave.addWidget(self.lbl_brave_status)
        layout.addWidget(self.grp_brave)

    def initializePage(self):
        # Scan resources
        res = self.checker.check_system_resources()
        win_label = "Windows 7 (متوافق مع مكتبات التوافق)" if res["is_win7"] else res["os"]
        self.lbl_res.setText(
            f"<b style='color:#f8fafc;'>• نظام التشغيل:</b> <span style='color:#38bdf8;'>{win_label}</span><br>"
            f"<b style='color:#f8fafc;'>• الذاكرة العشوائية:</b> <span style='color:#10b981;'>{res['total_ram_gb']} GB</span> (المتاح: {res['avail_ram_gb']} GB) ✅<br>"
            f"<b style='color:#f8fafc;'>• أنوية المعالج:</b> <span style='color:#10b981;'>{res['cpu_cores']} Cores</span> ✅"
        )
        self.lbl_res.setTextFormat(Qt.TextFormat.RichText)

        # Scan browsers
        while self.v_browsers.count():
            item = self.v_browsers.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        browsers = self.checker.detect_browsers()
        for b_id, b_info in browsers.items():
            status = "مثبت ومكتشف ✅" if b_info["installed"] else "غير مثبت ❌"
            color = "#10b981" if b_info["installed"] else "#ef4444"
            l = QLabel(f"<b style='color:#f8fafc;'>• {b_info['name']}:</b> <span style='color:{color}; font-weight:bold;'>{status}</span>")
            l.setTextFormat(Qt.TextFormat.RichText)
            self.v_browsers.addWidget(l)

        # If Brave is already installed, hide the download checkbox
        if browsers["brave"]["installed"]:
            self.grp_brave.setVisible(False)
            self.chk_install_brave.setChecked(False)
        else:
            self.grp_brave.setVisible(True)
            self.chk_install_brave.setChecked(True)

# Page 3: Protection & Extensions Config
class ConfigPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("خيارات الحماية والإضافات وتعيين كلمة المرور ⚙️")
        layout = QVBoxLayout(self)

        grp_opt = QGroupBox("خيارات الحماية الإجبارية:")
        v_opt = QVBoxLayout(grp_opt)
        self.chk_ext = QCheckBox("تثبيت إضافة حصين تلقائياً في Chrome و Edge و Brave")
        self.chk_ext.setChecked(True)
        self.chk_policy = QCheckBox("قفل إعدادات البروكسي وتعطيل التصفح الخفي (Incognito)")
        self.chk_policy.setChecked(True)
        self.chk_firewall = QCheckBox("تكوين قواعد جدار حماية ويندوز تلقائياً للسماح بالمنفذ المحلي 8089")
        self.chk_firewall.setChecked(True)
        v_opt.addWidget(self.chk_ext)
        v_opt.addWidget(self.chk_policy)
        v_opt.addWidget(self.chk_firewall)
        layout.addWidget(grp_opt)

        # Password configuration with verification & existing password check
        sec = SecurityManager()
        stored_hash = sec.db.get_setting("admin_password_hash", "")
        self.has_existing_pwd = bool(stored_hash and stored_hash != "$2b$12$K1fK72eD0p6tFq49oTzN.OMkEreZ9vE7N0nE2eFvA/fF9GfO8mG4u") # check if customized
        
        grp_pass = QGroupBox("حماية كلمة مرور ولي الأمر:")
        v_pass = QVBoxLayout(grp_pass)
        
        if self.has_existing_pwd:
            self.chk_keep_pwd = QCheckBox("الإبقاء على كلمة المرور الحالية المحفوظة دون تغيير (موصى به) 🔒")
            self.chk_keep_pwd.setChecked(True)
            self.chk_keep_pwd.setStyleSheet("color: #10b981; font-weight: bold;")
            v_pass.addWidget(self.chk_keep_pwd)
        else:
            self.chk_keep_pwd = None
            
        lbl_p = QLabel("كلمة المرور هذه تحمي لوحة التحكم وتمنع الطفل من إغلاق أو حذف البرنامج:")
        lbl_p.setStyleSheet("color: #94a3b8; font-size: 12px;")
        v_pass.addWidget(lbl_p)

        self.in_pwd = QLineEdit()
        self.in_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_pwd.setPlaceholderText("كلمة المرور الجديدة")
        if not self.has_existing_pwd:
            self.in_pwd.setText("haseen2026")
            
        self.in_pwd_confirm = QLineEdit()
        self.in_pwd_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_pwd_confirm.setPlaceholderText("تأكيد كلمة المرور الجديدة")
        if not self.has_existing_pwd:
            self.in_pwd_confirm.setText("haseen2026")
            
        self.chk_show_wiz_pwd = QCheckBox("👁️ إظهار كلمة المرور للتأكد")
        self.chk_show_wiz_pwd.setStyleSheet("color: #38bdf8;")
        self.chk_show_wiz_pwd.toggled.connect(self._toggle_wiz_pwd)

        v_pass.addWidget(self.in_pwd)
        v_pass.addWidget(self.in_pwd_confirm)
        v_pass.addWidget(self.chk_show_wiz_pwd)
        
        if self.chk_keep_pwd:
            def on_keep_toggled(checked):
                self.in_pwd.setEnabled(not checked)
                self.in_pwd_confirm.setEnabled(not checked)
                self.chk_show_wiz_pwd.setEnabled(not checked)
            self.chk_keep_pwd.toggled.connect(on_keep_toggled)
            on_keep_toggled(True)
            
        layout.addWidget(grp_pass)

    def _toggle_wiz_pwd(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.in_pwd.setEchoMode(mode)
        self.in_pwd_confirm.setEchoMode(mode)

# Page 4: Install Progress
class InstallPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("جاري التثبيت والتهيئة ⏳")
        layout = QVBoxLayout(self)

        self.lbl_status = QLabel("جاهز لبدء التثبيت...")
        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(10)

        layout.addWidget(self.lbl_status)
        layout.addWidget(self.prog_bar)

    def initializePage(self):
        self.lbl_status.setText("جاري ضبط سياسات المتصفحات وجدار الحماية...")
        self.prog_bar.setValue(30)
        QApplication.processEvents()

        # Apply security policies
        sec = SecurityManager()
        p2 = self.wizard().page(2)
        should_set_pwd = True
        if hasattr(p2, 'chk_keep_pwd') and p2.chk_keep_pwd and p2.chk_keep_pwd.isChecked():
            should_set_pwd = False
            
        if should_set_pwd:
            pwd = p2.in_pwd.text().strip()
            if pwd:
                sec.set_admin_password(pwd)

        if self.wizard().page(2).chk_policy.isChecked():
            sec.apply_browser_registry_policies()

        if self.wizard().page(2).chk_firewall.isChecked():
            checker = SystemPreflightChecker()
            checker.setup_firewall_rules_automatic()

        self.prog_bar.setValue(60)
        self.lbl_status.setText("جاري إعداد قواعد البيانات والتهيئة...")
        QApplication.processEvents()

        # Download Brave if requested
        if self.wizard().page(1).chk_install_brave.isChecked():
            self.lbl_status.setText("جاري تثبيت متصفح Brave...")
            self.thread = BraveDownloaderThread()
            self.thread.progress_signal.connect(self.lbl_status.setText)
            self.thread.finished_signal.connect(self.on_brave_finished)
            self.thread.start()
        else:
            self.finish_install()

    def on_brave_finished(self, ok, msg):
        self.finish_install()

    def finish_install(self):
        # Create Desktop Shortcut with hassen_icon.ico
        try:
            desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
            shortcut_path = os.path.join(desktop, "حَصِين للأطفال.lnk")
            icon_path = os.path.join(BASE_DIR, "hassen_icon.ico")
            target_path = os.path.join(BASE_DIR, "scripts", "run_all.bat")
            vbs = f"""
Set ws = CreateObject("WScript.Shell")
Set sc = ws.CreateShortcut("{shortcut_path}")
sc.TargetPath = "{target_path}"
sc.WorkingDirectory = "{BASE_DIR}"
sc.IconLocation = "{icon_path},0"
sc.Description = "حَصِين للأطفال | Haseen Kids"
sc.Save
"""
            vbs_file = os.path.join(BASE_DIR, "temp_shortcut.vbs")
            with open(vbs_file, "w", encoding="utf-8") as f:
                f.write(vbs)
            subprocess.run(["cscript", "//nologo", vbs_file], shell=True)
            if os.path.exists(vbs_file):
                os.remove(vbs_file)
        except Exception:
            pass

        self.prog_bar.setValue(100)
        self.lbl_status.setText("اكتمل التثبيت والتهيئة بنجاح! ✅")

# Page 5: Completion
class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("تم التثبيت بنجاح 🎉")
        layout = QVBoxLayout(self)

        lbl = QLabel(
            "تهانينا! تم تثبيت برنامج <strong>حَصِين للأطفال</strong> وتكوين إعدادات الحماية بنجاح.<br><br>"
            "• تم ضبط المتصفحات وجدار الحماية تلقائياً.<br>"
            "• كلمة مرور ولي الأمر الافتراضية مفعلة.<br>"
            "• يمكنك تشغيل البرنامج في أي وقت من خلال اختصار البرنامج.<br><br>"
            "انقر فوق <strong>إنهاء (Finish)</strong> لبدء حماية أطفالك فوراً."
        )
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setStyleSheet("line-height: 1.6; font-size: 14px; color: #cbd5e1;")
        layout.addWidget(lbl)

        self.chk_launch = QCheckBox("تشغيل برنامج حصين للأطفال الآن 🚀")
        self.chk_launch.setChecked(True)
        layout.addWidget(self.chk_launch)

class HaseenSetupWizard(QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("معالج تثبيت حَصِين للأطفال | Haseen Kids Setup")
        self.resize(680, 520)
        self.setWizardStyle(QWizard.WizardStyle.ClassicStyle)
        self.setStyleSheet(STYLE_WIZARD)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        from PyQt6.QtGui import QColor, QPalette
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#0f172a"))
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#f8fafc"))
        pal.setColor(QPalette.ColorRole.Base, QColor("#1e293b"))
        pal.setColor(QPalette.ColorRole.Text, QColor("#f8fafc"))
        pal.setColor(QPalette.ColorRole.Button, QColor("#1e293b"))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor("#f8fafc"))
        self.setPalette(pal)

        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setButtonText(QWizard.WizardButton.NextButton, "التالي >")
        self.setButtonText(QWizard.WizardButton.BackButton, "< السابق")
        self.setButtonText(QWizard.WizardButton.FinishButton, "إنهاء وتفعيل ✅")
        self.setButtonText(QWizard.WizardButton.CancelButton, "إلغاء ❌")

        self.addPage(WelcomePage())
        self.addPage(DiagnosticsPage())
        self.addPage(ConfigPage())
        self.addPage(InstallPage())
        self.addPage(FinishPage())

        self.accepted.connect(self.on_finish)

    def on_finish(self):
        finish_page = self.page(4)
        if hasattr(finish_page, 'chk_launch') and finish_page.chk_launch.isChecked():
            # Launch app
            py_exe = sys.executable
            app_script = os.path.join(BASE_DIR, "run.py")
            subprocess.Popen([py_exe, app_script], cwd=BASE_DIR)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = HaseenSetupWizard()
    wizard.show()
    sys.exit(app.exec())
