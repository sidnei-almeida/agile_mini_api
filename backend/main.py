import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
from typing import List, Optional

# Instu00e2ncia do FastAPI
app = FastAPI(title="API Agile Mini")

# Configurau00e7u00e3o CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configurau00e7u00e3o do banco de dados (PostgreSQL no Render, SQLite local)
# Verifica se estamos no Render (usando a variável de ambiente RENDER)
if "RENDER" in os.environ:
    # Usar PostgreSQL no Render
    db_url = os.environ.get("DATABASE_URL", "")
    # O Render fornece URLs do tipo postgres://, mas o SQLAlchemy 2.0+ requer postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URL = db_url
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
else:
    # Usar SQLite localmente - com caminho absoluto ou relativo
    # Verificar se o banco existe na pasta atual, se não, usar na pasta pai
    if os.path.exists('./agile_mini.db'):
        SQLALCHEMY_DATABASE_URL = "sqlite:///./agile_mini.db"
    else:
        SQLALCHEMY_DATABASE_URL = "sqlite:///../agile_mini.db"
        
    print(f"Usando banco de dados: {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo SQLAlchemy
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    status = Column(String, default="Ativo")  # Ativo, Concluído, Pausado
    start_date = Column(DateTime, nullable=True)  # Data de início do projeto
    end_date = Column(DateTime, nullable=True)  # Data de término prevista do projeto
    created_at = Column(DateTime, default=datetime.utcnow)
    sprints = relationship("Sprint", back_populates="project_rel")

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String, default="Ativo")  # Ativo, Concluído, Planejado
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    tasks = relationship("Task", back_populates="sprint_rel")
    project_rel = relationship("Project", back_populates="sprints")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, index=True)  # To Do, Doing, Done
    project = Column(String, nullable=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=True)
    points = Column(Integer, nullable=True)  # Story points
    priority = Column(String, index=True, default="Média")  # Baixa, Média, Alta
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    sprint_rel = relationship("Sprint", back_populates="tasks")

# Modelos Pydantic
class ProjectBase(BaseModel):
    name: str
    description: str = None
    status: str = "Ativo"
    start_date: datetime = None
    end_date: datetime = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime = None
    class Config:
        orm_mode = True  # Para compatibilidade com versões anteriores
        from_attributes = True  # Para Pydantic v2

