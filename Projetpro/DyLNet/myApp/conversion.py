from bs4 import BeautifulSoup
import os
import json
import unicodedata 
from praatio import tgio 
from bs4 import BeautifulSoup
import unicodedata
import spacy
import string
from unidecode import unidecode

def unicode_normalisation(text):
    try:
        return unicode(text, "utf-8")
    except NameError:  
        return str(text)

def strip_accents(text):
    text = (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )
    return str(text)

def eaf2jsonDER(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    results = derprocess_eaf_content(xml_content, os.path.splitext(os.path.basename(file_path))[0])
    return results 

def derprocess_eaf_content(xml_content, file_name):
    soup = BeautifulSoup(xml_content, 'xml')
    time_slots = {slot['TIME_SLOT_ID']: int(slot['TIME_VALUE']) for slot in soup.find_all('TIME_SLOT')}
    annotations_tier = soup.find('TIER', {'TIER_ID': lambda x: x.startswith('*') and x.endswith('_nettoye')})
    situation_tier = soup.find('TIER', {'TIER_ID': 'Activité en cours'})
    
    results = []

    if annotations_tier and situation_tier:
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

"""
Ce script concerne les enfants et les adultes
fichiers d'entrée : .textgrid (fichier hypothese)         
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


def normalize_french(text):
    # Charger le modèle spaCy pour le français
    nlp = spacy.load('fr_core_news_sm')
    doc = nlp(text.lower())
    translator = str.maketrans('', '', string.punctuation.replace('<', '').replace('>', ''))
    return " ".join([token.text.translate(translator) for token in doc])

# Fonction pour convertir le format EAF en format JSON
def eaf2jsonWER(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_content = file.read()

    results = werprocess_eaf_content(xml_content, os.path.splitext(os.path.basename(file_path))[0])
    return results

def werprocess_eaf_content(xml_content, file_name):
    soup = BeautifulSoup(xml_content, 'xml')
    time_slots = {slot['TIME_SLOT_ID']: int(slot['TIME_VALUE']) for slot in soup.find_all('TIME_SLOT')}
    annotations_tier = soup.find('TIER', {'TIER_ID': lambda x: x.startswith('*') and x.endswith('_nettoye')})
    situation_tier = soup.find('TIER', {'TIER_ID': 'Activité en cours'})
    results = []

    if annotations_tier and situation_tier:
        for annotation, situation_annotation in zip(annotations_tier.find_all('ALIGNABLE_ANNOTATION'), situation_tier.find_all('ALIGNABLE_ANNOTATION')):
            start_time = round(time_slots[annotation['TIME_SLOT_REF1']] / 1000, 2)
            end_time = round(time_slots[annotation['TIME_SLOT_REF2']] / 1000, 2)
            orthographic_transcript = strip_accents(annotation.find('ANNOTATION_VALUE').text)
            orthographic_transcript = normalize_french(orthographic_transcript)
            situation = strip_accents(situation_annotation.find('ANNOTATION_VALUE').text)  
            file_id_parts = file_name.split('-')
            file_id = '-'.join(file_id_parts[:7])
            parts_speaker = file_id.split('-')
            speaker_id = parts_speaker[3].strip()
            class_parts = file_name.split('-')
            class_id = class_parts[0].strip()

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


def txt2json(file_path):

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    lines = [line.strip() for line in lines]


    for i in range(12, len(lines), 5):
        file_id_full = lines[i]
        file_id_parts = file_id_full.split("_")
        file_part = "_".join(file_id_parts[:-3]).strip()
        file_id = file_part[:-2]

        line_parts = file_id.split("-")
        speaker_id = line_parts[3].strip()
        class_id = line_parts[0].strip()

        file_id_nower = lines[i]
        file_id_parts2 = file_id_nower.split(",")
        nower = file_id_parts2[0]
        nofile = nower.split("-")
        rvb = nofile[-1]
        times = rvb.split("_")
        start_time = times[2]
        end_time = times[3]

        hypothesis = lines[i + 3]
        processed_hypothesis = ' '.join(hypothesis.split(';')).lower().strip()
        processed_hypothesis = unidecode(processed_hypothesis)
        results = []
    
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