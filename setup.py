import os
import sys
import subprocess

def setup_project():
    print("🚀 Configurando Sistema de Clientes...")
    
    # Instalar dependências
    print("📦 Instalando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Criar estrutura de diretórios
    print("📁 Criando estrutura de diretórios...")
    dirs = [
        'static/css',
        'static/js',
        'static/img',
        'templates/admin',
        'templates/errors'
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    print("✅ Configuração concluída!")
    print("\nPara iniciar o sistema:")
    print("1. Execute: python app.py")
    print("2. Acesse: http://localhost:5000")
    print("3. Login padrão: admin / admin123")

if __name__ == "__main__":
    setup_project()