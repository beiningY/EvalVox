import numpy as np
import json
from jiwer import compute_measures, process_words
import os
from pyannote.core import Segment, Annotation
from pyannote.metrics.detection import DetectionErrorRate

################################Class_WERDER#####################################
"""
Cette partie ne concerne que les adultes
WER et DER pour toutes les classes
fichiers d'entrée : fichier de référence converti par eaf2jsonWER et fichier d'hypothèse converti par txt2json pour la partie WER
                  : fichier de référence converti par eaf2jsonDER et fichier d'hypothèse converti par textgrid2json pour la partie DER
sorties : WER et DER par classe sans détails avec deux graphiques comparatives générées
"""
# Fonction pour calculer le WER entre le fichier hypothèse et le fichier de référence
def calculate_wer_class(hypothesis_file, reference_file):
    hypothesis_data = json.load(hypothesis_file)
    reference_data = json.load(reference_file)

    measures_by_class = {}

    # Parcourir les segments dans les fichiers d'hypothèse et de référence
    for h_segment in hypothesis_data:
        for r_segment in reference_data:
            if h_segment['class_id'] == r_segment['class_id']:
                # Vérifier si les segments correspondent
                if (h_segment['file_id'] == r_segment['file_id'] and
                    (h_segment['start_time'] == r_segment['start_time'] or abs(h_segment['end_time'] - r_segment['end_time']) < 0.1)):
                        class_id = h_segment['class_id']
                        h_text = h_segment['hypothesis']
                        r_text = r_segment['transcript']
                        measures = compute_measures(r_text, h_text)

                        # Calculer et stocker les mesures pour chaque classe
                        if class_id not in measures_by_class:
                            measures_by_class[class_id] = {"total_errors": 0, "total_words": 0}
                        measures_by_class[class_id]["total_errors"] += measures["wer"] * len(h_text.split())
                        measures_by_class[class_id]["total_words"] += len(h_text.split())

    # Calculer le WER total par classe
    total_wer_by_class = {class_id: {"wer": measures["total_errors"] / measures["total_words"] if measures["total_words"] > 0 else 0} for class_id, measures in measures_by_class.items()}

    return total_wer_by_class

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

        # Créer et stocker l'annotation pour chaque classe et fichier
        if class_id not in annotations_by_class_file:
            annotations_by_class_file[class_id] = {}
        if label not in annotations_by_class_file[class_id]:
            annotations_by_class_file[class_id][label] = Annotation()

        annotations_by_class_file[class_id][label][segment] = label
    return annotations_by_class_file

# Fonction pour calculer le DER entre le fichier hypothèse et le fichier de référence
def calculate_der_class(hypothesis_fileder, reference_fileder):
    reference_annotations = load_annotation_from_json_class(reference_fileder)
    hypothesis_annotations = load_annotation_from_json_class(hypothesis_fileder)

    der_results = {}  

    # Parcourir les annotations de référence par classe
    for class_id, file_annotations in reference_annotations.items():
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et annotations de référence
        for file_id, reference_annotation in file_annotations.items():
            hypothesis_annotation = hypothesis_annotations.get(class_id, {}).get(file_id, Annotation())  
            components = der(reference_annotation, hypothesis_annotation, detailed=True)

            total_miss += components['miss']
            total_false_alarm += components['false alarm']
            total_total += components['total']

        # Calculer et stocker le taux d'erreur de détection (DER) pour chaque classe
        if total_total != 0:
            error_rate = (total_miss + total_false_alarm) / total_total
            der_results[class_id] = {"der": error_rate}

    return der_results

