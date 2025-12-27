"""Configuración del sistema."""

from os import getenv
from dotenv import load_dotenv

load_dotenv()

INTEREST_RATE = float(getenv("INTEREST_RATE", "0.1"))
APPROVED_DURATIONS = list(range(3, 7))  
API_KEY = getenv("OPENAI_API_KEY")
API_BASE_URL = getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
TWILIO_ACCOUNT_SID= getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN= getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER= getenv("TWILIO_WHATSAPP_NUMBER")
