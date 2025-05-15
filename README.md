# Sistema de Arquivos Distribuído com Pyro5 (Python Remote Objects)

Este projeto implementa um **sistema de arquivos distribuído** utilizando a biblioteca **Pyro5**, que permite a chamada remota de métodos entre cliente e servidor. Inspirado no funcionamento básico de sistemas de arquivos, a aplicação permite ao usuário **listar diretórios**, **copiar arquivos** e **remover arquivos** no servidor remoto por meio de comandos interativos via terminal.

---

## Componentes Principais

- **Servidor:** hospeda os métodos do sistema de arquivos e executa operações reais no sistema de arquivos local do servidor a partir o diretório **~/tmp/SERVER**.
- **Cliente:** conecta-se ao servidor, envia comandos no estilo Unix (`ls`, `cp`, `rm`) e exibe o resultado das operações para o usuário.

---

## Funcionalidades Disponíveis

O sistema implementa as seguintes funcionalidades acessíveis via terminal no cliente:

### `ls <diretório>`
Lista o conteúdo de um diretório remoto.  
Exemplo:
```bash
ls .
```

### `cp <origem> <destino>`
Copia arquivos locais para um diretório remoto no servidor ou copia arquivos do servidor remoto para a sua máquina (**dependendo se a origem ou destino comeca com "remoto:"**).  
O envio é feito em blocos de 64 KB com detecção de fim de arquivo.
Exemplo:
```bash
cp ./video.mp4 ./teste
```

### `rm <arquivo1> <arquivo2> ...`
Remove arquivos localizados no sistema remoto.  
Exemplo:
```bash
rm arquivo1.txt
```

---

## Requisitos

- Python 3.x
- Biblioteca Pyro5 instalada

Instale o Pyro5 com o comando:

```bash
pip install Pyro5
```

---

## Como Executar

### 1. Inicie o **Name Server** do Pyro5

O **Name Server** permite o registro e localização de objetos remotos.  
Este passo deve ser executado **antes** do servidor.

Abra um terminal e execute:
```bash
python3 -m Pyro5.nameserver
```

Esse comando inicia o name server na porta padrão (9090).  
Deixe essa janela aberta enquanto o sistema estiver rodando.

---

### 2. Execute o **Servidor do Sistema de Arquivos**

Abra um novo terminal e execute o arquivo `servidor.py`:
```bash
python3 servidor.py
```

Este servidor irá:
- Criar uma instância da classe `Server`.
- Expor os métodos `listar`, `copy` e `remover` para acesso remoto.
- Registrar o objeto no Name Server com o nome `"sistema.arquivos"`.

---

### 3. Execute o **Cliente do Sistema de Arquivos**

Abra um terceiro terminal e execute o cliente:
```bash
python3 client.py
```

Você verá o seguinte menu:

```
=== Sistema de Arquivos ===
ls <diretório>
cp <origem> <destino>
rm <arquivo1> <arquivo2> ...
0. SAIR
```

Você poderá digitar comandos para manipular os arquivos no servidor.

---

## Detalhes Técnicos

### Comunicação Cliente-Servidor

- O servidor utiliza `@Pyro5.api.expose` para tornar os métodos acessíveis remotamente.
- O cliente localiza o objeto `"sistema.arquivos"` registrado no Name Server e se conecta a ele usando um **proxy remoto**.
- A comunicação usa o **serializador "marshal"** para melhor desempenho com objetos simples como bytes e strings.

### Transferência de Arquivos

- Os arquivos são lidos em blocos de 64 KB.
- Cada bloco é enviado através de chamadas consecutivas ao método `copy()`.
- O fim do arquivo é sinalizado por um bloco vazio (`b''`), permitindo saber quando encerrar a escrita.

### Remoção de Arquivos

- A operação de remoção recebe uma lista de caminhos de arquivos.
- O servidor itera sobre cada um, tenta apagar e retorna um log indicando o sucesso ou erro para cada um.

---

## Estrutura dos Arquivos

- `servidor.py`: código do servidor Pyro5 com os métodos `listar`, `copy` e `remover`.
- `client.py`: código do cliente que envia comandos e interage com o servidor remotamente.

---

## Encerrando a Aplicação

1. No cliente, digite `0` para sair.
2. Encerre o servidor com `Ctrl+C`.
3. Finalize o Name Server com `Ctrl+C`.