def adult_class(hypothesis_filewer, reference_filewer, hypothesis_fileder, reference_fileder):
    # Calcul des résultats WER et DER 
    wer_results = calculate_wer_class(hypothesis_filewer, reference_filewer)
    der_results = calculate_der_class(hypothesis_fileder, reference_fileder)

    # Fusion des clés des résultats WER et DER pour garantir que toutes les classes sont incluses
    classes = list(set(wer_results.keys()) | set(der_results.keys()))

    # Extraction des valeurs WER et DER par classe
    wer_values = [wer_results.get(cl, {"wer": 0})["wer"] for cl in classes]
    der_values = [der_results.get(cl, {"der": 0})["der"] for cl in classes]

    # Création des données pour le graphique
    chart_data = {
        'labels': classes,
        'datasets': [
            {
                'label': 'WER',
                'data': wer_values,
                'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1,
                'yAxisID': 'y',
            }
        ]
    }

    # Ajout du jeu de données DER uniquement s'il existe des valeurs DER non nulles
    if any(der_values):
        chart_data['datasets'].append({
            'label': 'DER',
            'data': der_values,
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1,
            'yAxisID': 'y',
        })

    # Création des données pour le nuage de points
    scatter_data = [{'x': wer, 'y': der} for wer, der in zip(wer_values, der_values) if der != 0]

    # Contexte contenant les résultats WER et DER
    context = {
        'wer_results': wer_results,
        'der_results': der_results,
    }
    return context, chart_data, scatter_data

#####################################################################

################################Situation_WERDER#####################################
"""
Cette partie ne concerne que les adultes
WER et DER pour toutes les situations
fichiers d'entrée : fichier de référence converti par eaf2jsonWER et fichier d'hypothèse converti par txt2json pour la partie WER
                  : fichier de référence converti par eaf2jsonDER et fichier d'hypothèse converti par textgrid2json pour la partie DER
sorties : WER et DER par situation sans détails avec deux graphiques comparatives générées
"""
# Fonction pour calculer le WER entre le fichier hypothèse et le fichier de référence
def calculate_wer_situation(hypothesis_file, reference_file):
    hypothesis_data = json.load(hypothesis_file)

    reference_data = json.load(reference_file)

    measures_by_situation = {}

    # Parcourir les segments dans les fichiers d'hypothèse et de référence
    for r_segment in reference_data:
        for h_segment in hypothesis_data:
            # Vérifier si les segments correspondent
            if (h_segment['file_id'] == r_segment['file_id'] and
                (h_segment['start_time'] == r_segment['start_time'] or abs(h_segment['end_time'] - r_segment['end_time']) < 0.1)):
                situation = r_segment['situation']
                h_text = h_segment['hypothesis']
                r_text = r_segment['transcript']
                measures = compute_measures(r_text, h_text)

                # Calculer et stocker les mesures pour chaque situation
                if situation not in measures_by_situation:
                    measures_by_situation[situation] = {"total_errors": 0, "total_words": 0}
                measures_by_situation[situation]["total_errors"] += measures["wer"] * len(h_text.split())
                measures_by_situation[situation]["total_words"] += len(h_text.split())

    # Calculer le WER total par situation
    total_wer_by_situation = {situation: {"wer": measures["total_errors"] / measures["total_words"] if measures["total_words"] > 0 else 0} for situation, measures in measures_by_situation.items()}

    return total_wer_by_situation

# Fonction pour charger les annotations depuis des fichiers JSON
def load_annotation_from_json_situation(ref_json_file, hyp_json_file):
    annotations_by_situation_file = {}

    ref_data = json.load(ref_json_file)
    hyp_data = json.load(hyp_json_file)

    # Parcourir les données de référence et d'hypothèse en parallèle
    for ref_segment_data, hyp_segment_data in zip(ref_data, hyp_data):
        ref_start_time = ref_segment_data.get('start_time', 0)
        ref_end_time = ref_segment_data.get('end_time', 0)
        ref_segment = Segment(ref_start_time, ref_end_time)
        ref_label = str(ref_segment_data.get('file_id', ''))
        ref_speaker_id = ref_segment_data.get('speaker_id', '')
        ref_situation = ref_segment_data.get('situation', '')
        ref_class_id = ref_segment_data.get('class_id', '')  

        hyp_start_time = hyp_segment_data.get('start_time', 0)
        hyp_end_time = hyp_segment_data.get('end_time', 0)
        hyp_segment = Segment(hyp_start_time, hyp_end_time)
        hyp_label = str(hyp_segment_data.get('file_id', ''))

        # Créer et stocker l'annotation pour chaque situation et fichier
        if ref_situation not in annotations_by_situation_file:
            annotations_by_situation_file[ref_situation] = {}
        if ref_label not in annotations_by_situation_file[ref_situation]:
            annotations_by_situation_file[ref_situation][ref_label] = []

        annotations_by_situation_file[ref_situation][ref_label].append((ref_segment, hyp_segment))

    return annotations_by_situation_file

