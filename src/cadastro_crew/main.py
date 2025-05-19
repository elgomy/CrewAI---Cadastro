#!/usr/bin/env python
import sys
import warnings
from textwrap import dedent
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path # Adicionado para manipulação de caminhos

from .crew import CadastroCrew
from .tools import SupabaseDocumentContentTool # Importar a nova ferramenta

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ID do projeto Supabase (deve ser o 'id' alfanumérico, não o 'name')
SUPABASE_PROJECT_ID = os.getenv("SUPABASE_PROJECT_ID", "aguoqgqbdbyipztgrmbd") # Usar o ID correto

# Nome da configuração do checklist na tabela app_configs
CHECKLIST_CONFIG_NAME = "checklist_cadastro_pj"
CLIENT_DOC_CONTRATO_NAME = "4- CONTRATO SOCIAL AD PRODUTOS E SERVIÇOS.pdf"
# Adicione outros nomes de documentos do cliente aqui se necessário
# CLIENT_DOC_CNPJ_NAME = "1- CNPJ.pdf"

def get_checklist_from_app_configs(project_id: str, config_name: str) -> str:
    """
    Obtém o conteúdo do checklist da tabela 'app_configs' no Supabase.
    Esta função simula a necessidade de uma chamada a Supabase, idealmente usando
    uma biblioteca cliente ou uma ferramenta MCP configurada.
    Para este exemplo, vamos hardcodear a lógica de como se faria com mcp_supabase_execute_sql
    se estivesse diretamente disponível ou se usássemos o cliente python supabase.
    """
    print(f"INFO: Tentando obter o checklist \'{config_name}\' da tabela app_configs.")
    
    # Esta é uma representação simplificada. Em um cenário real com MCP,
    # você chamaria algo como:
    # from some_mcp_library import mcp_supabase_execute_sql
    # response = mcp_supabase_execute_sql(project_id=project_id, query=f"SELECT content FROM app_configs WHERE config_name = \'{config_name}\' LIMIT 1;")
    # e depois parsearia a resposta.
    # Como não posso chamar mcp_supabase_execute_sql diretamente daqui sem a tool_code,
    # e para manter o main.py executável de forma independente para testes locais se necessário,
    # esta função precisaria ser adaptada ou ter o cliente Supabase injetado/disponível.
    # Por simplicidade, vamos assumir que a crewAI em si (ou uma ferramenta) faria esta consulta.
    # No contexto de um script que prepara inputs para a Crew, o ideal seria usar o cliente Supabase padrão.
    
    # Simulação de falha para demonstração se o SUPABASE_URL/KEY não estiverem setados para uma chamada real.
    # Em um contexto onde este script é executado e as MCPs não estão disponíveis para ele diretamente:
    try:
        from supabase import create_client, Client
        supabase_url: str = os.environ.get("SUPABASE_URL")
        supabase_key: str = os.environ.get("SUPABASE_SERVICE_KEY") # Usar service key para ler configs
        if not supabase_url or not supabase_key:
            raise EnvironmentError("SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar definidos no .env para carregar o checklist.")
        
        supabase: Client = create_client(supabase_url, supabase_key)
        response = supabase.table('app_configs').select('content').eq('config_name', config_name).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            content = response.data[0].get('content')
            if content:
                print(f"INFO: Checklist \'{config_name}\' carregado com sucesso da app_configs. Tamanho: {len(content)}")
                return content
            else:
                raise ValueError(f"Checklist \'{config_name}\' encontrado na app_configs, mas o conteúdo está vazio.")
        else:
            raise ValueError(f"Checklist \'{config_name}\' não encontrado na tabela app_configs ou dados inacessíveis.")
            
    except ImportError:
        print("AVISO: A biblioteca \'supabase-py\' não está instalada. Não é possível carregar o checklist dinamicamente. Retornando placeholder.")
        print("Execute: pip install supabase")
        raise ValueError("Biblioteca supabase-py não instalada, não é possível carregar o checklist.")
    except EnvironmentError as e:
        print(f"ERRO DE AMBIENTE: {e}")
        raise
    except Exception as e:
        print(f"ERRO CRÍTICO ao tentar obter o checklist \'{config_name}\' da app_configs: {e}")
        raise

