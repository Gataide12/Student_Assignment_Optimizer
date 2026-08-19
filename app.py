import streamlit as st
import pandas as pd
import random
import copy
import math
import time
import matplotlib.pyplot as plt

def gerar_salas(IDs, numero_salas):
  IDs_emb = IDs.copy()
  random.shuffle(IDs_emb)
  salas = {i: [] for i in range(1, numero_salas + 1)}
  for aluno_id in IDs_emb:
    sala = random.choice(list(salas.keys()))
    salas[sala].append(aluno_id)
  return salas

def preparar_dados(arquivo, numero_salas):

  # Lê os dados da planilha
  if arquivo is not None:
    df = None
    for sep_char in [';', ',', '\t']:
      try:
        arquivo.seek(0)
        df = pd.read_csv(arquivo, sep=sep_char, engine='python')
        if 'aluno' in df.columns and ('ID' in df.columns or 'id' in df.columns):
            break
      except Exception:
        continue

    if df is None or ('aluno' not in df.columns or ('ID' not in df.columns and 'id' not in df.columns)):
      st.error("Não foi possível ler o arquivo CSV com os separadores ';', ',' ou '\t' e/ou as colunas 'aluno' e 'ID' (ou 'id') não foram encontradas. Verifique o formato do arquivo.")
      return None, None, None, None, None, None

    if 'id' in df.columns and 'ID' not in df.columns:
      df.rename(columns={'id': 'ID'}, inplace=True)

    if 'ID' not in df.columns:
      st.error(f"A coluna 'ID' não foi encontrada no arquivo CSV. As colunas disponíveis são: {df.columns.tolist()}. Por favor, verifique se o nome da coluna está correto ou se o arquivo possui um ID.")
      return None, None, None, None, None, None

    df['ID'] = df['ID'].apply(lambda x: int(float(x)) if pd.notna(x) else None)
    nome_to_id_map = {}
    id_para_nome = {}

    for _, row in df.iterrows():
      if pd.isna(row['ID']):
        continue

      nome = str(row['aluno']).lower().strip()
      id_num = int(row['ID'])

      nome_to_id_map[nome] = id_num
      id_para_nome[id_num] = nome


    # Geração de salas
    IDs = list(id_para_nome.keys())
    salas = gerar_salas(IDs, numero_salas)

    # Converter amizades de nome para ID

    nome_para_id = {nome: id for id, nome in id_para_nome.items()}

    amizades = {}

    for _, row in df.iterrows():
      aluno_nome = str(row['aluno']).lower().strip()
      amizades_raw = row['amizades']

      if pd.notna(amizades_raw) and amizades_raw.strip():

        lista_amigos_nomes = [a.strip().lower() for a in str(amizades_raw).split(',')]
        amizades[aluno_nome] = lista_amigos_nomes

    amizades_id = {}

    for nome, lista_amigos_nomes in amizades.items():
      id_aluno = nome_para_id.get(nome)
      if id_aluno is not None:
        amizades_id[id_aluno] = []

        for amigo_nome in lista_amigos_nomes:
          id_amigo = nome_para_id.get(amigo_nome)
          if id_amigo is not None:
            amizades_id[id_aluno].append(id_amigo)

    inimizades = {}

    for _, row in df.iterrows():
      aluno_nome = str(row['aluno']).lower().strip()
      inimizades_raw = row['inimizades']

      if pd.notna(inimizades_raw) and inimizades_raw.strip():
        lista_inimigos_nomes = [i.strip().lower() for i in str(inimizades_raw).split(',')]
        inimizades[aluno_nome] = lista_inimigos_nomes

    inimizades_id = {}

    for nome, lista_inimigos_nomes in inimizades.items():
      id_aluno = nome_para_id.get(nome)
      if id_aluno is not None:
        inimizades_id[id_aluno] = []

        for inimigo_nome in lista_inimigos_nomes:
          id_inimigo = nome_para_id.get(inimigo_nome)
          if id_inimigo is not None:
            inimizades_id[id_aluno].append(id_inimigo)


    df_indexed = df.set_index('ID')

    # Criar alunos_data_dict
    alunos_data_dict = {}

    for aluno_id, row_data in df_indexed.iterrows():
        alunos_data_dict[aluno_id] = {
            'sexo': row_data.get('sexo'),
            'desempenho': row_data.get('desempenho'),
            'comportamento': row_data.get('comportamento')
    }

    for aluno_id, amigos_list in amizades_id.items():
        if aluno_id in alunos_data_dict:
            alunos_data_dict[aluno_id]['amizades'] = amigos_list

    for aluno_id, inimigos_list in inimizades_id.items():
        if aluno_id in alunos_data_dict:
            alunos_data_dict[aluno_id]['inimizades'] = inimigos_list

    return salas, amizades_id, inimizades_id, alunos_data_dict, IDs, id_para_nome

  # Avaliação de cada sala