# Fonction pour calculer le DER entre le fichier hypothèse et le fichier de référence
def calculate_der_situation(hypothesis_fileder, reference_fileder):
    reference_annotations = load_annotation_from_json_situation(reference_fileder, hypothesis_fileder)

    der_results = {}  # Dictionnaire pour stocker les résultats DER pour chaque situation

    # Parcourir les annotations de référence par situation
    for situation, file_annotations in reference_annotations.items():
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et segments d'annotations de référence
        for file_id, segments in file_annotations.items():
            reference_annotation = Annotation()
            hypothesis_annotation = Annotation()

            # Ajouter les segments d'annotations pour le fichier donné
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
            der_results[situation] = {"der": error_rate}

    return der_results

def adult_situation(hypothesis_filewer, reference_filewer, hypothesis_fileder, reference_fileder):
    # Calcul des résultats WER et DER
    wer_results = calculate_wer_situation(hypothesis_filewer, reference_filewer)
    der_results = calculate_der_situation(hypothesis_fileder, reference_fileder)

    # Fusion des clés des résultats WER et DER pour garantir que toutes les situations sont incluses
    situations = list(set(wer_results.keys()) | set(der_results.keys()))

    # Extraction des valeurs WER et DER par situation
    wer_values = [wer_results.get(st, {"wer": 0})["wer"] for st in situations]
    der_values = [der_results.get(st, {"der": 0})["der"] for st in situations]

    # Création des données pour le graphique
    chart_data = {
        'labels': situations,
        'datasets': [
            {
                'label': 'WER',
                'data': wer_values,
                'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                'borderColor': 'rgba(255, 99, 132, 1)',
                'borderWidth': 1,
                'yAxisID': 'y',
            }
        ]
    }

    # Ajout du jeu de données DER uniquement s'il existe des valeurs DER non nulles
    if any(der_values):  
        chart_data['datasets'].append({
            'label': 'DER',
            'data': der_values,
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1,
            'yAxisID': 'y',
        })

    # Création des données pour le nuage de points
    scatter_data = [{'x': wer, 'y': der} for wer, der in zip(wer_values, der_values) if der != 0]

    # Contexte contenant les résultats WER et DER
    context = {
        'wer_results': wer_results,
        'der_results': der_results,
    }
    return context, chart_data, scatter_data

#####################################################################

################################Speaker_WERDER#####################################
"""
Cette partie ne concerne que les adultes
WER et DER pour tous les locuteurs
fichiers d'entrée : fichier de référence converti par eaf2jsonWER et fichier d'hypothèse converti par txt2json pour la partie WER
                  : fichier de référence converti par eaf2jsonDER et fichier d'hypothèse converti par textgrid2json pour la partie DER
sorties : WER et DER par locuteur sans détails avec deux graphiques comparatives générées
"""
# Fonction pour calculer le WER entre le fichier hypothèse et le fichier de référence
def calculate_wer_speaker(hypothesis_filewer, reference_filewer):
    hypothesis_data = json.load(hypothesis_filewer)
    reference_data = json.load(reference_filewer)

    measures_by_speaker = {}

    # Parcourir les segments dans les fichiers d'hypothèse et de référence
    for h_segment in hypothesis_data:
        for r_segment in reference_data:
            # Vérifier si les segments correspondent au même locuteur et fichier
            if h_segment['speaker_id'] == r_segment['speaker_id']:
                if (h_segment['file_id'] == r_segment['file_id'] and
                        (h_segment['start_time'] == r_segment['start_time'] or abs(h_segment['end_time'] - r_segment['end_time']) < 0.1)):
                        speaker_id = h_segment['speaker_id']
                        h_text = h_segment['hypothesis']
                        r_text = r_segment['transcript']
                        measures = compute_measures(r_text, h_text)

                        # Calculer et stocker les mesures pour chaque locuteur
                        if speaker_id not in measures_by_speaker:
                            measures_by_speaker[speaker_id] = {"total_errors": 0, "total_words": 0}
                        measures_by_speaker[speaker_id]["total_errors"] += measures["wer"] * len(h_text.split())
                        measures_by_speaker[speaker_id]["total_words"] += len(h_text.split())

    # Calculer le WER total par locuteur
    total_wer_by_speaker = {speaker: {"wer": measures["total_errors"] / measures["total_words"] if measures["total_words"] > 0 else 0} for speaker, measures in measures_by_speaker.items()}

    return total_wer_by_speaker

