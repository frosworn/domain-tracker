import customtkinter as ctk
import random
import time
from tkinter import END
import datetime
import webbrowser 
import threading
import whois 
import sqlite3
import requests

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

USE_PROXY = False
PROXY_DICT = {
    "http": "http://kullaniciadi:sifre@ip_adresi:port",
    "https": "http://kullaniciadi:sifre@ip_adresi:port"
}

POPULAR_DOMAINS = {
    "amazonprimeplus.com": "E-Ticaret",
    "meta-universe.net": "Sosyal Medya",
    "nvidia-ai-labs.org": "Teknoloji/Yapay Zeka",
    "teslamotors.co": "Otomotiv/Enerji",
    "microsoftcorp.net": "Yazılım",
    "apple-ios-dev.info": "Mobil/Donanım",
    "taktakasla.com": "Medya/Eğlence",
}

FORCED_OCCUPIED_DOMAINS = [
    "taktakasla.com", 
] 
FORCED_OCCUPIED_DOMAINS = [d.lower() for d in FORCED_OCCUPIED_DOMAINS]

PLATFORM_DATA = {
    "GoDaddy Backorder": {"price_range": (50.00, 70.00), "avantaj": "Drop-catch garantisi", "url": "https://www.godaddy.com/domains/search"},
    
    "GoDaddy Tescil": {"price_range": (14.99, 17.99), "avantaj": "1 yıllık özel gizlilik", "url": "https://www.godaddy.com/domains/search"},
    "Namecheap Tescil": {"price_range": (9.98, 11.88), "avantaj": "Ömür boyu ücretsiz WHOIS koruması", "url": "https://www.namecheap.com/domains/registration/results"},
    "Google Domains": {"price_range": (12.00, 13.00), "avantaj": "Kolay entegrasyon (DNS, E-posta)", "url": "https://domains.google.com/registrar/search"},
    "Dynadot": {"price_range": (8.99, 10.99), "avantaj": "Toplu alımlarda ekstra indirim", "url": "https://www.dynadot.com/domain/search"},
    "Cloudflare": {"price_range": (8.50, 9.50), "avantaj": "Toptan maliyetle tescil (En düşük fiyat)", "url": "https://www.cloudflare.com/products/registrar/"},
    "IONOS": {"price_range": (13.00, 15.00), "avantaj": "Ücretsiz profesyonel e-posta", "url": "https://www.ionos.com/domains"},
    "Hostinger": {"price_range": (10.50, 12.50), "avantaj": "Yüksek hızlı hosting deneme süresi", "url": "https://www.hostinger.com/domain-name-search"},
    "Wix Domains": {"price_range": (15.50, 18.50), "avantaj": "1 yıllık ücretsiz Wix Premium aboneliği", "url": "https://www.wix.com/domain/name-search"},
    "Natro": {"price_range": (11.00, 13.50), "avantaj": "Türkiye lokasyonlu özel DNS desteği", "url": "https://www.natro.com/domain-sorgulama"},
}

def get_platform_price(domain, platform):
    """Belirli bir alan adı ve platform için rastgele fiyat ve avantaj döndürür (Simülasyon)."""
    price_range = PLATFORM_DATA[platform]["price_range"]
    base_price = random.uniform(*price_range)
        
    if domain.lower() in [d.lower() for d in POPULAR_DOMAINS.keys()]:
        price = base_price * random.uniform(1.2, 1.8) 
    else:
        price = base_price
    
    return {
        "fiyat": round(price, 2),
        "avantaj": PLATFORM_DATA[platform].get("avantaj", "Varsayılan hizmetler"),
        "platform": platform,
        "url": PLATFORM_DATA[platform]["url"]
    }

def find_all_prices(domain):
    """Tüm tescil platformlarını tarar ve tüm fiyatları listeler (Backorder olanları hariç)."""
    all_options = []
    for platform in PLATFORM_DATA.keys():
        if "Backorder" not in platform:
             all_options.append(get_platform_price(domain, platform))
            
    all_options.sort(key=lambda x: x['fiyat'])
    return all_options

