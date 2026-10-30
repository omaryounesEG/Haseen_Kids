import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DBManager

WHITELIST_DOMAINS = [
    # Egyptian & Arab Educational & Government platforms
    ("moe.gov.eg", "SCHOOL", "ALLOW", "LIST_WHITELIST", "وزارة التربية والتعليم المصرية"),
    ("emis.gov.eg", "SCHOOL", "ALLOW", "LIST_WHITELIST", "بوابة مركز المعلومات وزارة التربية والتعليم"),
    ("ekb.eg", "EDU", "ALLOW", "LIST_WHITELIST", "بنك المعرفة المصري"),
    ("edmodo.org", "EDU", "ALLOW", "LIST_WHITELIST", "منصة إدمودو التعليمية"),
    ("nafham.com", "EDU", "ALLOW", "LIST_WHITELIST", "منصة نفهم التعليمية"),
    ("moe.gov.sa", "SCHOOL", "ALLOW", "LIST_WHITELIST", "وزارة التعليم السعودية"),
    ("madrasati.sa", "SCHOOL", "ALLOW", "LIST_WHITELIST", "منصة مدرستي"),
    ("tawakkalna.sdaia.gov.sa", "SCHOOL", "ALLOW", "LIST_WHITELIST", "توكلنا"),
    ("ien.edu.sa", "SCHOOL", "ALLOW", "LIST_WHITELIST", "بوابة عين التعليمية"),
    ("noor.moe.gov.sa", "SCHOOL", "ALLOW", "LIST_WHITELIST", "نظام نور"),
    
    # Global Educational & Safe Children Sites
    ("wikipedia.org", "EDU", "ALLOW", "LIST_WHITELIST", "ويكيبيديا"),
    ("ar.wikipedia.org", "EDU", "ALLOW", "LIST_WHITELIST", "ويكيبيديا العربية"),
    ("khanacademy.org", "EDU", "ALLOW", "LIST_WHITELIST", "Khan Academy"),
    ("ar.khanacademy.org", "EDU", "ALLOW", "LIST_WHITELIST", "خان أكاديمي بالعربي"),
    ("scratch.mit.edu", "EDU", "ALLOW", "LIST_WHITELIST", "Scratch MIT"),
    ("code.org", "EDU", "ALLOW", "LIST_WHITELIST", "Code.org تعلم البرمجة"),
    ("duolingo.com", "EDU", "ALLOW", "LIST_WHITELIST", "Duolingo"),
    ("natgeokids.com", "EDU", "ALLOW", "LIST_WHITELIST", "National Geographic Kids"),
    ("kids.nationalgeographic.com", "EDU", "ALLOW", "LIST_WHITELIST", "National Geographic Kids"),
    ("pbskids.org", "EDU", "ALLOW", "LIST_WHITELIST", "PBS Kids"),
    ("funbrain.com", "EDU", "ALLOW", "LIST_WHITELIST", "Funbrain"),
    ("starfall.com", "EDU", "ALLOW", "LIST_WHITELIST", "Starfall Education"),
    ("coursera.org", "EDU", "ALLOW", "LIST_WHITELIST", "Coursera"),
    ("edx.org", "EDU", "ALLOW", "LIST_WHITELIST", "edX"),
    ("google.com", "SAFE", "ALLOW", "LIST_WHITELIST", "Google Search (SafeSearch enforced)"),
    ("classroom.google.com", "SCHOOL", "ALLOW", "LIST_WHITELIST", "Google Classroom"),
    ("drive.google.com", "SCHOOL", "ALLOW", "LIST_WHITELIST", "Google Drive"),
    ("docs.google.com", "SCHOOL", "ALLOW", "LIST_WHITELIST", "Google Docs"),
    ("teams.microsoft.com", "SCHOOL", "ALLOW", "LIST_WHITELIST", "Microsoft Teams Education"),
    ("zoom.us", "SCHOOL", "ALLOW", "LIST_WHITELIST", "Zoom Meetings"),
    ("classera.com", "SCHOOL", "ALLOW", "LIST_WHITELIST", "منصة كلاسيرا التعليمية"),
    ("office.com", "SCHOOL", "ALLOW", "LIST_WHITELIST", "Microsoft Office Online"),
    ("w3schools.com", "EDU", "ALLOW", "LIST_WHITELIST", "W3Schools تعلّم البرمجة"),
    ("weforum.org", "EDU", "ALLOW", "LIST_WHITELIST", "World Economic Forum"),
    ("britishcouncil.org", "EDU", "ALLOW", "LIST_WHITELIST", "British Council Learn English"),
    ("ted.com", "EDU", "ALLOW", "LIST_WHITELIST", "TED Talks"),
    ("nasa.gov", "EDU", "ALLOW", "LIST_WHITELIST", "NASA Kids & Education"),
    ("si.edu", "EDU", "ALLOW", "LIST_WHITELIST", "Smithsonian Museums")
]

