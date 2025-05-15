import Pyro5.api
import os

def mostrar_menu():
    """
        Limpa a tela do terminal e exibe o menu principal com as opções 
        disponíveis ao usuário.
        
        Autor: Seu Nome Aqui
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n=== Sistema de Arquivos ===")
    print("ls <diretório>")
    print("cp <origem> <destino>")
    print("rm <arquivo1> <arquivo2> ...")
    print("0. SAIR")

class Client:
    """
        Cliente que se conecta a um servidor remoto de sistema de arquivos via Pyro5.
        
        Responsável por enviar comandos como listar, copiar e remover arquivos.
        
        Autor: Lucas Reis
    """
    def __init__(self):
        """
            Inicializa o cliente, localiza o Name Server do Pyro5 e estabelece uma conexão 
            com o objeto remoto registrado como "sistema.arquivos".
            
            Define também o serializador para 'marshal' para eficiência.
            
            Autor: Lucas Reis
        """

        # Localiza o nameserver Pyro5
        ns = Pyro5.api.locate_ns()
        
        # Obtém a URI do servidor do sistema de arquivos
        sys_uri = ns.lookup("sistema.arquivos")  # Nome registrado no servidor Pyro5

        # Conecta ao servidor e cria um proxy para o objeto remoto
        self.sistema_arquivos = Pyro5.api.Proxy(sys_uri)
        self.sistema_arquivos._pyroSerializer = "marshal"

    def copy(self, args):
        """
            Copia arquivos entre cliente e servidor.
            
            Sintaxe: cp <origem> <destino>
            - Se origem começar com "remoto:", o cliente recebe do servidor
            - Se destino começar com "remoto:", o cliente envia para o servidor
            - Caso contrário, retorna erro
            
            Parâmetros:
                args (str): String contendo origem e destino separados por espaço
                
            Exceções:
                ValueError: Caso os argumentos não sigam o formato especificado
                Exception: Caso ocorra erro durante a transferência
                
            Autor: Lucas Reis
        """

        # Converte args para string se for lista
        if isinstance(args, list):
            args = ' '.join(args)
        
        if not args.strip():
            return "Uso correto: cp <origem> <destino>"
        
        parts = args.strip().split()
        if len(parts) != 2:
            return "Erro: Você deve especificar exatamente 2 argumentos (origem e destino)"
        
        source, destination = parts
        source_remote = source.startswith("remoto:")
        destination_remote = destination.startswith("remoto:")
        
        if source_remote and destination_remote:
            return "Erro: Ambos origem e destino não podem ser remotos"
        elif not source_remote and not destination_remote:
            return "Erro: Pelo menos um dos argumentos deve ser remoto (começar com 'remoto:')"
        
        print("\n")
        
        if destination_remote:
            # Modo envio para servidor (origem local, destino remoto)
            local_file = source
            remote_path = destination[7:]  # Remove "remoto:"
            
            if not os.path.exists(local_file):
                return f"Erro: Arquivo local {local_file} não encontrado"
            
            filename = os.path.basename(local_file)
            with open(local_file, "rb") as f:
                try:
                    while True:
                        data = f.read(65536)

                        if not data:
                            # Envia um bloco vazio para indicar fim do arquivo
                            self.sistema_arquivos.copy(b'', remote_path, filename)
                            return f"Arquivo {filename} copiado com sucesso"

                        # Envia um bloco
                        self.sistema_arquivos.copy(data, remote_path, filename)

                except Exception as e:
                    return f"Erro durante envio: {e}"
        else:
            # Modo recebimento do servidor (origem remota, destino local)
            remote_file = source[7:]  # Remove "remoto:"
            local_path = os.path.abspath(destination)

            # Verifica se arquivo já existe localmente
            if not os.path.exists(local_path):
                os.makedirs(local_path, exist_ok=True)
            
            base_name = os.path.basename(remote_file)
            local_path = os.path.join(local_path, base_name)
            try:
                with open(local_path, "wb") as f:
                    while True:
                        # Envia blocos vazios para solicitar dados do servidor
                        data = self.sistema_arquivos.copy(b'', remote_file, "SOLICITA_DADOS")
                        if data == b'':
                            return f"Arquivo {remote_file} copiado com sucesso"
                        f.write(data)

            except Exception as e:
                return f"Erro durante recebimento: {e}"

    def update(self):
        """
            Laço principal que executa o menu interativo para o usuário.
            
            Interpreta comandos digitados e chama as funções correspondentes: 
            - `ls` para listar arquivos
            - `cp` para copiar arquivos
            - `rm` para remover arquivos
            - `0` para sair
            
            Também trata erros de entrada e exibe mensagens apropriadas.
            
            Autor: Lucas Reis
        """
        while True:
            opcao = mostrar_menu()
            cmd = input("\n$").strip()

            if not cmd:
                continue

            parts = cmd.split()
            command = parts[0]
            args = parts[1:]
            
            if opcao == '0':
                print("Saindo...")
                break
            
            try:
                if command in ['listar', 'ls']:

                    if len(args) >= 2:
                        print("Uso correto: ls <diretório>")
                    else:
                        resultado = self.sistema_arquivos.listar(args)
                        print(f"\n{resultado}")
                    
                elif command in ['copy', 'cp']:
                    resultado = self.copy(args)
                    print(f"\n{resultado}")

                elif command in ['remover', 'rm']:
                    if len(args) == 0:
                        print("\nUso correto: rm <arquivo1> <arquivo2> ...")
                    else:
                        resultado = self.sistema_arquivos.remover(args)
                        print(f"\n{resultado}")
                    
                else:
                    print("Opção inválida! Tente novamente.")
                    
            except ValueError as ve:
                print(f"Erro: {ve}")
            except Exception as e:
                print(f"Ocorreu um erro: {e}")

            input("\nPressione ENTER para continuar...")



def main():
    """
        Função principal que instancia o cliente e inicia o loop de atualização.
        
        Autor: Lucas Reis
    """
    client = Client()
    client.update()

if __name__ == "__main__":
    main()