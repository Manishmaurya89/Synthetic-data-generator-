import math
import re
import requests
from config import LANG_CODE_MAP, OLLAMA_URL
from scripts import has_foreign_letters, script_share


BATCH_SIZE = 60
MAX_CALLS_PER_BATCH = 3
MIN_SCRIPT_SHARE = 0.7

LIST_MARKER = re.compile(r"^(?:[-*•]|\d{1,3}[.)])\s+")


def clean_output(text, language_code):
    """Turn a model reply into a list of unique sentences in the requested language.

    Drops list markers, intro lines like "Here are 60 sentences:", fragments
    under 5 characters, and lines that are mostly in another script.
    """
    cleaned = []

    for line in text.split("\n"):
        line = LIST_MARKER.sub("", line.strip()).strip()

        if line.lower().startswith("here are") or line.endswith(":"):
            continue
        if len(line) < 5:
            continue
        if script_share(line, language_code) < MIN_SCRIPT_SHARE or has_foreign_letters(line, language_code):
            continue

        cleaned.append(line)

    return list(dict.fromkeys(cleaned))


def call_llm(prompt, model):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.9}
            },
            timeout=(10, 600)
        )

        response.raise_for_status()

        return response.json().get("response", "")

    except Exception as e:
        print("LLM Error:", e)
        return None