def aval_amizades(sala_ids, amizades_id_map):
  pares_amigos_internos = set()
  sala_ids_set = set(sala_ids)

  for aluno_id1 in sala_ids:
    if aluno_id1 in amizades_id_map:
      amigos_de_aluno1 = amizades_id_map[aluno_id1]
      for aluno_id2 in amigos_de_aluno1:
        if aluno_id2 in sala_ids_set:

          pares_amigos_internos.add(tuple(sorted((aluno_id1, aluno_id2))))
  return len(pares_amigos_internos)

def aval_inimizades(sala_ids, inimizades_id_map):
  pares_inimigos_internos = set()
  sala_ids_set = set(sala_ids)

  for aluno_id1 in sala_ids:
    if aluno_id1 in inimizades_id_map:
      inimigos_de_aluno1 = inimizades_id_map[aluno_id1]
      for aluno_id2 in inimigos_de_aluno1:
        if aluno_id2 in sala_ids_set:

          pares_inimigos_internos.add(tuple(sorted((aluno_id1, aluno_id2))))
  return len(pares_inimigos_internos)

def aval_genero(sala_ids, all_alunos_data):
  M = 0
  F = 0
  for aluno_id in sala_ids:
    if aluno_id in all_alunos_data:
      student_data = all_alunos_data[aluno_id]
      if student_data["sexo"] == "M":
        M += 1
      elif student_data["sexo"] == "F":
        F += 1
  dif_gen = abs(M - F)
  return -dif_gen

def aval_tamanho(sala_ids, ide_len, tolerancia = 2):
  dif = abs(len(sala_ids) - ide_len)
  if dif <= tolerancia:
    return 0
  return -dif

def aval_notas(sala_ids, all_alunos_data):
  if not sala_ids:
    return 0
  total_desempenho = 0
  valid_alunos_count = 0
  for aluno_id in sala_ids:
    if aluno_id in all_alunos_data:
      student_data = all_alunos_data[aluno_id]
      if pd.notna(student_data["desempenho"]):
        total_desempenho += student_data["desempenho"]
        valid_alunos_count += 1
  mediaN = total_desempenho / valid_alunos_count if valid_alunos_count > 0 else 0
  return mediaN


def penalidade_notas():
  medias = []
  for sala_ids in all_salas.values():
    media = aval_notas(salas_ids, all_alunos_data)
    medias.append(media)
  media_geral = sum(medias)/len(medias)
  penalidade = sum(abs(media-media_geral) for media in medias)
  return -penalidade

def aval_comportamento(sala_ids, all_alunos_data):
  if not sala_ids:
    return 0
  total_comportamento = 0
  valid_alunos_count = 0
  for aluno_id in sala_ids:
    if aluno_id in all_alunos_data:
      student_data = all_alunos_data[aluno_id]
      if pd.notna(student_data["comportamento"]):
        total_comportamento += student_data["comportamento"]
        valid_alunos_count += 1
  mediaC = total_comportamento / valid_alunos_count if valid_alunos_count > 0 else 0
  return mediaC

