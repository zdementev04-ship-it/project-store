from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB = ROOT / "store.db"
SECRET = os.getenv("STORE_SECRET", "change-this-secret-before-deployment")

app = FastAPI(title="Sever Store API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=150)
    password: str = Field(min_length=6, max_length=128)
class LoginIn(BaseModel):
    email: str = Field(min_length=5, max_length=150)
    password: str
class CartIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=99)
class QuantityIn(BaseModel):
    quantity: int = Field(ge=1, le=99)
class OrderIn(BaseModel):
    phone: str = Field(min_length=5, max_length=30)
    address: str = Field(min_length=5, max_length=250)

def conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; c.execute("PRAGMA foreign_keys = ON"); return c
def hash_password(password: str) -> str:
    salt = os.urandom(16).hex(); digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex(); return f"{salt}${digest}"
def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$", 1); check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex(); return hmac.compare_digest(check, digest)
def token_for(user: sqlite3.Row) -> str:
    payload = {"sub": user["id"], "role": user["role"], "exp": int((datetime.now(timezone.utc)+timedelta(hours=12)).timestamp())}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("="); sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest(); return f"{body}.{sig}"
def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        body, signature = authorization[7:].split("."); expected=hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected): raise ValueError()
        data=json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body)%4)))
        if data["exp"] < int(datetime.now(timezone.utc).timestamp()): raise ValueError()
    except Exception: raise HTTPException(status_code=401, detail="Недействительный токен")
    c=conn(); user=c.execute("SELECT id,name,email,role FROM users WHERE id=?",(data["sub"],)).fetchone(); c.close()
    if not user: raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user
def require_admin(user=Depends(current_user)):
    if user["role"] != "admin": raise HTTPException(status_code=403, detail="Доступ только для администратора")
    return user
def product_dict(row): return dict(row)