class SprintBase(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime
    status: str = "Ativo"
    project_id: int = None

class SprintCreate(SprintBase):
    pass

class SprintResponse(SprintBase):
    id: int
    status_calculado: str = None
    class Config:
        orm_mode = True  # Para compatibilidade com versões anteriores
        from_attributes = True  # Para Pydantic v2

class TaskCreate(BaseModel):
    title: str
    description: str = None
    status: str = "To Do"
    project: str = None
    sprint_id: int = None
    points: int = None
    priority: str = "Média"
    started_at: datetime = None
    completed_at: datetime = None

    @validator("points")
    def points_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Points devem ser positivos")
        return v

    @validator("status")
    def status_must_be_valid(cls, v):
        allowed = ["To Do", "Doing", "Done"]
        if v not in allowed:
            raise ValueError(f"Status inválido. Use um de: {allowed}")
        return v

    @validator("priority")
    def priority_must_be_valid(cls, v):
        allowed = ["Baixa", "Média", "Alta"]
        if v not in allowed:
            raise ValueError(f"Prioridade inválida. Use um de: {allowed}")
        return v

class TaskUpdate(BaseModel):
    title: str = None
    description: str = None
    status: str = None
    project: str = None
    sprint_id: int = None
    points: int = None
    priority: str = None
    started_at: datetime = None
    completed_at: datetime = None

    @validator("points")
    def points_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("Points devem ser positivos")
        return v

    @validator("status")
    def status_must_be_valid(cls, v):
        if v is None:
            return v
        allowed = ["To Do", "Doing", "Done"]
        if v not in allowed:
            raise ValueError(f"Status inválido. Use um de: {allowed}")
        return v

    @validator("priority")
    def priority_must_be_valid(cls, v):
        if v is None:
            return v
        allowed = ["Baixa", "Média", "Alta"]
        if v not in allowed:
            raise ValueError(f"Prioridade inválida. Use um de: {allowed}")
        return v

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str = None
    status: str
    project: str = None
    sprint_id: int = None
    points: int = None
    priority: str = "Média"
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    atrasada: bool = False

    class Config:
        orm_mode = True  # Para compatibilidade com versões anteriores
        from_attributes = True  # Para Pydantic v2

# Criar as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    # Obter porta do ambiente do Render ou usar 8000 localmente
    port = int(os.environ.get("PORT", 8000))
    # Se estiver no Render, use 0.0.0.0 para vincular a todas as interfaces
    host = "0.0.0.0" if "RENDER" in os.environ else "127.0.0.1"
    # Ajusta o caminho de importação com base no ambiente
    app_path = "main:app" if "RENDER" in os.environ else "backend.main:app"
    uvicorn.run(app_path, host=host, port=port, reload=True)

# Dependência para obter sessão do banco
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints Sprint
from fastapi import Query, Body

@app.get("/sprints", response_model=List[SprintResponse])
def list_sprints(db: Session = Depends(get_db)):
    sprints = db.query(Sprint).all()
    now = datetime.utcnow()
    sprint_responses = []
    for s in sprints:
        if now < s.start_date:
            status_calc = "Planejado"
        elif s.start_date <= now <= s.end_date:
            status_calc = "Ativo"
        else:
            status_calc = "Concluído"
        sprint_responses.append(SprintResponse(
            id=s.id,
            name=s.name,
            start_date=s.start_date,
            end_date=s.end_date,
            status=s.status,
            status_calculado=status_calc
        ))
    return sprint_responses

@app.post("/sprints", response_model=SprintResponse)
def create_sprint(sprint: SprintCreate, db: Session = Depends(get_db)):
    # Verificar se o projeto existe, se um project_id foi fornecido
    if sprint.project_id:
        # Buscar o projeto para verificar as datas
        project = db.query(Project).filter(Project.id == sprint.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
            
        # Verificar se as datas do sprint estão dentro do período do projeto
        if project.start_date and sprint.start_date < project.start_date:
            raise HTTPException(status_code=400, detail="A data de início do sprint não pode ser anterior à data de início do projeto")
            
        if project.end_date and sprint.end_date > project.end_date:
            raise HTTPException(status_code=400, detail="A data de término do sprint não pode ser posterior à data de término do projeto")
    
    db_sprint = Sprint(**sprint.dict())
    db.add(db_sprint)
    db.commit()
    db.refresh(db_sprint)
    # Calcula status ao retornar
    now = datetime.utcnow()
    if now < db_sprint.start_date:
        status_calc = "Planejado"
    elif db_sprint.start_date <= now <= db_sprint.end_date:
        status_calc = "Ativo"
    else:
        status_calc = "Concluído"
    return SprintResponse(
        id=db_sprint.id,
        name=db_sprint.name,
        start_date=db_sprint.start_date,
        end_date=db_sprint.end_date,
        status=db_sprint.status,
        status_calculado=status_calc
    )

@app.get("/sprints/{sprint_id}", response_model=SprintResponse)
def get_sprint(sprint_id: int, db: Session = Depends(get_db)):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    now = datetime.utcnow()
    if now < sprint.start_date:
        status_calc = "Planejado"
    elif sprint.start_date <= now <= sprint.end_date:
        status_calc = "Ativo"
    else:
        status_calc = "Concluído"
    return SprintResponse(
        id=sprint.id,
        name=sprint.name,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        status=sprint.status,
        status_calculado=status_calc
    )

# Endpoint para listar todos os projetos únicos
@app.get("/projects", response_model=List[str])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Task.project).distinct().all()
    return [p[0] for p in projects if p[0]]

# Endpoints agregados para gráficos
from collections import defaultdict
from fastapi.encoders import jsonable_encoder

@app.get("/burndown/{sprint_id}")
def burndown_chart(sprint_id: int, db: Session = Depends(get_db)):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    tasks = db.query(Task).filter(Task.sprint_id == sprint_id).all()
    # Gera lista de datas do sprint
    days = []
    current = sprint.start_date.date()
    while current <= sprint.end_date.date():
        days.append(current)
        current = current.fromordinal(current.toordinal() + 1)
    # Para cada dia, calcula tarefas/pontos restantes
    burndown = []
    for day in days:
        remaining_tasks = 0
        remaining_points = 0
        for t in tasks:
            completed = t.completed_at.date() if t.completed_at else None
            if not completed or completed > day:
                remaining_tasks += 1
                remaining_points += t.points if t.points else 0
        burndown.append({
            "date": str(day),
            "remaining_tasks": remaining_tasks,
            "remaining_points": remaining_points
        })
    return burndown

@app.get("/velocity")
def velocity_chart(db: Session = Depends(get_db)):
    sprints = db.query(Sprint).all()
    sprint_map = {s.id: s for s in sprints}
    tasks = db.query(Task).filter(Task.sprint_id != None).all()
    # Agrupa tarefas concluídas por sprint
    velocity = defaultdict(lambda: {"completed_tasks": 0, "completed_points": 0, "sprint_name": ""})
    for t in tasks:
        if t.completed_at and t.sprint_id in sprint_map:
            velocity[t.sprint_id]["completed_tasks"] += 1
            velocity[t.sprint_id]["completed_points"] += t.points if t.points else 0
            velocity[t.sprint_id]["sprint_name"] = sprint_map[t.sprint_id].name
    # Monta lista ordenada
    result = []
    for sprint_id, data in sorted(velocity.items()):
        result.append({
            "sprint_id": sprint_id,
            "sprint_name": data["sprint_name"],
            "completed_tasks": data["completed_tasks"],
            "completed_points": data["completed_points"]
        })
    return result

# Endpoint resumo de status por sprint
@app.get("/summary/sprint/{sprint_id}")
def sprint_summary(sprint_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.sprint_id == sprint_id).all()
    summary = {"To Do": {"tasks": 0, "points": 0}, "Doing": {"tasks": 0, "points": 0}, "Done": {"tasks": 0, "points": 0}}
    total_tasks = 0
    total_points = 0
    for t in tasks:
        status = t.status if t.status in summary else "To Do"
        summary[status]["tasks"] += 1
        summary[status]["points"] += t.points if t.points else 0
        total_tasks += 1
        total_points += t.points if t.points else 0
    summary["total_tasks"] = total_tasks
    summary["total_points"] = total_points
    return summary

# Endpoint lead time e cycle time
from statistics import mean, median
@app.get("/leadtime/sprint/{sprint_id}")
def sprint_leadtime(sprint_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.sprint_id == sprint_id, Task.completed_at != None).all()
    lead_times = []
    cycle_times = []
    for t in tasks:
        if t.completed_at and t.created_at:
            lead_times.append((t.completed_at - t.created_at).total_seconds() / 3600.0)  # horas
        if t.completed_at and t.started_at:
            cycle_times.append((t.completed_at - t.started_at).total_seconds() / 3600.0)  # horas
    return {
        "lead_time_avg": round(mean(lead_times), 2) if lead_times else None,
        "cycle_time_avg": round(mean(cycle_times), 2) if cycle_times else None,
        "lead_time_median": round(median(lead_times), 2) if lead_times else None,
        "cycle_time_median": round(median(cycle_times), 2) if cycle_times else None
    }

# Endpoint Cumulative Flow Diagram (CFD)
@app.get("/cfd/{sprint_id}")
def cfd_chart(sprint_id: int, db: Session = Depends(get_db)):
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    tasks = db.query(Task).filter(Task.sprint_id == sprint_id).all()
    days = []
    current = sprint.start_date.date()
    while current <= sprint.end_date.date():
        days.append(current)
        current = current.fromordinal(current.toordinal() + 1)
    cfd = []
    for day in days:
        status_count = {"To Do": 0, "Doing": 0, "Done": 0}
        for t in tasks:
            # Determina status da tarefa naquele dia
            if t.completed_at and t.completed_at.date() <= day:
                status = "Done"
            elif t.started_at and t.started_at.date() <= day:
                status = "Doing"
            else:
                status = "To Do"
            status_count[status] += 1
        cfd.append({"date": str(day), **status_count})
    return cfd

# Rotas CRUD

@app.get("/tasks", response_model=List[TaskResponse])
def read_tasks(
    status: str = Query(None),
    project: str = Query(None),
    sprint: int = Query(None),
    priority: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if project:
        query = query.filter(Task.project == project)
    if sprint is not None:
        query = query.filter(Task.sprint_id == sprint)
    if priority:
        query = query.filter(Task.priority == priority)
    tasks = query.all()
    # Cálculo de atraso
    now = datetime.utcnow()
    task_responses = []
    
    try:
        print(f"Processando {len(tasks)} tarefas encontradas")
        
        for t in tasks:
            try:
                atrasada = False
                
                # Verificar sprint de forma segura
                if hasattr(t, 'sprint_rel') and t.sprint_rel:
                    if hasattr(t.sprint_rel, 'end_date') and t.sprint_rel.end_date:
                        if t.status != "Done" and now > t.sprint_rel.end_date:
                            atrasada = True
                
                # Criar resposta para esta tarefa
                task_responses.append(TaskResponse(
                    id=t.id,
                    title=t.title,
                    description=t.description,
                    status=t.status,
                    project=t.project,
                    sprint_id=t.sprint_id,
                    priority=t.priority,
                    created_at=t.created_at,
                    started_at=t.started_at,
                    completed_at=t.completed_at,
                    atrasada=atrasada
                ))
            except Exception as task_error:
                print(f"Erro ao processar tarefa {t.id}: {str(task_error)}")
                # Continuar processando outras tarefas
        
        print(f"Retornando {len(task_responses)} respostas de tarefas")
    except Exception as e:
        import traceback
        print(f"Erro no endpoint /tasks: {str(e)}")
        print(traceback.format_exc())
    return task_responses

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    # Verificar se o sprint existe e se as datas da tarefa estão dentro do período do sprint
    if task.sprint_id:
        sprint = db.query(Sprint).filter(Sprint.id == task.sprint_id).first()
        if not sprint:
            raise HTTPException(status_code=404, detail="Sprint não encontrado")
        
        # Se a tarefa tiver datas de início e conclusão, verificar se estão dentro do período do sprint
        if task.started_at and task.started_at < sprint.start_date:
            raise HTTPException(status_code=400, detail="A data de início da tarefa não pode ser anterior à data de início do sprint")
            
        if task.completed_at and task.completed_at > sprint.end_date:
            raise HTTPException(status_code=400, detail="A data de conclusão da tarefa não pode ser posterior à data de término do sprint")
    
    db_task = Task(**task.dict(exclude_unset=True))
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = task.dict(exclude_unset=True)

    # Lógica para preencher started_at automaticamente
    status_before = db_task.status
    status_after = update_data.get("status", status_before)
    if status_before != "Doing" and status_after == "Doing" and not db_task.started_at:
        db_task.started_at = datetime.utcnow()

    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return {"detail": "Task deleted"}

@app.get("/")
def read_root():
    return {"message": "Bem-vindo à API Agile Mini!"} 

@app.get("/migrate-db")
def migrate_database():
    """Endpoint para migrar o banco de dados e adicionar todas as colunas necessárias."""
    try:
        # Conectar ao banco de dados
        db = SessionLocal()
        
        # Verificar se as colunas já existem
        import sqlalchemy as sa
        from sqlalchemy import inspect
        
        inspector = inspect(db.bind)
        
        # Verificar e adicionar colunas na tabela projects
        project_columns = [column['name'] for column in inspector.get_columns('projects')]
        
        if 'start_date' not in project_columns:
            db.execute(sa.text("ALTER TABLE projects ADD COLUMN start_date TIMESTAMP"))
            print("Coluna start_date adicionada à tabela projects!")
        
        if 'end_date' not in project_columns:
            db.execute(sa.text("ALTER TABLE projects ADD COLUMN end_date TIMESTAMP"))
            print("Coluna end_date adicionada à tabela projects!")
        
        # Verificar e adicionar colunas na tabela sprints
        sprint_columns = [column['name'] for column in inspector.get_columns('sprints')]
        
        if 'project_id' not in sprint_columns:
            db.execute(sa.text("ALTER TABLE sprints ADD COLUMN project_id INTEGER"))
            print("Coluna project_id adicionada à tabela sprints!")
        
        # Verificar e adicionar colunas na tabela tasks
        task_columns = [column['name'] for column in inspector.get_columns('tasks')]
        
        if 'sprint_id' not in task_columns:
            db.execute(sa.text("ALTER TABLE tasks ADD COLUMN sprint_id INTEGER"))
            print("Coluna sprint_id adicionada à tabela tasks!")
        
        db.commit()
        db.close()
        
        return {
            "success": True,
            "message": "Migração concluída com sucesso! Colunas start_date e end_date adicionadas à tabela projects."
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"Erro ao migrar banco de dados: {str(e)}",
            "traceback": traceback.format_exc()
        }

@app.get("/seed-demo-data")
def seed_demo_data():
    """Endpoint para criar dados de demonstração no banco de dados."""
    try:
        # Data atual
        today = datetime.utcnow()
        
        # Verificar se o projeto já existe
        db = SessionLocal()
        existing_project = db.query(Project).filter(Project.name == "Projeto Demonstração").first()
        
        if existing_project:
            # Usar o projeto existente
            project_id = existing_project.id
            # Atualizar as datas do projeto existente
            existing_project.start_date = today
            existing_project.end_date = today + timedelta(days=90)
            existing_project.status = "Ativo"
            db.commit()
            db.refresh(existing_project)
        else:
            # Criar um novo projeto demo
            project_data = Project(
                name="Projeto Demonstração",
                description="Um projeto de demonstração para testar as funcionalidades do Agile Mini",
                status="Ativo",
                start_date=today,
                end_date=today + timedelta(days=90)
            )
            
            db.add(project_data)
            db.commit()
            db.refresh(project_data)
            
            project_id = project_data.id
        
        # Verificar se já existem sprints para este projeto
        existing_sprints = db.query(Sprint).filter(Sprint.project_id == project_id).all()
        
        # Se existirem sprints, excluí-los para criar novos
        if existing_sprints:
            for sprint in existing_sprints:
                # Verificar se existem tarefas associadas a este sprint
                tasks = db.query(Task).filter(Task.sprint_id == sprint.id).all()
                # Excluir as tarefas primeiro
                for task in tasks:
                    db.delete(task)
                # Depois excluir o sprint
                db.delete(sprint)
            db.commit()
        
        # Criar sprints para o projeto
        sprints = []
        for i in range(3):
            sprint_start = today + timedelta(days=i*14)
            sprint_end = sprint_start + timedelta(days=13)
            
            sprint = Sprint(
                name=f"Sprint {i+1}",
                start_date=sprint_start,
                end_date=sprint_end,
                status="Ativo" if i == 0 else ("Planejado" if i > 0 else "Concluído"),
                project_id=project_id
            )
            
            db.add(sprint)
            db.commit()
            db.refresh(sprint)
            sprints.append(sprint)
        
        # Criar tarefas para os sprints
        statuses = ["A Fazer", "Em Andamento", "Concluído"]
        priorities = ["Baixa", "Média", "Alta"]
        tasks_count = 0
        
        for sprint in sprints:
            for i in range(5):  # 5 tarefas por sprint
                # Distribuir tarefas entre os status
                import random
                status_idx = random.randint(0, 2)
                status = statuses[status_idx]
                
                # Definir datas com base no status
                started_at = None
                completed_at = None
                
                if status == "Em Andamento" or status == "Concluído":
                    started_at = today - timedelta(days=random.randint(1, 5))
                
                if status == "Concluído":
                    completed_at = today
                
                task = Task(
                    title=f"Tarefa {i+1} do {sprint.name}",
                    description=f"Esta é uma tarefa de demonstração para o sprint {sprint.name}",
                    status=status,
                    priority=random.choice(priorities),
                    points=random.choice([1, 2, 3, 5, 8]),
                    project=str(project_id),
                    sprint_id=sprint.id,
                    started_at=started_at,
                    completed_at=completed_at
                )
                
                db.add(task)
                db.commit()
                tasks_count += 1
        
        db.close()
        
        return {
            "success": True,
            "message": "Dados de demonstração criados com sucesso!",
            "project": {"id": project_id, "name": "Projeto Demonstração"},
            "sprints_count": len(sprints),
            "tasks_count": tasks_count
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "message": f"Erro ao criar dados de demonstração: {str(e)}",
            "traceback": traceback.format_exc()
        }

# Endpoints para Projetos
@app.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects

@app.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_data: ProjectCreate, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for key, value in project_data.dict().items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@app.delete("/projects/{project_id}", response_model=dict)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted successfully"}

@app.get("/projects/{project_id}/sprints", response_model=List[SprintResponse])
def get_project_sprints(project_id: int, db: Session = Depends(get_db)):
    sprints = db.query(Sprint).filter(Sprint.project_id == project_id).all()
    return sprints

@app.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
def get_project_tasks(project_id: int, db: Session = Depends(get_db)):
    # Busca todas as tarefas associadas a sprints do projeto
    tasks = db.query(Task).join(Sprint).filter(Sprint.project_id == project_id).all()
    return tasks


# Endpoint para adicionar mais dados de demonstrau00e7u00e3o diversificados
@app.get("/seed-more-data")
def seed_more_data():
    """Endpoint para criar mais dados de demonstrau00e7u00e3o com sprints e tarefas em diferentes estu00e1gios."""
    try:
        # Data atual e datas passadas/futuras para criar sprints em diferentes estu00e1gios
        today = datetime.utcnow()
        two_months_ago = today - timedelta(days=60)
        
        # Criar um novo projeto com nome u00fanico
        db = SessionLocal()
        
        # Verificar se o projeto ju00e1 existe para evitar duplicau00e7u00e3o
        project_name = f"Projeto Desenvolvimento {today.strftime('%Y%m%d')}"
        existing_project = db.query(Project).filter(Project.name == project_name).first()
        
        if existing_project:
            # Se existir, apenas retornar o projeto existente
            project_id = existing_project.id
            project = existing_project
        else:
            # Criar um novo projeto com datas realistas
            project = Project(
                name=project_name,
                description="Um projeto de desenvolvimento com sprints em diferentes estu00e1gios e tarefas variadas",
                status="Ativo",
                start_date=two_months_ago,  # Iniciou 2 meses atru00e1s
                end_date=today + timedelta(days=120)  # Termina daqui a 4 meses
            )
            
            db.add(project)
            db.commit()
            db.refresh(project)
            project_id = project.id
        
        # Criar 6 sprints em diferentes estu00e1gios (2 conclu00eddos, 1 em andamento, 3 planejados)
        sprints = []
        sprint_statuses = ["Concluído", "Concluído", "Ativo", "Planejado", "Planejado", "Planejado"]
        
        for i in range(6):
            # Calcular datas do sprint: 2 sprints no passado, 1 atual, 3 futuros
            if i < 2:  # Sprints passados (concluídos)
                sprint_start = two_months_ago + timedelta(days=i*14)
                sprint_end = sprint_start + timedelta(days=13)
                status = "Concluído"
            elif i == 2:  # Sprint atual
                sprint_start = today - timedelta(days=7)  # Comeou00e7ou uma semana atru00e1s
                sprint_end = sprint_start + timedelta(days=13)  # Dura duas semanas
                status = "Ativo"
            else:  # Sprints futuros
                sprint_start = today + timedelta(days=(i-3)*14 + 7)  # Comeou00e7am apu00f3s o sprint atual
                sprint_end = sprint_start + timedelta(days=13)
                status = "Planejado"
            
            sprint = Sprint(
                name=f"Sprint {i+1}",
                start_date=sprint_start,
                end_date=sprint_end,
                status=status,
                project_id=project_id
            )
            
            db.add(sprint)
            db.commit()
            db.refresh(sprint)
            sprints.append(sprint)
        
        # Criar tarefas para os sprints com diferentes estados
        tasks_count = 0
        status_options = {
            "Concluído": ["A Fazer", "Em Andamento", "Concluído"],  # Para sprints concluídos
            "Ativo": ["A Fazer", "Em Andamento", "Concluído"],  # Para sprint em andamento
            "Planejado": ["A Fazer"]  # Para sprints planejados
        }
        
        # Pesos para cada status conforme o estado do sprint
        status_weights = {
            "Concluído": [0.1, 0.2, 0.7],  # Maioria concluída em sprints finalizados
            "Ativo": [0.3, 0.5, 0.2],  # Maioria em andamento no sprint atual
            "Planejado": [1.0]  # Todas a fazer em sprints futuros
        }
        
        # Nomes de tarefas mais realistas
        task_prefixes = [
            "Desenvolver", "Implementar", "Testar", "Corrigir", "Criar", 
            "Atualizar", "Documentar", "Refatorar", "Otimizar", "Revisar"
        ]
        
        task_subjects = [
            "funcionalidade de login", "mu00f3dulo de relatu00f3rios", "integraau00e7u00e3o com API", 
            "interface do usuu00e1rio", "banco de dados", "autenticaau00e7u00e3o", 
            "componente de visualizaau00e7u00e3o", "sistema de notificaau00e7u00f5es", 
            "mecanismo de busca", "processo de deploy", "algoritmo de recomendaau00e7u00e3o",
            "cache de dados", "dashboard", "endpoint REST", "validaau00e7u00e3o de formulau00e1rios"
        ]
        
        for sprint in sprints:
            # Nu00famero de tarefas variam por sprint - mais em sprints em andamento
            num_tasks = 12 if sprint.status == "Ativo" else (10 if sprint.status == "Concluído" else 8)
            
            for i in range(num_tasks):
                # Escolher status da tarefa baseado no status do sprint
                import random
                import numpy as np
                
                # Selecionar status baseado nos pesos definidos para o tipo de sprint
                status_options_for_sprint = status_options[sprint.status]
                weights = status_weights[sprint.status]
                status = np.random.choice(status_options_for_sprint, p=weights)
                
                # Gerar nomes de tarefas mais realistas
                task_name = f"{random.choice(task_prefixes)} {random.choice(task_subjects)}"
                
                # Definir pontos e prioridade
                priority = random.choice(["Baixa", "Mu00e9dia", "Alta"])
                points = random.choice([1, 2, 3, 5, 8, 13])  # Escala Fibonacci
                
                # Definir datas com base no status
                started_at = None
                completed_at = None
                
                if status == "Em Andamento" or status == "Concluído":
                    started_at = sprint.start_date + timedelta(days=random.randint(0, 3))
                
                if status == "Concluído":
                    # Se concluído, definir data de conclusu00e3o entre a data de início e o fim do sprint
                    if started_at:
                        days_until_end = (sprint.end_date - started_at).days
                        if days_until_end > 0:
                            days_to_complete = random.randint(1, min(days_until_end, 7))  # No mu00e1ximo 7 dias para concluir
                            completed_at = started_at + timedelta(days=days_to_complete)
                        else:
                            completed_at = sprint.end_date
                
                task = Task(
                    title=task_name,
                    description=f"Esta tarefa envolve {task_name.lower()} para o projeto {project.name}",
                    status=status,
                    priority=priority,
                    points=points,
                    project=str(project_id),
                    sprint_id=sprint.id,
                    started_at=started_at,
                    completed_at=completed_at
                )
                
                db.add(task)
                db.commit()
                tasks_count += 1
        
        db.close()
        
        return {
            "success": True,
            "message": "Dados adicionais criados com sucesso!",
            "project": {"id": project_id, "name": project_name},
            "sprints_count": len(sprints),
            "tasks_count": tasks_count
        }
    except Exception as e:
        import traceback
        print(f"Erro ao criar dados adicionais: {str(e)}")
        print(traceback.format_exc())
        return {
            "success": False,
            "message": f"Erro ao criar dados adicionais: {str(e)}",
            "traceback": traceback.format_exc()
        }
        
# Endpoint de diagnu00f3stico para verificar o estado da API
@app.get("/diagnostico")
def diagnostico():
    import os
    import traceback
    
    try:
        # Testar conexão com o banco de dados
        db = SessionLocal()
        # Tentar executar uma consulta simples
        projects_count = db.query(Project).count()
        db.close()
        
        # Verificar arquivos de banco de dados
        current_dir = os.path.abspath('.')
        parent_dir = os.path.abspath('..')
        
        files_info = {
            'current_directory': current_dir,
            'parent_directory': parent_dir,
            'db_in_current': os.path.exists('./agile_mini.db'),
            'db_in_parent': os.path.exists('../agile_mini.db'),
            'connection_string': SQLALCHEMY_DATABASE_URL,
            'projects_count': projects_count
        }
        
        return {
            'status': 'OK',
            'message': 'API funcionando corretamente',
            'database_info': files_info,
            'cors_config': {
                'allow_origins': ["*"],
                'allow_credentials': True,
                'allow_methods': ["*"],
                'allow_headers': ["*"]
            }
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': str(e),
            'traceback': traceback.format_exc()
        }

# Iniciar o servidor Uvicorn diretamente quando o arquivo for executado
if __name__ == "__main__":
    import uvicorn
    
    print("Iniciando servidor Agile Mini API...")
    print("A API estaru00e1 disponu00edvel em: http://127.0.0.1:8000")
    print("Acesse http://127.0.0.1:8000/diagnostico para verificar o estado da API")
    print("Pressione CTRL+C para encerrar o servidor")
    
    # Inicia o servidor Uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
