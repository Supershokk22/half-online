# Half Online

> Projeto comunitário para partidas privadas entre amigos.
> **Assinado: shokk**

## Sobre

Half Online é um projeto público, não oficial e em desenvolvimento. A proposta
é oferecer uma forma simples de jogar em sala privada com duas cópias legítimas
do jogo, cada pessoa no seu próprio PC.

## Atualização atual

- Sala privada para duas pessoas.
- Presença do outro jogador no cenário.
- Controles básicos para a sala do host.
- Melhorias de estabilidade e organização.

## Como jogar

### Pré-requisitos (nos dois PCs)
1. Instale o Tailscale e entre na mesma rede.
2. Instale Python 3.10+ e `pip install "websockets>=17,<18"`.
3. Execute `INSTALAR-MOD-FASE-1.ps1` uma vez com o jogo fechado.

### Host (quem cria a sala)
1. Execute `HOSTEAR.cmd`
2. Envie seu IP Tailscale (100.x.x.x) pro amigo
3. Pronto — o jogo abre e o mod carrega sozinho

### Amigo (quem entra)
1. Execute `CONECTAR.cmd 100.x.x.x` (com o IP do host)
2. Pronto — conecta ao relay e abre o jogo automaticamente

Ambos vao direto pro hub. Naveguem ate Spar/Training e comecem a lutar.
O mod sincroniza posicao e rotacao entre os dois jogadores em tempo real.

Leia [CHANGELOG.md](CHANGELOG.md) para acompanhar as mudanças públicas.

## Aviso

Projeto independente e não oficial. Use apenas cópias legítimas do jogo e uma
rede privada entre pessoas de confiança. Recursos continuam em teste e recebem
correções conforme a comunidade reporta problemas.

## Suporte

Abra uma issue com uma descrição curta do problema, versão do jogo e os passos
para reproduzir — sem compartilhar dados pessoais.

```text
 /////   //  //   /////   //  //   //  //
//       //  //  //   //  // //    // //
 /////   //////  //   //  ///      ////
     //  //  //  //   //  // //    // //
/////    //  //   /////   //  //   //  //
```

**SHOKK**
