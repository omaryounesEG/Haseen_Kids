import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from database.db_manager import DBManager
from core.security import SecurityManager

class AdminEmergencyResetDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("استرجاع كلمة مرور ولي الأمر (صلاحيات المسؤول)")
        self.setFixedSize(400, 260)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        icon_path = os.path.join(BASE_DIR, "hassen_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout(self)
        title = QLabel("إعادة تعيين كلمة مرور ولي الأمر (طوارئ 🛡️):")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #0284c7;")
        layout.addWidget(title)

        lbl_desc = QLabel("تم التحقق من صلاحيات مسؤول الجهاز (Administrator).\nيمكنك الآن إدخال كلمة مرور جديدة للبرنامج:")
        lbl_desc.setStyleSheet("color: #475569; font-size: 12px;")
        layout.addWidget(lbl_desc)

        self.in_p1 = QLineEdit()
        self.in_p1.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_p1.setPlaceholderText("كلمة المرور الجديدة")

        self.in_p2 = QLineEdit()
        self.in_p2.setEchoMode(QLineEdit.EchoMode.Password)
        self.in_p2.setPlaceholderText("تأكيد كلمة المرور الجديدة")

        self.chk_show = QCheckBox("👁️ إظهار كلمة المرور للتأكد")
        self.chk_show.toggled.connect(self.toggle_show)

        layout.addWidget(self.in_p1)
        layout.addWidget(self.in_p2)
        layout.addWidget(self.chk_show)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("حفظ كلمة المرور الجديدة ✅")
        btn_save.setStyleSheet("background-color: #10b981; color: white; padding: 8px; font-weight: bold;")
        btn_save.clicked.connect(self.save_new_pwd)
        btn_cancel = QPushButton("إلغاء ❌")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def toggle_show(self, checked):
        m = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.in_p1.setEchoMode(m)
        self.in_p2.setEchoMode(m)

    def save_new_pwd(self):
        p1 = self.in_p1.text().strip()
        p2 = self.in_p2.text().strip()

        if len(p1) < 4:
            QMessageBox.warning(self, "تنبيه", "يجب أن تكون كلمة المرور 4 أحرف أو أرقام على الأقل.")
            return

        if p1 != p2:
            QMessageBox.warning(self, "عدم تطابق", "كلمتا المرور غير متطابقتين! يرجى إعادة التحقق.")
            return

        sec = SecurityManager()
        sec.set_admin_password(p1)
        QMessageBox.information(self, "تم النجاح", "تم تعيين كلمة مرور ولي الأمر الجديدة بنجاح! ✅")
        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = AdminEmergencyResetDialog()
    dlg.exec()
