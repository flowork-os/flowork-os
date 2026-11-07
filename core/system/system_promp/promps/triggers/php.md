# 🐘 PASSIVE TRIGGER: PHP & ENTERPRISE WEB DOCTRINE
* **Konteks Terdeteksi**: Workspace aktif memuat berkas `.php` atau `composer.json`.
* **Aturan Khusus**:
  1. Patuhi standar PHP 8.2+ modern: strict typing (`declare(strict_types=1);`), typed properties, constructor property promotion.
  2. Gunakan PSR-12 coding standard dan PSR-4 autoloading.
  3. Hindari fungsi usang, pastikan penanganan error menggunakan try-catch berstruktur dan logging yang aman.
  4. Untuk interaksi database, wajib menggunakan PDO dengan prepared statements untuk mencegah SQL Injection.
