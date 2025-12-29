from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, date
import csv
import io

app = Flask(__name__)
app.secret_key = "chave_super_secreta_altere_esta_chave"

# Conectar banco
def get_db_connection():
    conn = sqlite3.connect('clientes.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

# Criar tabelas
def criar_tabelas():
    conn = get_db_connection()
    
    # Tabela de usuários
    conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )''')
    
    # Tabela de clientes com data_cadastro
    conn.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        email TEXT,
                        telefone TEXT,
                        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    
    conn.commit()
    conn.close()
    print("✅ Tabelas criadas/verificadas")

# Criar admin inicial
def criar_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        senha_hash = generate_password_hash("admin123")
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?,?)", 
                       ("admin", senha_hash))
        conn.commit()
        print("✅ Admin criado (admin / admin123)")
    conn.close()

# Criar clientes de teste
def criar_clientes_teste():
    """Cria alguns clientes de teste se não houver nenhum"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clientes")
    count = cursor.fetchone()[0]
    
    if count == 0:
        clientes_teste = [
            ("João Silva", "joao@email.com", "(11) 99999-9999"),
            ("Maria Santos", "maria@email.com", "(21) 88888-8888"),
            ("Pedro Oliveira", "pedro@email.com", "(31) 77777-7777"),
            ("Ana Costa", "ana@email.com", "(41) 66666-6666"),
            ("Carlos Souza", "carlos@email.com", "(51) 55555-5555"),
        ]
        
        for nome, email, telefone in clientes_teste:
            cursor.execute("INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
                          (nome, email, telefone))
        
        conn.commit()
        print(f"✅ {len(clientes_teste)} clientes de teste criados")
    
    conn.close()

# Rotas
@app.route('/')
def home():
    if "user" not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    
    # Estatísticas
    total_clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
    clientes_com_email = conn.execute("SELECT COUNT(*) FROM clientes WHERE email IS NOT NULL AND email != ''").fetchone()[0]
    clientes_com_telefone = conn.execute("SELECT COUNT(*) FROM clientes WHERE telefone IS NOT NULL AND telefone != ''").fetchone()[0]
    
    # Cadastros este mês
    mes_atual = date.today().strftime('%Y-%m')
    cadastros_mes = conn.execute("""SELECT COUNT(*) FROM clientes 
                                   WHERE strftime('%Y-%m', data_cadastro) = ?""",
                                (mes_atual,)).fetchone()[0]
    
    # Busca
    search = request.args.get('search', '')
    ordenar = request.args.get('ordenar', '')
    
    query = "SELECT * FROM clientes WHERE 1=1"
    params = []
    
    if search:
        query += " AND nome LIKE ?"
        params.append(f"%{search}%")
    
    if ordenar == 'nome_asc':
        query += " ORDER BY nome ASC"
    elif ordenar == 'nome_desc':
        query += " ORDER BY nome DESC"
    else:
        query += " ORDER BY id DESC"
    
    clientes = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template("index.html", 
                         clientes=clientes,
                         total_clientes=total_clientes,
                         clientes_com_email=clientes_com_email,
                         clientes_com_telefone=clientes_com_telefone,
                         cadastros_mes=cadastros_mes)

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
            flash("Login realizado com sucesso!", "success")
            return redirect("/")
        else:
            return render_template("login.html", erro="Usuário ou senha incorretos")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("Você saiu do sistema.", "info")
    return redirect("/login")

@app.route('/cliente/add', methods=['GET','POST'])
def add():
    if "user" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        
        conn = get_db_connection()
        conn.execute("INSERT INTO clientes (nome,email,telefone) VALUES (?,?,?)", 
                     (nome,email,telefone))
        conn.commit()
        conn.close()
        
        flash("Cliente adicionado com sucesso!", "success")
        return redirect("/")
    
    return render_template("adicionar.html")

@app.route('/cliente/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    if "user" not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    
    if request.method == "POST":
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        
        conn.execute("UPDATE clientes SET nome=?, email=?, telefone=? WHERE id=?", 
                     (nome,email,telefone,id))
        conn.commit()
        conn.close()
        
        flash("Cliente atualizado com sucesso!", "success")
        return redirect("/")
    
    cliente = conn.execute("SELECT * FROM clientes WHERE id = ?", (id,)).fetchone()
    conn.close()
    
    return render_template("adicionar.html", cliente=cliente)

@app.route('/delete/<int:id>')
def delete(id):
    if "user" not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    
    # Pegar nome do cliente para mensagem
    cliente = conn.execute("SELECT nome FROM clientes WHERE id = ?", (id,)).fetchone()
    
    conn.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    if cliente:
        flash(f"Cliente '{cliente['nome']}' excluído com sucesso!", "success")
    else:
        flash("Cliente excluído com sucesso!", "success")
    
    return redirect("/")

@app.route('/export/csv')
def export_csv():
    if "user" not in session:
        return redirect("/login")
    
    conn = get_db_connection()
    clientes = conn.execute("SELECT * FROM clientes").fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Cabeçalho
    writer.writerow(['ID', 'Nome', 'Email', 'Telefone', 'Data Cadastro'])
    
    # Dados
    for cliente in clientes:
        writer.writerow([
            cliente['id'],
            cliente['nome'],
            cliente['email'] or '',
            cliente['telefone'] or '',
            cliente['data_cadastro']
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'clientes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

if __name__ == '__main__':
    criar_tabelas()
    criar_admin()
    criar_clientes_teste()
    app.run(debug=True, host='0.0.0.0', port=5000)
