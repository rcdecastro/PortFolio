
import pandas as pd
import numpy as np
import io
import os
import math
from itertools import combinations

#priorizar os containteres a serem recebidos
#avaliar a ocupação do CD
#Quantos consigo receber no mesmo dia
#inclusão no modelo a previsão de venda

#Função que retorna se há elementos que se repetem em duas listas
def common_member(a, b):
    a_set = set(a)
    b_set = set(b)
    if (a_set & b_set):
        return True 
    else:
        return False    

''' Tratamento das Bases de Dados'''


#Definição de caminho para chamada das bases dados
caminho_drive = r"C:\Modelo Recebimento\BaseDados"

#Chamada das bases para tratamento
df_item = pd.read_excel(caminho_drive + "\ZLIT_ITEM.XLSX")
df_mard = pd.read_excel(caminho_drive + '\MARD.XLSX')
df_jatr = pd.read_excel(caminho_drive + '\ZLIT_JATR.XLSX')
df_s800 = pd.read_excel(caminho_drive + '\S800.XLSX')
df_agd = pd.read_excel(caminho_drive + '\CD.XLSX')

#Tratamento das bases de dados ZLIT
df_jatritem = pd.merge(df_jatr, df_item, on=['Chave de acesso de 44 posições'], how='left') #Unir JATR com ITEM através da chave de 44 dígitos
df_jatritem = df_jatritem.drop(columns=['Chave de acesso de 44 posições', 'Registro deletado', 'Nº CNPJ']) #Remover colunas desnecessárias (não precisa mais da chave)
df_jatritem = df_jatritem.groupby(['Código agendamento','Material']).agg({"Quantidade":np.sum}) #Agrupar quantidade de material por material por agendamento
df_jatritem = df_jatritem.reset_index() #Resetar índice para renomear colunas
df_jatritem.columns=['Código agendamento','Material','Quantidade'] #Renomear colunas
'''Ao final do tratamento, temos um DF com a quantidade de cada material por container'''

#Tratamento da base de estoque CD
df_mard = df_mard.drop(columns=["Centro", "Depósito"]) #Remover colunas desnecessárias
df_mard = df_mard.groupby(["Material"]).sum() #Somar estoques dos diferentes depósitos de MM
'''Ao final do tratamento, temos um DF com a quantidade de cada material dentro do CD'''

#Define quantidade de dias de cobertura
Cobert = 25

#Define parâmetro de peso para retornos (mais difícil enviar que retornar)
Peso = 4

#Tratamento da base de vendas
df_s800 = df_s800.groupby("Material").agg(
    {"Quantidade faturada": np.sum, "Data": pd.Series.nunique} 
) #Contagem da quantidade de dias em que houve venda do material
df_s800["Cobertura"] = df_s800["Quantidade faturada"] / df_s800[
    "Data"] * Cobert  # Divide quantidade faturada por quantidade de dias diferentes vendidos (venda diária), multiplica por 15 para atingir cobertura
df_s800["Cobertura"] = df_s800["Cobertura"].apply(np.ceil)  # Arredonda para cima as coberturas

df_baseprincipal = pd.merge(df_mard, df_s800, on=['Material'], how='left') #cria base principal
df_baseprincipal = df_baseprincipal.drop(columns=["Quantidade faturada", "Data"]) #limpa base principal
#Ao final do tratamento, temos um DF com a demanda diária de cada material





'''Tratamento da base de dados com materiais a serem recebidos no CD'''

s_agdcd = pd.Series(df_agd['Agendamentos CD'])
s_agds2go = pd.Series(df_agd['Agendamentos S2GO'])

for i in s_agdcd:
    if pd.isnull(i):
        continue
    df_agdcdmat = df_jatritem[df_jatritem['Código agendamento']== i]
    df_baseprincipal = pd.merge(df_baseprincipal,df_agdcdmat, on=['Material'], how='left')
    df_baseprincipal = df_baseprincipal.rename(columns={'Quantidade':f'{i}'}) #renomeia coluna mergida para número do agendamento
    df_baseprincipal = df_baseprincipal.drop(columns=["Código agendamento"]) #retira coluna com o código do agendamento

df_baseprincipal = df_baseprincipal.fillna(0) #adiciona zeros ao dataframe

for i in s_agdcd:
    if pd.isnull(i):
        continue
    df_baseprincipal['Utilização livre'] = df_baseprincipal['Utilização livre'] + df_baseprincipal[f'{i}']#inicializa variável
    df_baseprincipal = df_baseprincipal.drop(columns=[f'{i}']) #retira coluna com o código do agendamento

df_jatritem = df_jatritem[df_jatritem['Código agendamento'].isin(s_agdcd) == False]
df_jatritem = df_jatritem[df_jatritem['Código agendamento'].isin(s_agds2go) == False]

'''Separação de agendamentos com materiais que se repetem ou não em outros agendamentos'''

