# BOTHelper

BOTHelper adalah sistem chatbot Telegram yang memungkinkan pengguna berinteraksi satu-satu dengan admin melalui sistem antrian. Bot ini dirancang untuk memfasilitasi komunikasi langsung antara pengguna dan admin dengan cara yang terorganisir dan efisien.

## Fitur Utama

- Sistem antrian pengguna untuk berinteraksi dengan admin
- Sesi obrolan langsung antara pengguna dan admin
- Batas waktu otomatis untuk mengakhiri obrolan
- Pemberitahuan posisi dalam antrian
- Perlindungan untuk mencegah pengguna ganda dalam sesi obrolan
- Dukungan untuk pesan teks dan media

## Instalasi

### Prasyarat

- Python 3.8 atau lebih baru
- Docker dan Docker Compose (opsional)

### Langkah-langkah Instalasi

1. Clone repositori ini:
   ```bash
   git clone https://github.com/username/BOTHelper.git
   cd BOTHelper
   ```

2. Buat file `.env` berdasarkan contoh:
   ```bash
   cp .env.example .env
   ```

3. Isi file `.env` dengan informasi yang diperlukan:
   - `TELEGRAM_BOT_TOKEN`: Token bot Telegram dari @BotFather
   - `ADMIN_USER_ID`: ID Telegram admin (dalam bentuk angka)
   - `CHAT_TIMEOUT`: Durasi timeout obrolan dalam detik (default: 300)
   - `MAX_QUEUE_SIZE`: Jumlah maksimum pengguna dalam antrian (default: 10)

4. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```

## Konfigurasi

Bot ini menggunakan beberapa variabel lingkungan untuk konfigurasi:

- `TELEGRAM_BOT_TOKEN` (wajib): Token bot Telegram dari @BotFather
- `ADMIN_USER_ID` (wajib): ID Telegram admin (dalam bentuk angka)
- `CHAT_TIMEOUT` (opsional): Durasi timeout obrolan dalam detik (default: 300)
- `MAX_QUEUE_SIZE` (opsional): Jumlah maksimum pengguna dalam antrian (default: 10)

## Penggunaan

### Melalui Python

1. Pastikan semua dependensi terinstal
2. Jalankan bot:
   ```bash
   python app/bot.py
   ```

### Melalui Docker

1. Bangun dan jalankan kontainer:
   ```bash
   docker-compose up --build
   ```

## Perintah Bot

- `/start` - Memulai percakapan dengan bot
- `/chat` - Bergabung dalam antrian untuk berbicara dengan admin
- `/queue` - Melihat posisi Anda dalam antrian
- `/stop` - Mengakhiri sesi obrolan saat ini
- `/help` - Menampilkan pesan bantuan ini

## Struktur Proyek

```
BOTHelper/
├── app/
│   ├── bot.py              # File utama bot
│   ├── config/
│   │   └── settings.py     # Konfigurasi aplikasi
│   ├── handlers/
│   │   ├── command_handlers.py     # Handler perintah
│   │   ├── message_handlers.py     # Handler pesan
│   │   └── callback_handlers.py    # Handler callback
│   ├── models/
│   │   └── chat_manager.py # Manajer obrolan dan antrian
│   └── utils/
│       └── helpers.py      # Fungsi-fungsi pembantu
├── .env.example            # Contoh file konfigurasi lingkungan
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Kontribusi

1. Fork repositori ini
2. Buat branch fitur (`git checkout -b fitur/Ajaib`)
3. Commit perubahan Anda (`git commit -m 'Tambah fitur Ajaib'`)
4. Push ke branch (`git push origin fitur/Ajaib`)
5. Buka Pull Request

## Lisensi

Proyek ini dilisensikan di bawah MIT License - lihat file [LICENSE](LICENSE) untuk detail selengkapnya.