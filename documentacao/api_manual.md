# Manual da API e Uso do Sistema

## Introdução

Este documento fornece informações detalhadas sobre a API REST do sistema de armazenamento chave-valor distribuído. A API permite operações básicas de armazenamento, recuperação e eliminação de pares chave-valor.

Também é possível acessar à página "swagger" da documentação da API, para isso basta acessar a https://localhost/docs assim que o sistema se encontrar a correr.


## Endpoints da API

A API REST oferece os seguintes endpoints:

### Operações com Chave-Valor

#### GET /{key}

Recupera o valor associado à chave especificada.

**Parâmetros URL:**
- `key` (obrigatório): A chave a ser recuperada

**Códigos de Resposta:**
- `200 OK`: Operação bem-sucedida
- `404 Not Found`: Chave não encontrada
- `503 Service Unavailable`: Serviço de cache indisponível
- `500 Internal Server Error`: Erro interno do servidor

**Exemplo de Resposta (200 OK):**
```json
{
  "data": {
    "value": "test-value"
  }
}
```

**Exemplo de Comando:**
```bash
curl -X GET http://localhost/test-key
```

#### PUT /

Armazena um par chave-valor.

**Corpo da Requisição:**
```json
{
  "data": {
    "key": "string",
    "value": "string"
  }
}
```

**Códigos de Resposta:**
- `200 OK`: Operação bem-sucedida
- `503 Service Unavailable`: Serviço de cache indisponível
- `500 Internal Server Error`: Erro interno do servidor

**Exemplo de Resposta (200 OK):**
```json
{
  "status": "success"
}
```

**Exemplo de Comando:**
```bash
curl -X PUT http://localhost/ -H 'Content-Type: application/json' -d '{"data": {"key": "test-key", "value": "test-value"}}'
```

#### DELETE /{key}

Elimina o par chave-valor especificado.

**Parâmetros URL:**
- `key` (obrigatório): A chave a ser removida

**Códigos de Resposta:**
- `200 OK`: Operação bem-sucedida
- `503 Service Unavailable`: Serviço de cache indisponível
- `500 Internal Server Error`: Erro interno do servidor

**Exemplo de Resposta (200 OK):**
```json
{}
```

**Exemplo de Comando:**
```bash
curl -X DELETE http://localhost/test-key
```

### Endpoints de Status

#### GET /info

Retorna informações básicas sobre a API.

**Exemplo de Resposta:**
```json
{
  "message": "Key-Value Store API",
  "instance": "api-1"
}
```

**Exemplo de Comando:**
```bash
curl -X GET http://localhost/info
```

#### GET /health

Retorna o status de saúde da API e suas dependências.

**Exemplo de Resposta (Saudável):**
```json
{
  "status": "healthy",
  "instance": "api-1"
}
```

**Exemplo de Resposta (Degradado):**
```json
{
  "status": "degraded",
  "instance": "api-1",
  "services": {
    "redis": "unavailable"
  }
}
```

**Exemplo de Comando:**
```bash
curl -X GET http://localhost/health
```

## Exemplos de Uso com Ferramentas Diferentes

### Utilizando o cURL

#### Armazenar um par chave-valor:
```bash
curl -X PUT http://localhost/ -H 'Content-Type: application/json' -d '{"data": {"key": "hello", "value": "world"}}'
```

#### Aceder a um valor:
```bash
curl -X GET http://localhost/hello
```

#### Remover um par chave-valor:
```bash
curl -X DELETE http://localhost/hello
```


## Práticas Recomendadas

1. **Tratamento de Erros**: Implementar sempre tratamento adequado de erros ao interagir com a API, especialmente para lidar com indisponibilidade temporária do serviço.

2. **Retentativas**: Para operações críticas, implementar lógica de retentativa com backoff exponencial para lidar com falhas transitórias.

3. **Chaves Complexas**: Evitar o uso de caracteres especiais nas chaves, pois eles podem exigir codificação URL adequada.

4. **Valores Grandes**: Para valores muito grandes (> 1MB), considere dividi-los em chunks ou usar um sistema de armazenamento de objetos separado.

5. **Monitoramento**: Utilizar o endpoint `/health` para monitoramento regular da saúde da API.

## Limitações da API

1. A API não implementa autenticação ou autorização.
2. Não há suporte para expiração automática de chaves (TTL).
3. Não há suporte para operações em lote.
4. O tamanho máximo das chaves e valores não é explicitamente limitado, mas valores muito grandes podem afetar o desempenho.