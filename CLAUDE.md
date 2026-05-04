# EMLMS — Claude Code Context

## Project Overview

A full-stack Learning Management System built with Django 5.1. Supports free and paid courses (Paystack), multiple lesson types (video, text, quiz, downloadable resources), student progress tracking, auto-generated PDF certificates, per-course discussions, and coupon/discount codes.

**GitHub:** https://github.com/Emmakhris/emlms  
**Target market:** Ghana / Africa (GHS currency, Paystack)  
**Deployment target:** Ubuntu 24.04 VPS — Nginx + Gunicorn

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | Django 5.1.4 |
| Auth | django-allauth (email login, email verification) |
| Frontend | Django templates + Tailwind CSS + Alpine.js + HTMX |
| Video player | Plyr.js (HLS adaptive streaming) |
| Media storage | Cloudinary (signed URLs for paid content) |
| Payments | Paystack (GHS, webhook + verify flow) |
| Background tasks | Celery + Redis |
| PDF certificates | WeasyPrint (requires GTK libs — works on Linux, not Windows) |
| Database | PostgreSQL (production) / SQLite (development) |
| Cache | Redis (production) / LocMemCache (development) |
| Email | django-anymail / Mailgun (production) / console (development) |
| Error tracking | Sentry (production) |

**Do not suggest:** Stripe, React, S3, or any alternative to the above unless the user explicitly asks.

---

## Development Setup

```bash
# Activate virtualenv
source venv/Scripts/activate          # Windows (Git Bash)
source venv/bin/activate              # Linux/Mac

# Run dev server (always use --noreload to avoid stale multi-process issues on Windows)
python manage.py runserver 8000 --settings=emlms.settings.development --noreload

# Tailwind (watch mode)
npx tailwindcss -i ./static/src/input.css -o ./static/css/output.css --watch

# Migrations
python manage.py makemigrations --settings=emlms.settings.development
python manage.py migrate --settings=emlms.settings.development

# Seed initial data (categories, SiteSettings, Celery Beat schedules)
python manage.py setup_initial_data --settings=emlms.settings.development

# Create superuser
python manage.py createsuperuser --settings=emlms.settings.development
```

**Windows gotcha:** Multiple stale `runserver` processes can all bind to port 8000, causing random 500 errors. Kill them all first:
```powershell
# PowerShell — find and kill all processes on port 8000
netstat -ano | Select-String "8000"
Stop-Process -Id <PID> -Force
```

---

## Environment Variables

Copy `.env.example` → `.env` and fill in values. Required for production:

```
SECRET_KEY, DATABASE_URL, REDIS_URL,
CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
PAYSTACK_PUBLIC_KEY, PAYSTACK_SECRET_KEY,
DEFAULT_FROM_EMAIL, ANYMAIL_MAILGUN_API_KEY, MAILGUN_SENDER_DOMAIN,
SENTRY_DSN, SITE_URL
```

Development works with only `SECRET_KEY` and `DATABASE_URL=sqlite:///db.sqlite3`.

---

## Project Structure

```
emlms/
├── emlms/                    # Django project package
│   ├── settings/
│   │   ├── base.py           # Shared settings
│   │   ├── development.py    # DEBUG=True, SQLite, console email, no axes
│   │   └── production.py     # PostgreSQL, Redis, Sentry, SSL
│   ├── celery.py
│   └── urls.py
├── apps/
│   ├── accounts/             # Custom User model, profiles, auth views
│   ├── courses/              # Course catalog, categories, reviews
│   ├── lessons/              # Sections, lessons, progress, curriculum CRUD
│   ├── enrollments/          # Enrollment + CourseProgress tracking
│   ├── payments/             # Paystack checkout, webhook, orders
│   ├── quizzes/              # Quiz engine (MCQ/MSQ/T-F), attempts, grading
│   ├── certificates/         # PDF generation, QR code, public verify
│   ├── discussions/          # Per-course Q&A threads, nested replies
│   ├── coupons/              # Discount codes (percentage + fixed)
│   ├── dashboard/            # Student + instructor dashboards
│   └── core/                 # SiteSettings, Notifications, context processors
├── templates/                # All HTML (one subdir per app)
├── static/
│   ├── src/input.css         # Tailwind directives
│   └── css/output.css        # Compiled Tailwind (committed)
├── deploy/                   # Nginx, Gunicorn, systemd, deploy.sh
├── requirements/
│   ├── base.txt
│   ├── development.txt       # + debug-toolbar, pytest, factory-boy
│   └── production.txt        # + gunicorn, whitenoise, sentry-sdk
└── manage.py
```

---

## URL Map

| Prefix | App | Namespace |
|--------|-----|-----------|
| `/` | core | `core` |
| `/accounts/` | allauth + accounts | `accounts` |
| `/courses/` | courses | `courses` |
| `/courses/` | lessons | `lessons` |
| `/courses/` | quizzes | `quizzes` |
| `/courses/` | discussions | `discussions` |
| `/checkout/` | payments | `checkout` |
| `/payments/` | payments | `payments` |
| `/certificates/` | certificates | `certificates` |
| `/coupons/` | coupons | `coupons` |
| `/dashboard/` | dashboard | `dashboard` |
| `/enroll/` | enrollments | `enrollments` |
| `/admin-emlms-secure/` | Django admin | — |

