import requests
import random
from config import LANG_CODE_MAP, DEFAULT_MODEL, OLLAMA_URL



def clean_output(lines):
    cleaned = []

    for line in lines:
        line = line.strip()

        # Remove unwanted intro text
        if line.lower().startswith("here are"):
            continue

        # Remove numbering (1. 2. )
        if line[:3].strip().replace(".", "").isdigit():
            line = line.split(".", 1)[-1].strip()

        # Remove short lines
        if len(line) < 5:
            continue

        cleaned.append(line)

    # Remove duplicates
    cleaned = list(set(cleaned))

    return cleaned



def call_llm(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": DEFAULT_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        text = response.json().get("response", "")

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        lines = clean_output(lines)

        return lines

    except Exception as e:
        print("LLM Error:", e)
        return []



def build_prompt(language_code, count, topic):

    if language_code == "eng":
        return f"""
Generate {count} simple English sentences about "{topic}".

Rules:
- Use only English
- No numbering
- No explanation
- Do NOT include phrases like "Here are"
- Each sentence on a new line
"""

    elif language_code == "hin":
        return f"""
"{topic}" विषय पर {count} सरल हिंदी वाक्य लिखें।

नियम:
- केवल हिंदी भाषा का उपयोग करें
- अंग्रेजी शब्द न लिखें
- क्रम संख्या (1,2,3) न दें
- कोई व्याख्या न दें
- हर वाक्य नई लाइन में हो
"""

    elif language_code == "ben":
        return f"""
"{topic}" বিষয়ের উপর {count}টি সহজ বাংলা বাক্য লিখুন।

নিয়ম:
- শুধুমাত্র বাংলা ব্যবহার করুন
- ইংরেজি ব্যবহার করবেন না
- নম্বরিং করবেন না
- প্রতিটি বাক্য নতুন লাইনে লিখুন
"""

    elif language_code == "urd":
        return f"""
"{topic}" کے بارے میں {count} آسان اردو جملے لکھیں۔

قواعد:
- صرف اردو زبان استعمال کریں
- انگریزی استعمال نہ کریں
- نمبرنگ نہ کریں
- ہر جملہ نئی لائن میں ہو
"""

    elif language_code == "tam":
        return f"""
"{topic}" பற்றிய {count} எளிய தமிழ் வாக்கியங்களை எழுதுங்கள்.

விதிகள்:
- தமிழ் மட்டும் பயன்படுத்தவும்
- ஆங்கிலம் பயன்படுத்த வேண்டாம்
- எண்கள் இட வேண்டாம்
- ஒவ்வொரு வாக்கியமும் புதிய வரியில் இருக்க வேண்டும்
"""

    elif language_code == "tel":
        return f"""
"{topic}" గురించి {count} సులభమైన తెలుగు వాక్యాలు రాయండి.

నియమాలు:
- తెలుగు మాత్రమే ఉపయోగించాలి
- ఆంగ్ల పదాలు ఉపయోగించకూడదు
- సంఖ్యలు ఇవ్వకండి
- ప్రతి వాక్యం కొత్త లైన్లో ఉండాలి
"""

    elif language_code == "mar":
        return f"""
"{topic}" विषयावर {count} सोपी मराठी वाक्ये लिहा.

नियम:
- फक्त मराठी वापरा
- इंग्रजी शब्द वापरू नका
- क्रमांक देऊ नका
- प्रत्येक वाक्य नवीन ओळीत लिहा
"""

    elif language_code == "guj":
        return f"""
"{topic}" વિષય પર {count} સરળ ગુજરાતી વાક્યો લખો.

નિયમો:
- ફક્ત ગુજરાતી ભાષા વાપરો
- અંગ્રેજી શબ્દો ન વાપરો
- નંબરિંગ ન કરો
- દરેક વાક્ય નવી લાઇનમાં લખો
"""

    elif language_code == "pan":
        return f"""
"{topic}" ਬਾਰੇ {count} ਸਧਾਰਣ ਪੰਜਾਬੀ ਵਾਕ ਲਿਖੋ।

ਨਿਯਮ:
- ਸਿਰਫ ਪੰਜਾਬੀ ਵਰਤੋ
- ਅੰਗ੍ਰੇਜ਼ੀ ਨਾ ਵਰਤੋ
- ਨੰਬਰ ਨਾ ਦਿਓ
- ਹਰ ਵਾਕ ਨਵੀਂ ਲਾਈਨ ਵਿੱਚ ਹੋਵੇ
"""

    elif language_code == "mal":
        return f"""
"{topic}" എന്ന വിഷയത്തിൽ {count} ലളിതമായ മലയാളം വാക്യങ്ങൾ എഴുതുക.

നിയമങ്ങൾ:
- മലയാളം മാത്രം ഉപയോഗിക്കുക
- ഇംഗ്ലീഷ് ഉപയോഗിക്കരുത്
- നമ്പറിംഗ് ചെയ്യരുത്
- ഓരോ വാക്യവും പുതിയ വരിയിൽ എഴുതുക
"""

    elif language_code == "kan":
        return f"""
"{topic}" ವಿಷಯದ ಬಗ್ಗೆ {count} ಸರಳ ಕನ್ನಡ ವಾಕ್ಯಗಳನ್ನು ಬರೆಯಿರಿ.

ನಿಯಮಗಳು:
- ಕನ್ನಡ ಮಾತ್ರ ಬಳಸಿ
- ಇಂಗ್ಲಿಷ್ ಬಳಸದಿರಿ
- ಸಂಖ್ಯೆ ಹಾಕಬೇಡಿ
- ಪ್ರತಿಯೊಂದು ವಾಕ್ಯವೂ ಹೊಸ ಸಾಲಿನಲ್ಲಿ ಇರಲಿ
"""

    elif language_code == "nep":
        return f"""
"{topic}" विषयमा {count} सरल नेपाली वाक्यहरू लेख्नुहोस्।

नियमहरू:
- केवल नेपाली प्रयोग गर्नुहोस्
- अंग्रेजी प्रयोग नगर्नुहोस्
- नम्बर नदिनुहोस्
- प्रत्येक वाक्य नयाँ लाइनमा लेख्नुहोस्
"""

    elif language_code == "sin":
        return f"""
"{topic}" පිළිබඳ {count} සරල සිංහල වාක්‍ය ලියන්න.

නීති:
- සිංහල භාෂාව පමණක් භාවිතා කරන්න
- ඉංග්‍රීසි භාවිතා නොකරන්න
- අංක යොදන්න එපා
- සෑම වාක්‍යයක්ම නව පේළියක ලියන්න
"""

    else:
        return f"""
Generate {count} sentences about "{topic}" in {language_code}.

Rules:
- One sentence per line
- No explanation
"""



def generate_sentences(language_code, total_count, topic):
    base_size = 60

    prompt = build_prompt(language_code, base_size, topic)

    base = call_llm(prompt)

    if not base:
        print(f"Failed for {language_code}")
        return []

    data = []

    while len(data) < total_count:
     random.shuffle(base)
     data.extend(base)

# Trim to required size
    data = data[:total_count]

    return data[:total_count]