'''Para reduzir a necessidade de combinações, separei agendamentos onde os materiais não se repetem em outros containeres, _
pois não faz diferença a combinação, a avaliação é única, receber ou não, independe de outros containeres'''


df1 = pd.DataFrame(df_jatritem['Material'].value_counts()) #Contagem de materiais que se repetem
df2 = df1.reset_index() #Resetar índice para renomear colunas
df2.columns=['Material','Rep'] #rRenomear colunas

df_tratamento = pd.merge(df_jatritem,df2,on='Material',how='left') #Unir base com quantidade de materiais que se repetem

df_tratamento = df_tratamento.groupby('Código agendamento').agg(
    {'Material': np.count_nonzero, "Rep": np.sum} 
) #Agrupar por container quantos materiais tem, e quantos são repetidos. Se coluna 1 != coluna 2, quer dizer que esse material se repete em outro container
df_tratamento = df_tratamento.reset_index()  #reseta índice para renomear
df_tratamento.columns = ['Código agendamento','Material','Rep'] #renomeia colunas
df_tratamento['Test'] = np.where(df_tratamento['Material']==df_tratamento['Rep'],True,False) #Se material tem apenas em um container, verdadeiro, se não, falso


df_noncomb = df_tratamento[df_tratamento['Test'] == True] #Cria DF para tratar agendamentos com materiais que não se repetem
df_noncomb = df_noncomb.drop(columns=['Test','Rep'])
df_comb = df_tratamento[df_tratamento['Test'] == False] #Cria DF para tratar agendamentos com materiais que se repetem
df_comb = df_comb.drop(columns=['Test','Rep'])


'''Mais uma ideia para tentar reduzir ainda mais a quantidade de combinações necessárias é _
criar DFs apenas para containeres têm materiais repetidos entre si (traduzindo, praticamente um DF por fornecedor ou transportadora)'''

df_combteste = df_jatritem[df_jatritem['Código agendamento'].isin(df_comb['Código agendamento'])] #Cria base com material e agendamentos de combinação
df_combteste['Comb'] = 0 #cria coluna para receber contador de combinação
df_combteste.reset_index()

counter = 0 #inicializa contador de combinação


for item in df_comb['Código agendamento']: #Iteração sobre cada um dos agendamentos
    if df_combteste.loc[df_combteste['Código agendamento'] == item,'Comb'].all() == 0: #Se não há combinação para esse agendamento
        counter += 1 
        df_combteste.loc[df_combteste['Código agendamento'] == item,'Comb'] = counter #, atribui combinação
    else: #Se há combinação para o agendamento
        continue #Segue para o próximo agendamento

    df_apoio = df_combteste.loc[df_combteste['Código agendamento'] == item] #Cria dataframe com todos os materiais que estarão na combinação
    df_apoio = df_apoio.drop_duplicates(subset='Material')
    valid = False #inicializa variável para sair do teste: O teste finalizará quando não houver novos materiais incluídos na combinação

    while valid == False: #enquanto forem incluídos novos materiais na combinação
        df_valid = df_apoio #validador de nova combinação recebe combinação da última iteração
        for item2 in df_comb['Código agendamento']: #iteração para comparar agendamentos
            if common_member(
            df_apoio['Material'],df_combteste.loc[df_combteste['Código agendamento'] == item2,'Material']
            ) == True: #Se há algum material na combinação de materiais que existe no agendamento "item2"
                df_apoio2 = df_combteste.loc[df_combteste['Código agendamento'] == item2]
                df_apoio = pd.concat([df_apoio,df_apoio2], ignore_index=True) #adiciona os materiais do agendamento na combinação de materiais
                df_apoio = df_apoio.drop_duplicates()
        
        
        if len(df_valid['Material']) != len(df_apoio['Material']): #se a quantidade de materiais na lista atualizada for diferente da anterior
            valid = False #reiniciaremos a iteração para procurar pelos novos materiais adicionados
        else:
            valid = True #finalizaremos a iteração para este grupo de materiais
            df_apoio = df_apoio.drop_duplicates(subset='Código agendamento')
            for agd in df_apoio['Código agendamento']:
                df_combteste.loc[df_combteste['Código agendamento'] == agd,'Comb'] = counter #todos os agendamentos que contém estes materiais farão parte da mesma combinação


df_combteste = df_combteste.drop_duplicates(subset='Código agendamento') #remove duplicatas para ter apenas agendamento e de qual combinação fará parte

''' Cálculo para definição dos containeres'''

agdfinal = [] #Cria lista para receber resultados

'''Combinação para materiais em apenas um container'''


QtdAgdnc = len(df_noncomb.index) #quantidade de agendas
z=[] #lista para receber agendamentos a receber

