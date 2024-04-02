import logging
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Response, Request
from starlette.background import BackgroundTask
from starlette.types import Message

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World, 안녕 세상"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post('/')
def main(payload: Dict[Any, Any]):
    return payload


logger = logging.getLogger("main")
logging.basicConfig(level=logging.DEBUG, encoding='utf-8')
steam_handler = logging.FileHandler('info.log', mode='w', encoding='utf-8')
logger.addHandler(steam_handler)


async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {'type': 'http.request', 'body': body}
    request._receive = receive


@app.middleware('http')
async def some_middleware(request: Request, call_next):
    req_headers = request.headers
    req_body = await request.body()
    await set_body(request, req_body)
    response = await call_next(request)
    res_headers = response.headers
    res_status_code = response.status_code
    res_body = b''
    async for chunk in response.body_iterator:
        res_body += chunk
    task = BackgroundTask(func=log_info,
                          req_headers=req_headers,
                          req_body=req_body,
                          res_status_code=res_status_code,
                          res_headers=res_headers,
                          res_body=res_body)
    return Response(content=res_body, status_code=response.status_code,
                    headers=dict(response.headers), media_type=response.media_type, background=task)


def log_info(req_headers, req_body, res_status_code, res_headers, res_body):
    logging.info(f">>> REQUEST HEADERS: {req_headers}")
    logging.info(f">>> REQUEST BODY: {req_body.decode('utf-8')}")
    logging.info(f">>> RESPONSE STATUS CODE: {res_status_code}")
    logging.info(f">>> RESPONSE HEADERS: {res_headers}")
    logging.info(f">>> RESPONSE BODY: {res_body.decode('utf-8')}")


if __name__ == '__main__':
    uvicorn.run(app)
