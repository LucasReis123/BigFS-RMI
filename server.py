import Pyro5.api
import math
import shutil
import glob
import os


@Pyro5.api.expose
class Server:
    def __init__(self):
        """
            Inicializa o servidor de arquivos.

            Autor: Lucas Reis

            Cria o diretório base em ~/tmp/SERVER, caso não exista e inicializa a
            lista de arquivos abertos para escrita.
        """

        usuario = os.getlogin()
        self.base_dir = os.path.join("/home", usuario, "tmp/SERVER")

        if not os.path.exists(self.base_dir):
            os.makedirs(os.path.expanduser(self.base_dir), exist_ok=True)

        self.openned_files = {}


    def listar(self, args):
        """
            Lista arquivos em um diretório.

            Autor: Lucas Reis

            Parâmetros:
                args (list): Lista contendo 0 ou 1 argumento.
                            - Se vazia, lista o diretório base.
                            - Se contiver um caminho, lista o conteúdo do caminho fornecido.

            Retorna:
                str: Lista de arquivos separados por nova linha ou mensagens de erro.
        """

        # Listar arquivos no diretório atual
        if len(args) == 0:
            dir = self.abs_path()
            files = os.listdir(dir)
            response = '\n'.join(files)

        # Listar arquivos em um diretório específico
        elif len(args) == 1:
            dir = self.abs_path(args[0])
            try:
                files = os.listdir(f"{dir}")
                response = '\n'.join(files)

            except FileNotFoundError:
                response = "Diretório não encontrado"
        
        # Agumentos inválidos
        else:
            response = "Argumentos Errados"

        return response
    
    def copy(self, data, destination, filename):
        """
            Método para enviar/receber arquivos com tratamento completo.
            
            Parâmetros:
                data (bytes): 
                    - Se enviando: bloco de dados
                    - Se recebendo: b'' para solicitar próximo bloco
                destination (str): Caminho de destino ou origem
                filename (str): 
                    - Se enviando: nome do arquivo destino
                    - Se recebendo: "SOLICITA_DADOS" para modo recebimento
            
            Comportamento:
                - Verifica se arquivo já existe no modo envio
                - Gerencia corretamente arquivos grandes (>64KB)
                - Mantém estado entre chamadas para transferências grandes
        """
        filepath = os.path.join(self.base_dir, destination, filename if filename != "SOLICITA_DADOS" else "")
        
        # Modo envio (cliente -> servidor)
        if filename != "SOLICITA_DADOS":
            # Verifica se é o primeiro bloco do arquivo
            if filepath not in self.openned_files:
                # Verifica se arquivo já existe
                if os.path.exists(filepath):
                    raise FileExistsError(f"Arquivo {filepath} já existe")
                
                # Cria diretório se não existir
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                # Abre o arquivo e armazena o handle
                self.openned_files[filepath] = open(filepath, "wb")
            
            # Se recebeu bloco vazio, finaliza transferência
            if data == b'':
                if filepath in self.openned_files:
                    self.openned_files[filepath].close()
                    del self.openned_files[filepath]
                return
            
            # Escreve o bloco recebido
            self.openned_files[filepath].write(data)
            return
        
        # Modo recebimento (servidor -> cliente)
        else:
            filepath = os.path.join(self.base_dir, destination)
            
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Arquivo {filepath} não encontrado")

            # Se é a primeira solicitação, abre o arquivo
            if filepath not in self.openned_files:
                self.openned_files[filepath] = open(filepath, "rb")

            f = self.openned_files[filepath]
            block = f.read(65536)

            # Se chegou ao final do arquivo
            if not block:
                f.close()
                del self.openned_files[filepath]
                return b''

            return block
        

    def remover(self, arquivos):
        """
            Remove arquivos ou diretórios especificados.

            Autor: Lucas Reis

            Parâmetros:
                arquivos (list): Lista de caminhos relativos a serem removidos.

            Retorna:
                str: Mensagens de sucesso ou erro para cada arquivo.
        """

        mensagens = []
        for arquivo in arquivos:
            caminho = self.abs_path(arquivo)

            if os.path.exists(caminho):
                try:
                    if os.path.isdir(caminho):
                        shutil.rmtree(caminho)
                        mensagens.append(f"Diretório removido: {arquivo}")
                    else:
                        os.remove(caminho)
                        mensagens.append(f"Arquivo removido: {arquivo}")
                except Exception as e:
                    mensagens.append(f"Erro ao remover {arquivo}: {e}")
            else:
                mensagens.append(f"Arquivo não encontrado: {arquivo}")

        return '\n'.join(mensagens)
    
    def abs_path(self, path=""):
        """Retorna o caminho absoluto dentro da pasta tmp"""
        return os.path.abspath(os.path.join(self.base_dir, path))

def main():
    """
        Inicia o servidor Pyro5 e registra o serviço no Name Server.

        Autor: Lucas Reis

        Comportamento:
            - Cria a instância do servidor.
            - Inicializa o daemon Pyro5.
            - Registra o servidor no Name Server com o nome "sistema.arquivos".
            - Inicia o loop de escuta.
    """
    sistema_arquivos = Server()
    
    daemon = Pyro5.api.Daemon()

    try:
        ns = Pyro5.api.locate_ns()
    except Pyro5.errors.NamingError:
        print("Erro: Não foi possível localizar o nameserver.")
        return

    
    uri = daemon.register(sistema_arquivos)
    ns.register("sistema.arquivos", uri)

    print("Servidor do sistema de arquivos inicializado...")
    daemon.requestLoop()

if __name__ == "__main__":
    main()