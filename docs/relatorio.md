# MineFleet: Middleware Distribuído para Monitoramento e Controle de Frota de Mineração

**Disciplina:** OBBGSIN.037 – Sistemas Distribuídos  
**Curso:** Bacharelado em Sistemas de Informação – IFMG  
**Aluno:** Felipe Alexandre Vieira Mendes  
**Instituição:** IFMG – Campus Ouro Branco

## 1. Introdução
Este trabalho apresenta o MineFleet, protótipo de middleware distribuído para monitoramento de uma frota de caminhões de mineração. O sistema recebe telemetria publicada por sensores simulados, coordena controladores replicados e disponibiliza operações para clientes por meio de uma API. O cenário industrial permite explorar comunicação assíncrona, replicação, tolerância a falhas e integridade das respostas.

## 2. Arquitetura e funcionamento
O broker Eclipse Mosquitto recebe mensagens MQTT dos sensores no tópico `minefleet/sensors/telemetry`. O middleware FastAPI assina esse tópico e mantém os dados mais recentes por veículo. Clientes interagem por HTTP/JSON. Para executar um comando, o middleware envia a solicitação às quatro réplicas. Cada controlador é um processo independente, possui banco SQLite próprio e registra a operação usando um identificador único. O middleware valida as assinaturas e realiza votação. Um resultado só é confirmado quando pelo menos três réplicas concordam. Após a confirmação, o middleware publica o comando no tópico MQTT destinado aos atuadores.

## 3. Replicação dos dados
Foram implementadas quatro instâncias independentes de controlador, cada uma com volume persistente e banco SQLite próprio. A mesma operação é encaminhada às quatro instâncias. O campo `operation_id` funciona como chave de idempotência: uma solicitação repetida retorna o resultado já registrado. A replicação ocorre pela execução e persistência da mesma solicitação em cada controlador, não pelo compartilhamento de um único banco.

## 4. Tolerância a falhas
O middleware exige quórum de três respostas concordantes entre quatro réplicas. Uma réplica pode ficar indisponível e as três restantes ainda podem confirmar a operação. Se apenas duas respostas válidas forem obtidas, o middleware retorna HTTP 503 e não afirma que o comando foi confirmado. A garantia depende de pelo menos três réplicas corretas, alcançáveis e independentes.

## 5. Segurança e respostas divergentes
Cada resposta contém assinatura HMAC-SHA256. Cada controlador recebe uma chave própria por variável de ambiente, e o middleware mantém o conjunto de chaves necessário à validação. Assim, uma réplica não precisa receber as chaves privadas das demais. O middleware verifica a assinatura e confere se os campos correspondem à solicitação. Respostas malformadas, com assinatura inválida ou conteúdo incompatível são descartadas antes da votação. A maioria impede que uma única réplica divergente determine o resultado.

HMAC oferece autenticação e integridade; não cifra o conteúdo e não comprova a veracidade física de uma medição. Se o segredo mestre for obtido, as assinaturas podem ser comprometidas. Em produção, os segredos devem ficar fora do código, protegidos por gerenciador de segredos, e a comunicação deve usar TLS. Também seria necessário autenticar sensores, controlar acesso aos tópicos MQTT e manter auditoria.

## 6. Testes e demonstrações
Os testes automatizados verificam que três respostas iguais atingem o quórum, duas não são suficientes, uma resposta divergente é vencida pela maioria, assinatura válida é aceita, alteração do conteúdo invalida a assinatura e chaves de réplicas diferentes não são intercambiáveis. Com Docker Compose, é possível parar uma réplica e repetir uma operação.

## 7. Limitações
O protótipo usa sensores e atuadores simulados, SQLite local por réplica e votação coordenada pelo middleware. Não implementa consenso persistente entre controladores, eleição de líder ou transações atômicas entre bancos. MQTT QoS 1 pode entregar uma mensagem mais de uma vez; atuadores reais precisariam tratar identificadores de operação de forma idempotente. A solução demonstra conceitos acadêmicos, mas não deve controlar equipamentos industriais reais.

## 8. Conclusão
O MineFleet demonstra o middleware como intermediário entre clientes e um processo distribuído. MQTT permite comunicação assíncrona com sensores e atuadores; replicação, quórum e validação HMAC oferecem mecanismos para lidar com indisponibilidade e respostas inconsistentes. Os testes permitem observar as condições de sucesso e os limites da solução.

## 9. Referências
ECLIPSE FOUNDATION. *Eclipse Mosquitto*. Disponível em: https://mosquitto.org/. Acesso em: 12 nov. 2026.

FASTAPI. *FastAPI documentation*. Disponível em: https://fastapi.tiangolo.com/. Acesso em: 12 nov. 2026.

OASIS. *MQTT Version 5.0*. Disponível em: https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html. Acesso em: 12 nov. 2026.
