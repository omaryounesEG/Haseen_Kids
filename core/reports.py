import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager

class WeeklyReportGenerator:
    def __init__(self, db=None):
        self.db = db or DBManager()

    def gather_week_stats(self):
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            # Usage
            cursor.execute('''
                SELECT SUM(entertainment_used_seconds), SUM(general_used_seconds), SUM(school_used_seconds)
                FROM daily_usage
                WHERE usage_date BETWEEN ? AND ?
            ''', (start_date.isoformat(), end_date.isoformat()))
            row = cursor.fetchone()
            ent_sec = row[0] or 0
            gen_sec = row[1] or 0
            sch_sec = row[2] or 0

            # Top domains
            cursor.execute('''
                SELECT domain, category, COUNT(*) as visits, SUM(duration_seconds)
                FROM activity_log
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY domain
                ORDER BY visits DESC
                LIMIT 10
            ''')
            top_domains = cursor.fetchall()

            # Blocked attempts count
            cursor.execute('''
                SELECT COUNT(*) FROM activity_log
                WHERE action IN ('BLOCK', 'BEDTIME', 'TIME_EXPIRED')
                AND timestamp >= datetime('now', '-7 days')
            ''')
            blocked_count = cursor.fetchone()[0]

        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} إلى {end_date.strftime('%Y-%m-%d')}",
            "entertainment_hours": round(ent_sec / 3600, 1),
            "general_hours": round(gen_sec / 3600, 1),
            "school_hours": round(sch_sec / 3600, 1),
            "total_hours": round((ent_sec + gen_sec + sch_sec) / 3600, 1),
            "top_domains": top_domains,
            "blocked_count": blocked_count
        }

    def generate_ai_insights(self, stats):
        settings = self.db.get_all_settings()
        gemini_key = settings.get("gemini_api_key", "")
        deepseek_key = settings.get("deepseek_api_key", "")

        prompt = (
            f"أنت خبير تربوي وتقني في برنامج حماية الأطفال 'حصين'. لخص تقرير استخدام الطفل للكمبيوتر هذا الأسبوع في 3 نقاط ذكية وموجزة موجهة لولي الأمر:\n"
            f"ساعات التعليم: {stats['school_hours']} س\n"
            f"ساعات الترفيه: {stats['entertainment_hours']} س\n"
            f"ساعات التصفح العام: {stats['general_hours']} س\n"
            f"عدد محاولات دخول المواقع المحجوبة التي تصدى لها البرنامج: {stats['blocked_count']}\n"
            f"أهم المواقع: {[d[0] for d in stats['top_domains']]}\n"
            f"اكتب التقرير بأسلوب عربي راقٍ ومشجع مع نصيحة تربوية واحدة."
        )

        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(prompt)
                return res.text.strip()
            except Exception:
                pass

        return (
            "• أظهر طفلك التزاماً جيداً بالوقت المخصص للتصفح والتعليم هذا الأسبوع.<br>"
            "• نجح نظام حصين في حماية الطفل وتأمين التصفح من أي محتوى غير لائق.<br>"
            "• نصيحة تربوية: شجع طفلك على إتمام أهدافه التعليمية أولاً قبل وقت الترفيه."
        )

    def send_weekly_digest(self):
        stats = self.gather_week_stats()
        ai_insights = self.generate_ai_insights(stats)

        settings = self.db.get_all_settings()
        parent_email = settings.get("parent_email")
        smtp_user = settings.get("smtp_user")
        smtp_pass = settings.get("smtp_app_password")
        smtp_server = settings.get("smtp_server", "smtp.gmail.com")
        smtp_port = int(settings.get("smtp_port", 587))

        if not smtp_user or not smtp_pass or not parent_email:
            return False, "إعدادات SMTP غير مكتملة"

        subject = f"📊 [حصين] التقرير الأسبوعي لنشاط طفلك ({stats['period']})"

        html = f"""
        <div dir="rtl" style="font-family: Arial, sans-serif; background-color: #f1f5f9; padding: 25px; color: #0f172a;">
            <div style="max-width: 650px; margin: 0 auto; background: white; border-radius: 12px; padding: 25px; border: 1px solid #cbd5e1; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 15px; margin-bottom: 20px;">
                    <h2 style="color: #1e3a8a; margin: 0;">🛡️ نظام حصين | التقرير الأسبوعي</h2>
                    <p style="color: #64748b; font-size: 14px; margin: 5px 0 0 0;">فترة التقرير: {stats['period']}</p>
                </div>

                <div style="display: flex; justify-content: space-between; margin-bottom: 20px; text-align: center;">
                    <div style="background: #eff6ff; padding: 12px; border-radius: 8px; flex: 1; margin: 0 4px; border: 1px solid #bfdbfe;">
                        <span style="font-size: 13px; color: #1e40af;">ساعات التعليم</span><br>
                        <strong style="font-size: 20px; color: #1d4ed8;">{stats['school_hours']} س</strong>
                    </div>
                    <div style="background: #fdf2f8; padding: 12px; border-radius: 8px; flex: 1; margin: 0 4px; border: 1px solid #fbcfe8;">
                        <span style="font-size: 13px; color: #9d174d;">ساعات الترفيه</span><br>
                        <strong style="font-size: 20px; color: #be185d;">{stats['entertainment_hours']} س</strong>
                    </div>
                    <div style="background: #ecfdf5; padding: 12px; border-radius: 8px; flex: 1; margin: 0 4px; border: 1px solid #a7f3d0;">
                        <span style="font-size: 13px; color: #065f46;">المواقع الممنوعة المحجوبة</span><br>
                        <strong style="font-size: 20px; color: #047857;">{stats['blocked_count']}</strong>
                    </div>
                </div>

                <div style="background: #f8fafc; border-right: 4px solid #3b82f6; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
                    <h3 style="color: #1e3a8a; margin-top: 0; font-size: 16px;">💡 تحليل الذكاء الاصطناعي والتوصيات الأبوية:</h3>
                    <div style="font-size: 14px; line-height: 1.7; color: #334155;">
                        {ai_insights}
                    </div>
                </div>

                <p style="font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; margin-top: 25px;">
                    تم إنشاء هذا التقرير تلقائياً بواسطة حارس الأمان "حصين | Haseen Kids".
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
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, parent_email, msg.as_string())
            return True, "تم إرسال التقرير الأسبوعي بنجاح"
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    rep = WeeklyReportGenerator()
    stats = rep.gather_week_stats()
    print("Gathered week stats:", stats)
