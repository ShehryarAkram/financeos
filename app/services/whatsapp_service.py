import json, re, httpx
from app.core.config import settings

INTENT_SYSTEM_PROMPT = """You are a financial assistant for Pakistani shopkeepers. Parse their WhatsApp messages and extract transaction intents.

Return ONLY valid JSON, no other text, no markdown, no backticks. Format:
{"intent": "cash_income"|"cash_expense"|"udhar_sale"|"udhar_payment"|"balance_query"|"daily_summary"|"unknown","amount": <number or null>,"contact_name": <string or null>,"description": <string or null>,"description_ur": <string or null>,"confidence": <0.0 to 1.0>}

Rules:
- "aaya","mila","aai","income" → cash_income
- "gaya","gai","kharch" without contact name → cash_expense
- "<name> ka udhar","<name> ko diya" → udhar_sale
- "<name> ne diya","<name> ka payment" → udhar_payment
- "hisaab","balance","<name> ka hisaab" → balance_query
- "report","summary","aaj ka" → daily_summary

Examples:
"500 aaya kapra" → {"intent":"cash_income","amount":500,"contact_name":null,"description":"Cloth sale","description_ur":"کپڑے کی فروخت","confidence":0.95}
"Ahmed ka 2000 udhar" → {"intent":"udhar_sale","amount":2000,"contact_name":"Ahmed","description":"Credit sale","description_ur":"احمد کا ادھار","confidence":0.95}
"bijli ka bill 3500 gaya" → {"intent":"cash_expense","amount":3500,"contact_name":null,"description":"Electricity bill","description_ur":"بجلی کا بل","confidence":0.98}
"Ahmed ne 500 diya" → {"intent":"udhar_payment","amount":500,"contact_name":"Ahmed","description":"Payment received","description_ur":"احمد کی ادائیگی","confidence":0.95}
"hisaab" → {"intent":"daily_summary","amount":null,"contact_name":null,"description":"Daily summary","description_ur":"روزانہ حساب","confidence":0.99}
"Ahmed ka hisaab" → {"intent":"balance_query","amount":null,"contact_name":"Ahmed","description":"Balance query","description_ur":"احمد کا حساب","confidence":0.99}"""


def _clean_json(raw: str) -> dict:
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)


async def _parse_with_groq(message: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                "max_tokens": 300,
                "temperature": 0.1,
            },
        )
        data = resp.json()
        if resp.status_code != 200:
            raise Exception(f"Groq error {resp.status_code}: {data}")
        return _clean_json(data["choices"][0]["message"]["content"])


async def _parse_with_anthropic(message: str) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=300,
        system=INTENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
    )
    return _clean_json(response.content[0].text)


class UrduNLPService:

    @classmethod
    async def parse_intent(cls, message: str) -> dict:
        try:
            if settings.AI_PROVIDER == "groq":
                return await _parse_with_groq(message)
            elif settings.AI_PROVIDER == "anthropic":
                return await _parse_with_anthropic(message)
            else:
                raise ValueError(f"Unknown provider: {settings.AI_PROVIDER}")
        except Exception as e:
            print(f"[NLP Error] provider={settings.AI_PROVIDER} error={e}")
        return {"intent": "unknown", "amount": None, "contact_name": None,
                "description": None, "description_ur": None, "confidence": 0.0}

    @staticmethod
    def format_amount(amount: float) -> str:
        return f"Rs. {amount:,.0f}"

    @classmethod
    def get_reply(cls, intent: dict, result: dict | None = None) -> str:
        amt = intent.get("amount") or 0
        a = cls.format_amount(amt)
        c = intent.get("contact_name") or ""
        d = intent.get("description_ur") or "لین دین"
        r = result or {}
        i = intent.get("intent", "unknown")

        if i == "cash_income":
            return f"✅ *{a}* ki amdani darj ho gayi.\n📝 {d}\n📊 Summary: *hisaab* likhein"
        elif i == "cash_expense":
            return f"✅ *{a}* ka kharch darj ho gaya.\n📝 {d}"
        elif i == "udhar_sale":
            return f"✅ *{c}* ka *{a}* udhar darj.\n📋 {c} ki kul baqi: *{cls.format_amount(r.get('new_balance',0))}*"
        elif i == "udhar_payment":
            return f"✅ *{c}* se *{a}* wapas mila.\n📋 {c} ki kul baqi: *{cls.format_amount(r.get('new_balance',0))}*"
        elif i == "balance_query":
            return f"📋 *{c}* ki baqi: *{cls.format_amount(r.get('balance',0))}*" if c else "📋 Kis ka hisaab? Naam likhein."
        elif i == "daily_summary":
            return (f"📊 *Aaj ka hisaab:*\n"
                    f"💰 Aaya: {cls.format_amount(r.get('income',0))}\n"
                    f"💸 Gaya: {cls.format_amount(r.get('expense',0))}\n"
                    f"📈 Faida: {cls.format_amount(r.get('profit',0))}\n"
                    f"👥 Udhar baqi: {cls.format_amount(r.get('total_udhar',0))}")
        return ("🤔 Samajh nahi aaya. Try karein:\n"
                "• *500 aaya* — amdani\n"
                "• *200 gaya* — kharch\n"
                "• *Ahmed ka 1000 udhar* — udhar\n"
                "• *Ahmed ne 500 diya* — payment\n"
                "• *hisaab* — summary")


class WhatsAppService:
    @classmethod
    async def send_message(cls, to: str, message: str) -> bool:
        if not settings.WHATSAPP_TOKEN:
            print(f"\n[WA MOCK] To: {to}\n{message}\n")
            return True
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_ID}/messages",
                json={"messaging_product": "whatsapp", "to": to,
                      "type": "text", "text": {"body": message}},
                headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"},
            )
            return resp.status_code == 200

    @classmethod
    async def send_reminder(cls, to: str, contact_name: str, amount: float,
                             custom_message: str | None = None) -> bool:
        msg = (custom_message.replace("{name}", contact_name).replace("{amount}", f"Rs. {amount:,.0f}")
               if custom_message else
               f"Assalam o Alaikum *{contact_name}*! 🙏\nAap ki *Rs. {amount:,.0f}* ki raqam baqi hai.\nMeherbani farma ke jald ada karein. 🤝")
        return await cls.send_message(to, msg)
