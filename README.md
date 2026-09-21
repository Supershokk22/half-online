# Half Online — v2.0 PRO

> Projeto comunitário para partidas privadas entre amigos.
> **Assinado: shokk**

---

## ⚔ VERSÃO 2.0 PRO ⚔

## Sobre

Half Online é um projeto público, não oficial e em desenvolvimento. A proposta
é oferecer uma forma simples de jogar em sala privada com duas cópias legítimas
do jogo, cada pessoa no seu próprio PC.

## O que há de novo na v2.0 PRO

- Criação de sala pública via Cloudflare Tunnel funcionando corretamente
- Relay rodando in-process — sem dependência de subprocesso externo
- UI renovada: status em tempo real, link gerado automaticamente
- Lobby visual para criar, guardar e entrar em salas por convite
- Correção de bug crítico onde o link público nunca era gerado
- Estabilidade geral e organização do código

## Como jogar

### Pré-requisitos (nos dois PCs)
1. Instale Python 3.10+ e execute: `pip install "websockets>=17,<18"`
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

Ambos abrem o Half Sword pela Steam, vão pro Spar/Training e começam a lutar.
O mod sincroniza posição e rotação em tempo real.

## Aviso

Projeto independente e não oficial. Use apenas cópias legítimas do jogo e uma
rede privada entre pessoas de confiança.

## Suporte

Abra uma issue com descrição curta do problema, versão do jogo e passos para
reproduzir.

```text
 /////   //  //   /////   //  //   //  //
//       //  //  //   //  // //    // //
 /////   //////  //   //  ///      ////
     //  //  //  //   //  // //    // //
/////    //  //   /////   //  //   //  //
```

**SHOKK — v2.0 PRO**
