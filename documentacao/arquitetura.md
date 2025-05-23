# Diagrama de Arquitetura do Sistema 

## Visão Geral da Arquitetura

O sistema é um armazenamento de chave-valor distribuído projetado para alta disponibilidade, escalabilidade e tolerância a falhas. A arquitetura é composta por várias camadas, cada uma com sua função específica e mecanismos de redundância.
A estrutura geral da arquitetura pode ser vista no diagrama da imagem [./Imagens/ArquiteturaSistema.png]

## Fluxos de Dados 

### Operação de Leitura (GET)
1. Cliente envia requisição GET para o Nginx
2. Nginx roteia a requisição para uma instância da API no cluster
3. API tenta ler o valor do Redis via Envoy Proxy
4. Se encontrado no cache, retorna imediatamente
5. Se não encontrado, retorna 404 e contacta diretamente a base de dados

### Operação de Escrita (PUT)
1. Cliente envia requisição PUT para o Nginx
2. Nginx roteia a requisição para uma instância da API no cluster
3. API armazena o valor no Redis via Envoy Proxy
4. API envia uma mensagem para o cluster RabbitMQ
5. API retorna confirmação para o cliente
6. Um consumidor do cluster de consumidores processa a mensagem assincronamente
7. Consumidor coloca/altera o valor no cluster CockroachDB via HAProxy

### Operação de Exclusão (DELETE)
1. Cliente envia requisição DELETE para o Nginx
2. Nginx roteia a requisição para uma instância da API no cluster
3. API remove o valor do Redis via Envoy Proxy
4. API envia uma mensagem para o cluster RabbitMQ
5. API retorna confirmação para o cliente
6. Um consumidor do cluster de consumidores processa a mensagem assincronamente
7. Consumidor remove o valor do cluster CockroachDB via HAProxy

## Componentes da Arquitetura

### 1. Camada de Acesso 

- **Load Balancer (Nginx)**:
  - Distribui as requisições HTTP entre múltiplas instâncias da API no cluster
  - Fornece um ponto único de acesso para os clientes
  - Implementa health checks para garantir que apenas instâncias saudáveis recebam tráfego

- **Cluster de API REST (FastAPI)**:
  - Múltiplas instâncias da API trabalhando em paralelo
  - Cada instância expõe endpoints HTTP para operações de leitura (GET) e escrita (PUT, DELETE)
  - Gerencia conexões com o cache Redis via Envoy e com o cluster RabbitMQ
  - Implementa tratamento de erros e retentativas para garantir resiliência

### 2. Camada de Cache (Redis HA)

- **Envoy Proxy**:
  - Atua como balanceador e proxy para o cluster Redis
  - Gerencia a disponibilidade das instâncias Redis através de health checks
  - Redireciona o tráfego para instâncias saudáveis em caso de falha

- **Cluster Redis**:
  - **Redis Master**: Instância principal que aceita operações de leitura e escrita
  - **Redis Replica**: Instância secundária sincronizada com o master para alta disponibilidade
  - Comunicação bidirecional para replicação e failover automático
  - Em caso de falha da Master, a replica poderá ser promovida a Master

### 3. Camada de Envio de Mensagens (RabbitMQ)

- **Cluster RabbitMQ**:
  - Implementa o padrão de envio de mensagens para processamento assíncrono com consumer
  - Garante a durabilidade das mensagens mesmo em caso de falha
  - Possui alta disponibilidade através de um cluster com múltiplos nós
  - Recebe mensagens das APIs para operações de escrita (PUT, DELETE)

### 4. Camada de Processamento (Consumidores)

- **Cluster de Consumidores**:
  - Múltiplas instâncias de consumidores podendo processar mensagens em paralelo
  - Consomem mensagens do cluster RabbitMQ
  - Executam operações de escrita no banco de dados via HAProxy
  - Escalam horizontalmente para aumentar a capacidade de processamento

### 5. Camada de Armazenamento de Dados (CockroachDB)

- **HAProxy para CockroachDB**:
  - Atua como load balancer para o cluster CockroachDB
  - Distribui as conexões entre os nós usando algoritmos como round-robin
  - Implementa health checks para detectar falhas nos nós
  - Redireciona conexões para nós saudáveis em caso de falha

- **Cluster CockroachDB**:
  - Banco de dados distribuído com múltiplos nós que funciona como um único sistema
  - Usa o protocolo de consenso Raft para:
    - Replicação síncrona de dados entre nós
    - Manter consistência forte (serializable)
    - Coordenar eleição de líder
  - Mantém disponibilidade mesmo com falha de um nó (N-1)
  - Permite escalabilidade horizontal adicionando novos nós
  - Processo simplificado:
    - Escrita: Cliente envia para qualquer nó → maioria confirma → mudança aplicada
    - Leitura: Cliente lê de qualquer nó → dados consistentes retornados 