import discord
from discord.ext import commands
import random
import json
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

# --- VERİ KAYIT SİSTEMİ (JSON) ---
DATA_FILE = 'oyuncular.json'

def veri_yukle():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def veri_kaydet(veri):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)

# Oyuncu verisini getirir, yoksa yeni profil oluşturur
def oyuncu_getir(user_id):
    veri = veri_yukle()
    user_str = str(user_id)
    if user_str not in veri:
        veri[user_str] = {
            "ant": 0,
            "altin_ant": 0,
            "para": 0  # M€ cinsinden bakiye
        }
        veri_kaydet(veri)
    return veri, user_str

@bot.event
async def on_ready():
    print(f'{bot.user.name} olarak futbol sunucusuna giriş yapıldı! Bot hazır, aga.')

# --- 1. NORMAL ANTRENMAN KOMUTLARI ---
@bot.command()
async def ant(ctx):
    veri, user_str = oyuncu_getir(ctx.author.id)
    
    if veri[user_str]["ant"] < 10:
        veri[user_str]["ant"] += 1
        
        # 10/10 olunca ödül ver
        if veri[user_str]["ant"] == 10:
            veri[user_str]["para"] += 3
            veri_kaydet(veri)
            await ctx.send(f"⚽ **{ctx.author.display_name}** Normal Antrenmanı tamamladı! **(10/10)**\n🎉 **+3 M€** kazandın! Güncel Piyasa Değerin: **{veri[user_str]['para']} M€**")
        else:
            veri_kaydet(veri)
            await ctx.send(f"⚽ **{ctx.author.display_name}** Normal Antrenman: **{veri[user_str]['ant']}/10**")
    else:
        await ctx.send(f"⚠️ Normal antrenmanın zaten bitti! (10/10)\nSıfırlamak için `.resetant` yazabilirsin.")

@bot.command()
async def resetant(ctx):
    veri, user_str = oyuncu_getir(ctx.author.id)
    veri[user_str]["ant"] = 0
    veri_kaydet(veri)
    await ctx.send(f"🔄 **{ctx.author.display_name}** Normal antrenman sayacın sıfırlandı!")

# --- 2. ALTIN ANTRENMAN KOMUTLARI ---
@bot.command()
async def altinant(ctx):
    veri, user_str = oyuncu_getir(ctx.author.id)
    
    if veri[user_str]["altin_ant"] < 10:
        veri[user_str]["altin_ant"] += 1
        
        # 10/10 olunca özel ödül ver
        if veri[user_str]["altin_ant"] == 10:
            veri[user_str]["para"] += 5
            veri_kaydet(veri)
            await ctx.send(f"🌟 **{ctx.author.display_name}** ALTIN ANTRENMANI tamamladı! **(10/10)**\n🔥 **+5 M€** kazandın! Güncel Piyasa Değerin: **{veri[user_str]['para']} M€**")
        else:
            veri_kaydet(veri)
            await ctx.send(f"🌟 **{ctx.author.display_name}** Altın Antrenman: **{veri[user_str]['altin_ant']}/10**")
    else:
        await ctx.send(f"⚠️ Altın antrenmanın zaten bitti! (10/10)\nSıfırlamak için `.resetaltin` yazabilirsin.")

@bot.command()
async def resetaltin(ctx):
    veri, user_str = oyuncu_getir(ctx.author.id)
    veri[user_str]["altin_ant"] = 0
    veri_kaydet(veri)
    await ctx.send(f"🔄 **{ctx.author.display_name}** Altın antrenman sayacın sıfırlandı!")

# --- 3. PROFİL VE PARAYI GÖRME KOMUTU ---
@bot.command()
async def profil(ctx):
    veri, user_str = oyuncu_getir(ctx.author.id)
    p = veri[user_str]
    await ctx.send(
        f"📋 **{ctx.author.display_name} Futbolcu Profili:**\n"
        f"💰 Piyasa Değeri: **{p['para']} M€**\n"
        f"⚽ Normal Antrenman: **{p['ant']}/10**\n"
        f"🌟 Altın Antrenman: **{p['altin_ant']}/10**"
    )

# --- 4. PENALTI KOMUTU ---
@bot.command()
async def penalti(ctx):
    sonuclar = [
        "⚽ **GOL!** Harika bir vuruş, top ağlarda!",
        "🧤 **KURTARIŞ!** Kaleci köşeyi doğru bildi ve topu çıkardı!",
        "🧱 **DİREK!** Top sertçe direğe çarpıp dışarı gitti!",
        "💨 **DIŞARI!** Top farklı şekilde avuta çıktı!"
    ]
    secilen_sonuc = random.choice(sonuclar)
    await ctx.send(f"👟 **{ctx.author.display_name}** penaltı noktasında... Vuruşunu yapıyor...\n\n{secilen_sonuc}")

import os

# Kodunun en sonundaki bot çalıştırma satırını böyle yap:
bot.run(os.environ.get("TOKEN"))
