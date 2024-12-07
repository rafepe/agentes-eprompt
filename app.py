from guardrails import Guard
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Optional
import json

load_dotenv()

class ItemVinculado(BaseModel):
    seq: int = Field(description="Sequencial do item")
    cod_item: str = Field(description="Código do produto")
    desc_item: str = Field(description="Descrição do Item")
    qt_item: float = Field(description="Quantidade")
    valor_un: float = Field(description="Valor unitário")
    valor_total: float = Field(description="Valor Total do Item")
    forma_vinculacao: str = Field(description="Forma como foi vinculado o item da lista 01 com o item da lista 02 (Regra 00 | Regra 01 | Regra 02 | Regra 03)")

class ItemLista01(BaseModel):
    chv_nfe: str = Field(description="Chave da nota fiscal")
    seq: int = Field(description="Sequencial do item")
    cod_item: str = Field(description="Código do produto")
    desc_item: str = Field(description="Descrição do Item")
    qt_item: float = Field(description="Quantidade")
    valor_un: float = Field(description="Valor unitário")
    valor_total: float = Field(description="Valor Total do Item")
    vinculados: Optional[List[ItemVinculado]] = Field(description="Lista de itens vinculados da Lista 02")

class ModelReturn(BaseModel):
    itens_lista_01: List[ItemLista01] = Field(description="Lista de itens da Lista 01 com os dados vinculados da lista 02")

def analisar_vinculacao(df_efd, df_xml):
    
    prompt_analise = """
	Realize a vinculação dos itens da lista 01: <dadosEfd>"""+df_efd+"""</dadosEfd> \n
    com os da lista 02: <dadosXml>"""+df_xml+"""</dadosXml>. \n

    As informações na lista 01 e 02 estão separadas por pipe |, sendo a primeira linha o cabeçalho descritivo do que é cada informação.

    Para vinculação considere as seguintes regras: \n
    <regra 01>
        Faça a vinculação pela similaridade considerando apenas o campo 'Descrição' da lista 01 com a lista 02.
        Não pode existir outra ocorrência com a mesma similaridade.
    </regra 01>
    <regra 02>
        Faça a vinculação pela aproximação do 'Valor Total', considerando o percentual da diferença entre o valor da lista 01 com o valor da lista 02.
        Para calcular o percentual, siga as instruções do <exemplo>
        <exemplo>Subtraia o valor total do item 2 do valor total do item 1 (100 - 99), desconsidere o sinal de negativo, 
        e divida o resultado pelo valor total do item 1 (1 / 100 = 0,01) e multiplique por 100 (0,01 x 100 = 1). 
        </exemplo>
        Se resultado for menor que 2 (2%) faça a vincuação, desde que não tenha outro item com uma aproximação menor ou igual.
    </regra 02>
    <regra 03>
        Passo 1: Verifique se a lista 01 possui a mesma quantidade de itens da lista 02. Caso as listas tenham quantidade diferentes,
        selecione a lista que possui mais itens e faça o seguinte:
            - Para fins de calculo na etapa 2, some o valor total dos itens que possuirem a mesma descrição, e considere esse valor para o passo 2,
            por exemplo, o item 01 possui um valor de 100 e o item 02 um valor de 50, para o passo 2, considere para esses dois itens o valor de 150. 
       Passo 2: Aplique a regra 02 desconsideração a margem de aproximação de 5%, vinculando os itens pelo valor mais aproximado. Para desempate aplique a regra 01.     
    </regra 03>

    Para realizar a vinculação execute as seguintes etapas:
    <etapa 1>
        Para cada item da lista 01 aplique a regra 01 para todos os itens da lista 02 que ainda não tenham sido vinculados.
        Ao realizar a vinculação, retire da lista 01 e da lista 02 o item que vinculado.
        Caso a lista 01 ou lista 02 tenha apenas um item sem resolução, realize a vinculação desses itens e considere como resolução a Regra 00.
    </etapa 1>
    <etapa 2>
        Para cada item da lista 01 que não tenha sido resolvido na regra 01, aplique a regra 02 para todos os itens da lista 02 que ainda não tenham sido vinculados.
        Ao realizar a vinculação, retire da lista 01 e da lista 02 o item que foi vinculado.
        Caso a lista 01 ou lista 02 tenha apenas um item resolução, realize a vinculação desses itens e considere como resolução a Regra 00.
    </etapa 2>
    <etapa 3>
        Para cada item da lista 01 que não tenha sido resolvido nas etapas anteriores, aplique a regra 03 para todos os itens da lista 02 que ainda não tenham sido vinculados.
        Ao realizar a vinculação, retire da lista 01 e da lista 02 o item que vinculado.
        Caso a lista 01 ou lista 02 tenha apenas um item resolução, realize a vinculação desses itens e considere como resolução a Regra 00.
    </etapa 3>
    <etapa 4>
        Execute a etapa 3 até que todos os itens da lista 1 e da lista 2 tenham vinculação.
    </etapa 4>
    \n  

    ${gr.complete_json_suffix_v2}
    """
    guard = Guard.for_pydantic(output_class=ModelReturn)

    res = guard(
        model="gpt-4o-mini-2024-07-18",
        messages=[{
            "role": "user",
            "content": prompt_analise
        }]
    )
    formatted_json = json.dumps(res.validated_output, indent=4, ensure_ascii=False)
    print(formatted_json)



df_efd = """
Chave NFE|Seq|Código do Item|Descrição|Quantidade|Valor UN|Valor Total
'31240161365557000110550010009047751102632318'|1|000001|MANTEIGA AVIAÇÃO TABL.S/S C/24|24|292,95|7030,8
'31240161365557000110550010009047751102632318'|2|000007|MANTEIGA AVIAÇÃO TABL.C/S C/24|60|284,58|17074,8
'31240161365557000110550010009047751102632318'|3|000002|MANTEIGA AVIAÇÃO LATA  C/S C/30|30|268,32|8049,6
'31240161365557000110550010009047751102632318'|4|000004|MANTEIGA AVIAÇÃO POTE S/S C/48|480|189,42|90921,6
'31240161365557000110550010009047751102632318'|5|000008|MANTEIGA AVIAÇÃO POTE C/S C/24|360|164,25|59130
'31240161365557000110550010009047751102632318'|6|000011|DOCE LEITE AVIAÇÃO PT|240|21,42|5140,8
'31240161365557000110550010009047751102632318'|7|001005|REQUEIJÃO COPO AVIAÇÃO ERVAS FINAS|1|147,36|147,36""" 

df_xml = """
Chave NFE|Seq|Código do Item|Descrição|Quantidade|Valor UN|Valor Total
'31240161365557000110550010009047751102632318'|1|R-001|REQUEIJAO AVIACAO ERVAS F 180G|1|147,36|147,36
'31240161365557000110550010009047751102632318'|2|M-001|MANT AVIACAO TAB 24X100G C/S|60|284,58|17074,8
'31240161365557000110550010009047751102632318'|3|M-002|MANT AVIACAO POTE 24X500G C/S|360|164,25|59130
'31240161365557000110550010009047751102632318'|4|M-004|MANT AVIACAO LATA 30 X 200G|30|268,32|8049,6
'31240161365557000110550010009047751102632318'|5|M-006|MANT AVIACAO POTE 48X200G S/S|480|189,42|90921,6
'31240161365557000110550010009047751102632318'|6|D-001|DOCE LEITE AVIACAO PT 400G|240|21,42|5140,8
'31240161365557000110550010009047751102632318'|7|M-007|MANT AVIACAO POTE 24X200G S/S|24|292,95|7030,8"""


analisar_vinculacao(df_efd, df_xml)