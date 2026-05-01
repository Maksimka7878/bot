"""
Транскрибация MP3 + оценка лида через Gemini API.
Используется ботом: from transcribe import transcribe_bytes, score_lead
"""

import os
import json
import time

from google import genai
from google.genai import types

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-3.1-flash-lite-preview"
FALLBACK_MODELS = [
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.5-flash",
]

TRANSCRIPTION_PROMPT = """
Ты — профессиональный транскрибатор телефонных разговоров.

Твоя задача — полностью транскрибировать данную аудиозапись.

Формат ответа — строго JSON:
{
  "duration_seconds": <общая длительность в секундах>,
  "speakers_count": <количество уникальных спикеров>,
  "language": "<определённый язык>",
  "segments": [
    {
      "start": "<MM:SS>",
      "end":   "<MM:SS>",
      "speaker": "Менеджер" | "Клиент",
      "text": "<точный текст фразы>"
    }
  ],
  "full_text": "<весь текст разговора одним блоком>",
  "summary": "<краткое резюме разговора 2-3 предложения>"
}

Требования:
- Фиксируй КАЖДУЮ фразу, даже короткие реплики («угу», «да», «хорошо»).
- Различай спикеров по роли: тот кто предлагает/продаёт — "Менеджер", тот кому звонят — "Клиент".
- Временны́е метки — формат MM:SS.
- Текст передавай дословно, сохраняй разговорный стиль, слова-паразиты, паузы (...).
- Если слово неразборчиво — пиши [неразборчиво].
- Отвечай ТОЛЬКО валидным JSON, без markdown-блоков и пояснений.
"""

SCORING_PROMPT = """
Ты — эксперт по оценке лидов для брокера новостроек.

Тебе дана транскрипция телефонного разговора. Оцени лид от 0 до 100.

Идеальный лид (100 баллов) = клиент ищет новостройку, чётко назвал:
- бюджет
- локацию
- площадь / комнатность
- срок сдачи
- готов к покупке в ближайшее время
- охотно общается, заинтересован

Критерии и веса:
1. Интерес к новостройке (не вторичка) — до 20 баллов
2. Бюджет назван чётко — до 20 баллов (частично = 5-10)
3. Локация определена — до 15 баллов (примерно = 5-8)
4. Площадь / комнатность названы — до 15 баллов
5. Срок покупки — до 15 баллов (чем быстрее, тем выше)
6. Готовность к контакту / вовлечённость — до 10 баллов
7. Нет жёсткого отказа, диалог состоялся — до 5 баллов

Ответь строго JSON:
{
  "score": <0-100>,
  "grade": "Горячий" | "Тёплый" | "Холодный" | "Мусор",
  "criteria": {
    "новостройка": <0-20>,
    "бюджет": <0-20>,
    "локация": <0-15>,
    "площадь_комнатность": <0-15>,
    "срок_покупки": <0-15>,
    "вовлечённость": <0-10>,
    "контакт_состоялся": <0-5>
  },
  "extracted": {
    "бюджет": "<сумма или null>",
    "локация": "<локация или null>",
    "площадь": "<диапазон или null>",
    "комнатность": "<кол-во комнат или null>",
    "срок_сдачи": "<срок или null>",
    "тип_жилья": "новостройка" | "вторичка" | "не определено"
  },
  "strengths": ["<сильная сторона лида>"],
  "weaknesses": ["<слабая сторона лида>"],
  "recommendation": "<1-2 предложения: стоит ли брать лид и почему>"
}

Отвечай ТОЛЬКО валидным JSON, без markdown и пояснений.
"""


def _clean_json(raw: str) -> str:
    if raw.startswith("```"):
        lines = [l for l in raw.split("\n") if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    return raw


def _call_gemini(client, model: str, contents: list) -> str:
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=8192),
    )
    return response.text.strip()


def _try_models(client, contents: list) -> str:
    for m in [MODEL_NAME] + FALLBACK_MODELS:
        try:
            return _call_gemini(client, m, contents)
        except Exception as e:
            err = str(e)
            if "503" in err or "UNAVAILABLE" in err:
                time.sleep(2)
                continue
            elif "429" in err or "RESOURCE_EXHAUSTED" in err:
                retry_in = 30
                if "Please retry in" in err:
                    try:
                        retry_in = int(float(err.split("Please retry in")[1].split("s")[0].strip())) + 2
                    except Exception:
                        pass
                time.sleep(retry_in)
                try:
                    return _call_gemini(client, m, contents)
                except Exception:
                    continue
            else:
                raise
    raise RuntimeError("Все Gemini-модели недоступны. Проверь API ключ и квоту.")


def transcribe_bytes(audio_bytes: bytes, api_key: str = None) -> dict:
    """Транскрибирует MP3 из байтов. Возвращает dict с segments, full_text, summary."""
    key = api_key or GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY не задан.")
    client = genai.Client(api_key=key)
    contents = [
        types.Part.from_text(text=TRANSCRIPTION_PROMPT),
        types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg"),
    ]
    raw = _try_models(client, contents)
    return json.loads(_clean_json(raw))


def score_lead(transcription: dict, api_key: str = None) -> dict:
    """Оценивает лид 0-100. Принимает результат transcribe_bytes()."""
    key = api_key or GEMINI_API_KEY
    if not key:
        raise ValueError("GEMINI_API_KEY не задан.")
    client = genai.Client(api_key=key)
    dialog = "\n".join(
        f"[{s['start']}] {s['speaker']}: {s['text']}"
        for s in transcription.get("segments", [])
    )
    content = f"ДИАЛОГ:\n{dialog}\n\nПОЛНЫЙ ТЕКСТ:\n{transcription.get('full_text', '')}"
    contents = [
        types.Part.from_text(text=SCORING_PROMPT),
        types.Part.from_text(text=content),
    ]
    raw = _try_models(client, contents)
    return json.loads(_clean_json(raw))


def format_tg_reply(transcription: dict, score: dict) -> str:
    """Форматирует итоговое сообщение для Telegram."""
    grade_emoji = {"Горячий": "🔥", "Тёплый": "🌤", "Холодный": "🧊", "Мусор": "🗑"}.get(score.get("grade", ""), "")
    ex = score.get("extracted", {})
    strengths = "\n".join(f"  ✅ {s}" for s in score.get("strengths", []))
    weaknesses = "\n".join(f"  ❌ {w}" for w in score.get("weaknesses", []))

    lines = [
        f"{grade_emoji} <b>Оценка лида: {score['score']}/100 — {score.get('grade', '')}</b>",
        "",
        f"💰 Бюджет: {ex.get('бюджет') or '—'}",
        f"📍 Локация: {ex.get('локация') or '—'}",
        f"📐 Площадь: {ex.get('площадь') or '—'}",
        f"🛏 Комнатность: {ex.get('комнатность') or '—'}",
        f"📅 Срок сдачи: {ex.get('срок_сдачи') or '—'}",
        f"🏗 Тип жилья: {ex.get('тип_жилья') or '—'}",
        "",
        f"🕐 Длит. разговора: {transcription.get('duration_seconds', '?')} сек",
        "",
        strengths,
        weaknesses,
        "",
        f"💡 <i>{score.get('recommendation', '')}</i>",
    ]
    return "\n".join(l for l in lines if l is not None)