# Fonction pour charger les annotations depuis un fichier JSON
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

        # Créer et stocker l'annotation pour chaque locuteur et fichier
        if speaker_id not in annotations_by_speaker_file:
            annotations_by_speaker_file[speaker_id] = {}
        if label not in annotations_by_speaker_file[speaker_id]:
            annotations_by_speaker_file[speaker_id][label] = Annotation()

        annotations_by_speaker_file[speaker_id][label][segment] = label
    return annotations_by_speaker_file

# Fonction pour calculer le DER entre le fichier hypothèse et le fichier de référence
def calculate_der_speaker(hypothesis_fileder, reference_fileder):
    reference_annotations = load_annotation_from_json_speaker(reference_fileder)
    hypothesis_annotations = load_annotation_from_json_speaker(hypothesis_fileder)

    der_results = {}  # Dictionnaire pour stocker les résultats DER pour chaque locuteur

    # Parcourir les annotations de référence par locuteur
    for speaker_id, file_annotations in reference_annotations.items():
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et segments d'annotations de référence
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

    return der_results

def adult_speaker(hypothesis_filewer, reference_filewer, hypothesis_fileder, reference_fileder):
    # Calcul des résultats WER et DER
    wer_results = calculate_wer_speaker(hypothesis_filewer, reference_filewer)
    der_results = calculate_der_speaker(hypothesis_fileder, reference_fileder)

    # Fusion des clés des résultats WER et DER pour garantir que tous les locuteurs sont inclus
    speakers = list(set(wer_results.keys()).union(der_results.keys()))

    # Initialisation des listes pour les valeurs WER et DER
    wer_values = []
    der_values = []

    # Initialisation des jeux de données pour les données du graphique avec WER et DER
    datasets = [
        {
            'label': 'WER',
            'data': [],
            'backgroundColor': 'rgba(255, 99, 132, 0.5)',
            'borderColor': 'rgba(255, 99, 132, 1)',
            'borderWidth': 1,
            'yAxisID': 'y',
        },
        {
            'label': 'DER',
            'data': [],
            'backgroundColor': 'rgba(54, 162, 235, 0.5)',
            'borderColor': 'rgba(54, 162, 235, 1)',
            'borderWidth': 1,
            'yAxisID': 'y',
        }
    ]

    # Boucle sur chaque locuteur
    for speaker in speakers:
        # Ajout des valeurs WER pour tous les locuteurs
        wer_value = wer_results.get(speaker, {}).get("wer", 0)  # Utilisation de 0 si WER n'est pas disponible
        datasets[0]['data'].append(wer_value)

        # Ajout des valeurs DER seulement si elles sont disponibles
        if speaker in der_results:
            der_value = der_results[speaker]["der"]
            datasets[1]['data'].append(der_value)
        else:
            # Si les données DER ne sont pas disponibles pour un locuteur, ne pas les inclure dans le jeu de données DER
            datasets[1]['data'].append(None)  # Vous pouvez choisir comment gérer les valeurs DER manquantes

    # Création des données pour le graphique
    chart_data = {
        'labels': speakers,
        'datasets': datasets
    }

    # Création des données pour le nuage de points
    scatter_data = [
        {'x': wer, 'y': der or 0}  # Remplacer None par 0 ou une autre logique pour le nuage de points
        for wer, der in zip(datasets[0]['data'], datasets[1]['data'])
        if der is not None  # Inclure uniquement les points avec à la fois WER et DER
    ]

    # Contexte contenant les résultats WER et DER
    context = {
        'wer_results': wer_results,
        'der_results': der_results,
    }
    return context, chart_data, scatter_data
#####################################################################