def get_real_whois_data(domain):
    """Gerçek WHOIS sorgusu yapar ve veriyi arayüz formatına dönüştürür."""
    domain_lower = domain.lower()
    is_available = True
    whois_data = {}
    
    if domain_lower in FORCED_OCCUPIED_DOMAINS or domain_lower in [d.lower() for d in POPULAR_DOMAINS.keys()]:
        is_available = False
        expiration_date = datetime.date(2027, 4, 1) 
        current_date = datetime.date.today()
        kalan_sure = (expiration_date - current_date).days
        return {
            "Alan Adı": domain,
            "Tescil Ettiren": "Kurumsal Hesap (Simüle)", 
            "Registrar": "MarkMonitor Inc. (Simüle)",
            "Tescil Tarihi": "2005-04-01 (Simüle)",
            "Bitiş Tarihi": expiration_date.strftime("%Y-%m-%d"),
            "Kalan Süre": f"{kalan_sure} gün",
            "Durum Kodları": "clientTransferProhibited",
            "is_available": is_available
        }
        
    try:
        w = whois.whois(domain)

        raw_text = str(w.text).lower() if w.text else ""
        
        available_keywords = [
            "no match", "not found", "no data found", "no entries found", 
            "status: free", "is available", "available for registration", 
            "does not exist", "not registered", "nothing found", "no object found"
        ]

        if w.domain_name is None or any(kw in raw_text for kw in available_keywords):
            is_available = True
            whois_data = {
                "Alan Adı": domain,
                "Tescil Ettiren": "MÜSAİT (Hemen Tescil Edilebilir)",
                "Registrar": "Çoklu Platform",
                "Tescil Tarihi": "YOK",
                "Bitiş Tarihi": "YOK",
                "Kalan Süre": "0 gün", 
                "Durum Kodları": "available"
            }
        else:
            is_available = False
            
            def get_date_from_raw(raw_text, date_type):
                if not raw_text: return None
                import re
                raw_text = str(raw_text).lower()
                if date_type == "creation":
                    patterns = [r"creation date:\s*([^\n\r]+)", r"created on[.]*:\s*([^\n\r]+)", r"registration date:\s*([^\n\r]+)", r"created:\s*([^\n\r]+)", r"domain created:\s*([^\n\r]+)"]
                else:
                    patterns = [r"registry expiry date:\s*([^\n\r]+)", r"registrar registration expiration date:\s*([^\n\r]+)", r"expires on[.]*:\s*([^\n\r]+)", r"expiration date:\s*([^\n\r]+)", r"paid-till:\s*([^\n\r]+)", r"expire date:\s*([^\n\r]+)", r"valid until:\s*([^\n\r]+)", r"expires:\s*([^\n\r]+)"]
                
                for p in patterns:
                    match = re.search(p, raw_text)
                    if match: return match.group(1).strip()
                
                # ZORAKİ ARAMA: Eğer kelime bazlı bulamazsa, metin içindeki tüm YYYY-MM-DD tarihlerini bul ve en büyüğünü bitiş say
                if date_type == "expiration":
                    fallback = re.findall(r'(20\d{2})[-\./](0[1-9]|1[0-2])[-\./](0[1-9]|[12]\d|3[01])', raw_text)
                    if fallback:
                        dates = [f"{m[0]}-{m[1]}-{m[2]}" for m in fallback]
                        return max(dates)
                return None
                
            def resolve_date(date_obj, raw_text, date_type):
                raw_val = None
                if date_obj:
                    if isinstance(date_obj, list):
                        date_obj = date_obj[0]
                    if isinstance(date_obj, (datetime.datetime, datetime.date)):
                        return date_obj.strftime("%Y-%m-%d")
                    raw_val = str(date_obj)
                
                if not raw_val or raw_val.lower() == "none":
                    raw_val = get_date_from_raw(raw_text, date_type)
                    
                if not raw_val:
                    return "Bilinmiyor"
                    
                import re
                d1 = re.search(r'(\d{4})[-\./](\d{1,2})[-\./](\d{1,2})', raw_val)
                if d1: return f"{d1.group(1)}-{d1.group(2).zfill(2)}-{d1.group(3).zfill(2)}"
                
                d2 = re.search(r'(\d{1,2})[-\./](\d{1,2})[-\./](\d{4})', raw_val)
                if d2: return f"{d2.group(3)}-{d2.group(2).zfill(2)}-{d2.group(1).zfill(2)}"
                
                val_lower = raw_val.lower()
                aylar = {"jan":"01", "feb":"02", "mar":"03", "apr":"04", "may":"05", "jun":"06", "jul":"07", "aug":"08", "sep":"09", "oct":"10", "nov":"11", "dec":"12"}
                for ay, num in aylar.items():
                    if ay in val_lower:
                        ym = re.search(r'(\d{4})', val_lower)
                        dm = re.search(r'(?<!\d)(\d{1,2})(?!\d)', val_lower)
                        if ym and dm: return f"{ym.group(1)}-{num}-{dm.group(1).zfill(2)}"
                        
                return raw_val[:20] # Format bulamazsa olduğu gibi göster
                
            def format_value(value):
                if isinstance(value, list):
                    return ', '.join(map(str, value))
                return str(value) if value else "Bilinmiyor"
            
            creation_date = resolve_date(w.creation_date, w.text, "creation")
            expiration_date = resolve_date(w.expiration_date, w.text, "expiration")
            
            # Kütüphane tarihleri bulamadıysa, şansımızı çok daha güçlü olan API ile denemek için bilerek hata verdiriyoruz.
            if expiration_date == "Bilinmiyor" or "?" in expiration_date:
                raise ValueError("Tarihler gizlenmiş, API'ye yönlendiriliyor...")

            kalan_sure = "Hesaplanamadı"
            if expiration_date != "Bilinmiyor":
                try:
                    exp_date_obj = datetime.datetime.strptime(expiration_date[:10], "%Y-%m-%d").date()
                    kalan_sure = f"{(exp_date_obj - datetime.date.today()).days} gün"
                except:
                    kalan_sure = f"? ({expiration_date})"
                
            whois_data = {
                "Alan Adı": domain,
                "Tescil Ettiren": format_value(w.name) or format_value(w.registrar) or "Gizli / Bilinmiyor",
                "Registrar": format_value(w.registrar),
                "Tescil Tarihi": creation_date,
                "Bitiş Tarihi": expiration_date,
                "Kalan Süre": kalan_sure, 
                "Durum Kodları": format_value(w.statuses),
            }
            
    except Exception as e:
        error_msg = str(e).lower()
        
        available_keywords = ["no match", "not found", "no data", "no entries", "free", "available", "does not exist"]
        if type(e).__name__ == "PywhoisError" or any(kw in error_msg for kw in available_keywords):
            is_available = True
            whois_data = {
                "Alan Adı": domain,
                "Tescil Ettiren": "MÜSAİT (Hemen Tescil Edilebilir)",
                "Registrar": "Çoklu Platform",
                "Tescil Tarihi": "YOK",
                "Bitiş Tarihi": "YOK",
                "Kalan Süre": "0 gün", 
                "Durum Kodları": "available"
            }
        else:
            # --- PORT 43 ENGELLİYSE API FALLBACK ---
            try:
                req_proxies = PROXY_DICT if USE_PROXY else None
                # YENİ NESİL, ICANN ONAYLI RDAP API'Sİ KULLANILIYOR
                res = requests.get(f"https://rdap.org/domain/{domain}", timeout=10, proxies=req_proxies)
                
                if res.status_code == 404:
                    return {
                        "Alan Adı": domain,
                        "Tescil Ettiren": "MÜSAİT (Hemen Tescil Edilebilir)",
                        "Registrar": "Çoklu Platform",
                        "Tescil Tarihi": "YOK",
                        "Bitiş Tarihi": "YOK",
                        "Kalan Süre": "0 gün", 
                        "Durum Kodları": "available (RDAP API)",
                        "is_available": True
                    }
                elif res.status_code == 200:
                    data = res.json()
                    
                    c_date = "Bilinmiyor"
                    exp_date = "Bilinmiyor"
                    for ev in data.get("events", []):
                        if ev.get("eventAction") == "registration":
                            c_date = ev.get("eventDate", "Bilinmiyor")[:10]
                        elif ev.get("eventAction") == "expiration":
                            exp_date = ev.get("eventDate", "Bilinmiyor")[:10]
                        
                    kalan_sure = "Hesaplanamadı"
                    if exp_date != "Bilinmiyor":
                        try:
                            ed = datetime.datetime.strptime(exp_date[:10], "%Y-%m-%d").date()
                            kalan_sure = f"{(ed - datetime.date.today()).days} gün"
                        except:
                            kalan_sure = f"? ({exp_date})"
                            
                    reg = "Gizli/Bilinmiyor"
                    for ent in data.get("entities", []):
                        if "registrar" in ent.get("roles", []):
                            try:
                                vcard = ent.get("vcardArray", [[]])[1]
                                for item in vcard:
                                    if item[0] == "fn":
                                        reg = item[3]
                                        break
                            except: pass

                    return {
                        "Alan Adı": domain,
                        "Tescil Ettiren": reg,
                        "Registrar": reg,
                        "Tescil Tarihi": c_date,
                        "Bitiş Tarihi": exp_date,
                        "Kalan Süre": kalan_sure, 
                        "Durum Kodları": "RDAP API Başarılı",
                        "is_available": False
                    }
            except:
                pass # API de çökerse orijinal hata mesajına geç

            # API de hata verirse standart hata ekranını göster
            is_available = False
            
            if "10060" in error_msg or "timeout" in error_msg or "connection" in error_msg:
                detay = "Port 43 Kapalı & API Yanıtsız"
            elif "quota" in error_msg or "limit" in error_msg:
                detay = "WHOIS Limiti Aşıldı"
            else:
                detay = f"Sistem Hatası: {str(e)[:25]}"
                
            whois_data = {
                "Alan Adı": domain,
                "Tescil Ettiren": "HATA: Sorgu Başarısız",
                "Registrar": "HATA",
                "Tescil Tarihi": "HATA",
                "Bitiş Tarihi": "HATA",
                "Kalan Süre": "HATA", 
                "Durum Kodları": detay
            }
        
    whois_data["is_available"] = is_available
    return whois_data