def run():
    """
    Função principal para configurar e executar a CadastroCrew.
    """
    print("INFO: Iniciando a execução da CadastroCrew a partir de main.py...")

    try:
        # Obter o conteúdo do checklist da tabela app_configs
        parsed_checklist_content = get_checklist_from_app_configs(SUPABASE_PROJECT_ID, CHECKLIST_CONFIG_NAME)
    except Exception as e: # Captura exceções mais genéricas da carga do checklist
        print(f"ERRO FATAL: Não foi possível carregar o checklist. {e}")
        print("Verifique a configuração do Supabase (URL, KEY) e a existência do item na tabela \'app_configs\'.")
        return # Abortar se o checklist não puder ser carregado

    # Inputs para a crew
    case_id = os.getenv('CASE_ID', 'CASO-CLIENTE-REAL-001')
    inputs = {
        'case_id': case_id,
        'documents': [
            {
                'type': 'ContratoSocial',
                'name': CLIENT_DOC_CONTRATO_NAME,
                'case_id': case_id
            },
            {
                'type': 'CNPJ',
                'name': '1- CNPJ.pdf',
                'case_id': case_id
            },
            {
                'type': 'ComprovanteEnderecoSocio',
                'name': '7- COMP ENDEREÇO SOCIO REF 062024.pdf',
                'case_id': case_id
            },
            {
                'type': 'QuadroSocietario',
                'name': '1.1- QSA.pdf',
                'case_id': case_id
            },
            {
                'type': 'DocumentoIdentificacaoSocio',
                'name': '6- CNH ATUAL.pdf',
                'case_id': case_id
            },
            {
                'type': 'CertidaoSimplificada',
                'name': '4- Certidao Simplificada - 06.2024.pdf',
                'case_id': case_id
            }
        ],
        'checklist': parsed_checklist_content, 
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'dados_pj.cnpj': os.getenv('DADOS_PJ_CNPJ_FALLBACK', ''), # Este CNPJ é para a tarefa_geracao_relatorio
        'lista_cpfs_socios': [], 
        'cpf_socio_principal': os.getenv('CPF_SOCIO_PRINCIPAL_FALLBACK', '') 
    }

    print(f"DEBUG: Inputs preparados para a CadastroCrew: {inputs}")

    cadastro_crew = CadastroCrew(inputs=inputs)
    print("INFO: Iniciando a execução do método run() do CadastroCrew...")
    try:
        resultado = cadastro_crew.run()
        print("\n---\nRESULTADO FINAL DA EXECUÇÃO DO CREW:\n")
        print(resultado)
        print("---")

        # Salvar o resultado em um arquivo Markdown
        try:
            # Determinar o diretório raiz do projeto (assumindo que main.py está em src/cadastro_crew)
            project_root = Path(__file__).resolve().parent.parent.parent 
            reports_dir = project_root / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True) # Cria o diretório se não existir

            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            file_name = f"relatorio_crew_{timestamp}.md"
            file_path = reports_dir / file_name

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Relatório da Execução da Crew - {timestamp}\\n\\n")
                f.write("## Inputs Fornecidos:\\n\\n")
                # Para não expor chaves de API ou conteúdo muito longo do checklist nos inputs do relatório
                safe_inputs_to_log = {k: v for k, v in inputs.items() if k != 'checklist'}
                safe_inputs_to_log['checklist_length'] = len(inputs.get('checklist', ''))
                
                import json
                f.write(f"```json\\n{json.dumps(safe_inputs_to_log, indent=2, ensure_ascii=False)}\\n```\\n\\n")
                f.write("## Resultado da Crew:\\n\\n")
                if isinstance(resultado, str):
                    f.write(resultado)
                else:
                    # Se o resultado não for uma string (ex: objeto complexo), converter para string
                    f.write(str(resultado))
            
            print(f"INFO: Resultado da crew salvo em: {file_path}")

        except Exception as e_save:
            print(f"AVISO: Falha ao salvar o resultado da crew em arquivo: {e_save}")

    except Exception as e:
        print(f"ERRO: Uma exceção ocorreu durante a execução da crew: {e}")
        import traceback
        traceback.print_exc()

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        CadastroCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        CadastroCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    
    try:
        CadastroCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    # Este bloco permite executar o main.py diretamente com `python -m cadastro_crew.main`
    # ou `python src/cadastro_crew/main.py` (dependendo de como PYTHONPATH está configurado)
    run()