for i in df_noncomb['Código agendamento']:
    df_mpa = df_jatritem[df_jatritem["Código agendamento"] == i] #filtra df para buscar agendamento
    df_calculo = pd.merge(df_baseprincipal,df_mpa, on=['Material'], how='left') #merge do agendamento ao DF principal
    df_calculo = df_calculo.fillna(0) #adiciona zeros ao dataframe
    df_calculo['Sum'] = df_calculo['Utilização livre'] + df_calculo['Quantidade'] #Calcula total de saldo quando recebe o container

    df_calculo['Var Rupt'] = (df_calculo['Sum'] - df_calculo['Cobertura']) #Calcula variação do total para a ruptura
    df_calculo.loc[df_calculo['Var Rupt'] > 0,'Var Rupt'] = df_calculo['Var Rupt']*Peso #Aplicação do peso de retornos
    VarFinal = df_calculo['Var Rupt'].abs().sum() #soma total de variação do estoque em relação a ruptura (valor final)

    df_calculo['Var Rupt2'] = (df_calculo['Utilização livre'] - df_calculo['Cobertura'])
    df_calculo.loc[df_calculo['Var Rupt2'] > 0,'Var Rupt2'] = df_calculo['Var Rupt2']*Peso #Aplicação do peso de retornos
    VarFinal2 = df_calculo['Var Rupt2'].abs().sum() #soma total de variação do estoque em relação a ruptura (valor final)

    if VarFinal < VarFinal2:
        z.append(i) #Adiciona agendamento à solução

print(z)

'''Combinação para materiais em mais de um container'''

df_calculo = df_baseprincipal #inicializa DF

#monta dataframe a utilizar nos testes com todos os agendamentos
for i in df_comb['Código agendamento']:
    df_mpa = df_jatritem[df_jatritem["Código agendamento"] == i] #filtra df para buscar agendamento
    df_calculo = pd.merge(df_calculo,df_mpa, on=['Material'], how='left') #merge do agendamento ao DF principal
    df_calculo = df_calculo.rename(columns={'Quantidade':f'{i}'}) #renomeia coluna mergida para número do agendamento
    df_calculo = df_calculo.drop(columns=["Código agendamento"]) #retira coluna com o código do agendamento

df_calculo = df_calculo.fillna(0) #adiciona zeros ao dataframe
df_calculo['Sum'] = df_calculo['Utilização livre'] #inicializa variável

lastcomb = df_combteste['Comb'].max() #busca quantas combinações de agendamentos com materiais que se repetem existem

for b in range(1,lastcomb+1): 
    z1 = [] #lista para receber valor final de variação em relação a ruptura
    z2 = [] #lista para receber combinação de agendamentos

    df_combunit = df_combteste.loc[df_combteste['Comb'] == b]
    QtdAgdc = len(df_combunit.index) #quantidade de agendas
    df_mpa = df_comb[df_comb["Código agendamento"] == 1] #inicializa DF

    for a in range(1,QtdAgdc+1): #realizar combinações de 1, 2, 3... n agendamentos entre si
        if a == 1:
            df_calculo['Var Rupt2'] = (df_calculo['Utilização livre'] - df_calculo['Cobertura'])
            df_calculo.loc[df_calculo['Var Rupt2'] > 0,'Var Rupt2'] = df_calculo['Var Rupt2']*Peso #Aplicação do peso de retornos
            VarFinal2 = df_calculo['Var Rupt2'].abs().sum() #soma total de variação do estoque em relação a ruptura (valor final)
            z2.append('-')
            z1.append(VarFinal2)
        
        comb = list(combinations(df_combunit['Código agendamento'], a)) #cria lista de combinações de 'a'(quantidade) agendamentos
        combagd=np.array(comb) #transforma lista em array
        
        for x in combagd: #inicia leitura do arranjo de combinações
            df_calculo['Sum'] = df_calculo['Utilização livre'] #inicializa variável de cálculo de ruptura
            z2.append(x) #adiciona agendamentos a lista
            for y in x: #buscar agendamento único dentro da lista de agendamentos
                df_calculo['Sum'] = df_calculo['Sum'] + df_calculo[f'{y}'] #Calcula total de saldo quando recebe o container
            
            df_calculo['Var Rupt'] = (df_calculo['Sum'] - df_calculo['Cobertura']) #Calcula variação do total para a ruptura
            df_calculo.loc[df_calculo['Var Rupt'] > 0,'Var Rupt'] = df_calculo['Var Rupt']*Peso #Aplicação do peso de retornos

            VarFinal = df_calculo['Var Rupt'].abs().sum() #soma total de variação do estoque em relação a ruptura (valor final)
            z1.append(VarFinal)#insere valor final em lista

    min_value = min(z1) #busca menor valor na lista de soluções
    min_index = z1.index(min_value) #busca índice da menor solução na lista

    print(z2[min_index]) #busca agendamentos do menor valor

print('Avaliação Finalizada')

os.system("pause")