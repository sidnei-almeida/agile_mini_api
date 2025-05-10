import os
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, validator
from datetime import datetime

# Configuração do banco de dados (PostgreSQL no Render, SQLite local)
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
    # Usar SQLite localmente
    SQLALCHEMY_DATABASE_URL = "sqlite:///./agile_mini.db"
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

# Instância do FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Configuração do CORS para aceitar qualquer origem
origins = ["*"]  # Permite todas as origens

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP
    allow_headers=["*"],  # Permite todos os cabeçalhos
    expose_headers=["*"],  # Expõe todos os cabeçalhos
    max_age=86400,  # Cache de preflight por 24 horas
)

# Adicionar cabeçalhos CORS a todas as respostas
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Rota OPTIONS para lidar com preflight requests
@app.options("/{full_path:path}")
async def options_route(full_path: str):
    return JSONResponse(
        content="{}",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
        }
    )

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
        project = db.query(Project).filter(Project.id == sprint.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
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
    for t in tasks:
        atrasada = False
        if t.sprint_rel and t.sprint_rel.end_date and t.status != "Done":
            if now > t.sprint_rel.end_date:
                atrasada = True
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
    return task_responses

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
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
