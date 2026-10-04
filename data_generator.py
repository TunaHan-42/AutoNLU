from google import genai
import json
import csv
import time
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)


def generate_nlp_data():
    db_file = 'Data/obd_database.json'
    csv_file = 'Data/nlp_dataset.csv'

    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            obd_db = json.load(f)
    except FileNotFoundError:
        print(f"Hata: {db_file} bulunamadı.")
        return

    #csv dosyası varmı yokmu
    islenen = set()
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) == 2:
                    islenen.add(row[1])
        print(f"{len(islenen)} arıza kodu zaten CSV'de mevcut. Kaldığı yerden devam ediliyor...")
    else:#csv dosyası yok. oluştur
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["text", "label"])

    #Şikayet cümlelerinin üretimi
    for code, data in obd_db.items():
        if code in islenen:
            continue #kod zaten işlenmiş sonrakine geç

        print(f"\n[{code}] için şikayet cümleleri üretiliyor...")
        belirtiler = ', '.join(data.get('symptoms', []))
        sebepler = ', '.join(data.get('causes', []))


        prompt = f"""
        Arıza Kodu: {code}
        Belirtiler: {belirtiler}
        Sebepler: {sebepler}

        Görev: SADECE yukarıda verilen arıza koduna, belirtilere ve sebeplere KESİNLİKLE bağlı kalarak, bu arızayı yaşayan ve mekanikten çok anlamayan sıradan bir müşterinin ağzından 20 farklı şikayet cümlesi yaz.

        KURALLAR:
        1. KAPSAM DIŞINA ÇIKMA: Sadece sana verilen arızayı anlat. Kendi kendine alakasız sorunlar uydurma.
        2. SPESİFİK OL (ÇOK ÖNEMLİ): Sadece "araba çalışmıyor", "lamba yandı" gibi yuvarlak ve genel laflar KULLANMA. Verilen belirti ve sebepleri müşterinin HİSSEDECEĞİ fiziksel durumlara çevir (örn: arıza yakıtla ilgiliyse "benzin kokuyor, su gibi yakıyor", tekleme ise "araba beşik gibi sallanıyor, gaz yemiyor" gibi o arızaya ÖZEL ayrıştırıcı kelimeler kullan).
        3. HALK DİLİ: Müşteri usta gibi konuşmasın (teknik parça isimleri verme), sadece o parçanın bozulduğunda araçta yarattığı hissi halk ağzıyla söyle.
        4. KISA VE ÖZ: Cümleler en fazla 10-15 kelime olsun. Destan yazma.
        5. FORMAT: Numara veya tire kullanma, alt alta düz cümleler yaz.
        """

        #Api isteği
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt
            )

            cumleler = response.text.strip().split('\n')

            #Verileri temizleyip .csv dosyasına ekle
            with open(csv_file, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                eklenen = 0
                for c in cumleler:
                    temiz = c.strip().lstrip("0123456789.-* ")
                    if temiz:
                        writer.writerow([temiz, code])
                        eklenen += 1

            print(f"Başarılı! {code} -> {eklenen} cümle kaydedildi.")

            #dakikada 15 istek atma sınırımız var
            time.sleep(5)

        except Exception as e:
            print(f"API Hatası veya Limit Uyarısı: {e}")
            print("Sistem 60 saniye dinlenmeye alınıyor.")
            time.sleep(60)


if __name__ == "__main__":
    generate_nlp_data()