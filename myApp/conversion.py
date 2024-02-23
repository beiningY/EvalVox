import os
import json
import unicodedata 
from praatio import tgio 
from bs4 import BeautifulSoup
import spacy
import string
from unidecode import unidecode

########################EAF2JSONDER#####################
"""
Cette partie concerne les enfants et les adultes
fichiers d'entrée : .eaf (fichier de référence)         
sorties : .json 
"""
def unicode_normalisation(text):
    # Convertit le texte en Unicode en utilisant UTF-8 si possible, sinon renvoie une chaîne
    try:
        return unicode(text, "utf-8")
    except NameError:  
        return str(text)

def strip_accents(text):
    # Supprime les accents du texte en le normalisant en NFD, puis en le convertissant en ASCII en ignorant les caractères non ASCII
    text = (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
    return str(text)

def eaf2jsonDER(file_path):
    # Fonction principale pour convertir un fichier EAF en format JSON DER
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    results = derprocess_eaf_content(xml_content, os.path.splitext(os.path.basename(file_path))[0])
    return results 

def derprocess_eaf_content(xml_content, file_name):
    # Fonction pour traiter le contenu XML d'un fichier EAF et extraire les informations pertinentes
    soup = BeautifulSoup(xml_content, 'xml')
    time_slots = {slot['TIME_SLOT_ID']: int(slot['TIME_VALUE']) for slot in soup.find_all('TIME_SLOT')}
    annotations_tier = soup.find('TIER', {'TIER_ID': lambda x: x.startswith('*') and x.endswith('_nettoye')})
    situation_tier = soup.find('TIER', {'TIER_ID': 'Activité en cours'})
    
    results = []

    if annotations_tier and situation_tier:
        # Parcours des annotations alignables et des annotations de situation
        for annotation, situation_annotation in zip(annotations_tier.find_all('ALIGNABLE_ANNOTATION'), situation_tier.find_all('ALIGNABLE_ANNOTATION')):
            start_time = round(time_slots[annotation['TIME_SLOT_REF1']] / 1000, 2)
            end_time = round(time_slots[annotation['TIME_SLOT_REF2']] / 1000, 2)
            orthographic_transcript = strip_accents(annotation.find('ANNOTATION_VALUE').text)  
            situation = strip_accents(situation_annotation.find('ANNOTATION_VALUE').text)  
            file_id_parts = file_name.split('-')
            file_id = '-'.join(file_id_parts[:7])
            parts_speaker = file_id.split('-')
            speaker_id = parts_speaker[3].strip()
            class_parts = file_name.split('-')
            class_id = class_parts[0].strip()

            # Création d'un dictionnaire pour chaque segment avec les informations extraites
            segment_dict = {
                "file_id": file_id,
                "speaker_id": speaker_id,
                "class_id": class_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "transcript": orthographic_transcript,
                "situation": situation
            }

            results.append(segment_dict)

    return results
#######################################################

########################TEXTGRID2JSON#####################
"""
Cette partie concerne les enfants et les adultes
fichiers d'entrée : .textgrid (fichier d'hypothèse)         
sorties : .json 
"""
def textgrid2json(file_path):
    # Ouvre le fichier TextGrid avec la bibliothèque praatio
    tg = tgio.openTextgrid(file_path)

    # Nom du tier à extraire du TextGrid
    tier_name = "silences"
    
    # Récupère le tier spécifié du TextGrid
    tier = tg.tierDict[tier_name]

    # Obtient le nom du fichier sans extension
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # Extraire les parties du file_id
    file_id_parts = file_name.split('-')[:7]
    
    # Construit le file_id en rejoignant les parties
    file_id = '-'.join(file_id_parts)
    
    # Obtient le speaker_id à partir du file_id
    parts_speaker = file_id.split('-')
    speaker_id = parts_speaker[3].strip()
    
    # Obtient le class_id à partir du file_id
    class_parts = file_name.split('-')
    class_id = class_parts[0].strip()
    results = []
    # Parcours chaque entrée dans le tier et la convertit en format JSON
    for entry in tier.entryList:
        start_time = round(entry[0], 2)
        end_time = round(entry[1], 2)
        orthographic_transcript = entry[2]
        duration = end_time - start_time

        # Crée un dictionnaire pour chaque segment et l'ajoute à la liste de résultats
        segment_dict = {
            "file_id": file_id,
            "speaker_id": speaker_id,
            "class_id": class_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "transcript": orthographic_transcript
        }

        results.append(segment_dict)
    return results
#######################################################

########################EAF2JSONWER#####################
"""
Cette partie ne concerne que les adultes
fichiers d'entrée : .eaf (fichier de référence)         
sorties : .json avec annotation tokenisée et normalisée
"""
def normalize_french(text):
    # Charger le modèle spaCy pour le français
    nlp = spacy.load('fr_core_news_sm')
    # Convertir le texte en minuscules et le traiter avec le modèle spaCy
    doc = nlp(text.lower())
    # Supprimer la ponctuation, sauf les chevrons (< et >)
    translator = str.maketrans('', '', string.punctuation.replace('<', '').replace('>', ''))
    # Rejoindre les tokens traités en une chaîne de caractères
    return " ".join([token.text.translate(translator) for token in doc])

def eaf2jsonWER(file_path):
    # Fonction principale pour convertir un fichier EAF en format JSON WER
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    results = werprocess_eaf_content(xml_content, os.path.splitext(os.path.basename(file_path))[0])
    return results

def werprocess_eaf_content(xml_content, file_name):
    # Fonction pour traiter le contenu XML d'un fichier EAF et extraire les informations pertinentes
    soup = BeautifulSoup(xml_content, 'xml')
    # Créer un dictionnaire des repères temporels
    time_slots = {slot['TIME_SLOT_ID']: int(slot['TIME_VALUE']) for slot in soup.find_all('TIME_SLOT')}
    # Trouver les tiers d'annotations et de situations
    annotations_tier = soup.find('TIER', {'TIER_ID': lambda x: x.startswith('*') and x.endswith('_nettoye')})
    situation_tier = soup.find('TIER', {'TIER_ID': 'Activité en cours'})
    results = []

    if annotations_tier and situation_tier:
        # Parcourir les annotations alignables et les annotations de situation
        for annotation, situation_annotation in zip(annotations_tier.find_all('ALIGNABLE_ANNOTATION'), situation_tier.find_all('ALIGNABLE_ANNOTATION')):
            # Extraire les temps de début et de fin
            start_time = round(time_slots[annotation['TIME_SLOT_REF1']] / 1000, 2)
            end_time = round(time_slots[annotation['TIME_SLOT_REF2']] / 1000, 2)
            # Extraire la transcription orthographique et la normaliser
            orthographic_transcript = strip_accents(annotation.find('ANNOTATION_VALUE').text)
            orthographic_transcript = normalize_french(orthographic_transcript)
            # Extraire la situation
            situation = strip_accents(situation_annotation.find('ANNOTATION_VALUE').text)  
            file_id_parts = file_name.split('-')
            file_id = '-'.join(file_id_parts[:7])
            parts_speaker = file_id.split('-')
            speaker_id = parts_speaker[3].strip()
            class_parts = file_name.split('-')
            class_id = class_parts[0].strip()

            # Création d'un dictionnaire pour chaque segment avec les informations extraites
            segment_dict = {
                "file_id": file_id,
                "speaker_id": speaker_id,
                "class_id": class_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "transcript": orthographic_transcript,
                "situation": situation
            }

            results.append(segment_dict)

    return results
#######################################################

########################TXT2JSON#####################
"""
Cette partie ne concerne que les adultes
fichiers d'entrée : .txt (fichier d'hypothèse)         
sorties : .json 
"""
def txt2json(file_path):
    # Initialisation de la liste de résultats
    results = []
    # Lecture du fichier texte
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # Suppression des caractères de nouvelle ligne et des espaces en début et fin de ligne
    lines = [line.strip() for line in lines]

    # Parcours des lignes à partir de la 12ème ligne avec un pas de 5 lignes
    for i in range(12, len(lines), 5):
        # Extraction de l'identifiant complet du fichier
        file_id_full = lines[i]
        # Séparation de l'identifiant en parties
        file_id_parts = file_id_full.split("_")
        file_part = "_".join(file_id_parts[:-3]).strip()
        file_id = file_part[:-2]

        # Extraction de l'identifiant du locuteur et de la classe
        line_parts = file_id.split("-")
        speaker_id = line_parts[3].strip()
        class_id = line_parts[0].strip()

        # Extraction des temps de début et de fin
        file_id_nower = lines[i]
        file_id_parts2 = file_id_nower.split(",")
        nower = file_id_parts2[0]
        nofile = nower.split("-")
        rvb = nofile[-1]
        times = rvb.split("_")
        start_time = times[2]
        end_time = times[3]

        # Extraction de l'hypothèse et prétraitement
        hypothesis = lines[i + 3]
        processed_hypothesis = ' '.join(hypothesis.split(';')).lower().strip()
        processed_hypothesis = unidecode(processed_hypothesis)
        
        # Création d'un dictionnaire pour chaque segment avec les informations extraites
        segment_dict = {
            "file_id": file_id,
            "speaker_id": speaker_id,
            "class_id": class_id,
            "start_time": int(start_time) / 1000,
            "end_time": int(end_time) / 1000,
            "duration": int(end_time) - int(start_time),
            "hypothesis": processed_hypothesis,
        }

        results.append(segment_dict)
    return results
#######################################################