# --- YENİ REAL-TIME WHOIS FONKSİYONU SONU ---

# --- SQLite Veritabanı Kurulumu ---
def init_db():
    conn = sqlite3.connect("domain_history.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT,
            status TEXT,
            registrar TEXT,
            creation_date TEXT,
            expiration_date TEXT,
            query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(whois_data):
    try:
        conn = sqlite3.connect("domain_history.db")
        cursor = conn.cursor()
        status = "MÜSAİT" if whois_data.get("is_available") else "DOLU"
        if "HATA" in str(whois_data.get("Tescil Ettiren", "")):
            status = "HATA"
        
        cursor.execute('''
            INSERT INTO history (domain, status, registrar, creation_date, expiration_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            whois_data.get("Alan Adı", "Bilinmiyor"),
            status,
            whois_data.get("Registrar", "Bilinmiyor"),
            whois_data.get("Tescil Tarihi", "Bilinmiyor"),
            whois_data.get("Bitiş Tarihi", "Bilinmiyor")
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Veritabanı kayıt hatası:", e)

init_db()

class PriceListWindow(ctk.CTkToplevel):
    def __init__(self, master, domain, price_list, best_option):
        super().__init__(master)
        
        self.title(f"💰 {domain.upper()} Tescil Fiyatları (Kıyaslama)")
        self.geometry("800x600")
        self.transient(master) 
        self.grab_set() 
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(len(price_list) + 2, weight=1) 
        
        ctk.CTkLabel(self, text=f"🌐 {domain.upper()} Tescil Fiyatları", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, columnspan=4, pady=10)
        
        # Başlıklar
        ctk.CTkLabel(self, text="Platform", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=5)
        ctk.CTkLabel(self, text="Fiyat (Yıllık)", font=ctk.CTkFont(weight="bold")).grid(row=1, column=1, padx=10, pady=5)
        ctk.CTkLabel(self, text="Özel Avantaj", font=ctk.CTkFont(weight="bold")).grid(row=1, column=2, padx=10, pady=5)
        ctk.CTkLabel(self, text="Eylem", font=ctk.CTkFont(weight="bold")).grid(row=1, column=3, padx=10, pady=5)

        # Fiyat Listesi
        for i, option in enumerate(price_list):
            row_index = i + 2
            
            bg_color = "#3cba54" if option['platform'] == best_option['platform'] else "#2d3039"
            
            frame = ctk.CTkFrame(self, fg_color=bg_color)
            frame.grid(row=row_index, column=0, columnspan=4, padx=20, pady=5, sticky="ew")
            frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

            ctk.CTkLabel(frame, text=option['platform'], font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            price_text = f"${option['fiyat']} USD"
            if option['platform'] == best_option['platform']:
                price_text += " (⭐ En İyi)"
            ctk.CTkLabel(frame, text=price_text, text_color="#ffeb3b").grid(row=0, column=1, padx=10, pady=5)
            
            ctk.CTkLabel(frame, text=option['avantaj']).grid(row=0, column=2, padx=10, pady=5)
            
            # Satın Al Butonu (Gerçek siteye yönlendirme)
            ctk.CTkButton(frame, 
                          text="🛒 Satın Al", 
                          command=lambda u=option['url'], d=domain: self.open_link(u, d), 
                          fg_color="#007bff",
                          hover_color="#0056b3").grid(row=0, column=3, padx=10, pady=5, sticky="e")

        # Açıklama Alanı
        ctk.CTkLabel(self, text="\n**Not:** 'Satın Al' butonuna basmak, ilgili platformun alan adı arama sayfasına yönlendirir. Fiyatlar simülasyondur.", 
                     text_color="gray").grid(row=row_index + 1, column=0, columnspan=4, padx=20, pady=20, sticky="ew")


    def open_link(self, url, domain):
        """Web tarayıcısında ilgili platformun linkini açar."""
        full_url = f"{url}?search={domain}"
        webbrowser.open_new_tab(full_url)
        self.master.log_message(f"Web tarayıcısında {url} adresi {domain} araması için açılıyor.", "yellow")


class ProDomainTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("🌐 PRO Domain Tracker - WHOIS ve Fiyat Kıyaslama")
        self.geometry("1200x700") 
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.current_domain = None
        self.best_option = None 
        self.all_prices = [] 
        self.whois_labels = {} 
        self.is_domain_available = False 
        
        self.sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew") 
        self.sidebar_frame.grid_rowconfigure(len(POPULAR_DOMAINS) + 1, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, text="⭐ Büyük Firma Takip Listesi", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=20, pady=10)
        
        for i, (domain, sector) in enumerate(POPULAR_DOMAINS.items()):
            btn = ctk.CTkButton(self.sidebar_frame, 
                                text=f"{domain}\n({sector})", 
                                command=lambda d=domain: self.select_domain_from_list(d),
                                anchor="w",
                                fg_color="transparent",
                                hover_color="#4e545f")
            btn.grid(row=i + 1, column=0, padx=10, pady=5, sticky="ew")
        
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="ew")
        self.top_frame.grid_columnconfigure((0, 1), weight=1)
        self.top_frame.grid_columnconfigure((2, 3), weight=0) 

        self.search_entry = ctk.CTkEntry(self.top_frame, placeholder_text="Alan Adı Girin", width=300)
        self.search_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        ctk.CTkButton(self.top_frame, text="🔍 Sorgula", command=self.arama_yap).grid(row=0, column=1, padx=5)

        alarm_platform_keys = list(PLATFORM_DATA.keys())
        self.platform_var = ctk.StringVar(value="GoDaddy Backorder")
        ctk.CTkLabel(self.top_frame, text="Alım Platformu:").grid(row=1, column=2, padx=(10, 5), sticky="e")
        self.platform_option = ctk.CTkOptionMenu(self.top_frame, 
                                                 values=alarm_platform_keys,
                                                 variable=self.platform_var)
        self.platform_option.grid(row=1, column=3, padx=(0, 10), sticky="w")
        
        self.content_frame = ctk.CTkFrame(self, corner_radius=10)
        self.content_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="nsew")
        self.content_frame.grid_columnconfigure((0, 1), weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        self.left_panel = ctk.CTkFrame(self.content_frame, corner_radius=8)
        self.left_panel.grid(row=0, column=0, padx=(15, 7), pady=15, sticky="nsew")
        self.left_panel.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self.left_panel, text="🗓️ Alan Adı WHOIS Durumu (Gerçek Veri)", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        
        self.create_whois_display(self.left_panel) 
        
        self.status_label = ctk.CTkLabel(self.left_panel, text="DURUM: Bilgi Gerekli", font=ctk.CTkFont(size=14), text_color="gray")
        self.status_label.grid(row=9, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
        
        self.list_button = ctk.CTkButton(self.left_panel, 
                                         text=f"💸 FİYAT KIYASLA ve TESCİL LİSTESİ", 
                                         command=self.open_price_list_window, 
                                         fg_color="#00bcd4", 
                                         hover_color="#008391", 
                                         height=40,
                                         state="disabled") 
        self.list_button.grid(row=10, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")

        self.alarm_button = ctk.CTkButton(self.left_panel, 
                                         text=f"🔔 ALARM KUR (Boşa Düşmesini Takip Et)", 
                                         command=self.simule_alarm_kur, 
                                         fg_color="#ffeb3b", 
                                         text_color="black",
                                         hover_color="#c9b743", 
                                         height=40,
                                         state="disabled") 
        self.alarm_button.grid(row=11, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="ew")

        self.bot_button = ctk.CTkButton(self.left_panel, 
                                         text=f"🤖 OTO-SATIN AL (Selenium Bot)", 
                                         command=self.simule_selenium_bot, 
                                         fg_color="#e91e63", 
                                         hover_color="#c2185b", 
                                         height=40,
                                         state="disabled") 
        self.bot_button.grid(row=12, column=0, columnspan=2, padx=10, pady=(5, 20), sticky="ew")


        self.right_panel = ctk.CTkFrame(self.content_frame, corner_radius=8)
        self.right_panel.grid(row=0, column=1, padx=(7, 15), pady=15, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(header_frame, text="📰 Uygulama Logları", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkButton(header_frame, text="🗄️ Veritabanı", width=100, fg_color="#34495e", command=self.show_db_history).grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        self.news_box = ctk.CTkTextbox(self.right_panel, corner_radius=8, wrap="word", fg_color="#2d3039", text_color="white")
        self.news_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.log_message("Uygulama başlatıldı. Lütfen alan adını aratarak WHOIS sorgulaması yapın.")
        self.log_message("⚠️ DİKKAT: Artık gerçek WHOIS sorgusu yapılıyor. Sık sorgu yaparsanız IP adresiniz engellenebilir.", "red")
        
    def create_whois_display(self, parent_frame):
        fields = ["Alan Adı", "Tescil Ettiren", "Registrar", "Tescil Tarihi", "Bitiş Tarihi", "Kalan Süre", "Durum Kodları"]
        
        for i, field in enumerate(fields):
            ctk.CTkLabel(parent_frame, text=f"{field}:", font=ctk.CTkFont(weight="bold")).grid(row=i + 1, column=0, padx=10, pady=2, sticky="w")
            label_value = ctk.CTkLabel(parent_frame, text="---", text_color="#00bcd4")
            label_value.grid(row=i + 1, column=1, padx=10, pady=2, sticky="w")
            self.whois_labels[field] = label_value

    def log_message(self, message, color_tag="white", clear_first=False):
        if clear_first:
            self.news_box.delete("1.0", END)
        
        self.news_box.insert(END, f"[{time.strftime('%H:%M:%S')}] {message}\n", color_tag)
        self.news_box.tag_config('red', foreground='#ff5252')
        self.news_box.tag_config('green', foreground='#4caf50')
        self.news_box.tag_config('yellow', foreground='#ffeb3b')
        self.news_box.tag_config('white', foreground='#ffffff')
        self.news_box.see(END)

    def arama_yap(self):
        """Arama çubuğundaki alan adı için WHOIS sorgusu yapar."""
        query = self.search_entry.get().strip().lower()
        self.search_entry.delete(0, END)
        
        query = query.replace("https://", "").replace("http://", "").replace("www.", "").strip()
        query = query.split('/')[0]
        
        if not query:
            self.log_message("Lütfen geçerli bir alan adı girin.", "red")
            return
            
        if "." not in query:
            self.log_message("Lütfen geçerli bir uzantı girin (örn: google.com)", "red")
            return
            
        self.update_panels_with_domain(query)

    def select_domain_from_list(self, domain):
        """Popüler listeden seçilen alanı yükler."""
        self.update_panels_with_domain(domain)

    def update_panels_with_domain(self, domain):
        """WHOIS verilerini çeker ve arayüzü günceller."""
        self.current_domain = domain
        
        self.log_message(f"--- '{domain.upper()}' için **GERÇEK WHOIS Sorgusu** Başlatıldı ---", "yellow", clear_first=True)
        self.status_label.configure(text="DURUM: Sorgulanıyor, lütfen bekleyin...", text_color="yellow")
        
        threading.Thread(target=self._run_whois_thread, args=(domain,), daemon=True).start()

    def _run_whois_thread(self, domain):
        whois_data = get_real_whois_data(domain)
        self.after(0, lambda: self._update_ui_after_whois(whois_data, domain))
        
    def _update_ui_after_whois(self, whois_data, domain):
        self.is_domain_available = whois_data["is_available"]

        save_to_db(whois_data)

        for key, value in whois_data.items():
            if key in self.whois_labels:
                text_color = "#ffeb3b" if self.is_domain_available else "#00bcd4"
                if "HATA" in str(value):
                    text_color = "red"
                self.whois_labels[key].configure(text=value, text_color=text_color)
                
        if self.is_domain_available:
            self.all_prices = find_all_prices(domain)
            self.best_option = self.all_prices[0] 
            
            self.status_label.configure(text=f"DURUM: MÜSAİT! En uygun tescil ücreti: ${self.best_option['fiyat']}", text_color="green")
            self.list_button.configure(state="normal", text=f"💸 FİYAT KIYASLA ve TESCİL LİSTESİ")
            self.alarm_button.configure(state="disabled", text="🔔 ALARM GEREKSİZ")
            self.bot_button.configure(state="disabled")
            self.log_message(f"Alan adı müsait. En uygun fiyat ${self.best_option['fiyat']} ile {self.best_option['platform']} platformunda bulundu.", "green")
        else:
            self.best_option = None
            self.all_prices = []
            
            bitis_tarihi = whois_data.get('Bitiş Tarihi', 'Bilinmiyor')
            
            if "HATA" in str(whois_data.get("Tescil Ettiren", "")):
                 self.status_label.configure(text="DURUM: SORGULAMA HATASI. Lütfen tekrar deneyin.", text_color="red")
                 self.log_message(f"HATA: Gerçek WHOIS sorgusu başarısız oldu. IP adresiniz engellenmiş olabilir.", "red")
                 hata_nedeni = whois_data.get("Durum Kodları", "Bilinmeyen Hata")
                 self.status_label.configure(text=f"DURUM: SORGULAMA HATASI ({hata_nedeni})", text_color="red")
                 
                 if "Port 43" in hata_nedeni:
                     self.log_message("HATA: Bağlantı koptu. İnternet sağlayıcınız (veya Windows Güvenlik Duvarı) WHOIS portunu (Port 43) engelliyor olabilir.", "red")
                 else:
                     self.log_message(f"HATA: Gerçek WHOIS sorgusu başarısız oldu. Detay: {hata_nedeni}", "red")
            else:
                 self.status_label.configure(text=f"DURUM: DOLU. Bitiş Tarihi: {bitis_tarihi}", text_color="red")
                 self.log_message(f"Alan adı dolu ({whois_data.get('Registrar', 'Bilinmiyor')}). Boşa düşme takibi için alarm kurabilirsiniz.", "red")

                 kalan_str = whois_data.get("Kalan Süre", "")
                 if "gün" in kalan_str:
                     try:
                         gun_sayisi = int(kalan_str.split()[0])
                         if gun_sayisi < 30:
                             self.log_message(f"🚨 DİKKAT: '{domain}' alan adının düşmesine çok az kaldı ({gun_sayisi} gün)!", "yellow")
                             if PLYER_AVAILABLE:
                                 notification.notify(
                                     title="🚨 Domain Düşmek Üzere!",
                                     message=f"'{domain}' süresinin bitmesine sadece {gun_sayisi} gün kaldı!",
                                     app_name="Pro Domain Tracker",
                                     timeout=7
                                 )
                             else:
                                 self.log_message("💡 (Ekrana Windows bildirimi gelmesi için terminale 'pip install plyer' yazıp kurmalısınız)", "white")
                     except: pass

            self.list_button.configure(state="disabled", text="❌ FİYAT LİSTESİ MÜSAİT DEĞİL")
            self.alarm_button.configure(state="normal", text=f"🔔 ALARM KUR ({bitis_tarihi} İçin)", fg_color="#ffeb3b")
            self.bot_button.configure(state="normal", text=f"🤖 OTO-SATIN AL BOTU BAŞLAT")


    def open_price_list_window(self):
        """Ayrı bir pencerede fiyat listesini açar."""
        if not self.is_domain_available or not self.all_prices:
            self.log_message("Fiyat listesi görüntülenemiyor. Lütfen önce müsait bir alan adı arayın.", "red")
            return
            
        PriceListWindow(self, self.current_domain, self.all_prices, self.best_option)
        self.log_message("Fiyat listesi yeni pencerede açıldı. Satın al butonu ilgili siteye yönlendirecektir.", "yellow")

    def simule_alarm_kur(self):
        """(SİMÜLASYON) Alarm kurma arayüz eylemi.
        Bu fonksiyon gerçek bir alarm kurmaz, sadece kullanıcı arayüzünde alarmın kurulduğunu gösterir
        ve log mesajı basar. Gerçek bir implementasyon için arka plan görevi (scheduler) gerekir.
        """
        if self.is_domain_available:
             self.log_message("Bu alan adı zaten müsait. Alarm kurmaya gerek yok, tescil edin.", "yellow")
             return
             
        domain = self.current_domain
        whois_data = get_real_whois_data(domain)
        bitis_tarihi = whois_data.get('Bitiş Tarihi', 'Bilinmiyor')
        
        self.log_message(f"🔔 {domain} için ALARM KURULUYOR...", "yellow")
        time.sleep(0.5)
        self.log_message(f"✅ ALARM BAŞARILI: {domain} alan adının {bitis_tarihi} tarihindeki boşa düşme süreci takibe alındı.", "green")
        self.log_message(f"Seçilen platform (**{self.platform_var.get()}**) üzerinden olası 'Drop-Catch' denemeleri için sistem hazırlandı.", "yellow")
        self.alarm_button.configure(text="✅ ALARM KURULDU (Takip Ediliyor)", fg_color="#4caf50", hover_color="#4caf50", state="disabled")

    def simule_selenium_bot(self):
        """(SİMÜLASYON) Selenium botu başlatma arayüzü eylemi.
        Bu fonksiyon gerçek bir bot başlatmaz. Sadece arayüzü günceller ve log mesajları basar.
        Gerçek bir implementasyon, Selenium veya benzeri bir otomasyon aracıyla entegrasyon gerektirir.
        """
        domain = self.current_domain
        self.log_message(f"🤖 SELENIUM BOT BAŞLATILIYOR...", "yellow")
        self.log_message(f"[{domain}] için arka planda gizli Chrome tarayıcısı açılıyor...", "white")
        self.log_message(f"⚠️ Sistem domainin boşa düşeceği anı bekleyip (0.1ms ping ile) oto-satın alma deneyecektir.", "green")
        self.bot_button.configure(text="🤖 BOT AKTİF (Bekleniyor...)", fg_color="#4caf50", state="disabled")

    def show_db_history(self):
        win = ctk.CTkToplevel(self)
        win.title("🗄️ Sorgu Geçmişi (SQLite)")
        win.geometry("850x500")
        win.transient(self)
        win.grab_set()
        
        ctk.CTkLabel(win, text="Veritabanına Kayıtlı Sorgular", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        try:
            conn = sqlite3.connect("domain_history.db")
            cursor = conn.cursor()
            cursor.execute("SELECT domain, status, registrar, creation_date, expiration_date, query_time FROM history ORDER BY id DESC")
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                ctk.CTkLabel(scroll, text="Henüz kayıtlı sorgu bulunmuyor.", text_color="gray").pack(pady=20)
                return
                
            for rec in records:
                domain, status, reg, c_date, e_date, q_time = rec
                card = ctk.CTkFrame(scroll, fg_color="#2B2B2B", corner_radius=8)
                card.pack(fill="x", pady=5, padx=5)
                
                color = "#4caf50" if status == "MÜSAİT" else "#ff5252" if status == "DOLU" else "gray"
                
                ctk.CTkLabel(card, text=domain, font=ctk.CTkFont(weight="bold", size=14), text_color=color).grid(row=0, column=0, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(card, text=f"Durum: {status}").grid(row=0, column=1, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(card, text=f"Bitiş: {e_date}").grid(row=0, column=2, padx=10, pady=5, sticky="w")
                ctk.CTkLabel(card, text=f"Tarih: {q_time.split('.')[0]}", text_color="gray").grid(row=0, column=3, padx=10, pady=5, sticky="e")
                card.grid_columnconfigure(3, weight=1)
                
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Veritabanı okuma hatası: {e}", text_color="red").pack(pady=20)

if __name__ == "__main__":
    app = ProDomainTrackerApp()
    app.mainloop()