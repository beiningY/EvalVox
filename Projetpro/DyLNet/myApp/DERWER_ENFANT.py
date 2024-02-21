import matplotlib.pyplot as plt
import numpy as np
import json
from pyannote.core import Segment, Annotation
from pyannote.metrics.detection import DetectionErrorRate
"""
Ce script ne concerne que les enfants
DER pour toutes les classes
fichiers d'entrée : fichier reference converti par eaf2jsonDER et fichier hypothese converti par textgrid2json pour la partie DER           
sorties : DER par classe sans détails avec deux graphiques comparatives générées
"""
# Fonction pour charger les annotations depuis un fichier JSON
def load_annotation_from_json_class(json_file):
    annotations_by_class_file = {}
    data = json.load(json_file)
    for segment_data in data:
        start_time = segment_data.get('start_time', 0)
        end_time = segment_data.get('end_time', 0)
        segment = Segment(start_time, end_time)
        label = str(segment_data.get('file_id', ''))
        class_id = segment_data.get('class_id', '')
        situation = segment_data.get('situation', '')
        speaker_id = segment_data.get('speaker_id', '')

        # Créer et stocker l'annotation pour chaque classe, fichier et locuteur
        if class_id not in annotations_by_class_file:
            annotations_by_class_file[class_id] = {"annotations": {}, "speaker_ids": []}
        if label not in annotations_by_class_file[class_id]["annotations"]:
            annotations_by_class_file[class_id]["annotations"][label] = Annotation()

        annotations_by_class_file[class_id]["annotations"][label][segment] = label
        if speaker_id not in annotations_by_class_file[class_id]["speaker_ids"]:
            annotations_by_class_file[class_id]["speaker_ids"].append(speaker_id)

    return annotations_by_class_file

# Fonction pour calculer le DER entre le fichier hypothèse et le fichier de référence
def calculate_der_class(hypothesis_fileder, reference_fileder):

    reference_annotations = load_annotation_from_json_class(reference_fileder)
    hypothesis_annotations = load_annotation_from_json_class(hypothesis_fileder)
    
    der_results = {} 

    for class_id, class_data in reference_annotations.items():
        # 创建 DetectionErrorRate 实例
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # 遍历每个类别的参考注释文件和片段
        for file_id, reference_annotation in class_data["annotations"].items():
            hypothesis_annotation = hypothesis_annotations.get(class_id, {}).get("annotations", {}).get(file_id, Annotation())
            components = der(reference_annotation, hypothesis_annotation, detailed=True)

            total_miss += components['miss']
            total_false_alarm += components['false alarm']
            total_total += components['total']


        if total_total != 0:
            error_rate = (total_miss + total_false_alarm) / total_total
            
            speaker_ids_filtered = [speaker_id for speaker_id in class_data["speaker_ids"] if speaker_id.startswith('0')]
            
            if speaker_ids_filtered:
                der_results[class_id] = {"der": error_rate, "speaker_ids": speaker_ids_filtered}

    return der_results


def enfant_class(hypothesis_fileder, reference_fileder):

    der_results = calculate_der_class(hypothesis_fileder, reference_fileder)

   
    classes = list(der_results.keys())
    der_values = [der_results[class_id]["der"] for class_id in classes]

  
    chart_data = {
        'labels': classes, 
        'datasets': [
            {
                'label': 'DER',
                'data': der_values,
                'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1,
                'yAxisID': 'y',
            }
        ]
    }


    scatter_data = [{'x': class_id, 'y': values["der"]} for class_id, values in der_results.items() if isinstance(values, dict)]

    return der_results, chart_data, scatter_data


"""
Ce script ne concerne que les enfants
DER pour toutes les situations
fichiers d'entrée : fichier reference converti par eaf2jsonDER et fichier hypothese converti par textgrid2json pour la partie DER           
sorties : DER par situation sans détails avec deux graphiques comparatives générées
"""
# Fonction pour charger les annotations depuis les fichiers JSON de référence et d'hypothèse
def load_annotation_from_json_situation(ref_json_file, hyp_json_file):
    annotations_by_situation_file = {}

    ref_data = json.load(ref_json_file)
    hyp_data = json.load(hyp_json_file)

    for ref_segment_data, hyp_segment_data in zip(ref_data, hyp_data):
        ref_start_time = ref_segment_data.get('start_time', 0)
        ref_end_time = ref_segment_data.get('end_time', 0)
        ref_segment = Segment(ref_start_time, ref_end_time)
        ref_label = str(ref_segment_data.get('file_id', ''))
        ref_speaker_id = ref_segment_data.get('speaker_id', '')

        # Skip if the speaker_id does not start with '0'
        if not ref_speaker_id.startswith('0'):
            continue

        ref_situation = ref_segment_data.get('situation', '')
        ref_class_id = ref_segment_data.get('class_id', '')  

        hyp_start_time = hyp_segment_data.get('start_time', 0)
        hyp_end_time = hyp_segment_data.get('end_time', 0)
        hyp_segment = Segment(hyp_start_time, hyp_end_time)
        hyp_label = str(hyp_segment_data.get('file_id', ''))

        # Créer et stocker l'annotation pour chaque situation, fichier et locuteur
        if ref_situation not in annotations_by_situation_file:
            annotations_by_situation_file[ref_situation] = {"speaker_ids": []}
        if ref_label not in annotations_by_situation_file[ref_situation]:
            annotations_by_situation_file[ref_situation][ref_label] = []

        annotations_by_situation_file[ref_situation][ref_label].append((ref_segment, hyp_segment))
        
        # Ajouter le speaker_id à la liste s'il n'est pas déjà présent
        if ref_speaker_id not in annotations_by_situation_file[ref_situation]["speaker_ids"]:
            annotations_by_situation_file[ref_situation]["speaker_ids"].append(ref_speaker_id)

    return annotations_by_situation_file

