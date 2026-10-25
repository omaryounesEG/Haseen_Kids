import hmac
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager

SECRET_SALT = b"HaseenKids_Secure_Approval_Salt_2026"

class ApprovalManager:
    def __init__(self, db=None):
        self.db = db or DBManager()

    def generate_codes(self, domain):
        """
        Generates 6-digit deterministic HMAC-SHA256 codes tied to domain and today's date:
        - Code 1: Permanent domain unlock
        - Code 2: 30-minute temporary extension
        """
        today = date.today().isoformat()
        
        # Permanent code
        data_perm = f"{today}:{domain.lower()}:PERMANENT".encode('utf-8')
        h_perm = hmac.new(SECRET_SALT, data_perm, hashlib.sha256).hexdigest()
        code_perm = str(int(h_perm[:8], 16) % 900000 + 100000)

        # Temp 30m code
        data_temp = f"{today}:{domain.lower()}:TEMP30".encode('utf-8')
        h_temp = hmac.new(SECRET_SALT, data_temp, hashlib.sha256).hexdigest()
        code_temp = str(int(h_temp[:8], 16) % 900000 + 100000)

        return code_perm, code_temp

    def create_and_send_request(self, domain, url, child_reason):
        """
        Records the exception request in SQLite and sends notification email to the parent.
        """
        code_perm, code_temp = self.generate_codes(domain)
        exc_id = self.db.add_exception_request(domain, url, child_reason, code_perm, code_temp)

        # Send Email
        success, err = self.send_parent_email(domain, url, child_reason, code_perm, code_temp)
        if success:
            return True, "تم إرسال الطلب لبريد ولي الأمر بنجاح", code_perm, code_temp
        else:
            return True, f"تم تسجيل الطلب محلياً (تعذر إرسال الإيميل: {err})", code_perm, code_temp

    def send_parent_email(self, domain, url, child_reason, code_perm, code_temp):
        settings = self.db.get_all_settings()
        parent_email = settings.get("parent_email")
        smtp_user = settings.get("smtp_user")
        smtp_pass = settings.get("smtp_app_password")
        smtp_server = settings.get("smtp_server", "smtp.gmail.com")
        smtp_port = int(settings.get("smtp_port", 587))

        if not smtp_user or not smtp_pass or not parent_email:
            return False, "إعدادات SMTP أو بريد الأب غير مكتملة في لوحة التحكم"

        subject = f"🛡️ [حصين] طلب إذن جديد من طفلك لتصفح موقع: {domain}"

        html = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif; background-color: #f8fafc; padding: 25px; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 25px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 15px; margin-bottom: 20px;">
                    <h2 style="color: #1e3a8a; margin: 0;">🛡️ نظام حصين للرقابة الأبوية</h2>
                    <p style="color: #64748b; font-size: 14px; margin: 5px 0 0 0;">طلب استثناء وموافقة فورية</p>
                </div>
                
                <p style="font-size: 16px;">مرحباً ولي الأمر الكريم،</p>
                <p style="font-size: 15px; line-height: 1.6;">
                    قام طفلك بمحاولة فتح الرابط التالي المحجوب وطلب إذناً بالدخول:
                </p>
                
                <div style="background: #f1f5f9; padding: 12px 16px; border-radius: 8px; font-size: 14px; margin-bottom: 15px;">
                    <strong>الموقع:</strong> <span style="color: #2563eb; font-family: monospace;">{domain}</span><br>
                    <strong>سبب طلب الطفل:</strong> <span style="color: #0f172a; font-style: italic;">"{child_reason}"</span><br>
                    <strong>التاريخ والوقت:</strong> {datetime.now().strftime("%Y-%m-%d %I:%M %p")}
                </div>

                <h3 style="color: #0f172a; margin-top: 20px; font-size: 16px;">خيارات الموافقة (اختر ما يناسبك وزود طفلك بالرمز المناسب):</h3>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; background: #ecfdf5; width: 50%;">
                            <span style="color: #047857; font-weight: bold; font-size: 14px;">🔓 الخيار 1: فتح الموقع بشكل دائم</span><br>
                            <span style="font-size: 12px; color: #475569;">يضيف الموقع للقائمة البيضاء المسموحة دائماً.</span>
                            <div style="font-size: 24px; font-weight: bold; color: #065f46; letter-spacing: 4px; margin-top: 8px; text-align: center; background: white; padding: 6px; border-radius: 6px; border: 1px solid #a7f3d0;">
                                {code_perm}
                            </div>
                        </td>
                        <td style="padding: 12px; border: 1px solid #e2e8f0; background: #eff6ff; width: 50%;">
                            <span style="color: #1d4ed8; font-weight: bold; font-size: 14px;">⏱️ الخيار 2: تمديد وقت مؤقت (30 دقيقة)</span><br>
                            <span style="font-size: 12px; color: #475569;">يفتح الموقع لمدة نصف ساعة فقط ثم يعود للحجب.</span>
                            <div style="font-size: 24px; font-weight: bold; color: #1e40af; letter-spacing: 4px; margin-top: 8px; text-align: center; background: white; padding: 6px; border-radius: 6px; border: 1px solid #bfdbfe;">
                                {code_temp}
                            </div>
                        </td>
                    </tr>
                </table>

                <p style="font-size: 13px; color: #94a3b8; margin-top: 25px; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 15px;">
                    تم إنشاء هذا البريد تلقائياً من جهاز طفلك عبر برنامج حصين | Haseen Kids.
                </p>
            </div>
        </div>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = parent_email
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        try:
            clean_pass = smtp_pass.replace(" ", "")
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, clean_pass)
                server.sendmail(smtp_user, parent_email, msg.as_string())
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def test_smtp_connection(smtp_user, smtp_pass, smtp_server="smtp.gmail.com", smtp_port=587):
        """
        Tests SMTP connectivity and authentication with Gmail/custom SMTP server.
        """
        if not smtp_user or not smtp_pass:
            return False, "يرجى إدخال عنوان البريد وكلمة مرور التطبيق أولاً"
        clean_pass = smtp_pass.replace(" ", "")
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=8) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, clean_pass)
            return True, "تم الاتصال بنجاح بسيرفر البريد! كلمة المرور صحيحة ومفعلة للإرسال والاستقبال ✅"
        except smtplib.SMTPAuthenticationError as e:
            return False, f"فشل تسجيل الدخول: تأكد من استخدام كلمة مرور التطبيق المكونة من 16 حرفاً من حساب Google. الخطأ: {e}"
        except Exception as e:
            return False, f"تعذر الاتصال بسيرفر البريد: {str(e)}"

if __name__ == "__main__":
    am = ApprovalManager()
    p, t = am.generate_codes("scratch.mit.edu")
    print(f"Sample generated approval codes for scratch.mit.edu -> Permanent: {p}, Temp: {t}")
