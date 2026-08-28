import discord
from discord.ext import commands
import random
import json
import os
import re

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


# --- NICKNAME İÇİNDEKİ M€ DEĞERİNİ YÖNETEN YARDIMCI FONKSİYONLAR ---
# Nickname formatı örneği: "İsim | 🇹🇷 | 1M€"  ->  sondaki "1M€" kısmını yakalar
DEGER_REGEX = re.compile(r'(\d+(?:[.,]\d+)?)\s*M€', re.IGNORECASE)


def nickte_deger_bul(nick: str):
    """Nickname içindeki M€ değerini bulur. Bulamazsa None döner."""
    if not nick:
        return None
    eslesme = DEGER_REGEX.search(nick)
    if not eslesme:
        return None
    sayi_str = eslesme.group(1).replace(',', '.')
    try:
        return float(sayi_str)
    except ValueError:
        return None


def nickte_deger_guncelle(nick: str, yeni_deger: float) -> str:
    """Nickname içindeki M€ değerini yeni_deger ile değiştirip yeni nickname'i döner."""
    if yeni_deger == int(yeni_deger):
        yeni_deger_str = str(int(yeni_deger))
    else:
        yeni_deger_str = str(yeni_deger)
    return DEGER_REGEX.sub(f"{yeni_deger_str}M€", nick, count=1)


async def uyenin_degerini_degistir(member: discord.Member, miktar: float):
    """
    Üyenin nickname'indeki M€ değerini miktar kadar değiştirir (miktar negatif olabilir).
    Dönüş:
      - yeni_deger (float)  -> başarılı
      - None                -> nickname'de M€ formatı bulunamadı
      - "forbidden"         -> botun bu kullanıcının nickname'ini değiştirme izni yok
    """
    mevcut_nick = member.display_name
    mevcut_deger = nickte_deger_bul(mevcut_nick)
    if mevcut_deger is None:
        return None

    yeni_deger = mevcut_deger + miktar
    if yeni_deger < 0:
        yeni_deger = 0

    yeni_nick = nickte_deger_guncelle(mevcut_nick, yeni_deger)

    try:
        await member.edit(nick=yeni_nick)
        return yeni_deger
    except discord.Forbidden:
        return "forbidden"


# --- AFK SİSTEMİ (JSON) ---
AFK_FILE = 'afk.json'

def afk_yukle():
    if os.path.exists(AFK_FILE):
        with open(AFK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def afk_kaydet(veri):
    with open(AFK_FILE, 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)


@bot.event
async def on_ready():
    print(f'{bot.user.name} olarak futbol sunucusuna giriş yapıldı! Bot hazır, aga.')


@bot.event
async def on_message(message):
    # Botların kendi mesajlarını sayma / işleme
    if message.author.bot:
        return

    # --- Mesaj sayacını artır ---
    veri, user_str = oyuncu_getir(message.author.id)
    veri[user_str]["mesaj"] = veri[user_str].get("mesaj", 0) + 1
    veri_kaydet(veri)

    # --- Mesaj atan kişi AFK ise, AFK durumunu kaldır ---
    afk_verisi = afk_yukle()
    yazan_str = str(message.author.id)
    if yazan_str in afk_verisi:
        del afk_verisi[yazan_str]
        afk_kaydet(afk_verisi)
        await message.channel.send(f"👋 **{message.author.display_name}**, tekrar hoş geldin! AFK durumun kaldırıldı.")

    # --- Mesajda etiketlenen kullanıcılar AFK ise haber ver ---
    for uye in message.mentions:
        uye_str = str(uye.id)
        if uye_str in afk_verisi:
            await message.channel.send(f"💤 **{uye.display_name}** şu an AFK: **{afk_verisi[uye_str]}**")

    # Komutların çalışmaya devam etmesi için şart
    await bot.process_commands(message)

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
            await uyenin_degerini_degistir(ctx.author, 3)
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
            await uyenin_degerini_degistir(ctx.author, 5)
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

    # Eğer sonuç GOL ise, kullanıcının değerine 3 M€ ekle (hem JSON'a hem nickname'e)
    if "GOL" in secilen_sonuc:
        veri, user_str = oyuncu_getir(ctx.author.id)
        veri[user_str]["para"] += 3
        veri_kaydet(veri)
        await uyenin_degerini_degistir(ctx.author, 3)
        secilen_sonuc += f"\n💰 Penaltı golü! **+3 M€** kazandın!"

    await ctx.send(f"👟 **{ctx.author.display_name}** penaltı noktasında... Vuruşunu yapıyor...\n\n{secilen_sonuc}")


# --- 5. NICKNAME ÜZERİNDEN DEĞER EKLEME / SİLME KOMUTLARI ---
@bot.command(name='değerekle', aliases=['degerekle'])
async def deger_ekle(ctx, miktar: float, member: discord.Member = None):
    hedef = member or ctx.author
    sonuc = await uyenin_degerini_degistir(hedef, miktar)

    if sonuc is None:
        await ctx.send(f"⚠️ **{hedef.display_name}** adında `SayıM€` formatında bir değer bulunamadı (örn: `1M€`).")
    elif sonuc == "forbidden":
        await ctx.send("⚠️ Bu kullanıcının nickname'ini değiştirme yetkim yok (rol sıralaması ya da izin sorunu).")
    else:
        veri, user_str = oyuncu_getir(hedef.id)
        veri[user_str]["para"] = sonuc
        veri_kaydet(veri)
        await ctx.send(f"✅ **{hedef.display_name}** değerine **{miktar} M€** eklendi! Güncel Değer: **{sonuc} M€**")


@bot.command(name='değersil', aliases=['degersil'])
async def deger_sil(ctx, miktar: float, member: discord.Member = None):
    hedef = member or ctx.author
    sonuc = await uyenin_degerini_degistir(hedef, -miktar)

    if sonuc is None:
        await ctx.send(f"⚠️ **{hedef.display_name}** adında `SayıM€` formatında bir değer bulunamadı (örn: `1M€`).")
    elif sonuc == "forbidden":
        await ctx.send("⚠️ Bu kullanıcının nickname'ini değiştirme yetkim yok (rol sıralaması ya da izin sorunu).")
    else:
        veri, user_str = oyuncu_getir(hedef.id)
        veri[user_str]["para"] = sonuc
        veri_kaydet(veri)
        await ctx.send(f"✅ **{hedef.display_name}** değerinden **{miktar} M€** silindi! Güncel Değer: **{sonuc} M€**")


# --- 6. AFK KOMUTU ---
@bot.command()
async def afk(ctx, *, sebep="Belirtilmedi"):
    afk_verisi = afk_yukle()
    afk_verisi[str(ctx.author.id)] = sebep
    afk_kaydet(afk_verisi)
    await ctx.send(f"💤 **{ctx.author.display_name}** artık AFK: **{sebep}**")


# --- 7. MESAJ SAYISI KOMUTU ---
@bot.command(name='mesaj')
async def mesaj_sayisi(ctx, member: discord.Member = None):
    hedef = member or ctx.author
    veri, user_str = oyuncu_getir(hedef.id)
    sayi = veri[user_str].get("mesaj", 0)
    await ctx.send(f"💬 **{hedef.display_name}** toplam **{sayi}** mesaj attı.")


bot.run(os.environ.get("TOKEN"))