# Fonction pour calculer le DER entre le fichier hypothèse et le fichier de référence
def calculate_der_situation(hypothesis_fileder, reference_fileder):
    reference_annotations = load_annotation_from_json_situation(reference_fileder, hypothesis_fileder)

    der_results = {}  # Dictionnaire pour stocker les résultats DER pour chaque situation

    for situation, file_annotations in reference_annotations.items():
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et segments d'annotations de référence pour chaque situation
        for file_id, segments in file_annotations.items():
            if file_id == "speaker_ids":
                continue   # Ignorer ce file_id s'il ne correspond pas aux segments attendus

            reference_annotation = Annotation()
            hypothesis_annotation = Annotation()

            # Ajouter les segments à l'annotation de référence et d'hypothèse
            for ref_segment, hyp_segment in segments:
                reference_annotation[ref_segment] = situation
                hypothesis_annotation[hyp_segment] = situation

            components = der(reference_annotation, hypothesis_annotation, detailed=True)

            total_miss += components['miss']
            total_false_alarm += components['false alarm']
            total_total += components['total']
        
        # Calculer et stocker le taux d'erreur de détection (DER) pour chaque situation
        if total_total != 0:
            error_rate = (total_miss + total_false_alarm) / total_total
            der_results[situation] = {"der": error_rate, "speaker_ids": file_annotations["speaker_ids"]}

    # Filtrer les situations dont les identifiants de locuteurs commencent par "0"
    der_results_filtered = {situation: values for situation, values in der_results.items() if any(speaker_id.startswith('0') for speaker_id in values["speaker_ids"])}
    return der_results_filtered

def enfant_situation(hypothesis_fileder, reference_fileder):
    der_results = calculate_der_situation(hypothesis_fileder, reference_fileder)
    situations = list(der_results.keys())
    der_values = [der_results[situation]["der"] for situation in situations]

    chart_data = {
        'labels': situations,
        'datasets': [
            {
                'label': 'DER',
                'data': der_values,
                'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                'borderColor': 'rgba(54, 162, 235, 1)',
                'borderWidth': 1,
                'yAxisID': 'y',
            }
        ]
    }

    scatter_data = [
        {'x': index, 'y': value}
        for index, value in enumerate(der_values)
    ]

    return der_results, chart_data, scatter_data



"""
Ce script ne concerne que les enfants
DER pour tous les locuteurs
fichiers d'entrée : fichier reference converti par eaf2jsonDER et fichier hypothese converti par textgrid2json pour la partie DER           
sorties : DER par locuteur sans détails avec deux graphiques comparatives générées
"""
# Fonction pour charger les annotations depuis le fichier JSON
def load_annotation_from_json_speaker(json_file):
    annotations_by_speaker_file = {}

    data = json.load(json_file)
    for segment_data in data:
        start_time = segment_data.get('start_time', 0)
        end_time = segment_data.get('end_time', 0)
        segment = Segment(start_time, end_time)
        label = str(segment_data.get('file_id', ''))
        speaker_id = segment_data.get('speaker_id', '')
        situation = segment_data.get('situation', '')
        class_id = segment_data.get('class_id', '')

        # Créer une structure pour stocker les annotations par locuteur, fichier et segment
        if speaker_id not in annotations_by_speaker_file:
            annotations_by_speaker_file[speaker_id] = {}
        if label not in annotations_by_speaker_file[speaker_id]:
            annotations_by_speaker_file[speaker_id][label] = Annotation()

        annotations_by_speaker_file[speaker_id][label][segment] = label

    return annotations_by_speaker_file

# Fonction pour calculer le DER entre les fichiers hypothèse et de référence
def calculate_der_speaker(hypothesis_fileder, reference_fileder):
    reference_annotations = load_annotation_from_json_speaker(reference_fileder)
    hypothesis_annotations = load_annotation_from_json_speaker(hypothesis_fileder)

    der_results = {}  # Dictionnaire pour stocker les résultats DER pour chaque locuteur

    for speaker_id, file_annotations in reference_annotations.items():
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et annotations de référence pour chaque locuteur
        for file_id, reference_annotation in file_annotations.items():
            hypothesis_annotation = hypothesis_annotations.get(speaker_id, {}).get(file_id, Annotation())
            components = der(reference_annotation, hypothesis_annotation, detailed=True)

            total_miss += components['miss']
            total_false_alarm += components['false alarm']
            total_total += components['total']

        # Calculer et stocker le taux d'erreur de détection (DER) pour chaque locuteur
        if total_total != 0:
            error_rate = (total_miss + total_false_alarm) / total_total
            der_results[speaker_id] = {"der": error_rate}

    # Filtrer les locuteurs dont l'identifiant commence par "0"
    der_results_filtered = {speaker_id: values for speaker_id, values in der_results.items() if speaker_id.startswith('0')}

    return der_results_filtered

def enfant_speaker(hypothesis_fileder, reference_fileder):
    der_results = calculate_der_speaker(hypothesis_fileder, reference_fileder)

    speakers = list(der_results.keys())
    der_values = [result["der"] for result in der_results.values()]

    chart_data = {
        'labels': speakers,
        'datasets': [
            {
                'label': 'DER',
                'data': der_values,
                'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1,
                'yAxisID': 'y',
            }
        ]
    }

    scatter_data = [
        {'x': index, 'y': value}
        for index, value in enumerate(der_values)
    ]

    return der_results, chart_data, scatter_data

