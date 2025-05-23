# Sistema Distribuído de Armazenamento Key-Value

Este projeto implementa um sistema distribuído de armazenamento key-value, desenvolvido no âmbito da unidade curricular de Sistemas Paralelos e Distribuídos. O sistema foi concebido para ser altamente disponível, escalável e tolerante a falhas, seguindo os princípios de programação distribuída.

## Características Principais

- API REST para operações CRUD (PUT, GET, DELETE)
- Arquitetura distribuída com múltiplos nós
- Balanceamento de carga automático
- Tolerância a falhas
- Persistência de dados
- Escalabilidade horizontal
- Monitorização e health checks
- Containerização com Docker

## Requisitos do Sistema

- Docker e Docker Compose
- Sistema operativo GNU/Linux
- Mínimo de 4GB RAM disponível
- Portas 80, 8080, 5672, 15672 disponíveis

## Início Rápido

1. Clone o repositório:
```bash
git clone https://github.com/a79809/Atividade2SistemasDistribuidos.git
```

2. Execute o script de inicialização:
```bash
./start.sh
```

O sistema estará disponível em `http://localhost:80` ou `http://localhost`

## Documentação

A documentação completa do projeto está disponível na pasta `documentacao/`:

- [Manual da API](documentacao/api_manual.md) - Documentação detalhada dos endpoints e exemplos de uso
- [Guia de Instalação](documentacao/installation_guide.md) - Instruções detalhadas para instalação e configuração
- [Arquitetura do Sistema](documentacao/arquitetura.md) - Descrição da arquitetura e componentes
- [Relatório de Testes de Carga](documentacao/load_test_report.md) - Resultados e análise de performance
- [Bibliografia](documentacao/bibliography.md) - Referências e recursos utilizados

## Estrutura do Projeto

```
.
├── api/                 # Serviço de API REST
├── consumer/           # Serviço de processamento
├── nginx/             # Configuração do proxy reverso
├── envoy/             # Configuração do Load Balancer para Redis
├── documentacao/      # Documentação do projeto
├── docker-compose.yml # Configuração dos containers
└── start.sh          # Script de inicialização
```

## Endpoints da API

- `GET /{key}` - Retorna o valor associado à chave
- `PUT /` - Armazena um novo par chave-valor
- `DELETE /{key}` - Remove um par chave-valor

Para exemplos detalhados de uso, consulte o [Manual da API](documentacao/api_manual.md).