def penalidade_dif_scores(all_salas, amizades_id_map, inimizades_id_map, all_alunos_data, total_alunos, numero_salas):
   scores = []
   if not all_salas:
       return 0

   ide_len = total_alunos / numero_salas

   for sala_num, sala_ids in all_salas.items():
      score = (
        -(aval_inimizades(sala_ids, inimizades_id_map)) * 3 +
        aval_amizades(sala_ids, amizades_id_map) * 0.2 +
        aval_genero(sala_ids, all_alunos_data) * 0.8 +
        aval_notas(sala_ids, all_alunos_data) * 0.7 +
        aval_tamanho(sala_ids, ide_len) * 0.8 +
        aval_comportamento(sala_ids, all_alunos_data) * 1.0)
      scores.append(score)

   if not scores:
       return 0

   dif = max(scores) - min(scores)

   return -(dif ** 2) * 0.3

#Avaliação total

def aval_tot(all_salas, amizades_id_map, inimizades_id_map, all_alunos_data, total_alunos, numero_salas):
  total_score = 0

  ide_len = total_alunos / numero_salas

  for sala_num, sala_ids in all_salas.items():
    total_score += (
        -(aval_inimizades(sala_ids, inimizades_id_map)) * 3 +
        aval_amizades(sala_ids, amizades_id_map) * 0.2 +
        aval_genero(sala_ids, all_alunos_data) * 0.8 +
        aval_tamanho(sala_ids, ide_len) * 0.8 +
        aval_comportamento(sala_ids, all_alunos_data) * 1.0
    )
  total_score/= len(all_salas)
  total_score+= penalidade_notas(all_salas, all_alunos_data) * 0.7   
  total_score += penalidade_dif_scores(all_salas, amizades_id_map, inimizades_id_map, all_alunos_data, total_alunos, numero_salas)
  return total_score

# Criação dos vizinhos

def gerar_vizinho(salas_atuais, alunos_data_dict):
  vizinho = {sala_num: list(aluno_ids) for sala_num, aluno_ids in salas_atuais.items()}
  ndeci = random.random()
  if ndeci < 0.55:
    salas_origem_nao_nulas = [k for k, v in vizinho.items() if v]
    if not salas_origem_nao_nulas:
      return salas_atuais

    sala_origem = random.choice(salas_origem_nao_nulas)
    aluno_id3 = random.choice(vizinho[sala_origem])
    vizinho[sala_origem].remove(aluno_id3)

    available_destinations = [k for k in vizinho.keys() if k != sala_origem]
    if not available_destinations:
        vizinho[sala_origem].append(aluno_id3)
        return salas_atuais
    sala_destino = random.choice(available_destinations)
    vizinho[sala_destino].append(aluno_id3)

  elif ndeci > 0.55 and ndeci < 0.83:

    sala_escs= random.sample(list(vizinho.keys()),2)
    sala_esc1_key =sala_escs[0]
    sala_esc2_key =sala_escs[1]

    if not vizinho[sala_esc1_key] or not vizinho[sala_esc2_key]:
      return salas_atuais

    aluno_id1= random.choice(vizinho[sala_esc1_key])
    aluno_id2= random.choice(vizinho[sala_esc2_key])

    vizinho[sala_esc1_key].remove(aluno_id1)
    vizinho[sala_esc2_key].remove(aluno_id2)
    vizinho[sala_esc1_key].append(aluno_id2)
    vizinho[sala_esc2_key].append(aluno_id1)

  else:

     if len(vizinho.keys()) < 3:
         return salas_atuais

     sala_escs = random.sample(list(vizinho.keys()), 3)
     sala_esc1_key = sala_escs[0]
     sala_esc2_key = sala_escs[1]
     sala_esc3_key = sala_escs[2]

     if not vizinho[sala_esc1_key] or not vizinho[sala_esc2_key] or not vizinho[sala_esc3_key]:
         return salas_atuais

     aluno_id1 = random.choice(vizinho[sala_esc1_key])
     aluno_id2 = random.choice(vizinho[sala_esc2_key])
     aluno_id3 = random.choice(vizinho[sala_esc3_key])

     vizinho[sala_esc1_key].remove(aluno_id1)
     vizinho[sala_esc2_key].remove(aluno_id2)
     vizinho[sala_esc3_key].remove(aluno_id3)

     vizinho[sala_esc1_key].append(aluno_id3)
     vizinho[sala_esc2_key].append(aluno_id1)
     vizinho[sala_esc3_key].append(aluno_id2)


  return vizinho

