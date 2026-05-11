from src import create_app
from src.settings import setting

app = create_app()
if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host=setting.APP_HOST, port=setting.APP_PORT)
