import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time
import json
import os


def run_massive_scraper():
    try:
        with open('Data/valid_codes.json', 'r', encoding='utf-8') as f:
            valid_codes = json.load(f)
    except FileNotFoundError:
        print("Hata: valid_codes.json bulunamadı.")
        return

    db_file = 'Data/obd_database.json'
    firebase_file = 'Data/firebase_solutions.json'

    if os.path.exists(db_file) and os.path.exists(firebase_file):
        with open(db_file, 'r', encoding='utf-8') as f:
            obd_database = json.load(f)
        with open(firebase_file, 'r', encoding='utf-8') as f:
            firebase_solutions = json.load(f)
        print(f"Kayıtlı {len(obd_database)} kod bulundu. Kaldığı yerden devam edilecek.")
    else:
        obd_database = {}
        firebase_solutions = {}
        print("Yeni veri tabanları oluşturuluyor...")

    print("Başlıyor...")
    driver = uc.Chrome()

    try:
        for code in valid_codes:
            #Bazı çözüm yollarını çekme işlemi yapılmadığı için sorun fixlendi şuan çekilmişmi kontrol ediliyor
            if code in obd_database and code in firebase_solutions:
                if len(firebase_solutions[code].get("solution", "")) > 10:
                    print(f"[{code}] tam çekilmiş")
                    continue
                else:
                    print(f"[{code}] çözümü gelmemiş, tekrar aranıyor...")

            print(f"\n[{code}] için veriler çekiliyor...")
            url = f"https://www.obd-codes.com/{code.lower()}"

            driver.get(url)
            time.sleep(9)#Cloudflare doğrulaması için az bekliyoruz

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            symptoms_list, causes_list, solution_text = [], [], ""

            #İşlediğimiz kodun semptomlarını al ve listeye kaydet
            sym_header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and 'symptom' in tag.text.lower())
            if sym_header and sym_header.find_next_sibling('ul'):
                symptoms_list = [li.text.strip() for li in sym_header.find_next_sibling('ul').find_all('li')]

            #işlediğimiz kodun sebeplerini al ve listeye kaydet
            cause_header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and 'cause' in tag.text.lower())
            if cause_header and cause_header.find_next_sibling('ul'):
                causes_list = [li.text.strip() for li in cause_header.find_next_sibling('ul').find_all('li')]

            # Çözümü alıyoruz
            sol_header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h4'] and any(
                word in tag.text.lower() for word in ['solution', 'repair', 'fix', 'step', 'troubleshooting']))
            if sol_header:
                for sibling in sol_header.find_next_siblings():
                    #Bir sonraki ana başlığa kadar çözüm metni devam ettiği için bir sonraki ana başlığa geldiğimizde duruyoruz
                    if sibling.name == 'h2':
                        break
                    # Paragrafları metne ekle
                    if sibling.name == 'p':
                        solution_text += sibling.text.strip()
                    #Paragraf değilde maddeli şekilde ise araya "-" koyarak alıyoruz çözümü
                    elif sibling.name == 'ul':
                        for li in sibling.find_all('li'):
                            solution_text += "- " + li.text.strip()

            #Çektiğimiz verileri dosyalarına ekliyoruz
            obd_database[code] = {
                "symptoms": symptoms_list,
                "causes": causes_list
            }

            firebase_solutions[code] = {
                "solution": solution_text.strip()
            }

            print(
                f"Başarılı! Belirti: {len(symptoms_list)} | Neden: {len(causes_list)} | Çözüm: {len(solution_text)} karakter.")

            with open(db_file, 'w', encoding='utf-8') as f:
                json.dump(obd_database, f, indent=4)
            with open(firebase_file, 'w', encoding='utf-8') as f:
                json.dump(firebase_solutions, f, indent=4)

    except Exception as e:
        print(f"Döngüde hata oluştu: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        print(f"\nİşlem bitti. Veriler '{db_file}' ve '{firebase_file}' dosyalarında.")


if __name__ == "__main__":
    run_massive_scraper()