def gerar_vizinhoADP(salas_atuais, alunos_data_dict, T):
  vizinho = {sala_num: list(aluno_ids) for sala_num, aluno_ids in salas_atuais.items()}

  if T > 70:
    ATC = random.random()
    if ATC > 0.6:
      if len(vizinho.keys()) < 4:
         return salas_atuais

      sala_escs = random.sample(list(vizinho.keys()), 4)
      sala_esc1_key = sala_escs[0]
      sala_esc2_key = sala_escs[1]
      sala_esc3_key = sala_escs[2]
      sala_esc4_key = sala_escs[3]

      if not vizinho[sala_esc1_key] or not vizinho[sala_esc2_key] or not vizinho[sala_esc3_key] or not vizinho[sala_esc4_key]:
         return salas_atuais

      aluno_id1 = random.choice(vizinho[sala_esc1_key])
      aluno_id2 = random.choice(vizinho[sala_esc2_key])
      aluno_id3 = random.choice(vizinho[sala_esc3_key])
      aluno_id4 = random.choice(vizinho[sala_esc4_key])

      vizinho[sala_esc1_key].remove(aluno_id1)
      vizinho[sala_esc2_key].remove(aluno_id2)
      vizinho[sala_esc3_key].remove(aluno_id3)
      vizinho[sala_esc4_key].remove(aluno_id4)

      vizinho[sala_esc1_key].append(aluno_id3)
      vizinho[sala_esc2_key].append(aluno_id4)
      vizinho[sala_esc3_key].append(aluno_id2)
      vizinho[sala_esc4_key].append(aluno_id1)

      return vizinho
    else:
      sala_escs = random.sample(list(vizinho.keys()), 2)
      sala_esc1_key = sala_escs[0]
      sala_esc2_key = sala_escs[1]

      alunosA = random.sample(vizinho[sala_esc1_key], min(15, len(vizinho[sala_esc1_key])))
      alunosB = random.sample(vizinho[sala_esc2_key], min(15, len(vizinho[sala_esc2_key])))

      for aluno_id in alunosA:
        vizinho[sala_esc1_key].remove(aluno_id)

      for aluno_id in alunosB:
        vizinho[sala_esc2_key].remove(aluno_id)

      vizinho[sala_esc1_key].extend(alunosB)
      vizinho[sala_esc2_key].extend(alunosA)

      return vizinho
  elif 30 < T < 70:
    MTP = random.random()
    if MTP < 0.5:
      sala_escs = random.sample(list(vizinho.keys()), 2)
      sala_esc1_key = sala_escs[0]
      sala_esc2_key = sala_escs[1]

      alunosA = random.sample(vizinho[sala_esc1_key], min(3, len(vizinho[sala_esc1_key])))
      alunosB = random.sample(vizinho[sala_esc2_key], min(3, len(vizinho[sala_esc2_key])))

      for aluno_id in alunosA:
        vizinho[sala_esc1_key].remove(aluno_id)

      for aluno_id in alunosB:
        vizinho[sala_esc2_key].remove(aluno_id)

      vizinho[sala_esc1_key].extend(alunosB)
      vizinho[sala_esc2_key].extend(alunosA)


      return vizinho
    else:
      if len(vizinho.keys()) < 3:
         return salas_atuais

      sala_escs = random.sample(list(vizinho.keys()), 3)
      sala_esc1_key = sala_escs[0]
      sala_esc2_key = sala_escs[1]
      sala_esc3_key = sala_escs[2]

      if not vizinho[sala_esc1_key] or not vizinho[sala_esc2_key] or not vizinho[sala_esc3_key]:
         return salas_atuais

      aluno_id1 = random.choice(vizinho[sala_esc1_key])
      aluno_id2 = random.choice(vizinho[sala_esc2_key])
      aluno_id3 = random.choice(vizinho[sala_esc3_key])

      vizinho[sala_esc1_key].remove(aluno_id1)
      vizinho[sala_esc2_key].remove(aluno_id2)
      vizinho[sala_esc3_key].remove(aluno_id3)

      vizinho[sala_esc1_key].append(aluno_id3)
      vizinho[sala_esc2_key].append(aluno_id1)
      vizinho[sala_esc3_key].append(aluno_id2)

      return vizinho
  else:
    BTP = random.random()
    if BTP < 0.5:
      sala_escs= random.sample(list(vizinho.keys()),2)
      sala_esc1_key =sala_escs[0]
      sala_esc2_key =sala_escs[1]
      if not vizinho[sala_esc1_key] or not vizinho[sala_esc2_key]:
          return salas_atuais

      aluno_id1= random.choice(vizinho[sala_esc1_key])
      aluno_id2= random.choice(vizinho[sala_esc2_key])

      vizinho[sala_esc1_key].remove(aluno_id1)
      vizinho[sala_esc2_key].remove(aluno_id2)
      vizinho[sala_esc1_key].append(aluno_id2)
      vizinho[sala_esc2_key].append(aluno_id1)

      return vizinho
    else:
      sala_escs= random.sample(list(vizinho.keys()),2)
      sala_esc1_key =sala_escs[0]
      sala_esc2_key =sala_escs[1]
      if not vizinho[sala_esc1_key]:
          return salas_atuais

      aluno_id1= random.choice(vizinho[sala_esc1_key])

      vizinho[sala_esc1_key].remove(aluno_id1)
      vizinho[sala_esc2_key].append(aluno_id1)

      return vizinho

