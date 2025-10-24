from app import app, db
from models import Person, Holiday, Team
from datetime import date

def add_test_data():
    with app.app_context():
        # Takımlar ekle
        if not Team.query.first():
            team1 = Team(name="Yazılım Geliştirme", max_concurrent_leaves=2)
            team2 = Team(name="İnsan Kaynakları", max_concurrent_leaves=1)
            team3 = Team(name="Pazarlama", max_concurrent_leaves=1)
            db.session.add(team1)
            db.session.add(team2)
            db.session.add(team3)
            db.session.commit()
            print("Takımlar eklendi!")
        
        # Personel ekle
        if not Person.query.first():
            person1 = Person(
                name="Ahmet Yılmaz",
                email="ahmet@company.com",
                role="Yazılım Geliştirici",
                team_id=1,
                hire_date=date(2020, 1, 15)
            )
            person2 = Person(
                name="Ayşe Demir",
                email="ayse@company.com",
                role="İK Uzmanı",
                team_id=2,
                hire_date=date(2019, 3, 10)
            )
            person3 = Person(
                name="Mehmet Kaya",
                email="mehmet@company.com",
                role="Proje Yöneticisi",
                team_id=1,
                hire_date=date(2018, 6, 20)
            )
            person4 = Person(
                name="Fatma Özkan",
                email="fatma@company.com",
                role="Pazarlama Uzmanı",
                team_id=3,
                hire_date=date(2021, 9, 5)
            )
            person5 = Person(
                name="Ali Çelik",
                email="ali@company.com",
                role="Backend Developer",
                team_id=1,
                hire_date=date(2022, 2, 1)
            )
            
            db.session.add(person1)
            db.session.add(person2)
            db.session.add(person3)
            db.session.add(person4)
            db.session.add(person5)
            db.session.commit()
            print("Personeller eklendi!")
        
        # Tatiller ekle
        if not Holiday.query.first():
            holidays = [
                Holiday(date=date(2025, 1, 1), name="Yeni Yıl"),
                Holiday(date=date(2025, 4, 23), name="Ulusal Egemenlik ve Çocuk Bayramı"),
                Holiday(date=date(2025, 5, 1), name="İşçi Bayramı"),
                Holiday(date=date(2025, 5, 19), name="Atatürk'ü Anma ve Gençlik Spor Bayramı"),
                Holiday(date=date(2025, 7, 15), name="Demokrasi ve Milli Birlik Günü"),
                Holiday(date=date(2025, 8, 30), name="Zafer Bayramı"),
                Holiday(date=date(2025, 10, 29), name="Cumhuriyet Bayramı"),
                Holiday(date=date(2025, 12, 25), name="Noel"),
                Holiday(date=date(2025, 11, 11), name="Kurban Bayramı"),
            ]
            for holiday in holidays:
                db.session.add(holiday)
            db.session.commit()
            print("Tatiller eklendi!")
        
        print("Tüm test verileri başarıyla eklendi!")

if __name__ == "__main__":
    add_test_data()