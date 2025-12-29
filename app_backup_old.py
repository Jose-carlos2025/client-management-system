from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta"  # Para sess√µes de login

# Conectar banco
def get_db_connection():
    conn = sqlite3.connect('clientes.db')
    conn.row_factory = sqlite3.Row
    return conn

# Criar tabelas
conn = get_db_connection()
conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
conn.execute('''CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT,
                    telefone TEXT
                )''')
conn.commit()
conn.close()

# Criar usu√°rio admin inicial (uma vez)
def criar_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        senha_hash = generate_password_hash("admin123")
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?,?)", ("admin", senha_hash))
        conn.commit()
    conn.close()

criar_admin()

# Rotas
@app.route('/')
def home():
    if "user" not in session:
        return redirect("/login")
    conn = get_db_connection()
    clientes = conn.execute("SELECT * FROM clientes").fetchall()
    conn.close()
    return render_template("index.html", clientes=clientes)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            return redirect("/")
        else:
            return render_template("login.html", erro="Usu√°rio ou senha incorretos")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route('/add', methods=['GET','POST'])
def add():
    if "user" not in session:
        return redirect("/login")
    if request.method == "POST":
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        conn = get_db_connection()
        conn.execute("INSERT INTO clientes (nome,email,telefone) VALUES (?,?,?)", (nome,email,telefone))
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("adicionar.html")

@app.route('/delete/<int:id>')
def delete(id):
    if "user" not in session:
        return redirect("/login")
    conn = get_db_connection()
    conn.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    if "user" not in session:
        return redirect("/login")
    conn = get_db_connection()
    cliente = conn.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
    if request.method == "POST":
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        conn.execute("UPDATE clientes SET nome=?, email=?, telefone=? WHERE id=?", (nome,email,telefone,id))
        conn.commit()
        conn.close()
        return redirect("/")
    conn.close()
    return render_template("adicionar.html", cliente=cliente)

if __name__ == '__main__':
    app.run(debug=True)


# Criar clientes de teste
def criar_clientes_teste():
    """Cria alguns clientes de teste se n„o houver nenhum"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes")
    count = cursor.fetchone()[0]
    
    if count == 0:
        clientes_teste = [
            ("Jo„o Silva", "joao@email.com", "(11) 99999-9999"),
            ("Maria Santos", "maria@email.com", "(21) 88888-8888"),
            ("Pedro Oliveira", "pedro@email.com", "(31) 77777-7777"),
            ("Ana Costa", "ana@email.com", "(41) 66666-6666"),
            ("Carlos Souza", "carlos@email.com", "(51) 55555-5555"),
        ]
        
        for nome, email, telefone in clientes_teste:
            cursor.execute("INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
                          (nome, email, telefone))
        
        conn.commit()
        print(f"? {len(clientes_teste)} clientes de teste criados")
    
    conn.close()
