# Documentação dos Testes Unitários com Curl

Este documento descreve os testes unitários baseados em curl para a API de Armazenamento Chave-Valor. Estes testes verificam a funcionalidade básica das operações PUT, GET e DELETE da API utilizando comandos curl padrão. 

## Visão Geral

Os testes curl fornecem uma forma leve de verificar se a API está a funcionar corretamente. Estes testes podem ser executados sem dependências adicionais para além do bash e do curl.

## Testes Incluídos

### 1. Teste da Operação PUT

Testa o armazenamento de um par chave-valor no sistema.

```bash
curl -X PUT http://localhost/ -H 'Content-Type: application/json' -d '{"data": {"key": "hello", "value": "world"}}'
```

Resposta esperada:
```json
{"status":"success"}
```

### 2. Teste da Operação GET

Testa a recuperação de um par chave-valor previamente armazenado.

```bash
curl -X GET http://localhost:8080/test-key
```

Resposta esperada:
```json
{"data":{"value":"test-value"}}
```

### 3. Teste da Operação DELETE

Testa a eliminação de um par chave-valor do sistema.

```bash
curl -X DELETE http://localhost:8080/test-key
```

Resposta esperada:
```json
{}
```

### 4. Teste de Verificação

Verifica se uma chave eliminada já não está acessível.

```bash
curl -X GET -w "%{http_code}" http://localhost:8080/test-key -o /dev/null
```

Resposta esperada:
Código de estado HTTP `404` (Não Encontrado)

## Execução dos Testes

Para executar os testes curl:

1. Certifique-se de que o serviço da API está em execução


## Modificação dos Testes

Para testar contra um endpoint de API diferente, modifique a variável `API_URL` no início do script:

```bash
API_URL="http://endpoint-api:porta"
```

Também pode modificar a chave e o valor de teste alterando as variáveis `TEST_KEY` e `TEST_VALUE`.

## Limitações

Estes testes são simples e focam apenas na funcionalidade básica. Não testam:

- Autenticação/autorização
- Tratamento de erros para entradas inválidas
- Desempenho sob carga
- Acesso concorrente
- Persistência de dados entre reinícios

Para testes mais abrangentes, consultar a secção sobre [testes de carga](./load_test_report.md) na documentação do projeto.  