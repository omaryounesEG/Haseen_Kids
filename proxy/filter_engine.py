import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import DBManager

class SmartFilterEngine:
    def __init__(self, db=None):
        self.db = db or DBManager()
        self._load_keys()

    def _load_keys(self):
        self.gemini_key = self.db.get_setting("gemini_api_key", "")
        self.deepseek_key = self.db.get_setting("deepseek_api_key", "")
        self.groq_key = self.db.get_setting("groq_api_key", "")
        self.openrouter_key = self.db.get_setting("openrouter_api_key", "")
        self.ai_provider = self.db.get_setting("ai_provider", "gemini")

    def evaluate_url(self, url):
        """
        Executes the 3-Tier filtering funnel.
        Returns:
            action: 'ALLOW' | 'BLOCK' | 'REDIRECT_YOUTUBE' | 'BEDTIME' | 'TIME_EXPIRED'
            category: 'SAFE' | 'EDU' | 'SCHOOL' | 'GAMING' | 'ADULT' | 'VIOLENCE'
            reason: Explanation
            source: 'LIST_WHITELIST' | 'LIST_BLACKLIST' | 'AI_CACHE' | 'AI_EVALUATED' | 'QUOTA'
        """
        self._load_keys()
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if ':' in domain:
            domain = domain.split(':')[0]
        path = parsed.path

        # 0. Check for YouTube Watch redirection
        if "youtube.com" in domain or "youtu.be" in domain:
            if "watch" in path or "youtu.be/" in url or "shorts" in path:
                clean_mode = self.db.get_setting("youtube_clean_mode", "1")
                if clean_mode == "1":
                    return "REDIRECT_YOUTUBE", "YOUTUBE", "Clean YouTube Player Redirect", "YOUTUBE_ENGINE"

        # Check Bedtime and Quota first
        today_sched = self.db.get_today_schedule()
        today_usage = self.db.get_today_usage()

        # Check Bedtime
        now_time = datetime.now().strftime("%H:%M")
        bed_start = today_sched.get("bedtime_start", "21:00")
        bed_end = today_sched.get("bedtime_end", "07:00")
        is_bedtime = False
        if bed_start > bed_end:
            # Over midnight (e.g. 21:00 to 07:00)
            if now_time >= bed_start or now_time < bed_end:
                is_bedtime = True
        else:
            if bed_start <= now_time < bed_end:
                is_bedtime = True

        # Tier 1 & 2: Check SQLite Database (Local Lists & AI Cache)
        cached = self.db.get_domain_decision(domain)
        if cached:
            action, category, source = cached
            # School platforms bypass bedtime and time quotas
            if category in ["SCHOOL", "EDU"]:
                return "ALLOW", category, "School / Educational Platform", source

            if is_bedtime:
                return "BEDTIME", category, f"وقت النوم مفعل ({bed_start} - {bed_end})", "BEDTIME"

            # Check quota for entertainment vs general
            if category in ["ENTERTAINMENT", "GAMING", "YOUTUBE"]:
                ent_limit_sec = today_sched["entertainment_limit_mins"] * 60
                if today_usage["entertainment_seconds"] >= ent_limit_sec:
                    return "TIME_EXPIRED", category, "انتهت حصة الترفيه المحددة لليوم", "QUOTA"
            else:
                gen_limit_sec = today_sched["general_limit_mins"] * 60
                if today_usage["general_seconds"] >= gen_limit_sec:
                    return "TIME_EXPIRED", category, "انتهت حصة التصفح العام لليوم", "QUOTA"

            return action, category, f"قاعدة محلية: {category}", source

        # If domain is totally new:
        if is_bedtime:
            return "BEDTIME", "UNKNOWN", f"وقت النوم مفعل ({bed_start} - {bed_end})", "BEDTIME"

        # Tier 3: Micro-Prompting AI query
        action, category, reason, src = self._classify_via_ai(domain, url)

        # Apply quota restrictions to AI-determined category
        if category in ["ENTERTAINMENT", "GAMING"]:
            ent_limit_sec = today_sched["entertainment_limit_mins"] * 60
            if today_usage["entertainment_seconds"] >= ent_limit_sec:
                return "TIME_EXPIRED", category, "انتهت حصة الترفيه المحددة لليوم", "QUOTA"
        elif category not in ["SCHOOL", "EDU"]:
            gen_limit_sec = today_sched["general_limit_mins"] * 60
            if today_usage["general_seconds"] >= gen_limit_sec:
                return "TIME_EXPIRED", category, "انتهت حصة التصفح العام لليوم", "QUOTA"

        return action, category, reason, src

    def _extract_page_metadata(self, url):
        """Fetches only the head of the page to extract Title and Meta Description"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) HaseenKids/1.0'}
            # Limit download to first 15KB to save bandwidth and time
            with requests.get(url, headers=headers, timeout=2.5, stream=True) as r:
                chunk = r.raw.read(15000).decode('utf-8', errors='ignore')
                title_match = re.search(r'<title>(.*?)</title>', chunk, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else ""
                desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', chunk, re.IGNORECASE)
                desc = desc_match.group(1).strip() if desc_match else ""
                return title[:100], desc[:150]
        except Exception:
            return "", ""

    def _classify_via_ai(self, domain, url):
        """Tier 3: Evaluates domain using Gemini Flash or DeepSeek micro-prompt"""
        title, desc = self._extract_page_metadata(url or f"https://{domain}")

        # Check if any API keys exist
        if not any([self.gemini_key, self.deepseek_key, self.groq_key, self.openrouter_key]):
            action = "ALLOW"
            category = "SAFE"
            self.db.save_domain_decision(domain, action, category, "DEFAULT_FALLBACK", title=title)
            return action, category, "Default fallback (no AI key)", "DEFAULT_FALLBACK"

        prompt = {
            "sys": "Classify website for child safety. Reply ONLY with JSON: {\"cat\": \"SAFE|EDU|GAMING|ADULT|VIOLENCE\", \"act\": \"ALLOW|BLOCK\"}",
            "domain": domain,
            "title": title,
            "desc": desc
        }

        # Query Groq (Ultra-fast)
        if self.ai_provider == "groq" and self.groq_key:
            try:
                headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": "Classify website for child safety. Reply strictly JSON: {\"cat\": \"SAFE|EDU|GAMING|ADULT|VIOLENCE\", \"act\": \"ALLOW|BLOCK\"}"},
                        {"role": "user", "content": f"URL: {domain}, Title: {title}, Description: {desc}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 50
                }
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=2.5)
                if r.status_code == 200:
                    content = r.json()['choices'][0]['message']['content']
                    m = re.search(r'\{.*\}', content, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        act = data.get("act", "BLOCK")
                        cat = data.get("cat", "SAFE")
                        self.db.save_domain_decision(domain, act, cat, "AI_GROQ", title=title)
                        return act, cat, f"تصنيف ذكي (Groq): {cat}", "AI_GROQ"
            except Exception:
                pass

        # Query OpenRouter (Free Tier)
        if self.ai_provider == "openrouter" and self.openrouter_key:
            try:
                headers = {"Authorization": f"Bearer {self.openrouter_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "deepseek/deepseek-chat:free",
                    "messages": [
                        {"role": "system", "content": "Classify website for child safety. Reply strictly JSON: {\"cat\": \"SAFE|EDU|GAMING|ADULT|VIOLENCE\", \"act\": \"ALLOW|BLOCK\"}"},
                        {"role": "user", "content": f"URL: {domain}, Title: {title}, Description: {desc}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 50
                }
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=3.5)
                if r.status_code == 200:
                    content = r.json()['choices'][0]['message']['content']
                    m = re.search(r'\{.*\}', content, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        act = data.get("act", "BLOCK")
                        cat = data.get("cat", "SAFE")
                        self.db.save_domain_decision(domain, act, cat, "AI_OPENROUTER", title=title)
                        return act, cat, f"تصنيف ذكي (OpenRouter Free): {cat}", "AI_OPENROUTER"
            except Exception:
                pass

        # Query Gemini
        if self.ai_provider == "gemini" and self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(json.dumps(prompt))
                text = res.text.strip()
                # Extract json
                m = re.search(r'\{.*\}', text, re.DOTALL)
                if m:
                    data = json.loads(m.group(0))
                    act = data.get("act", "BLOCK")
                    cat = data.get("cat", "SAFE")
                    self.db.save_domain_decision(domain, act, cat, "AI_GEMINI", title=title)
                    return act, cat, f"تم تصنيف الموقع بالذكاء الاصطناعي: {cat}", "AI_GEMINI"
            except Exception as e:
                pass

        # Query DeepSeek
        if self.deepseek_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.deepseek_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a child safety web filter. Respond strictly with JSON: {\"cat\": \"SAFE|EDU|GAMING|ADULT|VIOLENCE\", \"act\": \"ALLOW|BLOCK\"}"},
                        {"role": "user", "content": f"URL: {domain}, Title: {title}, Description: {desc}"}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 50
                }
                r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=3.5)
                if r.status_code == 200:
                    content = r.json()['choices'][0]['message']['content']
                    m = re.search(r'\{.*\}', content, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        act = data.get("act", "BLOCK")
                        cat = data.get("cat", "SAFE")
                        self.db.save_domain_decision(domain, act, cat, "AI_DEEPSEEK", title=title)
                        return act, cat, f"تصنيف ذكي (DeepSeek): {cat}", "AI_DEEPSEEK"
            except Exception:
                pass

        # Heuristic fallback if AI network failed
        action = "ALLOW"
        category = "SAFE"
        self.db.save_domain_decision(domain, action, category, "HEURISTIC_FALLBACK", title=title)
        return action, category, "مسموح احتياطياً", "HEURISTIC_FALLBACK"

    @staticmethod
    def test_ai_provider(provider, api_key):
        """
        Tests API connectivity, validity and latency with a 1-token ping.
        """
        import time
        t0 = time.time()
        if not api_key:
            return False, "يرجى إدخال مفتاح الـ API أولاً"

        try:
            if provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content("Say PONG")
                latency = int((time.time() - t0) * 1000)
                return True, f"الاتصال بـ Google Gemini نشط وناجح! زمن الاستجابة: {latency}ms ✅"

            elif provider == "groq":
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "PONG"}], "max_tokens": 5}
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=5)
                latency = int((time.time() - t0) * 1000)
                if r.status_code == 200:
                    return True, f"الاتصال بـ Groq نشط وفائق السرعة! زمن الاستجابة: {latency}ms ⚡"
                return False, f"فشل الاتصال بـ Groq: كود {r.status_code} - {r.text[:120]}"

            elif provider == "openrouter":
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": "deepseek/deepseek-chat:free", "messages": [{"role": "user", "content": "PONG"}], "max_tokens": 5}
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=6)
                latency = int((time.time() - t0) * 1000)
                if r.status_code == 200:
                    return True, f"الاتصال بـ OpenRouter (Free) نشط وناجح! زمن الاستجابة: {latency}ms ✅"
                return False, f"فشل الاتصال بـ OpenRouter: كود {r.status_code} - {r.text[:120]}"

            elif provider == "deepseek":
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": "PONG"}], "max_tokens": 5}
                r = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=6)
                latency = int((time.time() - t0) * 1000)
                if r.status_code == 200:
                    return True, f"الاتصال بـ DeepSeek نشط ومفعل! زمن الاستجابة: {latency}ms ✅"
                return False, f"فشل الاتصال بـ DeepSeek: كود {r.status_code} - {r.text[:120]}"

            return False, f"مزود غير معروف: {provider}"
        except Exception as e:
            return False, f"حدث خطأ أثناء اختبار الاتصال: {str(e)}"

if __name__ == "__main__":
    fe = SmartFilterEngine()
    test_urls = [
        "https://moe.gov.eg/ar/home",
        "https://pornhub.com",
        "https://scratch.mit.edu",
        "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
        "https://unknown-learning-site-12345.org"
    ]
    for u in test_urls:
        act, cat, rsn, src = fe.evaluate_url(u)
        print(f"URL: {u[:40]} -> Action: {act}, Cat: {cat}, Source: {src}")
