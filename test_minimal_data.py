from app import app, db
from models import Person, Holiday, Team, User
from datetime import date

def add_minimal_test_data():
    with app.app_context():
        # Takım ekle
        if not Team.query.first():
            team = Team(name="Test Takımı", manager="Test Manager")
            db.session.add(team)
            db.session.commit()
            print("✓ Test takımı eklendi")
        
        # Personel ekle
        if not Person.query.first():
            team = Team.query.first()
            person = Person(
                name="Test Personel",
                email="test@test.com",
                team_id=team.id
            )
            db.session.add(person)
            db.session.commit()
            print("✓ Test personeli eklendi")
        
        # Resmi tatil ekle
        if not Holiday.query.first():
            holiday = Holiday(
                name="Cumhuriyet Bayramı",
                date=date(2025, 10, 29)
            )
            db.session.add(holiday)
            db.session.commit()
            print("✓ Test tatili eklendi")
        
        # Test kullanıcısı ekle
        if User.query.count() == 1:  # Sadece admin varsa
            test_user = User(
                username="testuser",
                email="testuser@test.com",
                role="personel"
            )
            test_user.set_password("test123")
            db.session.add(test_user)
            db.session.commit()
            print("✓ Test kullanıcısı eklendi")
        
        print("\n📊 Veritabanı Durumu:")
        print(f"- Kullanıcılar: {User.query.count()}")
        print(f"- Takımlar: {Team.query.count()}")
        print(f"- Personeller: {Person.query.count()}")
        print(f"- Tatiller: {Holiday.query.count()}")

if __name__ == '__main__':
    add_minimal_test_data()