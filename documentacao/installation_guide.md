# Guia de Instalação e Utilização

Este documento fornece instruções para instalar e utilizar o sistema de armazenamento chave-valor distribuído.

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Instalação Local](#instalação-local)
3. [Instalação em Cloud](#instalação-em-cloud)
4. [Utilização Básica](#utilização-básica)
5. [Monitorização](#monitorização)
6. [Resolução de Problemas](#resolução-de-problemas)

## Pré-requisitos

Para executar o sistema, necessita de:

- **Docker**: versão 20.10.0 ou superior
- **Docker Compose**: versão 2.0.0 ou superior
- **Bash**: para executar os scripts
- **cURL**: para testar a API

### Verificação de Pré-requisitos

```bash
# Verificar a versão do Docker
docker --version

# Verificar a versão do Docker Compose
docker-compose --version

# Verificar a versão do Bash
bash --version
```

## Instalação Local

### Passo 1: Obter o Código

```bash
git clone https://github.com/a79809/Atividade2SistemasDistribuidos.git
cd Atividade2SistemasDistribuidos
```

### Passo 2: Iniciar o Sistema

```bash
# Iniciar o sistema
docker-compose up --build -d

```

### Passo 3: Verificar a Instalação

```bash
# Listar os contentores em execução
docker ps

# Testar a API
curl -X GET http://localhost/info
```

A resposta deve ser:

```json
{
  "message": "Key-Value Store API",
  "instance": "api-1"
}
```

## Instalação em Cloud

### Azure

#### Pré-requisitos
- Conta Azure
- Azure CLI instalado
- Grupo de recursos criado

#### Passos

1. **Configurar Ambiente**
```bash
# Autenticar e criar recursos
az login
az group create --name kv-store-group --location eastus
az acr create --resource-group kv-store-group --name kvstoreacr --sku Basic
```

2. **Enviar Imagens**
```bash
# Construir e enviar imagens
docker-compose build
docker tag kv-store-api:latest kvstoreacr.azurecr.io/kv-store-api:latest
docker tag kv-store-consumer:latest kvstoreacr.azurecr.io/kv-store-consumer:latest
docker push kvstoreacr.azurecr.io/kv-store-api:latest
docker push kvstoreacr.azurecr.io/kv-store-consumer:latest
```

3. **Colocar no Azure Container Instances**
```bash
# Colocar serviços
az acr update -n kvstoreacr --admin-enabled true
az container create --resource-group kv-store-group --name kv-store-api --image kvstoreacr.azurecr.io/kv-store-api:latest --dns-name-label kv-store-api --ports 80
```

## Utilização Básica

### Armazenar um Par Chave-Valor

```bash
curl -X PUT http://localhost/ -H 'Content-Type: application/json' -d '{"data": {"key": "exemplo", "value": "valor de teste"}}'
```

### Aceder a um Valor

```bash
curl -X GET http://localhost/exemplo
```

### Remover um Par Chave-Valor

```bash
curl -X DELETE http://localhost/exemplo
```

### Verificar o Estado do Sistema

```bash
curl -X GET http://localhost/health
```

## Monitorização

### Visualizar Logs

```bash
# Ver todos os logs
docker-compose logs

# Acompanhar logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs api
```

### Interfaces de Monitorização

- **CockroachDB**: http://localhost:8080
- **RabbitMQ**: http://localhost:15672 (Utilizador: guest, Palavra-passe: guest)


## Resolução de Problemas

### 1. Serviços não iniciam

**Solução**:
```bash
# Verificar logs
docker-compose logs [nome-do-serviço]

# Reiniciar o sistema
docker-compose down
docker-compose up --build -d
```

### 2. Erro de Ligação ao Redis

**Solução**:
```bash
# Verificar estado do Redis
docker ps | grep redis

# Reiniciar serviços
docker-compose restart redis-master redis-replica envoy
```

### 3. Problemas de Consistência

**Solução**:
```bash
# Verificar fila RabbitMQ
curl -u guest:guest http://localhost:15672/api/queues/%2F/kv_operations

# Verificar logs do consumidor
docker-compose logs consumer
``` 