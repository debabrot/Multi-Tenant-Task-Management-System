from fastapi import FastAPI


def create_app() -> FastAPI:
    """
    Factory function that creates and configures a FastAPI application instance.
    """
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ping": "pong"}

    return app
