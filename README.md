# Half Online — v2.1

> Projeto comunitário para partidas privadas entre amigos.
> **Assinado: shokk**

---

## Sobre

Half Online é um projeto público, não oficial e em desenvolvimento. A proposta
é oferecer uma forma simples de jogar em sala privada com duas cópias legítimas
do jogo, cada pessoa no seu próprio PC.

## Estado da versão

- Sala privada para duas pessoas: host, convite, entrada e limite de dois jogadores
- Confirmação de sessão antes de abrir o jogo; arquivos de uma sala antiga não ativam o lobby
- Lobby Open World automático após a conexão aceita
- Sincronização experimental de posição e rotação, com avatar remoto de lobby
- Inimigos nativos permanecem nos modos normais enquanto não houver sessão online
- Painel de diagnóstico no jogo e instalador reversível

Consulte [STATUS-TECNICO.md](STATUS-TECNICO.md) para o que foi testado e as limitações atuais.

## Como jogar

### Pré-requisitos (nos dois PCs)
1. Instale Python 3.10+ e execute: `python -m pip install "websockets>=15,<18"`
2. Execute `INSTALAR-MOD-FASE-1.ps1` uma vez com o jogo fechado
3. Tenha o `cloudflared.exe` na pasta do projeto ou na Desktop

### Host (quem cria a sala)
1. Execute `real_launcher.py` (ou `HOSTEAR.cmd`)
2. Clique **Hospedar sala** — o link público aparece em segundos
3. Envie o link para o amigo

### Amigo (quem entra)
1. Execute `real_launcher.py`
2. Cole o link no campo **URL do host**
3. Clique **Entrar na sala**

O launcher só abre o jogo após o relay aceitar a sala. Os dois entram no lobby
Open World da mesma sessão. O mod sincroniza posição e rotação em tempo real.

## Aviso

Projeto independente e não oficial. Use apenas cópias legítimas do jogo e uma
rede privada entre pessoas de confiança.

## Suporte

Abra uma issue com descrição curta do problema, versão do jogo e passos para
reproduzir.

Para instalação assistida, conexão dos dois PCs e diagnóstico da sincronização,
consulte [GUIA-PARA-IA.md](GUIA-PARA-IA.md).

## Half Open World V1

A pasta [HalfOpenWorldV1](HalfOpenWorldV1/README.md) guarda o primeiro prototipo
editavel do projeto de expansao. Ela inclui mapa, menu de teste, scripts de
geracao, bridge UE4SS experimental e um guia de continuidade para outra IA.

Estado atual: o mapa V1 abre no Half Sword por bridge, o respawn manual foi
confirmado em log e o fluxo de autoria no Unreal funciona. A integracao do menu
principal e a validacao completa de movimento, combate e fisica ainda estao em
andamento.

```text
 /////   //  //   /////   //  //   //  //
//       //  //  //   //  // //    // //
 /////   //////  //   //  ///      ////
     //  //  //  //   //  // //    // //
/////    //  //   /////   //  //   //  //
```

**SHOKK — v2.1**
