import json
import socket
import time
import psycopg2
import pika
import os
import sys
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('consumer')

print("========== INICIANDO CONSUMER ==========")
print(f"Python version: {sys.version}")
print(f"Running in directory: {os.getcwd()}")
print(f"Environment variables: {os.environ}")
print("=======================================")

# Função para tentar resolver um nome de host
def resolve_hostname(hostname, max_retries=20, retry_interval=5):
    """Tenta resolver um nome de host com várias tentativas."""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Tenta resolver o nome de host
            logger.info(f"Tentando resolver hostname: {hostname}, tentativa {retry_count+1}/{max_retries}")
            ip_address = socket.gethostbyname(hostname)
            logger.info(f"Hostname {hostname} resolvido para {ip_address}")
            return ip_address
        except socket.gaierror as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Falha ao resolver hostname {hostname} após {max_retries} tentativas: {e}")
                return None
            logger.warning(f"Não foi possível resolver {hostname}, tentando novamente em {retry_interval} segundos...")
            time.sleep(retry_interval)

# Connect to CockroachDB
def get_db_connection():
    retry_count = 0
    max_retries = 10
    
    # Obter o host e porta do CockroachDB da variável de ambiente ou usar padrão
    cockroach_host = os.environ.get('COCKROACH_HOST', 'haproxy')
    cockroach_port = int(os.environ.get('COCKROACH_PORT', '26256'))
    
    print(f"DEBUG: Attempting to connect to CockroachDB at {cockroach_host}:{cockroach_port}")
    
    # Tenta resolver o hostname do CockroachDB
    resolve_hostname(cockroach_host)
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host=cockroach_host,
                port=cockroach_port,
                user="root",
                database="defaultdb",
                sslmode="disable"
            )
            print(f"Successfully connected to CockroachDB at {cockroach_host}:{cockroach_port}")
            return conn
        except psycopg2.OperationalError as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"Failed to connect to CockroachDB after {max_retries} attempts. Exiting.")
                sys.exit(1)
            print(f"Failed to connect to CockroachDB at {cockroach_host}:{cockroach_port}: {e}. Retrying in 5 seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(5)

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS key_value_store (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("Database initialized")

# Process message from RabbitMQ
def process_message(ch, method, properties, body):
    try:
        data = json.loads(body)
        operation = data.get("operation")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if operation == "PUT":
            key = data.get("key")
            value = data.get("value")
            
            # Upsert the key-value pair
            cursor.execute("""
            UPSERT INTO key_value_store (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, (key, value))
            
            print(f"Stored key: {key}, value: {value}")
            
        elif operation == "DELETE":
            key = data.get("key")
            
            # Delete the key-value pair
            cursor.execute("""
            DELETE FROM key_value_store
            WHERE key = %s
            """, (key,))
            
            print(f"Deleted key: {key}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        # Reject the message and requeue
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# Start consumer
def start_consumer():
    hostname = socket.gethostname()
    print(f"Starting consumer on {hostname}")
    
    # Esperar um tempo para garantir que os outros serviços estejam prontos
    print("Waiting for services to be ready...")
    time.sleep(20)
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Connect to RabbitMQ
    retry_count = 0
    max_retries = 30
    
    # Obter o host e porta do RabbitMQ da variável de ambiente ou usar padrão
    rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq-proxy')
    rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', '5670'))
    
    print(f"DEBUG: Attempting to connect to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}")
    
    # Tenta resolver o hostname do RabbitMQ
    if not resolve_hostname(rabbitmq_host, max_retries=30, retry_interval=10):
        print(f"Could not resolve hostname {rabbitmq_host}. Exiting.")
        sys.exit(1)
    
    while retry_count < max_retries:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=rabbitmq_host,
                    port=rabbitmq_port,
                    heartbeat=30,
                    blocked_connection_timeout=15,
                    socket_timeout=15,
                    connection_attempts=5,
                    retry_delay=5,
                    credentials=pika.PlainCredentials('guest', 'guest')
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue='kv_operations', durable=True)
            
            # Set QoS to only get one message at a time
            channel.basic_qos(prefetch_count=1)
            
            # Set up consumer
            channel.basic_consume(
                queue='kv_operations',
                on_message_callback=process_message
            )
            
            print(f"Consumer {hostname} waiting for messages. To exit press CTRL+C")
            channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"Failed to connect to RabbitMQ after {max_retries} attempts. Exiting.")
                sys.exit(1)
            print(f"Failed to connect to RabbitMQ at {rabbitmq_host}:{rabbitmq_port}: {e}. Retrying in 10 seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(10)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    start_consumer() 