# WorkTaskMe — دليل سهل

## أسهل تشغيل (زي السيرفر على جهازك)

من جذر المشروع:

```powershell
cd E:\WorkTaskMe
.\start.ps1
```

هيعمل تلقائي: migrate + ديمو داتا + سيرفر Daphne على البورت 8000.

افتح: **http://127.0.0.1:8000/**

| | |
|--|--|
| Email | `demo@worktaskme.com` |
| Password | `Demo1234!` |

### بديل Docker (أقرب للإنتاج: Postgres + Redis)

```powershell
cd E:\WorkTaskMe
docker compose up --build
```

## عربي / English

في الواجهة زر **AR | EN** — يغيّر اللغة واتجاه الصفحة (RTL/LTR).  
الـ API كمان يفهم `Accept-Language: ar` أو `en`.

## إيه اتصلح واتقوى في الباكند؟

- Dashboard stats: `/api/workspaces/{id}/stats/`
- تعديل Tasks (PATCH) بشكل موثوق
- دعوات + قائمة pending invites
- إشعارات In-app
- bootstrap_local
- i18n لرسائل الأخطاء

## الصلاحيات باختصار

| الدور | المعنى |
|-------|--------|
| admin | دعوة + أدوار + كل حاجة |
| project_manager | المشاريع والأعمدة |
| member | مهام وتقويم |
| viewer | قراءة فقط |

## مشاركة زميل

Team & Access → إيميل → Send invite → انسخ اللينك (أو شوف كونسول السيرفر للإيميل محلياً).

## Flutter

```powershell
cd mobile
flutter run -d chrome
```
