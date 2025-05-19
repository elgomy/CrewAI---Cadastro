#!/usr/bin/env python
import sys
import warnings
from textwrap import dedent
from datetime import datetime
import os
from dotenv import load_dotenv

from .crew import CadastroCrew
from .tools import SupabaseDocumentContentTool # Importar a nova ferramenta

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Nomes dos arquivos conforme definido pelo usuário
CHECKLIST_DOCUMENT_NAME = "checklist.pdf"
CLIENT_DOC_CONTRATO_NAME = "4- CONTRATO SOCIAL AD PRODUTOS E SERVIÇOS.pdf" # Ajustar se o nome for diferente
# Adicione outros nomes de documentos do cliente aqui se necessário
# CLIENT_DOC_CNPJ_NAME = "1- CNPJ.pdf"

def get_document_content_from_supabase(document_name: str) -> str:
    """
    Obtém o conteúdo textual de um documento da tabela 'documents' no Supabase.
    """
    print(f"INFO: Tentando obter o conteúdo do documento: '{document_name}' do Supabase.")
    try:
        # Poderíamos instanciar a ferramenta aqui, mas para evitar criar muitas instâncias
        # e para melhor separação, idealmente o cliente supabase seria gerenciado de forma mais central.
        # Por simplicidade neste script de teste, vamos criar uma instância ad-hoc.
        # Em um app real, você poderia ter um singleton ou injetar o cliente Supabase.
        tool = SupabaseDocumentContentTool()
        content = tool._run(document_name=document_name)
        if content.startswith("Error:"):
            print(f"AVISO: Não foi possível obter conteúdo para '{document_name}' do Supabase. Detalhe: {content}")
            # Para o checklist, é crítico. Para outros, poderia ser opcional.
            if document_name == CHECKLIST_DOCUMENT_NAME:
                 raise ValueError(f"Falha crítica ao carregar o checklist '{document_name}': {content}")
            return "CONTEÚDO NÃO ENCONTRADO OU ERRO"
        return content
    except Exception as e:
        print(f"ERRO CRÍTICO ao tentar obter '{document_name}' do Supabase: {e}")
        if document_name == CHECKLIST_DOCUMENT_NAME:
            raise # Re-lança a exceção se for o checklist, pois é essencial
        return "ERRO AO CARREGAR DOCUMENTO"

def run():
    """
    Função principal para configurar e executar a CadastroCrew.
    """
    print("INFO: Iniciando a execução da CadastroCrew a partir de main.py...")

    try:
        # Obter o conteúdo do checklist do Supabase
        parsed_checklist_content = get_document_content_from_supabase(CHECKLIST_DOCUMENT_NAME)
    except ValueError as e:
        print(f"ERRO: {e}")
        return # Abortar se o checklist não puder ser carregado

    # Inputs para a crew, agora com nomes de documentos para consulta via SupabaseDocumentContentTool
    inputs = {
        'case_id': os.getenv('CASE_ID', 'CASO-CLIENTE-REAL-001'),
        'documents': [
            # {
            #     'type': 'CNPJ',
            #     'name': CLIENT_DOC_CNPJ_NAME # Nome do arquivo na tabela 'documents' do Supabase
            # },
            {
                'type': 'ContratoSocial',
                'name': CLIENT_DOC_CONTRATO_NAME # Nome do arquivo na tabela 'documents' do Supabase
            }
            # Adicione mais documentos do cliente conforme necessário
        ],
        'checklist': parsed_checklist_content, 
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'dados_pj.cnpj': os.getenv('DADOS_PJ_CNPJ_FALLBACK', ''),
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
