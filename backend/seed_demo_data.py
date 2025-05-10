import requests
import json
from datetime import datetime, timedelta
import random

# URL base da API
API_URL = 'https://agile-mini-api.onrender.com'

# Função para fazer requisições à API
def api_request(endpoint, method='GET', data=None):
    url = f"{API_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    print(f"Fazendo requisição {method} para {url}")
    if data:
        print(f"Dados: {json.dumps(data, indent=2)}")
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Método HTTP não suportado: {method}")
        
        response.raise_for_status()  # Lança exceção para códigos de erro HTTP
        
        if response.status_code != 204:  # No Content
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        if hasattr(e.response, 'text'):
            print(f"Resposta da API: {e.response.text}")
        raise

# Função para criar um projeto demo
def create_demo_project():
    # Data atual
    today = datetime.now()
    
    # Criar projeto demo
    project_data = {
        "name": "Projeto Demonstração",
        "description": "Um projeto de demonstração para testar as funcionalidades do Agile Mini",
        "status": "Ativo",
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": (today + timedelta(days=90)).strftime("%Y-%m-%d")
    }
    
    project = api_request("/projects", "POST", project_data)
    print(f"Projeto criado: {project}")
    
    return project

# Função para criar sprints para o projeto
def create_demo_sprints(project_id, num_sprints=3):
    sprints = []
    today = datetime.now()
    
    # Criar sprints com duração de 2 semanas cada
    for i in range(num_sprints):
        sprint_start = today + timedelta(days=i*14)
        sprint_end = sprint_start + timedelta(days=13)
        
        sprint_data = {
            "name": f"Sprint {i+1}",
            "start_date": sprint_start.strftime("%Y-%m-%d"),
            "end_date": sprint_end.strftime("%Y-%m-%d"),
            "status": "Ativo" if i == 0 else ("Planejado" if i > 0 else "Concluído"),
            "project_id": project_id
        }
        
        sprint = api_request("/sprints", "POST", sprint_data)
        print(f"Sprint criado: {sprint}")
        sprints.append(sprint)
    
    return sprints

# Função para criar tarefas para os sprints
def create_demo_tasks(project_id, sprints, num_tasks_per_sprint=5):
    tasks = []
    statuses = ["A Fazer", "Em Andamento", "Concluído"]
    priorities = ["Baixa", "Média", "Alta"]
    
    for sprint in sprints:
        for i in range(num_tasks_per_sprint):
            # Distribuir tarefas entre os status
            status_idx = random.randint(0, 2)
            status = statuses[status_idx]
            
            # Definir datas com base no status
            started_at = None
            completed_at = None
            
            if status == "Em Andamento" or status == "Concluído":
                started_at = (datetime.now() - timedelta(days=random.randint(1, 5))).isoformat()
            
            if status == "Concluído":
                completed_at = datetime.now().isoformat()
            
            task_data = {
                "title": f"Tarefa {i+1} do Sprint {sprint['name']}",
                "description": f"Esta é uma tarefa de demonstração para o sprint {sprint['name']}",
                "status": status,
                "priority": random.choice(priorities),
                "points": random.choice([1, 2, 3, 5, 8]),
                "project": str(project_id),
                "sprint_id": sprint["id"],
                "started_at": started_at,
                "completed_at": completed_at
            }
            
            task = api_request("/tasks", "POST", task_data)
            print(f"Tarefa criada: {task['title']} - Status: {task['status']}")
            tasks.append(task)
    
    return tasks

# Função principal para criar todos os dados de demonstração
def create_demo_data():
    try:
        print("Iniciando criação de dados de demonstração...")
        
        # Criar projeto demo
        project = create_demo_project()
        
        # Criar sprints para o projeto
        sprints = create_demo_sprints(project["id"])
        
        # Criar tarefas para os sprints
        tasks = create_demo_tasks(project["id"], sprints)
        
        print("\nDados de demonstração criados com sucesso!")
        print(f"Projeto: {project['name']} (ID: {project['id']})")
        print(f"Sprints criados: {len(sprints)}")
        print(f"Tarefas criadas: {len(tasks)}")
        
    except Exception as e:
        print(f"Erro ao criar dados de demonstração: {e}")

# Executar o script
if __name__ == "__main__":
    create_demo_data()
