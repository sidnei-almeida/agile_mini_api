import uvicorn
import uvicorn

if __name__ == "__main__":
    # Rodar a API localmente na porta 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