def hill_climbing(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, max_iterations, total_alunos, numero_salas):
    progress_bar = st.progress(0, text="Hill Climbing: 0%")
    salas_atuaisHC = copy.deepcopy(inicial_salas)
    maior_scoreHC = aval_tot(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)
    melhor_solucaoHC = copy.deepcopy(salas_atuaisHC)

    historico = []
    tempo_inicial = time.time()

    for i in range(max_iterations):
      progress = (i + 1) / max_iterations
      progress_bar.progress(progress, text=f"Hill Climbing: {progress:.0%}")
      novo_vizinho = gerar_vizinho(salas_atuaisHC, alunos_data_dict)
      score_vizinho = aval_tot(novo_vizinho, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)

      if score_vizinho > maior_scoreHC:
        maior_scoreHC = score_vizinho
        melhor_solucaoHC = copy.deepcopy(novo_vizinho)
        salas_atuaisHC = copy.deepcopy(novo_vizinho)

      tempo_decorrido = time.time() - tempo_inicial
      historico.append({
          'Iteração': i + 1,
          'Score': maior_scoreHC,
          'Tempo Acumulado': tempo_decorrido
      })

    df_historico = pd.DataFrame(historico)
    return maior_scoreHC, melhor_solucaoHC, df_historico

def simulated_annealing(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, max_iterations, total_alunos, numero_salas):
    aceitou_pior = 0
    salas_atuais = copy.deepcopy(inicial_salas)
    maior_scoreSA = aval_tot(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)

    melhor_solucaoSA = copy.deepcopy(salas_atuais)
    score_atual = aval_tot(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)

    historico = []
    tempo_inicial = time.time()
    T = 100
    my_bar = st.progress(0, text="Simulated Annealing: 0%")
    for i in range(max_iterations):
      progress = (i + 1) / max_iterations
      my_bar.progress(progress, text=f"Simulated Annealing: {progress:.0%}, Temperatura: {T:.2f}")
      novo_vizinho = gerar_vizinho(salas_atuais, alunos_data_dict)
      score_vizinho = aval_tot(novo_vizinho, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)

      if score_vizinho > maior_scoreSA:
        maior_scoreSA = score_vizinho
        melhor_solucaoSA = copy.deepcopy(novo_vizinho)

      delta = score_vizinho - score_atual

      if delta > 0:
        salas_atuais = copy.deepcopy(novo_vizinho)
        score_atual = score_vizinho
      else:
          P = math.exp(delta / T)
          if random.random() < P:
            score_atual = score_vizinho
            salas_atuais = copy.deepcopy(novo_vizinho)
            aceitou_pior += 1

      tempo_decorrido = time.time() - tempo_inicial
      historico.append({
          'Iteração': i + 1,
          'Score': maior_scoreSA,
          'Temperatura': T,
          'Tempo Acumulado': tempo_decorrido
      })

      T = T * 0.9998849
      if T < 1e-10:
       T = 1e-10
    st.write(f"pioras aceitas:  {aceitou_pior}")

    df_historico = pd.DataFrame(historico)
    return maior_scoreSA, melhor_solucaoSA, df_historico

