# IGRS25G15 - Serviço de Chamadas e Redial 2.0
Este projeto implementa uma infraestrutura de VoIP baseada em Kamailio e Twinkle, permitindo o registo de utilizadores, chamadas básicas e um utilização de serviço de Redial 2.0. 


*⚙️  Funcionalidades*

Registo e Desregisto: Gestão de utilizadores do domínio acme.operador.

+ Validação por PIN: Necessário validar o utilizador através de uma mensagem SIP para o domínio acme.pt.

+ Serviço Redial 2.0: Configuração de uma lista de destinos alternativos caso a chamada original falhe (ocupado, sem resposta ou offline).

+ Chamadas Básicas: Suporte para chamadas de voz entre Alice, Bob.

*🛠️ Estrutura do Projeto*

+ kamailio: Servidor configurado com lógica B2BUA em Python (registrar-b2bua.py).

+ twinkle alice / bob / max: Terminais de utilizador pré-configurados.

+ scripts/: Contém ficheiros .cfg e .sys para os perfis dos utilizadores.



*📋 Como Utilizar*

1. Iniciar a Infraestrutura
Docker Compose para subir os serviços:

```bash
docker-compose -f compose_tp15_b2bua.yaml up -d
```

2. Registo do utilizador
Antes de utilizar e ativar o serviço, deve ser feito o registo quer através do botão Register ou através do envio de uma SIP MESSAGE:

Destino: sip:validar@acme.pt
Conteúdo: 0000

3. Configurar o Serviço Redial 2.0
Para ativar o serviço de redial automático em caso de falha, é necessário enviar uma SIP MESSAGE para o serviço interno:

Destino: redial@acme.operador
Ativar: ACTIVATE utilizador1 utilizador2

Desativar: DEACTIVATE

4. Efetuar chamada
Basta realizar uma chamada para o destinatário e caso este não atenda, é feito um redial automático mais duas vezes
