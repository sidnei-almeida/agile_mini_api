# Agile Mini

## Descrição
Agile Mini é um sistema leve e eficiente de gestão de projetos ágeis. Projetado para equipes de todos os tamanhos, ele oferece uma abordagem simples para gerenciar tarefas em quadros Kanban, sprints e monitoramento de progresso através de gráficos intuitivos.

## Funcionalidades Principais

### Gerenciamento de Tarefas
- **Quadro Kanban**: Visualize e mova tarefas entre os status To Do, Doing e Done
- **Priorização**: Defina prioridades (Baixa, Média, Alta) para suas tarefas
- **Story Points**: Estime o esforço usando story points
- **Gestão por Sprints**: Organize tarefas em ciclos de entrega curtos

### Analytics
- **Burndown Chart**: Acompanhe o progresso do sprint visualmente
- **Velocity Chart**: Monitore a produtividade da equipe ao longo do tempo
- **Cumulative Flow Diagram (CFD)**: Identifique gargalos no fluxo de trabalho

### Recursos Inteligentes
- **Detecção automática** de tarefas atrasadas
- **Cálculo automático** do status dos sprints (Planejado, Ativo, Concluído)
- **Lead Time e Cycle Time**: Entenda quanto tempo suas tarefas levam para serem concluídas

## Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework moderno e de alta performance para APIs REST
- **SQLAlchemy**: ORM para manipulação de banco de dados
- **PostgreSQL** (produção): Banco de dados robusto para ambiente de produção
- **SQLite** (desenvolvimento): Banco leve para desenvolvimento local
- **Pydantic**: Validação e serialização de dados

### Frontend
- **HTML/CSS/JavaScript**: Interface limpa e responsiva
- **Fetch API**: Comunicação assíncrona com o backend
- **Chart.js** (planejado): Visualização de gráficos de burndown e velocity

## Instalação e Uso

### Requisitos
- Python 3.8+
- Node.js (para desenvolvimento frontend)

### Configuração do Backend

1. Clone o repositório e navegue até a pasta
   ```bash
   git clone https://github.com/sidnei-almeida/agile_mini_api
   cd agile_mini
   ```

2. Crie e ative um ambiente virtual
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate  # Windows
   ```

3. Instale as dependências
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Execute o servidor
   ```bash
   python -m backend.main
   ```

5. Acesse a documentação da API em http://127.0.0.1:8000/docs

### Deploy (Render)
1. Crie um banco PostgreSQL no Render
2. Crie um Web Service apontando para seu repositório
3. Configure a variável de ambiente `DATABASE_URL` com a URL do seu banco PostgreSQL
4. Configure o diretório raiz como `/backend`

## Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.
