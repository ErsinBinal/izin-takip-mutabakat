# İzin Takip ve Mutabakat Sistemi

Flask tabanlı modern bir izin takip ve personel yönetim sistemi.

## 🌟 Özellikler

### Kullanıcı Yönetimi
- ✅ Flask-Login ile güvenli kimlik doğrulama
- ✅ Rol tabanlı erişim kontrolü (Admin, Yönetici, Personel)
- ✅ Kullanıcı CRUD işlemleri
- ✅ Şifre hashleme (Werkzeug)
- ✅ 8 saatlik session timeout

### İzin Yönetimi
- ✅ İzin talebi oluşturma
- ✅ Müsaitlik kontrolü
- ✅ İzin onay/red sistemi
- ✅ İzin bakiyesi takibi
- ✅ Dinamik personel listesi

### Admin Paneli
- ✅ Bekleyen izin talepleri yönetimi
- ✅ Kullanıcı yönetimi
- ✅ İzin bakiyesi yönetimi
- ✅ Personel listesi görüntüleme

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- pip
- virtualenv

### Adımlar

1. **Projeyi klonlayın**
```bash
git clone https://github.com/ErsinBinal/izin-takip-mutabakat.git
cd izin-takip-mutabakat
```

2. **Virtual environment oluşturun**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# veya
.venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Veritabanını oluşturun**
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. **Test verisi ekleyin (Opsiyonel)**
```bash
python add_test_data.py
```

6. **Uygulamayı başlatın**
```bash
python app.py
```

Uygulama `http://127.0.0.1:5004` adresinde çalışacaktır.

## 🔐 Varsayılan Giriş Bilgileri

**Admin Hesabı:**
- Kullanıcı Adı: `admin`
- Şifre: `7905`

> ⚠️ **Güvenlik Uyarısı:** Üretim ortamında bu bilgileri mutlaka değiştirin!

## 📁 Proje Yapısı

```
izin_takip_Projesi/
├── app.py                          # Ana Flask uygulaması
├── models.py                       # Veritabanı modelleri
├── requirements.txt                # Python bağımlılıkları
├── add_test_data.py               # Test verisi ekleme scripti
├── test_minimal_data.py           # Minimal test verisi
├── templates/
│   ├── base.html                  # Ana template
│   ├── login.html                 # Giriş sayfası
│   ├── index.html                 # Ana sayfa (İzin talebi)
│   ├── admin.html                 # Admin paneli
│   ├── admin_users.html           # Kullanıcı yönetimi
│   └── admin_leave_balances.html  # İzin bakiyesi yönetimi
└── .gitignore
```

## 🔧 Teknolojiler

- **Backend:** Flask 2.3.3
- **Veritabanı:** SQLite (SQLAlchemy ORM)
- **Kimlik Doğrulama:** Flask-Login 0.6.3
- **Şifreleme:** Werkzeug Security
- **Frontend:** Bootstrap 5, Tailwind CSS
- **JavaScript:** Vanilla JS (Fetch API)

## 📊 Veritabanı Modelleri

- **User:** Kullanıcı bilgileri ve kimlik doğrulama
- **Person:** Personel bilgileri
- **Team:** Takım/Departman bilgileri
- **LeaveRequest:** İzin talepleri
- **Holiday:** Resmi tatiller
- **LeaveBalance:** Personel izin bakiyeleri

## 🛡️ Güvenlik Özellikleri

- Werkzeug ile şifre hashleme
- Flask-Login session yönetimi
- Rol tabanlı erişim kontrolü
- CSRF koruması (Flask-WTF)
- SQL Injection koruması (SQLAlchemy ORM)

## 📝 API Endpoints

### Kimlik Doğrulama
- `POST /login` - Giriş yap
- `GET /logout` - Çıkış yap

### İzin İşlemleri
- `POST /api/leave/check` - Müsaitlik kontrolü
- `POST /api/leave/request` - İzin talebi oluştur
- `PUT /api/admin/leave/approve/<id>` - İzin onayla
- `PUT /api/admin/leave/reject/<id>` - İzin reddet

### Kullanıcı Yönetimi
- `GET /admin/users` - Kullanıcı listesi
- `POST /admin/users/create` - Kullanıcı oluştur
- `POST /admin/users/<id>/update` - Kullanıcı güncelle
- `POST /admin/users/<id>/delete` - Kullanıcı sil

### İzin Bakiyesi
- `GET /admin/leave-balances` - Bakiye listesi
- `POST /admin/leave-balances/update` - Bakiye güncelle

### Diğer
- `GET /api/admin/person/list` - Personel listesi

## 🎯 Kullanım

1. Admin hesabıyla giriş yapın
2. Admin menüsünden "Kullanıcı Yönetimi"ne girin
3. Yeni kullanıcılar ekleyin
4. "İzin Hakları" bölümünden izin bakiyelerini ayarlayın
5. Ana sayfadan izin talebi oluşturun
6. Admin panelinden talepleri onaylayın/reddedin

## 🚧 Geliştirme Planları

- [ ] Email bildirimleri
- [ ] Rapor ve export özellikleri
- [ ] Takvim görünümü
- [ ] Mobil responsive iyileştirmeleri
- [ ] PostgreSQL desteği
- [ ] Docker containerization
- [ ] CI/CD pipeline

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 👤 Geliştirici

**Ersin Binal**
- GitHub: [@ErsinBinal](https://github.com/ErsinBinal)

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📞 İletişim

Sorularınız veya önerileriniz için issue açabilirsiniz.

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