def simulated_annealingADP(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, max_iterations, total_alunos, numero_salas):
    aceitou_pior = 0
    salas_atuais = copy.deepcopy(inicial_salas)
    maior_scoreSAADP = aval_tot(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)

    melhor_solucaoSAADP = copy.deepcopy(salas_atuais)
    score_atual = aval_tot(inicial_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)

    historico = []
    tempo_inicial = time.time()

    T = 100
    progress_bar = st.progress(0, text="Simulated Annealing Adaptado: 0%")

    for i in range(max_iterations):
      progress = (i + 1) / max_iterations
      progress_bar.progress(progress, text=f"Simulated Annealing Adaptado: {progress:.0%}, Temperatura: {T:.2f}")
      novo_vizinho = gerar_vizinhoADP(salas_atuais, alunos_data_dict, T)
      score_vizinho = aval_tot(novo_vizinho, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)

      if score_vizinho > maior_scoreSAADP:
        maior_scoreSAADP = score_vizinho
        melhor_solucaoSAADP = copy.deepcopy(novo_vizinho)

      delta = score_vizinho - score_atual

      if delta > 0:
        salas_atuais = copy.deepcopy(novo_vizinho)
        score_atual = score_vizinho
      else:
          P = math.exp(delta / T)
          if random.random() < P:
            score_atual = score_vizinho
            salas_atuais = copy.deepcopy(novo_vizinho)
            aceitou_pior += 1

      tempo_decorrido = time.time() - tempo_inicial

      historico.append({
          'Iteração': i + 1,
          'Score': maior_scoreSAADP,
          'Temperatura': T,
          'Tempo Acumulado (s)': tempo_decorrido
      })

      T = T * 0.9998849
      if T < 1e-10:
       T = 1e-10

    st.write(f"pioras aceitas:  {aceitou_pior}")

    df_historico = pd.DataFrame(historico)

    return maior_scoreSAADP, melhor_solucaoSAADP, df_historico

def otimizar(metodo, salas, amizades_id_map, inimizades_id_map, alunos_data_dict, IDs, numero_salas, max_iterations, populacao=None, taxa_mutacao=None):
  st.subheader(f"Otimizando com {metodo}...")
  total_alunos = len(IDs)
  if metodo == "Hill Climbing":
    score_final, solucao_final, df_historico = hill_climbing(salas, amizades_id_map, inimizades_id_map, alunos_data_dict, max_iterations, total_alunos, numero_salas)
  elif metodo == "Simulated Annealing":
    score_final, solucao_final, df_historico = simulated_annealing(salas, amizades_id_map, inimizades_id_map, alunos_data_dict, max_iterations, total_alunos, numero_salas)
  elif metodo == "Simulated Annealing Adaptado":
    score_final, solucao_final, df_historico = simulated_annealingADP(salas, amizades_id_map, inimizades_id_map, alunos_data_dict, max_iterations, total_alunos, numero_salas)
  else:
    score_final, solucao_final, df_historico =  genetic_algorithm(populacao, max_iterations, numero_salas, IDs, amizades_id_map, inimizades_id_map, alunos_data_dict, taxa_mutacao, total_alunos)
  st.subheader(f"Otimização com {metodo} completa.")
  return score_final, solucao_final, df_historico

def dic_para_lista(salas, IDs):
  aluno_para_sala = {}

  for sala, alunos in salas.items():
    for aluno in alunos:
        aluno_para_sala[aluno] = sala

  individuo = []

  for aluno in IDs:
        individuo.append(aluno_para_sala[aluno])

  return individuo

