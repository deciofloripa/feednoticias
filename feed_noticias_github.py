import feedparser
import requests
import json
import os
from datetime        import datetime
from deep_translator import MyMemoryTranslator

# CONFIGURAÇÕES
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI&region=US&lang=en-US"#,
]
KEYWORDS = [
    "fed", "interest rate", "inflation", "cpi",
    "central bank", "fomc", "economy",
    "oil", "dollar", "treasury", "bond",
    "payroll", "gdp", "recession",
    "stocks", "nasdaq", "sp500", "dow jones"
]

vistos = set()
translator = MyMemoryTranslator(source='en-US', target='pt-BR')


# FUNÇÕES
def carregar_vistos():
    try:
        with open("vistos.json", "r") as f:
            return set(json.load(f))
    except:
        return set()

def salvar_vistos(vistos):
    with open("vistos.json", "w") as f:
        json.dump(list(vistos), f)

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        print("Erro Telegram")

def traduzir(texto):
    try:
        return translator.translate(texto)
    except:
        return texto

def relevante(titulo):
    t = titulo.lower()
    return any(k in t for k in KEYWORDS)

# 🧠 RESUMO ESTILO TRADER
def resumir_trader(titulo):
    t = titulo.lower()
    if "inflation" in t or "cpi" in t:
        return "Inflação em foco → impacto direto nos juros"
    if "interest rate" in t or "fed" in t or "fomc" in t:
        return "Juros / Fed → movimento forte no dólar"
    if "oil" in t:
        return "Petróleo → impacto em inflação e moedas"
    if "payroll" in t or "jobs" in t:
        return "Emprego EUA → volatilidade forte"
    if "gdp" in t:
        return "PIB → leitura da força econômica"
    if "recession" in t:
        return "Risco de recessão → aversão a risco"
    if "stocks" in t or "nasdaq" in t or "sp500" in t:
        return "Bolsas → influência no índice (WIN)"
    if "dollar" in t or "treasury" in t:
        return "Dólar / Treasuries → impacto direto no WDO"
    return "Notícia macro relevante"

def buscar(vistos):
    noticias = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                titulo = e.title.strip()
                link = e.link.strip()
                if link in vistos:
                    continue
                vistos.add(link)
                if relevante(titulo):
                    noticias.append({
                        "titulo": titulo,
                        "link": link
                    })
        except:
            print("Erro feed:", url)
    return noticias

def run_once():
    vistos = carregar_vistos()
    noticias = buscar(vistos)
    if noticias:
        agora = datetime.now().strftime("%d/%m %H:%M:%S")
        print(f"🔄 Atualizando {agora}")
        for n in noticias:
            titulo_en = n['titulo']
            titulo_pt = traduzir(titulo_en)
            resumo = resumir_trader(titulo_en)
            msg = (
                f"🕒 {datetime.now().strftime('%H:%M')}\n"
                f"📰 {titulo_pt}\n"
                f"📊 {resumo}\n"
                f"{n['link']}"
            )
            print(msg + "\n")
            enviar_telegram(msg)
    salvar_vistos(vistos)

# START
if __name__ == "__main__":
    run_once()