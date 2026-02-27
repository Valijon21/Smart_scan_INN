# SmartScan INN (INN TOp)

SmartScan INN (shuningdek, **INN TOp**) – kompyuter ekranidan rasmga olish orqali matnlarni tezkor o'quvchi va tahlil qiluvchi maxsus dastur. Ushbu dastur OCR texnologiyasidan foydalangan holda tashkilotlarning STIR (INN), rahbar ismi (FISH) va telefon raqamlarini avtomatik ravishda aniqlaydi.

## Asosiy Imkoniyatlar
- **F8 va F9 Tugmalari orqali Tezkor Rasmga Olish:**  
  F8 tugmasi orqali butun ekranni va F9 tugmasi orqali ekranning kerakli qismini kesib olish imkoniyati.
- **Avtomatik OCR va Tahlil:**  
  Olingan rasmdagi matnlar avtomatik yozma shaklga o'giriladi (TXT) hamda tashkilot ma'lumotlari aniqlanadi.
- **Aqlli Saqlash:**  
  Rasmlar va ularning matn fayllari aniqlangan ma'lumotlar bilan nomlanib, avtomatik ravishda (`INN_Tashkilot_FISH_Tel.png`) `ekran_rasimlar` papkasida saqlanadi.
- **Tarixni Ko'rish (History):**  
  Oldin olingan barcha rasmlar va ma'lumotlarni dasturning "Tarix" oynasidan tezda topish, ko'rish va o'qish mumkin.
- **Qidiruv Tizimi:**  
  Dasturning o'zidan tashkilot nomi yoki STIR (INN) orqali bazadan qidirish imkoniyati mavjud.

## Muallif Haqida
Dastur **Valijon Ergashev** tomonidan ishlab chiqilgan va dasturlashtirilgan.
- **Dasturchi:** Valijon Ergashev
- **Aloqa (Telefon):** +998 77 342 33 21

## Qanday Ishga Tushiriladi?
Dasturni ishga tushirish uchun Python o'rnatilgan bo'lishi kerak. Barcha kerakli modullarni o'rnatgach, quyidagi buyruqni bering:
```bash
python main.py
```
Yoki `.exe` faylga ogirilgan ko'rinishdan foydalanish mumkin (`Run_App.bat` orqali).
