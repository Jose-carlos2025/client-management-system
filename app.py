# -*- coding: utf-8 -*-
"""
Sistema de Gestão de Clientes - Versão Vercel Simplificada
"""

import os
from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_key_123")

# Configuração do banco
if 'VERCEL' in os.environ:
    DB_PATH = '/tmp/clientes.db'
else:
    DB_PATH = 'clientes.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados"""
    try:
        conn = get_db()
        
        # Tabela de usuários
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        
        # Tabela de clientes
        conn.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT,
                telefone TEXT
            )
        ''')
        
        # Criar admin se não existir
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
        if not cursor.fetchone():
            senha_hash = generate_password_hash("admin123")
            cursor.execute("INSERT INTO usuarios (username, password) VALUES ('admin', ?)", 
                          (senha_hash,))
        
        # Adicionar clientes exemplo se vazio
        cursor.execute("SELECT COUNT(*) FROM clientes")
        if cursor.fetchone()[0] == 0:
            exemplos = [
                ("João Silva", "joao@email.com", "(11) 99999-9999"),
                ("Maria Santos", "maria@email.com", "(21) 88888-8888"),
            ]
            for nome, email, telefone in exemplos:
                cursor.execute("INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
                              (nome, email, telefone))
        
        conn.commit()
        conn.close()
        print("✅ Banco inicializado")
        
    except Exception as e:
        print(f"⚠️  Erro ao inicializar banco: {e}")

# Inicializar banco
init_db()

# Rotas
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    clientes = conn.execute('SELECT * FROM clientes').fetchall()
    total = conn.execute('SELECT COUNT(*) FROM clientes').fetchone()[0]
    conn.close()
    
    return render_template('index.html', 
                         clientes=clientes,
                         total_clientes=total,
                         clientes_com_email=total,  # Simplificado
                         clientes_com_telefone=total,  # Simplificado
                         cadastros_mes=total)  # Simplificado

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', 
                           (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            flash('Login realizado!', 'success')
            return redirect('/')
        else:
            return render_template('login.html', erro='Credenciais inválidas')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Você saiu do sistema.', 'info')
    return redirect('/login')

@app.route('/cliente/add', methods=['GET', 'POST'])
def add():
    if 'user' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form.get('email', '')
        telefone = request.form.get('telefone', '')
        
        conn = get_db()
        conn.execute('INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)',
                    (nome, email, telefone))
        conn.commit()
        conn.close()
        
        flash('Cliente adicionado!', 'success')
        return redirect('/')
    
    return render_template('adicionar.html')

@app.route('/cliente/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form.get('email', '')
        telefone = request.form.get('telefone', '')
        
        conn.execute('UPDATE clientes SET nome=?, email=?, telefone=? WHERE id=?',
                    (nome, email, telefone, id))
        conn.commit()
        conn.close()
        
        flash('Cliente atualizado!', 'success')
        return redirect('/')
    
    cliente = conn.execute('SELECT * FROM clientes WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    return render_template('adicionar.html', cliente=cliente)

@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect('/login')
    
    conn = get_db()
    conn.execute('DELETE FROM clientes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Cliente excluído!', 'success')
    return redirect('/')

# Rota de saúde para Vercel
@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True)
else:
    # Para produção no Vercel
    print("🚀 Aplicação iniciada no Vercel")