def gerar_populacao(tamanho_populacao, IDs, numero_salas):
  populacao = []

  for i in range(tamanho_populacao):
    salas_iniciais = gerar_salas(IDs, numero_salas)
    individuo = dic_para_lista(salas_iniciais, IDs)
    populacao.append(individuo)
  return populacao

def list_dict(individuo, IDs, numero_salas):
  salas = {}

  for sala in range(1, numero_salas + 1):
    salas[sala] = []

  for posicao, sala in enumerate(individuo):
    aluno = IDs[posicao]

    salas[sala].append(aluno)

  return salas

def avaliar_pop(populacao, IDs, numero_salas, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos):

  lista_scores = []

  for individuo in populacao:
    salas = list_dict(individuo, IDs, numero_salas)
    score_ind = aval_tot(salas, amizades_id_map, inimizades_id_map, alunos_data_dict, total_alunos, numero_salas)
    lista_scores.append(score_ind)

  return lista_scores

def torneio(individuos, lista_scores, tamanho_torneio):
  candidatos = random.sample(range(len(individuos)), tamanho_torneio)

  melhor = random.choice(candidatos)

  for candidato in candidatos:
    if lista_scores[candidato] > lista_scores[melhor]:
      melhor = candidato

  return melhor

def crossover(pai1, pai2):
  ponto = random.randint(1, len(pai1)-1)
  filho1 = pai1[:ponto] + pai2[ponto:]
  filho2 = pai2[:ponto] + pai1[ponto:]

  return filho1, filho2

def mutacao(individuo, numero_salas, taxa_mutacao):
  novo_individuo = individuo.copy()
  if random.random() < taxa_mutacao:
    posicao = random.randint(0, len(novo_individuo)-1)
    nova_sala = random.randint(1, numero_salas)

    novo_individuo[posicao] = nova_sala

  return novo_individuo

def genetic_algorithm(populacao, max_iterations, numero_salas, IDs, amizades_id_map, inimizades_id_map, alunos_data_dict, taxa_mutacao, total_alunos):
  progress_bar = st.progress(0, text="Algoritmo Genético: 0%")
  melhor_scoreGA = float("-inf")
  melhor_solucaoGA = None
  tamanho_torneio = 3
  for geracao in range(max_iterations):
    progress = (geracao + 1) / max_iterations
    progress_bar.progress(progress, text=f"Algoritmo Genético: {progress:.0%}")

    nova_pop = []
    lista_score = avaliar_pop(
    populacao,
    IDs,
    numero_salas,
    amizades_id_map,
    inimizades_id_map,
    alunos_data_dict,
    total_alunos
)

    while len(nova_pop) < len(populacao):
      indice_pai1 = torneio(populacao, lista_score, tamanho_torneio)
      indice_pai2 = torneio(populacao, lista_score, tamanho_torneio)

      pai1 = populacao[indice_pai1]
      pai2 = populacao[indice_pai2]

      filho1, filho2 = crossover(pai1, pai2)

      filho1 = mutacao(filho1, numero_salas, taxa_mutacao)
      filho2 = mutacao(filho2, numero_salas, taxa_mutacao)

      nova_pop.append(filho1)

      if len(nova_pop) < len(populacao):
        nova_pop.append(filho2)

    for individuo in nova_pop:
      current_salas = list_dict(individuo, IDs, numero_salas)
      score_ind = aval_tot(
      current_salas,
      amizades_id_map,
      inimizades_id_map,
      alunos_data_dict,
      total_alunos,
      numero_salas
     )
      if score_ind > melhor_scoreGA:
        melhor_scoreGA = score_ind
        melhor_solucaoGA = copy.deepcopy(current_salas)
    populacao = nova_pop

  return melhor_scoreGA, melhor_solucaoGA, df_historico 

#Streamlit

