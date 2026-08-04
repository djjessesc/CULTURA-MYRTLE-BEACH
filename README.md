# Cultura Myrtle Beach

**Latino Business Directory & Community Hub for Myrtle Beach, South Carolina**

Bilingual (English / Spanish), mobile-first web app for discovering and listing Latino-owned and Latino-serving businesses on the Grand Strand.

## Tech Stack (portable, no lock-in)

- **Python 3 + Flask** — lightweight, free
- **SQLite** — single-file database, zero configuration
- **Leaflet + OpenStreetMap** — free maps, no API keys
- **Server-rendered HTML + CSS** — fast, SEO-friendly, no build step required

Works on any VPS, shared hosting with Python, or free PaaS (Render, Railway, Fly.io, PythonAnywhere, DigitalOcean, etc.). Move between hosts by copying the folder.

## Quick Start (Local)

```bash
# Install (once)
pip install flask python-slugify

# Run
cd CulturaMyrtleBeach
python app.py
```

Open http://127.0.0.1:5000

Database and 8 sample businesses are created automatically.

**Admin login:** http://127.0.0.1:5000/admin/login  
**Default password:** `cultura2026` (change it!)

### Environment variables

```bash
export SECRET_KEY="long-random-string"
export ADMIN_PASSWORD="your-strong-password"
export PORT=5000
export FLASK_DEBUG=0
```

## Features Implemented

1. Bilingual homepage (EN / ES language switcher)
2. Searchable business directory with category filters
3. List view + interactive map view (Leaflet)
4. Individual business profile pages
5. Click-to-call (`tel:`) buttons
6. WhatsApp buttons (`wa.me`)
7. Google Maps directions buttons
8. Website + social links (Facebook, Instagram, TikTok)
9. Public “Add Your Business” form (goes to pending queue)
10. Full admin panel to add / edit / approve / delete businesses (no code changes needed)
11. Responsive mobile-first design
12. SEO: unique titles, meta descriptions, clean URLs, sitemap.xml, robots.txt, Schema.org JSON-LD

## Business Data Fields

Name (EN+ES), Category, Logo, Cover, Description (EN+ES), Phone, WhatsApp, Address, Lat/Lng, Hours, Website, Facebook, Instagram, TikTok, Google Business Profile, Google Reviews, Services, Languages, Featured, Verified, Status.

## Adding Listings

- **Public:** `/add-business` → pending review
- **Admin:** `/admin` → create or edit directly, upload logos/covers, set featured/verified flags

## Database & Backup

File: `data/cultura.db`

```bash
# Backup
cp data/cultura.db data/backup-$(date +%Y%m%d).db
```

Restore by replacing the file and restarting.

## Deploy

1. Upload the whole folder.
2. `pip install flask python-slugify gunicorn`
3. `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
4. Point your domain (A/CNAME) and enable HTTPS (Let’s Encrypt).

For free PaaS: connect GitHub repo, set start command to the gunicorn line above, add env vars, optionally mount persistent disk on `data/`.

## Moving Hosts

Copy the project folder (especially `data/cultura.db` + `static/uploads/`) to the new server, install the same packages, start the app, update DNS. No vendor lock-in.

## Security

Change `ADMIN_PASSWORD` and `SECRET_KEY` before public launch.

---

¡Éxito! Built for the Myrtle Beach Latino community.
