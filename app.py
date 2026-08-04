#!/usr/bin/env python3
import os, sys, sqlite3, json
from datetime import datetime
from functools import wraps
sys.path.insert(0, "/root/.local/lib/python3.12/site-packages")
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify, abort
from werkzeug.utils import secure_filename
from slugify import slugify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cultura-mb-dev-secret-change-me")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
# Allow overriding data directory for persistent disks on hosts like Render
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE = os.path.join(DATA_DIR, "cultura.db")
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "cultura2026")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, name_es TEXT, slug TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL, logo TEXT, cover TEXT, description TEXT, description_es TEXT,
        phone TEXT, whatsapp TEXT, address TEXT, lat REAL, lng REAL, hours TEXT, website TEXT,
        facebook TEXT, instagram TEXT, tiktok TEXT, google_profile TEXT, google_reviews TEXT,
        services TEXT, languages TEXT DEFAULT 'Spanish, English', featured INTEGER DEFAULT 0,
        verified INTEGER DEFAULT 0, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name_en TEXT UNIQUE NOT NULL, name_es TEXT NOT NULL, icon TEXT, sort_order INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TEXT
    );
    """)
    if db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        cats = [("Restaurants & Food","Restaurantes y Comida","🍽️",1),("Grocery & Markets","Mercados y Abarrotes","🛒",2),("Beauty & Salons","Belleza y Salones","💅",3),("Auto Services","Servicios de Auto","🚗",4),("Professional Services","Servicios Profesionales","💼",5),("Entertainment & Nightlife","Entretenimiento y Vida Nocturna","🎉",6),("Health & Wellness","Salud y Bienestar","💪",7),("Retail & Shopping","Tiendas y Compras","🛍️",8),("Home & Construction","Hogar y Construcción","🏠",9),("Other","Otros","📌",10)]
        db.executemany("INSERT INTO categories (name_en,name_es,icon,sort_order) VALUES (?,?,?,?)", cats)
    if db.execute("SELECT COUNT(*) FROM businesses").fetchone()[0] == 0:
        now = datetime.utcnow().isoformat()
        samples = [
            ("El Trébol Discoteque","El Trébol Discoteque","el-trebol-discoteque","Entertainment & Nightlife","Premier Latino nightclub and event venue in Myrtle Beach.","El principal club nocturno latino en Myrtle Beach.","843-555-0101","18435550101","1200 S Kings Hwy, Myrtle Beach, SC 29577",33.6891,-78.8867,"Thu-Sun 9PM-3AM","","https://facebook.com/eltrebolmb","https://instagram.com/eltrebolmb","","","","Live Music, DJ Nights","Spanish, English",1,1),
            ("Taquería El Sabor Mexicano","Taquería El Sabor Mexicano","taqueria-el-sabor-mexicano","Restaurants & Food","Authentic Mexican street tacos and family recipes.","Auténticos tacos mexicanos y recetas familiares.","843-555-0202","18435550202","3501 N Kings Hwy, Myrtle Beach, SC 29577",33.7125,-78.8750,"Mon-Sun 11AM-10PM","","https://facebook.com/elsabormexicano","https://instagram.com/elsabormb","","","","Tacos, Burritos, Catering","Spanish, English",1,1),
            ("Mercado Latino La Esperanza","Mercado Latino La Esperanza","mercado-latino-la-esperanza","Grocery & Markets","Latino market for produce, meats, spices and more.","Mercado latino de productos, carnes y especias.","843-555-0303","18435550303","2100 Oak St, Myrtle Beach, SC 29577",33.6950,-78.8900,"Mon-Sat 8AM-8PM","","https://facebook.com/mercadoesperanza","","","","","Groceries, Butcher","Spanish, English",1,1),
            ("Salón de Belleza Rosita","Salón de Belleza Rosita","salon-de-belleza-rosita","Beauty & Salons","Full-service beauty salon for Latina hair care.","Salón completo de belleza para cuidado del cabello.","843-555-0404","18435550404","4500 Socastee Blvd, Myrtle Beach, SC 29588",33.6800,-79.0000,"Tue-Sat 9AM-7PM","","https://facebook.com/salonrosita","https://instagram.com/salonrosita_mb","","","","Haircuts, Color, Nails","Spanish, English",0,1),
            ("Auto Repair Hermanos García","Reparación de Autos Hermanos García","auto-repair-hermanos-garcia","Auto Services","Honest affordable auto repair.","Reparación de autos honestos y asequibles.","843-555-0505","18435550505","1800 Hwy 501, Myrtle Beach, SC 29577",33.7000,-78.9200,"Mon-Fri 8AM-6PM","","https://facebook.com/hermanosgarciaauto","","","","","Oil Change, Brakes","Spanish, English",0,1),
            ("Abogados del Pueblo","Abogados del Pueblo","abogados-del-pueblo","Professional Services","Immigration and family law. Bilingual attorneys.","Derecho de inmigración y familia. Abogados bilingües.","843-555-0606","18435550606","1301 38th Ave N, Myrtle Beach, SC 29577",33.7200,-78.8700,"Mon-Fri 9AM-5PM","https://example.com/abogados","https://facebook.com/abogadosdelpueblo","","","","","Immigration, Family Law","Spanish, English",1,1),
            ("Gym Cultura Fit","Gym Cultura Fit","gym-cultura-fit","Health & Wellness","Group training with bilingual coaches.","Entrenamiento en grupo con coaches bilingües.","843-555-0707","18435550707","2200 Carolina Forest Blvd, Myrtle Beach, SC 29579",33.7600,-79.0100,"Mon-Fri 5AM-9PM","https://example.com/culturafit","https://facebook.com/culturafitmb","https://instagram.com/culturafit","","","","Group Classes, Personal Training","Spanish, English",0,0),
            ("Panadería Dulce Hogar","Panadería Dulce Hogar","panaderia-dulce-hogar","Restaurants & Food","Fresh Mexican baked goods daily.","Panadería mexicana fresca diaria.","843-555-0808","18435550808","900 21st Ave N, Myrtle Beach, SC 29577",33.7050,-78.8650,"Tue-Sun 6AM-6PM","","https://facebook.com/dulcehogarmb","https://instagram.com/dulcehogar","","","","Bread, Pastries, Cakes","Spanish, English",0,1),
        ]
        for s in samples:
            db.execute("""INSERT INTO businesses (name,name_es,slug,category,description,description_es,phone,whatsapp,address,lat,lng,hours,website,facebook,instagram,tiktok,google_profile,google_reviews,services,languages,featured,verified,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'active',?,?)""", s + (now, now))
    db.commit()

def get_lang():
    lang = request.args.get("lang") or session.get("lang") or "en"
    return lang if lang in ("en","es") else "en"

def t(en, es):
    return es if get_lang() == "es" else en

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def home():
    lang = get_lang()
    db = get_db()
    featured = db.execute("SELECT * FROM businesses WHERE status='active' AND featured=1 ORDER BY name LIMIT 6").fetchall()
    categories = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    total = db.execute("SELECT COUNT(*) FROM businesses WHERE status='active'").fetchone()[0]
    return render_template("home.html", lang=lang, featured=featured, categories=categories, total=total, t=t)

@app.route("/set-lang/<lang>")
def set_language(lang):
    if lang in ("en","es"): session["lang"] = lang
    return redirect(request.args.get("next") or url_for("home"))

@app.route("/directory")
def directory():
    lang = get_lang()
    db = get_db()
    q = request.args.get("q","").strip()
    category = request.args.get("category","").strip()
    view = request.args.get("view","list")
    sql = "SELECT * FROM businesses WHERE status='active'"
    params = []
    if q:
        sql += " AND (name LIKE ? OR name_es LIKE ? OR description LIKE ? OR services LIKE ?)"
        like = f"%{q}%"
        params.extend([like]*4)
    if category:
        sql += " AND category=?"
        params.append(category)
    sql += " ORDER BY featured DESC, name ASC"
    businesses = db.execute(sql, params).fetchall()
    categories = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    return render_template("directory.html", lang=lang, businesses=businesses, categories=categories, q=q, category=category, view=view, t=t)

@app.route("/business/<slug>")
def business_profile(slug):
    lang = get_lang()
    db = get_db()
    biz = db.execute("SELECT * FROM businesses WHERE slug=? AND status='active'", (slug,)).fetchone()
    if not biz: abort(404)
    return render_template("business.html", lang=lang, biz=biz, t=t)

@app.route("/add-business", methods=["GET","POST"])
def add_business():
    lang = get_lang()
    db = get_db()
    categories = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    if request.method == "POST":
        data = {k: request.form.get(k,"").strip() for k in ["name","name_es","category","description","description_es","phone","whatsapp","address","website","facebook","instagram","tiktok","services","languages","hours"]}
        data["submitted_by"] = request.form.get("email","").strip()
        if not data["name"] or not data["category"] or not data["phone"]:
            flash(t("Please fill required fields.","Por favor complete los campos requeridos."), "error")
            return render_template("add_business.html", lang=lang, categories=categories, t=t, form=data)
        db.execute("INSERT INTO submissions (data,status,created_at) VALUES (?,'pending',?)", (json.dumps(data), datetime.utcnow().isoformat()))
        db.commit()
        flash(t("Thank you! Pending review.","¡Gracias! Pendiente de revisión."), "success")
        return redirect(url_for("home"))
    return render_template("add_business.html", lang=lang, categories=categories, t=t, form={})

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect password", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    businesses = db.execute("SELECT id,name,category,status,featured,verified FROM businesses ORDER BY name").fetchall()
    pending = db.execute("SELECT id,data,created_at FROM submissions WHERE status='pending'").fetchall()
    return render_template("admin_dashboard.html", businesses=businesses, pending=pending, pending_count=len(pending))

@app.route("/admin/business/new", methods=["GET","POST"])
@admin_required
def admin_business_new():
    db = get_db()
    categories = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    if request.method == "POST":
        return _save_business(None)
    return render_template("admin_business_form.html", biz=None, categories=categories)

@app.route("/admin/business/<int:biz_id>/edit", methods=["GET","POST"])
@admin_required
def admin_business_edit(biz_id):
    db = get_db()
    biz = db.execute("SELECT * FROM businesses WHERE id=?", (biz_id,)).fetchone()
    if not biz: abort(404)
    categories = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    if request.method == "POST":
        return _save_business(biz_id)
    return render_template("admin_business_form.html", biz=biz, categories=categories)

def _save_business(biz_id):
    db = get_db()
    name = request.form.get("name","").strip()
    if not name:
        flash("Name required", "error")
        return redirect(request.url)
    slug = request.form.get("slug","").strip() or slugify(name)
    now = datetime.utcnow().isoformat()
    fields = dict(
        name=name, name_es=request.form.get("name_es","").strip(), slug=slug,
        category=request.form.get("category","").strip(),
        description=request.form.get("description","").strip(), description_es=request.form.get("description_es","").strip(),
        phone=request.form.get("phone","").strip(), whatsapp=request.form.get("whatsapp","").strip().replace("+","").replace(" ","").replace("-",""),
        address=request.form.get("address","").strip(),
        lat=float(request.form.get("lat") or 0) or None, lng=float(request.form.get("lng") or 0) or None,
        hours=request.form.get("hours","").strip(), website=request.form.get("website","").strip(),
        facebook=request.form.get("facebook","").strip(), instagram=request.form.get("instagram","").strip(),
        tiktok=request.form.get("tiktok","").strip(), google_profile=request.form.get("google_profile","").strip(),
        google_reviews=request.form.get("google_reviews","").strip(), services=request.form.get("services","").strip(),
        languages=request.form.get("languages","Spanish, English").strip(),
        featured=1 if request.form.get("featured") else 0, verified=1 if request.form.get("verified") else 0,
        status=request.form.get("status","active"), updated_at=now
    )
    if biz_id:
        sets = ", ".join(f"{k}=?" for k in fields)
        db.execute(f"UPDATE businesses SET {sets} WHERE id=?", (*fields.values(), biz_id))
        flash("Updated", "success")
    else:
        fields["created_at"] = now
        cols = ", ".join(fields.keys())
        ph = ", ".join("?" for _ in fields)
        db.execute(f"INSERT INTO businesses ({cols}) VALUES ({ph})", tuple(fields.values()))
        flash("Created", "success")
    db.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/business/<int:biz_id>/delete", methods=["POST"])
@admin_required
def admin_business_delete(biz_id):
    get_db().execute("DELETE FROM businesses WHERE id=?", (biz_id,))
    get_db().commit()
    flash("Deleted", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/submission/<int:sub_id>/approve", methods=["POST"])
@admin_required
def admin_approve_submission(sub_id):
    db = get_db()
    row = db.execute("SELECT data FROM submissions WHERE id=?", (sub_id,)).fetchone()
    if not row: abort(404)
    data = json.loads(row["data"])
    now = datetime.utcnow().isoformat()
    slug = slugify(data["name"])
    while db.execute("SELECT id FROM businesses WHERE slug=?", (slug,)).fetchone():
        slug += "-1"
    db.execute("""INSERT INTO businesses (name,name_es,slug,category,description,description_es,phone,whatsapp,address,website,facebook,instagram,tiktok,services,languages,hours,status,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'active',?,?)""",
        (data.get("name"),data.get("name_es"),slug,data.get("category"),data.get("description"),data.get("description_es"),
         data.get("phone"),data.get("whatsapp"),data.get("address"),data.get("website"),data.get("facebook"),
         data.get("instagram"),data.get("tiktok"),data.get("services"),data.get("languages"),data.get("hours"),now,now))
    db.execute("UPDATE submissions SET status='approved' WHERE id=?", (sub_id,))
    db.commit()
    flash("Approved", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/submission/<int:sub_id>/reject", methods=["POST"])
@admin_required
def admin_reject_submission(sub_id):
    get_db().execute("UPDATE submissions SET status='rejected' WHERE id=?", (sub_id,))
    get_db().commit()
    flash("Rejected", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/api/businesses")
def api_businesses():
    db = get_db()
    q = request.args.get("q","").strip()
    category = request.args.get("category","").strip()
    sql = "SELECT id,name,name_es,slug,category,lat,lng,address,phone,featured FROM businesses WHERE status='active' AND lat IS NOT NULL"
    params = []
    if q:
        sql += " AND (name LIKE ? OR name_es LIKE ?)"
        params.extend([f"%{q}%"]*2)
    if category:
        sql += " AND category=?"
        params.append(category)
    return jsonify([dict(r) for r in db.execute(sql, params).fetchall()])

@app.route("/robots.txt")
def robots():
    return "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n", 200, {"Content-Type":"text/plain"}

@app.route("/sitemap.xml")
def sitemap():
    db = get_db()
    businesses = db.execute("SELECT slug,updated_at FROM businesses WHERE status='active'").fetchall()
    base = request.url_root.rstrip("/")
    urls = [f"<url><loc>{base}/</loc><priority>1.0</priority></url>", f"<url><loc>{base}/directory</loc><priority>0.9</priority></url>"]
    for b in businesses:
        urls.append(f"<url><loc>{base}/business/{b['slug']}</loc><lastmod>{(b['updated_at'] or '')[:10]}</lastmod></url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(urls) + "</urlset>"
    return xml, 200, {"Content-Type":"application/xml"}

@app.context_processor
def inject_globals():
    return {"current_lang": get_lang(), "t": t, "now_year": datetime.utcnow().year}

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=os.environ.get("FLASK_DEBUG","1")=="1")