st.title("**Otimizador de salas escolares**")
st.write("Começe colocando um arquivo no formato CSV com as informações dos estudantes")
arquivo = st.file_uploader("Coloque seu arquivo CSV aqui", type="csv")
metodo = st.selectbox("Escolha o método de otimização desejado: ", ["Hill Climbing", "Simulated Annealing", "Simulated Annealing Adaptado", "Algoritmo Génetico"])
numero_salas = st.number_input(
    label="Quantidade de salas desejada:",
    min_value=2,
    max_value=15,
    value=3,
    step=1
)

max_iterations = st.slider("Máximo de iterações:", min_value=100, max_value=1000000, value=1000)
st.write("(*Quanto mais iterações forem permitidas, maior será a qualidade da solução, porém mais tempo levará. Muitas iterações saturam o processo, rendendo menos score por iteração*)")

quer_grafico = st.checkbox("Deseja gerar os gráficos de desempenho da última execução?")


if metodo == "Algoritmo Génetico":
    tamanho_populacao = st.slider("Tamanho da população:", min_value=10, max_value=200, value=50)
    taxa_mutacao = st.slider("Taxa de mutação:", min_value=0.01, max_value=0.5, value=0.05, step=0.01)
else:
    tamanho_populacao = None
    taxa_mutacao = None


if arquivo and st.button("Otimizar"):
  with st.spinner("Processando dados e otimizando..."):
    salas, amizades, inimizades, dados_dict, IDs, id_para_nome = preparar_dados(arquivo, numero_salas)

    if salas is None:
        st.error("Não foi possível processar os dados do arquivo CSV. Por favor, verifique o arquivo e tente novamente.")
    else:
        populacao = None
        if metodo == "Algoritmo Génetico":
          populacao = gerar_populacao(tamanho_populacao, IDs, numero_salas)

        score, solucao_final, df_historico = otimizar(
            metodo,
            salas,
            amizades,
            inimizades,
            dados_dict,
            IDs,
            numero_salas,
            max_iterations,
            populacao,
            taxa_mutacao
        )

        #Salva os dados da última execução
        st.session_state.historico_rodada = df_historico
        st.session_state.score_rodada = score
        st.session_state.solucao_rodada = solucao_final
        st.session_state.id_para_nome_rodada = id_para_nome
        st.session_state.metodo_utilizado = metodo


        st.success(f"Concluído! Score: {score:.2f}")

if 'solucao_rodada' in st.session_state:
    st.subheader("Solução Final:")

    solucao = st.session_state.solucao_rodada
    id_para_nome = st.session_state.id_para_nome_rodada

    for room_num, student_ids in solucao.items():
        student_names = [
           id_para_nome.get(sid, f"ID Desconhecido ({sid})")
                   for sid in student_ids
        ]

        st.write(f"**Sala {room_num}:** {', '.join(student_names)}")

#Gráficos com Matplotlib
if quer_grafico and 'historico_rodada' in st.session_state and st.session_state.historico_rodada is not None:
  st.markdown("---")

  df_atual = st.session_state.historico_rodada
  metodo_atual = st.session_state.metodo_utilizado

  st.subheader("Configurações do Gráfico")

  colunas_disponiveis = list(df_atual.columns)

  eixo_x = st.selectbox("Escolha a variável do eixo X:", colunas_disponiveis, index=0)
  eixo_y = st.selectbox("Escolha a variável do eixo Y:", colunas_disponiveis, index=1)
  cor_linha = st.color_picker("Escolha a cor da linha:", "#00CC96")

  fig, ax = plt.subplots(figsize=(8, 4))

  ax.plot(df_atual[eixo_x], df_atual[eixo_y], color=cor_linha, linewidth=2, label="Evolução")
  ax.set_title(f"Evolução do método {metodo_atual} ({eixo_x} vs {eixo_y})", fontsize=11, fontweight='bold', pad=10)
  ax.set_xlabel(eixo_x, fontsize=9, fontweight='semibold')
  ax.set_ylabel(eixo_y, fontsize=9, fontweight='semibold')
  ax.grid(True, linestyle='--', alpha=0.3)
  ax.spines['top'].set_visible(False)
  ax.spines['right'].set_visible(False)
  ax.legend(loc="lower right", fontsize=8)

  st.pyplot(fig)


