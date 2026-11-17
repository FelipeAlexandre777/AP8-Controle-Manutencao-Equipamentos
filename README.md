# MineFleet — Middleware Distribuído para Monitoramento de Frota de Mineração

Projeto acadêmico do 1º Trabalho Prático de Sistemas Distribuídos (OBBGSIN.037).

## Objetivo
Demonstrar middleware que integra telemetria MQTT, controladores replicados, clientes HTTP e atuadores. São quatro réplicas independentes; o middleware exige três respostas válidas e concordantes para confirmar uma operação.

## Arquitetura
- Mosquitto: broker MQTT.
- Sensor simulado: publica em `minefleet/sensors/telemetry`.
- Middleware FastAPI: recebe telemetria, coordena comandos e oferece API ao cliente.
- Quatro controladores: processos independentes, cada um com SQLite próprio.
- Atuador simulado: assina `minefleet/actuators/commands`.
- Quórum: 3 de 4 respostas válidas e idênticas.
- Integridade: HMAC-SHA256 com chave derivada por réplica.

## Executar
Requisitos: Docker Desktop com Compose, VS Code e Git.

No terminal do VS Code, dentro da pasta:
```powershell
docker compose up --build
```
API: http://localhost:8000 | Documentação: http://localhost:8000/docs | MQTT: localhost:1883

Em outros terminais:
```powershell
docker compose run --rm sensor
docker compose run --rm actuator
```

## Testes
```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Exemplos
```powershell
curl.exe http://localhost:8000/status
curl.exe http://localhost:8000/telemetry
```
Comando:
```powershell
$body = '{"vehicle_id":"CAM-042","action":"REDUCE_SPEED","reason":"Temperatura elevada","operation_id":"op-0001"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/commands -ContentType "application/json" -Body $body
```

## Demonstrações
1. Operação normal: observar quórum 3/4 ou 4/4.
2. Queda de uma réplica: `docker compose stop controller4`; repetir o comando.
3. Queda de duas réplicas: parar mais uma; middleware deve retornar HTTP 503.
4. Resposta divergente: testes simulam voto divergente e mostram que uma réplica não vence a maioria.
5. Integridade: testes verificam HMAC.

## Limites
A votação 3-de-4 tolera até uma réplica arbitrariamente defeituosa, sob a hipótese de que as outras três são independentes e corretas. HMAC autentica origem e integridade, mas não comprova que a medição física é verdadeira. O protótipo não é um sistema certificado para controle industrial real.
