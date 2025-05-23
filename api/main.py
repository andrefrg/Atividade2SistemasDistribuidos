import os
import json
import socket
import logging
import time
import ipaddress
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import pika
from typing import Dict, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Key-Value Store API")

# Middleware CORS para permitir requisições cross-origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Registrar início da requisição
    logger.info(f"Request started: {request.method} {request.url.path}")
    
    # Processar a requisição
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Registrar conclusão bem-sucedida
        logger.info(f"Request completed: {request.method} {request.url.path} - Status: {response.status_code} - Took: {process_time:.4f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        
        # Registrar erro
        logger.error(f"Request failed: {request.method} {request.url.path} - Error: {str(e)} - Took: {process_time:.4f}s")
        raise

# Redis connection with retry logic
def get_redis_connection():
    retries = 5
    while retries > 0:
        try:
            # Always use redis-master for all operations
            redis_host = "redis-master"
            redis_port = 6379
            
            logger.info(f"Connecting to Redis at {redis_host}:{redis_port}")
            
            return redis.Redis(host=redis_host, port=redis_port, decode_responses=True, socket_timeout=5, socket_connect_timeout=5)
        except redis.exceptions.ConnectionError as e:
            if retries <= 1:
                raise e
            retries -= 1
            logger.warning(f"Redis connection failed, retrying... ({retries} attempts left)")
            time.sleep(1)

# Mapear endereços IP do RabbitMQ para evitar resolução de DNS
# Isso deve acelerar a conexão
RABBITMQ_IPS = {
    "rabbitmq-proxy": "172.24.0.13",  # Ajuste para o IP correto do RabbitMQ em sua rede
    "rabbitmq1": "172.24.0.11",
    "rabbitmq2": "172.24.0.12",
    "rabbitmq3": "172.24.0.13"
}

# RabbitMQ connection with improved error handling
def get_rabbitmq_connection():
    try:
        # Obter o host e porta do RabbitMQ da variável de ambiente ou usar padrão
        rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq-proxy')
        rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', '5670'))
        
        # Verificar se temos um IP mapeado para este host para evitar resolução DNS lenta
        if rabbitmq_host in RABBITMQ_IPS:
            logger.info(f"Using direct IP address for {rabbitmq_host}: {RABBITMQ_IPS[rabbitmq_host]}")
            rabbitmq_host = RABBITMQ_IPS[rabbitmq_host]
        
        logger.info(f"Connecting to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")
        
        # Reduzir timeout para não bloquear a resposta por muito tempo
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host,
                port=rabbitmq_port,
                heartbeat=5,  # Reduzido de 30 para 5
                blocked_connection_timeout=5,  # Reduzido de 10 para 5
                socket_timeout=3,  # Reduzido de 10 para 3
                connection_attempts=2,  # Reduzido de 3 para 2
                retry_delay=1,  # Reduzido de 5 para 1
                # Credenciais de autenticação (opcional)
                credentials=pika.PlainCredentials('guest', 'guest')
            )
        )
        channel = connection.channel()
        channel.queue_declare(queue='kv_operations', durable=True)
        return connection, channel
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
        # Não vamos levantar a exceção para evitar que a operação falhe
        return None, None

class DataPayload(BaseModel):
    key: str
    value: str

class PutRequest(BaseModel):
    data: DataPayload

hostname = socket.gethostname()

@app.get("/info")
def read_root():
    return {"message": "Key-Value Store API", "instance": hostname}

@app.get("/health")
def health_check():
    # Verificar conexão com Redis
    try:
        redis_client = get_redis_connection()
        redis_client.ping()
    except Exception as e:
        logger.warning(f"Health check: Redis connection failed - {str(e)}")
        return {"status": "degraded", "instance": hostname, "services": {"redis": "unavailable"}}
    
    return {"status": "healthy", "instance": hostname}

@app.get("/{key}")
def get_value(key: str):
    try:
        # Try to get from Redis cache first
        redis_client = get_redis_connection()
        value = redis_client.get(key)
        
        if value:
            return {"data": {"value": value}}
        
        # If not in cache, return not found
        # In a complete implementation, we would check the database here
        raise HTTPException(status_code=404, detail=f"Key '{key}' not found")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis error on GET: {str(e)}")
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error on GET: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/")
def put_value(request: PutRequest):
    try:
        key = request.data.key
        value = request.data.value
        
        # Store in Redis cache
        redis_client = get_redis_connection()
        redis_client.set(key, value)
        
        # Criar thread separada para publicação no RabbitMQ
        # para não bloquear a resposta HTTP
        import threading
        
        def send_to_rabbitmq():
            try:
                connection, channel = get_rabbitmq_connection()
                if connection and channel:
                    message = {
                        "operation": "PUT",
                        "key": key,
                        "value": value
                    }
                    
                    channel.basic_publish(
                        exchange='',
                        routing_key='kv_operations',
                        body=json.dumps(message),
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # make message persistent
                        )
                    )
                    
                    connection.close()
                    logger.info(f"Successfully queued key: {key} for persistence")
            except Exception as e:
                logger.error(f"Background RabbitMQ error on PUT: {str(e)}")
        
        # Iniciar thread em background para não bloquear a resposta
        threading.Thread(target=send_to_rabbitmq).start()
        
        logger.info(f"Successfully stored key: {key} in cache")
        return {"status": "success"}
    
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis error on PUT: {str(e)}")
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error on PUT: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/{key}")
def delete_value(key: str):
    try:
        # Delete from Redis cache
        redis_client = get_redis_connection()
        deleted = redis_client.delete(key)
        
        # Criar thread separada para publicação no RabbitMQ
        # para não bloquear a resposta HTTP
        import threading
        
        def send_to_rabbitmq():
            try:
                connection, channel = get_rabbitmq_connection()
                if connection and channel:
                    message = {
                        "operation": "DELETE",
                        "key": key
                    }
                    
                    channel.basic_publish(
                        exchange='',
                        routing_key='kv_operations',
                        body=json.dumps(message),
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # make message persistent
                        )
                    )
                    
                    connection.close()
                    logger.info(f"Successfully queued key: {key} for deletion")
            except Exception as e:
                logger.error(f"Background RabbitMQ error on DELETE: {str(e)}")
        
        # Iniciar thread em background para não bloquear a resposta
        threading.Thread(target=send_to_rabbitmq).start()
        
        logger.info(f"Successfully deleted key: {key} from cache")
        return {}
    
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Redis error on DELETE: {str(e)}")
        raise HTTPException(status_code=503, detail="Cache service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error on DELETE: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))