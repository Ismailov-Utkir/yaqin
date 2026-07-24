# yaqin — serverga o'rnatish (admin panel bilan)

Bu repoда **sayt** (`index.html`, `cars.json`, `ads.json`, rasmlар) va **admin panel** (`admin_server.py`) birga.

## Lokalda (kompyuterda)
- `ADMIN.bat` ni ishga tushiring → http://localhost:8765 → parol bilan kiring.
- Parol standart: `test1234`.

## Haqiqiy serverda (Linux/VPS)
1. Reponi klon qiling:
   ```
   git clone https://github.com/Ismailov-Utkir/yaqin.git
   cd yaqin
   ```
2. Git push ishlashi uchun serverda token sozlang (faqat shu server biladi):
   ```
   git remote set-url origin https://<TOKEN>@github.com/Ismailov-Utkir/yaqin.git
   ```
3. Kuchli parolni env orqali bering va admin panelни ishga tushiring:
   ```
   YAQIN_ADMIN_PASSWORD="KuchliParol123" python3 admin_server.py
   ```
4. Saytning o'zini xohlagan statik xosting yoki shu serverdan bering.

> ⚠️ **Parolni hech qachon kodga yozib, GitHub'ga yubormang.** Faqat serverда `YAQIN_ADMIN_PASSWORD` orqali bering.
> ⚠️ **Token** ham hech qachon kodda bo'lmasin — faqat serverning git sozlamasida.