# One prompt per language, written in that language. A natural prompt gets
# noticeably better sentences than an English one asking for another language.
# {count} and {topic} are filled in by build_prompt.
PROMPTS = {
    "eng": """
Generate {count} simple English sentences about "{topic}".

Rules:
- Use only English
- No numbering
- No explanation
- Do NOT include phrases like "Here are"
- Each sentence on a new line
""",
    "hin": """
"{topic}" विषय पर {count} सरल हिंदी वाक्य लिखें।

नियम:
- केवल हिंदी भाषा का उपयोग करें
- अंग्रेजी शब्द न लिखें
- क्रम संख्या (1,2,3) न दें
- कोई व्याख्या न दें
- हर वाक्य नई लाइन में हो
""",
    "ben": """
"{topic}" বিষয়ের উপর {count}টি সহজ বাংলা বাক্য লিখুন।

নিয়ম:
- শুধুমাত্র বাংলা ব্যবহার করুন
- ইংরেজি ব্যবহার করবেন না
- নম্বরিং করবেন না
- প্রতিটি বাক্য নতুন লাইনে লিখুন
""",
    "urd": """
"{topic}" کے بارے میں {count} آسان اردو جملے لکھیں۔

قواعد:
- صرف اردو زبان استعمال کریں
- انگریزی استعمال نہ کریں
- نمبرنگ نہ کریں
- ہر جملہ نئی لائن میں ہو
""",
    "tam": """
"{topic}" பற்றிய {count} எளிய தமிழ் வாக்கியங்களை எழுதுங்கள்.

விதிகள்:
- தமிழ் மட்டும் பயன்படுத்தவும்
- ஆங்கிலம் பயன்படுத்த வேண்டாம்
- எண்கள் இட வேண்டாம்
- ஒவ்வொரு வாக்கியமும் புதிய வரியில் இருக்க வேண்டும்
""",
    "tel": """
"{topic}" గురించి {count} సులభమైన తెలుగు వాక్యాలు రాయండి.

నియమాలు:
- తెలుగు మాత్రమే ఉపయోగించాలి
- ఆంగ్ల పదాలు ఉపయోగించకూడదు
- సంఖ్యలు ఇవ్వకండి
- ప్రతి వాక్యం కొత్త లైన్లో ఉండాలి
""",
    "mar": """
"{topic}" विषयावर {count} सोपी मराठी वाक्ये लिहा.

नियम:
- फक्त मराठी वापरा
- इंग्रजी शब्द वापरू नका
- क्रमांक देऊ नका
- प्रत्येक वाक्य नवीन ओळीत लिहा
""",
    "guj": """
"{topic}" વિષય પર {count} સરળ ગુજરાતી વાક્યો લખો.

નિયમો:
- ફક્ત ગુજરાતી ભાષા વાપરો
- અંગ્રેજી શબ્દો ન વાપરો
- નંબરિંગ ન કરો
- દરેક વાક્ય નવી લાઇનમાં લખો
""",
    "pan": """
"{topic}" ਬਾਰੇ {count} ਸਧਾਰਣ ਪੰਜਾਬੀ ਵਾਕ ਲਿਖੋ।

ਨਿਯਮ:
- ਸਿਰਫ ਪੰਜਾਬੀ ਵਰਤੋ
- ਅੰਗ੍ਰੇਜ਼ੀ ਨਾ ਵਰਤੋ
- ਨੰਬਰ ਨਾ ਦਿਓ
- ਹਰ ਵਾਕ ਨਵੀਂ ਲਾਈਨ ਵਿੱਚ ਹੋਵੇ
""",
    "mal": """
"{topic}" എന്ന വിഷയത്തിൽ {count} ലളിതമായ മലയാളം വാക്യങ്ങൾ എഴുതുക.

നിയമങ്ങൾ:
- മലയാളം മാത്രം ഉപയോഗിക്കുക
- ഇംഗ്ലീഷ് ഉപയോഗിക്കരുത്
- നമ്പറിംഗ് ചെയ്യരുത്
- ഓരോ വാക്യവും പുതിയ വരിയിൽ എഴുതുക
""",
    "kan": """
"{topic}" ವಿಷಯದ ಬಗ್ಗೆ {count} ಸರಳ ಕನ್ನಡ ವಾಕ್ಯಗಳನ್ನು ಬರೆಯಿರಿ.

ನಿಯಮಗಳು:
- ಕನ್ನಡ ಮಾತ್ರ ಬಳಸಿ
- ಇಂಗ್ಲಿಷ್ ಬಳಸದಿರಿ
- ಸಂಖ್ಯೆ ಹಾಕಬೇಡಿ
- ಪ್ರತಿಯೊಂದು ವಾಕ್ಯವೂ ಹೊಸ ಸಾಲಿನಲ್ಲಿ ಇರಲಿ
""",
    "nep": """
"{topic}" विषयमा {count} सरल नेपाली वाक्यहरू लेख्नुहोस्।

नियमहरू:
- केवल नेपाली प्रयोग गर्नुहोस्
- अंग्रेजी प्रयोग नगर्नुहोस्
- नम्बर नदिनुहोस्
- प्रत्येक वाक्य नयाँ लाइनमा लेख्नुहोस्
""",
    "sin": """
"{topic}" පිළිබඳ {count} සරල සිංහල වාක්‍ය ලියන්න.

නීති:
- සිංහල භාෂාව පමණක් භාවිතා කරන්න
- ඉංග්‍රීසි භාවිතා නොකරන්න
- අංක යොදන්න එපා
- සෑම වාක්‍යයක්ම නව පේළියක ලියන්න
""",
}

FALLBACK_PROMPT = """
Generate {count} sentences about "{topic}" in {language_code}.

Rules:
- One sentence per line
- No explanation
"""


def build_prompt(language_code, count, topic):
    template = PROMPTS.get(language_code, FALLBACK_PROMPT)
    return template.format(count=count, topic=topic, language_code=language_code)


def generate_sentences(language_code, total_count, topic, model):
    """Ask for sentences in batches until there are enough unique ones.

    Gives up after MAX_CALLS_PER_BATCH tries per batch, so a model that keeps
    repeating itself returns fewer sentences rather than duplicates.
    """
    if total_count <= 0:
        return []

    batch_size = min(BATCH_SIZE, total_count)
    max_calls = math.ceil(total_count / batch_size) * MAX_CALLS_PER_BATCH

    prompt = build_prompt(language_code, batch_size, topic)

    sentences = {}

    for _ in range(max_calls):
        if len(sentences) >= total_count:
            break

        text = call_llm(prompt, model)

        if text is None:
            break

        sentences.update(dict.fromkeys(clean_output(text, language_code)))

    data = list(sentences)[:total_count]

    if len(data) < total_count:
        print(f"Warning: only {len(data)} of {total_count} unique {LANG_CODE_MAP[language_code]} sentences were generated")

    return data