def init_db():
    c=conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user');
    CREATE TABLE IF NOT EXISTS categories(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, price REAL NOT NULL CHECK(price>=0), image TEXT NOT NULL, stock INTEGER NOT NULL DEFAULT 0, featured INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(category_id) REFERENCES categories(id));
    CREATE TABLE IF NOT EXISTS cart_items(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, product_id INTEGER NOT NULL, quantity INTEGER NOT NULL, UNIQUE(user_id,product_id), FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(product_id) REFERENCES products(id));
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, phone TEXT NOT NULL, address TEXT NOT NULL, total REAL NOT NULL, status TEXT NOT NULL DEFAULT 'Новый', created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id));
    CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL, product_id INTEGER NOT NULL, title TEXT NOT NULL, price REAL NOT NULL, quantity INTEGER NOT NULL, FOREIGN KEY(order_id) REFERENCES orders(id));
    ''')
    if not c.execute("SELECT 1 FROM categories LIMIT 1").fetchone():
        c.executemany("INSERT INTO categories(name) VALUES(?)", [("Для дома",),("Аксессуары",),("Техника",)])
        products=[(1,"Лампа Halo","Настольная лампа с мягким рассеянным светом.",3490,"https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=80",8,1),(1,"Органайзер Grid","Строгий порядок для рабочего пространства.",1890,"https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=900&q=80",14,1),(2,"Ремень Canvas","Лёгкий ремень из прочного текстиля.",2190,"https://images.unsplash.com/photo-1624222247344-550fb60583dc?auto=format&fit=crop&w=900&q=80",20,0),(3,"Колонка Orbit","Компактный звук для дома и поездок.",5490,"https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=900&q=80",7,1),(1,"Подставка Arc","Алюминиевая подставка для ноутбука.",2790,"https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=900&q=80",11,0),(2,"Сумка Field","Городская сумка на каждый день.",4290,"https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80",9,0)]
        c.executemany("INSERT INTO products(category_id,name,description,price,image,stock,featured) VALUES(?,?,?,?,?,?,?)",products)
        c.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",("Администратор","admin@sever.local",hash_password("admin123"),"admin"))
    c.commit(); c.close()
init_db()

@app.get('/health')
def health(): return {"status":"ok"}
@app.get('/categories')
def categories():
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM categories")]; c.close(); return rows
@app.get('/products')
def products(search: str="", category: Optional[int]=None, featured: Optional[bool]=None):
    q="SELECT p.*, c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE 1=1"; args=[]
    if search: q+=" AND lower(p.name || ' ' || p.description) LIKE ?"; args.append(f"%{search.lower()}%")
    if category: q+=" AND p.category_id=?"; args.append(category)
    if featured is not None: q+=" AND p.featured=?"; args.append(int(featured))
    q+=" ORDER BY p.featured DESC,p.id DESC"; c=conn(); rows=[product_dict(x) for x in c.execute(q,args)]; c.close(); return rows
@app.get('/products/{product_id}')
def product(product_id:int):
    c=conn(); row=c.execute("SELECT p.*,c.name category FROM products p JOIN categories c ON c.id=p.category_id WHERE p.id=?",(product_id,)).fetchone(); c.close()
    if not row: raise HTTPException(404,"Товар не найден")
    return product_dict(row)
@app.post('/auth/register', status_code=201)
def register(data:RegisterIn):
    c=conn()
    try: c.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",(data.name,data.email.lower(),hash_password(data.password))); c.commit()
    except sqlite3.IntegrityError: raise HTTPException(409,"Пользователь с таким email уже существует")
    user=c.execute("SELECT id,name,email,role FROM users WHERE email=?",(data.email.lower(),)).fetchone(); c.close(); return {"token":token_for(user),"user":dict(user)}
@app.post('/auth/login')
def login(data:LoginIn):
    c=conn(); user=c.execute("SELECT * FROM users WHERE email=?",(data.email.lower(),)).fetchone(); c.close()
    if not user or not verify_password(data.password,user['password_hash']): raise HTTPException(401,"Неверный email или пароль")
    return {"token":token_for(user),"user":{"id":user['id'],"name":user['name'],"email":user['email'],"role":user['role']}}
@app.get('/me')
def me(user=Depends(current_user)): return dict(user)
@app.get('/cart')
def get_cart(user=Depends(current_user)):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT ci.id item_id,ci.quantity,p.* FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.user_id=?",(user['id'],))]; c.close(); return {"items":rows,"total":round(sum(x['price']*x['quantity'] for x in rows),2)}
@app.post('/cart/items',status_code=201)
def add_cart(data:CartIn,user=Depends(current_user)):
    c=conn();
    if not c.execute("SELECT 1 FROM products WHERE id=?",(data.product_id,)).fetchone(): c.close(); raise HTTPException(404,"Товар не найден")
    c.execute("INSERT INTO cart_items(user_id,product_id,quantity) VALUES(?,?,?) ON CONFLICT(user_id,product_id) DO UPDATE SET quantity=quantity+excluded.quantity",(user['id'],data.product_id,data.quantity)); c.commit(); c.close(); return {"message":"Товар добавлен"}
@app.put('/cart/items/{product_id}')
def update_cart(product_id:int,data:QuantityIn,user=Depends(current_user)):
    c=conn(); cur=c.execute("UPDATE cart_items SET quantity=? WHERE user_id=? AND product_id=?",(data.quantity,user['id'],product_id)); c.commit(); c.close()
    if not cur.rowcount: raise HTTPException(404,"Позиция не найдена")
    return {"message":"Количество обновлено"}
@app.delete('/cart/items/{product_id}')
def delete_cart(product_id:int,user=Depends(current_user)):
    c=conn(); c.execute("DELETE FROM cart_items WHERE user_id=? AND product_id=?",(user['id'],product_id)); c.commit(); c.close(); return {"message":"Товар удалён"}
@app.post('/orders',status_code=201)
def create_order(data:OrderIn,user=Depends(current_user)):
    c=conn(); items=[dict(x) for x in c.execute("SELECT ci.quantity,p.* FROM cart_items ci JOIN products p ON p.id=ci.product_id WHERE ci.user_id=?",(user['id'],))]
    if not items: c.close(); raise HTTPException(400,"Корзина пуста")
    total=round(sum(i['price']*i['quantity'] for i in items),2); cur=c.execute("INSERT INTO orders(user_id,phone,address,total,created_at) VALUES(?,?,?,?,?)",(user['id'],data.phone,data.address,total,datetime.now().isoformat()))
    for i in items: c.execute("INSERT INTO order_items(order_id,product_id,title,price,quantity) VALUES(?,?,?,?,?)",(cur.lastrowid,i['id'],i['name'],i['price'],i['quantity']))
    c.execute("DELETE FROM cart_items WHERE user_id=?",(user['id'],)); c.commit(); order_id=cur.lastrowid; c.close(); return {"id":order_id,"total":total,"status":"Новый"}
@app.get('/orders')
def orders(user=Depends(current_user)):
    c=conn(); rows=[dict(x) for x in c.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",(user['id'],))]; c.close(); return rows


FRONTEND_DIST = ROOT.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
