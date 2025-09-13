# check_duplicates.py - Salve na raiz do projeto e execute
import re
import os

def check_duplicates():
    """Verifica duplicações no routes.py"""
    
    routes_file = 'app/cli/routes.py'
    
    if not os.path.exists(routes_file):
        print(f"❌ Arquivo {routes_file} não encontrado!")
        return
    
    print("🔍 Verificando duplicações em routes.py...\n")
    
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Buscar todas as definições de função com seus números de linha
    functions = {}
    decorators = {}  # Para armazenar os decorators das funções
    
    current_decorator = ""
    
    for i, line in enumerate(lines, 1):
        # Detectar decorators
        if line.strip().startswith('@cli_bp.route'):
            current_decorator = line.strip()
            continue
            
        # Detectar definições de função
        match = re.match(r'\s*def\s+(\w+)\s*\(', line)
        if match:
            func_name = match.group(1)
            
            if func_name in functions:
                functions[func_name].append((i, line.strip()))
                decorators[func_name].append(current_decorator)
            else:
                functions[func_name] = [(i, line.strip())]
                decorators[func_name] = [current_decorator]
            
            current_decorator = ""  # Reset
    
    # Encontrar duplicatas
    duplicates = {name: locations for name, locations in functions.items() if len(locations) > 1}
    
    if duplicates:
        print("🚨 FUNÇÕES DUPLICADAS ENCONTRADAS:")
        print("=" * 50)
        
        for func_name, locations in duplicates.items():
            print(f"\n📍 Função: {func_name}")
            print(f"   Aparece {len(locations)} vezes:")
            
            for j, (line_num, func_def) in enumerate(locations):
                decorator = decorators[func_name][j] if j < len(decorators[func_name]) else "Sem decorator"
                print(f"   {j+1}. Linha {line_num}: {func_def}")
                print(f"      Decorator: {decorator}")
            
            print(f"   ⚠️  REMOVER {len(locations)-1} versão(ões) duplicada(s)")
        
        print("\n" + "=" * 50)
        print("📋 INSTRUÇÕES PARA CORRIGIR:")
        print("1. Abra app/cli/routes.py no seu editor")
        print("2. Para cada função duplicada acima:")
        print("   - Vá para as linhas indicadas")
        print("   - Compare as versões")
        print("   - DELETE as versões antigas/incompletas")
        print("   - MANTENHA apenas a versão mais completa")
        print("3. Salve o arquivo")
        print("4. Execute: python run.py")
        
        # Gerar comando para busca rápida
        print("\n🔍 COMANDOS DE BUSCA (Ctrl+F no editor):")
        for func_name in duplicates.keys():
            print(f"   def {func_name}(")
    
    else:
        print("✅ Nenhuma função duplicada encontrada!")
        
    # Verificar também decorators duplicados
    print("\n" + "="*30)
    print("🔍 Verificando rotas duplicadas...")
    
    route_patterns = re.findall(r"@cli_bp\.route\(['\"]([^'\"]+)['\"].*?\)\s*@login_required\s*def\s+(\w+)", 
                               content, re.MULTILINE | re.DOTALL)
    
    route_counts = {}
    for route, func in route_patterns:
        if route in route_counts:
            route_counts[route].append(func)
        else:
            route_counts[route] = [func]
    
    duplicate_routes = {route: funcs for route, funcs in route_counts.items() if len(funcs) > 1}
    
    if duplicate_routes:
        print("\n🚨 ROTAS DUPLICADAS:")
        for route, funcs in duplicate_routes.items():
            print(f"   Rota: {route}")
            print(f"   Funções: {', '.join(funcs)}")
    else:
        print("✅ Nenhuma rota duplicada encontrada!")

if __name__ == "__main__":
    check_duplicates()