import pika
import json
import psycopg2
import redis
import os

def connect_db():
    # Obter o host e porta do CockroachDB da variável de ambiente ou usar padrão
    cockroach_host = os.environ.get('COCKROACH_HOST', 'haproxy')
    cockroach_port = int(os.environ.get('COCKROACH_PORT', '26256'))
    
    return psycopg2.connect(
        host=cockroach_host,
        user="root",
        database="defaultdb",
        port=cockroach_port
    )

def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def callback(ch, method, properties, body):
    data = json.loads(body)
    conn = connect_db()
    cursor = conn.cursor()
    redis_client = redis.Redis(host="redis", port=6379)  # Conexão Redis
    
    if data.get("action") == "delete":
        cursor.execute("DELETE FROM items WHERE key = %s", (data["key"],))
        redis_client.delete(data["key"])  # Remove do cache
    else:
        cursor.execute("""
            INSERT INTO items (key, value) 
            VALUES (%s, %s) 
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (data["key"], data["value"]))
        redis_client.set(data["key"], data["value"])  # Atualiza cache
    
    conn.commit()
    conn.close()

init_db()
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()
channel.queue_declare(queue="updates")
channel.basic_consume(queue="updates", on_message_callback=callback, auto_ack=True)
channel.start_consuming()