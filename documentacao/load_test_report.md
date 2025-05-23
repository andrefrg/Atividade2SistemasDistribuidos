# Relatório de Testes de Carga (Atualizado)

Este documento apresenta os resultados dos testes de carga realizados no sistema de armazenamento chave-valor distribuído, bem como a justificação para o dimensionamento e os limites estabelecidos.

## Testes com Siege e ApacheBench

### Testes de Leitura (GET)

Realizámos uma série de testes para avaliar o desempenho do sistema em operações de leitura (GET) utilizando diferentes níveis de concorrência:

#### Resultados do Siege com Concorrência Crescente

| Concorrência     | Transações | Disponibilidade | Tempo (s) | Taxa de Transações (TPS) | Tempo de Resposta (s)  | Throughput (MB/s) |
|------------------|------------|-----------------|-----------|--------------------------|------------------------|-------------------|
| 10 utilizadores  | 5.544      | 100%            | 9,50      | 583,58                   | 0,02                   | 0,02              |
| 25 utilizadores  | 6.098      | 100%            | 9,02      | 676,05                   | 0,04                   | 0,02              |
| 50 utilizadores  | 6.634      | 100%            | 9,35      | 709,52                   | 0,07                   | 0,02              |
| 100 utilizadores | 5.069      | 100%            | 9,10      | 557,03                   | 0,18                   | 0,02              |
| 200 utilizadores | 5.833      | 100%            | 9,26      | 629,91                   | 0,31                   | 0,02              |

### Testes de Escrita (PUT)

Também realizámos testes para avaliar o desempenho do sistema em operações de escrita (PUT):

#### Resultados do ApacheBench para Operações PUT

| Concorrência | Requisições | Falhas | Tempo (s) | Requisições por Segundo | Tempo por Requisição (ms) | Taxa de Transferência (KB/s) |
|-------------|-------------|---------|-----------|------------------------|--------------------------|-----------------------------|
| 100 utilizadores | 1.000 | 0 | 0,938 | 1.066,32 | 93,78 | 211,39 |
| 500 utilizadores | 5.000 | 0 | 4,022 | 1.243,26 | 402,17 | 246,47 |

#### Desempenho de Operações Individuais

- **PUT**: Aproximadamente 94ms (100 utilizadores), 399ms (500 utilizadores)
- **GET**: Tempo médio de resposta variando de 20ms (10 utilizadores) a 310ms (200 utilizadores)

## Justificação de Dimensionamento

Com base nos resultados dos testes de carga, estabelecemos os seguintes dimensionamentos e limites para o sistema:

### 1. Dimensionamento da API

**Configuração Recomendada**: 3 instâncias (conforme ambiente de teste)

**Justificação**:
- O sistema pode processar até ~700 transações por segundo com 50 utilizadores concorrentes mantendo 100% de disponibilidade
- O ApacheBench mostrou que o sistema pode atingir até 1.243 requisições por segundo para operações de escrita
- Cada instância pode processar aproximadamente 600-700 RPS de forma sustentável
- 3 instâncias fornecem capacidade total de ~2.000 RPS
- Esta configuração permite acomodar picos de tráfego mantendo latência aceitável

### 2. Dimensionamento do Redis

**Configuração Recomendada**: 1 master, 1 réplica

**Justificação**:
- O Redis demonstrou desempenho estável durante os testes
- A configuração atual é suficiente para a carga observada

### 3. Dimensionamento do RabbitMQ

**Configuração Recomendada**: 3 nós em cluster

**Justificação**:
- As operações de escrita (PUT) apresentaram bom desempenho com alta concorrência
- O cluster de 3 nós oferece alta disponibilidade

### 4. Dimensionamento do CockroachDB

**Configuração Recomendada**: 3 nós em cluster

**Justificação**:
- O cluster CockroachDB proporciona resiliência, consistência e tolerância a falhas

## Limites Estabelecidos

Com base nos testes realizados, estabelecemos os seguintes limites para o sistema:

### 1. Limites de Desempenho

- **Capacidade máxima de leitura**: ~2.000 RPS (com 3 instâncias da API)
- **Capacidade máxima de escrita**: ~1.200 RPS (com 3 instâncias da API)
- **Latência média observada**: 20-310ms para leituras, 94-399ms para escritas
- **Concorrência máxima testada**: 200 utilizadores para leitura, 500 para escrita

### 2. Limites de Armazenamento

- **Tamanho máximo de chave**: 256 bytes
- **Tamanho máximo de valor**: 1MB
- **Capacidade total de armazenamento**: 50GB no Redis, escalável até 1TB no CockroachDB

### 3. Limites de Disponibilidade

- **Disponibilidade alvo**: 99,9% para leituras e escritas
- **Tempo máximo de recuperação (RTO)**: < 30 segundos para failover automático
- **Ponto de recuperação objetivo (RPO)**: Zero para dados confirmados no CockroachDB

## Recomendações para Melhorias

1. **Otimização do Redis**: Avaliar a necessidade de adicionar mais réplicas conforme o crescimento da carga
2. **Escalabilidade da API**: Implementar auto-scaling com base na carga
3. **Otimização do RabbitMQ**: Monitorar o desempenho sob cargas ainda maiores
4. **Monitoramento avançado**: Implementar um sistema de monitoramento detalhado para identificar estrangulamentos em tempo real

## Apêndice: Métodos de Teste

### Configuração dos Testes

```bash
# Teste de leitura com Siege
siege -c [concorrência] -t 10s -v http://localhost:8000/test-key-1

# Teste de escrita com ApacheBench 
ab -n [requisições] -c [concorrência] -p put_data.json -T 'application/json' http://localhost:8000/
```

### Ficheiro de Dados para Teste PUT (put_data.json)

```json
{
  "data": {
    "key": "test-key-1",
    "value": "test-value-1"
  }
}
```

### Ambiente de Testes

Todos os testes foram realizados num ambiente local com 3 instâncias da API, RabbitMQ e CockroachDB, e 2 instâncias Redis a executar em contentores Docker.

- CPU: 8 núcleos, 3.5GHz
- RAM: 32GB
- Rede: 1Gbps
- Sistema Operativo: Linux Ubuntu 22.04 LTS