**Key URL patterns:**
```
/courses/<slug>/learn/                      # Resume last lesson
/courses/<slug>/learn/<uuid:lesson_id>/     # Specific lesson
/courses/<slug>/quiz/<int:quiz_id>/         # Take quiz
/courses/<slug>/curriculum/                 # Instructor curriculum editor
/courses/lessons/<uuid>/complete/           # Mark lesson complete (POST)
/courses/lessons/<uuid>/progress/           # Save video position (POST)
/payments/webhook/                          # Paystack webhook (no CSRF, no rate limit)
/certificates/verify/<code>/                # Public certificate verify
```

---

## Data Models (key relationships)

```
User (UUID PK, email login)
  ├── StudentProfile (1:1)
  └── InstructorProfile (1:1)

Course (UUID PK, slug)
  ├── Section (ordered)
  │   └── Lesson (UUID PK, type: video/text/quiz/resource)
  │       ├── VideoLesson (Cloudinary HLS)
  │       ├── TextLesson (Markdown → rendered_html property)
  │       ├── Quiz → Question → Choice
  │       └── DownloadableResource
  └── CourseReview

Enrollment (UUID PK)
  └── CourseProgress (percentage, last_accessed_lesson)
      └── LessonProgress (per lesson: status, last_position_seconds)

Order (UUID PK, Paystack reference)
  └── PaymentTransaction

Certificate (UUID PK, verification_code e.g. EMLMS-XXXXXXXX)

Thread → Reply (self-FK for nested replies)
Coupon ← CouponUsage
```

---

## Celery Tasks

| Task | App | Trigger |
|------|-----|---------|
| `process_successful_payment` | payments | Paystack webhook / verify |
| `check_and_issue_certificate` | certificates | Course reaches 100% |
| `generate_certificate_pdf` | certificates | After cert record created |
| `send_certificate_email` | certificates | After PDF generated |
| `send_enrollment_confirmation_email` | accounts | After enrollment |
| `notify_discussion_reply` | discussions | After reply posted |
| `check_course_completions` | core | Beat: hourly |
| `update_course_statistics` | core | Beat: nightly 2am |
| `send_weekly_progress_digest` | core | Beat: Sundays 8am |

In development `CELERY_TASK_ALWAYS_EAGER=True` — tasks run synchronously. WeasyPrint PDF generation degrades gracefully on Windows (logs a warning, skips PDF, certificate record still created).

---

## Paystack Flow

```
GET  /checkout/<slug>/           → show price, coupon input (HTMX validate)
POST /payments/initialize/       → create Order, call Paystack API, redirect
     → Paystack payment page
GET  /payments/verify/?ref=...   → verify with Paystack API, activate enrollment
POST /payments/webhook/          → async backup (HMAC-SHA512 validated)
```

Webhook URL must be registered in Paystack dashboard. No rate limiting on `/payments/webhook/`.

---

## HTMX Patterns

```html
<!-- Coupon validation -->
hx-post="/coupons/apply/" hx-target="#coupon-result"

<!-- Lesson complete toggle -->
hx-post="/courses/lessons/{{ lesson.id }}/complete/" hx-swap="outerHTML"

<!-- Discussion reply -->
hx-post="/courses/{{ course.slug }}/discuss/{{ thread.id }}/reply/"

<!-- Live course search -->
hx-get="/courses/" hx-trigger="keyup changed delay:400ms" hx-target="#course-grid"
```

---

## Admin

URL: `/admin-emlms-secure/` (obfuscated)  
Superuser: `admin@emlms.com` / `admin1234` (change in production)

38 models registered across 14 apps. Key admin customizations:
- `axes` — brute-force login attempts (disabled in dev via `AXES_ENABLED=False`)
- `django_celery_beat` — manage periodic tasks from admin
- `django_celery_results` — inspect task execution history

---

## Test Accounts (development only)

| Email | Password | Role |
|-------|----------|------|
| `admin@emlms.com` | `admin1234` | Superuser |
| `instructor@test.com` | `testpass123` | Instructor |
| `student@test.com` | `testpass123` | Student |

---

## Deployment

```bash
# First-time server setup (Ubuntu 24.04)
bash deploy/server_setup.sh

# Deploy updates
bash deploy/deploy.sh
```

Systemd services: `emlms.service`, `emlms.socket`, `emlms-celery.service`, `emlms-celerybeat.service`  
Nginx config: `deploy/nginx.conf` (rate limiting, static cache headers, webhook exemption)  
SSL: Certbot / Let's Encrypt

---

## Common Patterns

**Access control:**
- Enrolled students + course instructor can access lesson/discussion pages
- `EnrollmentRequiredMixin` in `apps/core/mixins.py`
- `_instructor_course(request, slug)` helper in curriculum views

**Template context:**
- `site_settings` and `notifications` available in every template via context processors
- Pass computed sets/booleans from views for sidebar state (e.g. `completed_lesson_ids`, `is_lesson_completed`) — Django templates cannot do dict lookups with dynamic keys

**Cloudinary signed URLs:**
```python
# lessons/utils.py
def get_signed_video_url(public_id, expires_in=3600):
    return cloudinary.utils.cloudinary_url(
        public_id, resource_type='video', type='authenticated',
        sign_url=True, expires_at=int(time.time()) + expires_in
    )[0]
```

**Decimal arithmetic:**  
Always use `Decimal` (not `float`) when working with prices, discounts, and course fees. `Coupon.calculate_discount()` expects a `Decimal` amount.

---

## Known Limitations / Future Work

- No analytics dashboard for instructors yet (`/courses/<slug>/analytics/` returns 404)
- WeasyPrint PDF generation requires GTK system libraries — only works on Linux/Mac in dev or production Ubuntu server
- No multi-instructor support yet (InstructorProfile exists; Course has single `instructor` FK)
- No mobile API yet (DRF installed but no endpoints defined)