BLACKLIST_DOMAINS = [
    # Proxy / VPN bypass sites
    ("proxysite.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Web Proxy Bypass"),
    ("hide.me", "ADULT", "BLOCK", "LIST_BLACKLIST", "Web Proxy / VPN"),
    ("kproxy.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Web Proxy"),
    ("croxyproxy.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Web Proxy"),
    ("vpnbook.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Proxy / VPN"),
    ("megaproxy.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Web Proxy"),
    ("whoer.net", "ADULT", "BLOCK", "LIST_BLACKLIST", "Anonymity / Proxy"),
    ("hidemyass.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "VPN / Proxy"),
    ("torproject.org", "ADULT", "BLOCK", "LIST_BLACKLIST", "Tor Anonymizer"),
    ("nordvpn.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "VPN Client"),
    ("expressvpn.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "VPN Client"),

    # Adult / Inappropriate Categories
    ("pornhub.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Adult Content"),
    ("xvideos.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Adult Content"),
    ("xnxx.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Adult Content"),
    ("redtube.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Adult Content"),
    ("xhamster.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Adult Content"),
    ("onlyfans.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Adult Content"),
    ("chaturbate.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Adult Content"),
    ("omegle.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Unsafe Anonymous Chat"),
    ("omegle.onl", "ADULT", "BLOCK", "LIST_BLACKLIST", "Unsafe Anonymous Chat"),
    ("chatrandom.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Unsafe Anonymous Chat"),
    ("bazoocam.org", "ADULT", "BLOCK", "LIST_BLACKLIST", "Unsafe Anonymous Chat"),
    ("chathub.cam", "ADULT", "BLOCK", "LIST_BLACKLIST", "Unsafe Anonymous Chat"),

    # Gambling & Betting
    ("bet365.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Gambling"),
    ("1xbet.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Gambling"),
    ("888casino.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Gambling"),
    ("pokerstars.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Gambling"),
    ("bwin.com", "ADULT", "BLOCK", "LIST_BLACKLIST", "Gambling"),

    # Violence & Gore & Dangerous
    ("bestgore.com", "VIOLENCE", "BLOCK", "LIST_BLACKLIST", "Violence / Gore"),
    ("crazyshit.com", "VIOLENCE", "BLOCK", "LIST_BLACKLIST", "Gore & Harmful Content"),
    ("kaotic.com", "VIOLENCE", "BLOCK", "LIST_BLACKLIST", "Gore & Violence")
]

def seed_database(only_if_empty=False, include_lists=True):
    db = DBManager()

    if only_if_empty:
        existing = len(db.list_rules())
        if existing > 0:
            print(f"[SKIP] {existing} domain rules already present - lists not touched.")
            return 0, 0

    count_white = 0
    count_black = 0

    for item in WHITELIST_DOMAINS:
        domain, cat, act, src, title = item
        db.save_domain_decision(domain, act, cat, src, title)
        count_white += 1

    for item in BLACKLIST_DOMAINS:
        domain, cat, act, src, title = item
        db.save_domain_decision(domain, act, cat, src, title)
        count_black += 1

    print(f"Successfully seeded Tier-1 lists: {count_white} whitelist domains, {count_black} blacklist domains.")
    return count_white, count_black


if __name__ == "__main__":
    seed_database(only_if_empty="--if-empty" in sys.argv)
