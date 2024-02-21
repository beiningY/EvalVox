import os
from pyannote.core import Segment, Annotation
from pyannote.metrics.detection import DetectionErrorRate
import json
import io
import sys

"""
Ce script concerne les adultes et les enfants
DER pour toutes les situations
fichiers d'entrée : fichier reference converti par eaf2jsonDER et fichier hypothese converti par textgrid2json
sorties : DER par situation avec détails (détails: total missed detection et total false alarm) et segments hypotheses, segments references, segments consideré comme missed alarms et false alarms
"""

# Fonction pour charger les annotations depuis les fichiers JSON de référence et hypothèse
def sit_load_annotation_from_json(ref_json_file, hyp_json_file):
    annotations_by_situation_file = {}

    with open(ref_json_file, 'r') as ref_file, open(hyp_json_file, 'r') as hyp_file:
        ref_data = json.load(ref_file)
        hyp_data = json.load(hyp_file)

        # Parcourir les données des fichiers de référence et hypothèse simultanément
        for ref_segment_data, hyp_segment_data in zip(ref_data, hyp_data):
            # Extraire les informations du segment de référence
            ref_start_time = ref_segment_data.get('start_time', 0)
            ref_end_time = ref_segment_data.get('end_time', 0)
            ref_segment = Segment(ref_start_time, ref_end_time)
            ref_label = str(ref_segment_data.get('file_id', ''))
            ref_speaker_id = ref_segment_data.get('speaker_id', '')
            ref_situation = ref_segment_data.get('situation', '')
            ref_class_id = ref_segment_data.get('class_id', '')  

            # Extraire les informations du segment d'hypothèse
            hyp_start_time = hyp_segment_data.get('start_time', 0)
            hyp_end_time = hyp_segment_data.get('end_time', 0)
            hyp_segment = Segment(hyp_start_time, hyp_end_time)
            hyp_label = str(hyp_segment_data.get('file_id', ''))

            # Créer une structure pour stocker les annotations par situation, fichier et segment
            # Utiliser les situations dans la reference et matcher avec l'hypothèse selon l'ordre des segments
            if ref_situation not in annotations_by_situation_file:
                annotations_by_situation_file[ref_situation] = {}
            if ref_label not in annotations_by_situation_file[ref_situation]:
                annotations_by_situation_file[ref_situation][ref_label] = []

            # Ajouter les segments de référence et d'hypothèse à la structure
            annotations_by_situation_file[ref_situation][ref_label].append((ref_segment, hyp_segment))


    return annotations_by_situation_file


# Fonction pour obtenir les segments manqués et les fausses alarmes
def sit_get_missed_and_false_alarm_segments(reference_annotation, hypothesis_annotation):
    reference_segments = set(reference_annotation.itertracks())
    hypothesis_segments = set(hypothesis_annotation.itertracks())

    missed_detections = reference_segments - hypothesis_segments
    false_alarms = hypothesis_segments - reference_segments

    return missed_detections, false_alarms

# Fonction pour obtenir les segments corrects
def sit_get_correct_segments(reference_annotation, hypothesis_annotation):
    reference_segments = set(reference_annotation.itertracks())
    hypothesis_segments = set(hypothesis_annotation.itertracks())

    correct_detections = reference_segments & hypothesis_segments

    return correct_detections

# Fonction pour formater un segment
def sit_format_segment(segment, file_id):
    start, end = segment
    start_hour, start_min = divmod(start, 3600)
    start_min, start_sec = divmod(start_min, 60)
    end_hour, end_min = divmod(end, 3600)
    end_min, end_sec = divmod(end_min, 60)
    return f"[ {start_hour:02.0f}:{start_min:02.0f}:{start_sec:06.3f} -->  {end_hour:02.0f}:{end_min:02.0f}:{end_sec:06.3f}] _ {file_id}"

def der_process_for_situation(ref,hyp):
    output = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = output

    # Charger les annotations de référence et d'hypothèse
    reference_annotations = sit_load_annotation_from_json(ref,hyp)
    # Parcourir les annotations par situation
    for situation, file_annotations in reference_annotations.items():
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et segments de référence pour chaque situation
        for file_id, segments in file_annotations.items():
            reference_annotation = Annotation()
            hypothesis_annotation = Annotation()

            # Ajouter les segments de référence et d'hypothèse aux annotations respectives
            for ref_segment, hyp_segment in segments:
                reference_annotation[ref_segment] = situation
                hypothesis_annotation[hyp_segment] = situation

            # Calculer les composants DER pour chaque fichier
            components = der(reference_annotation, hypothesis_annotation, detailed=True)

            # Cumuler les composants pour calculer le DER total
            total_miss += components['miss']
            total_false_alarm += components['false alarm']
            total_total += components['total']
        
        # Calculer et afficher le taux d'erreur de détection (DER) pour chaque situation
        if total_total != 0:
            error_rate = (total_miss + total_false_alarm) / total_total
            print(f'Detection Error Rate for Situation {situation}:')
            print(f'Total Missed Detections: {total_miss:.2f}')
            print(f'Total False Alarms: {total_false_alarm:.2f}')
            print(f'Total References: {total_total:.2f}')
            print(f'Error Rate: {error_rate:.2%}\n')
        else:
            print(f'No annotations found for Situation {situation}\n')

        # Afficher les segments manqués, les fausses alarmes et les segments corrects pour chaque fichier
        for file_id, segments in file_annotations.items():
            reference_annotation = Annotation()
            hypothesis_annotation = Annotation()

            # Ajouter les segments de référence et d'hypothèse aux annotations respectives
            for ref_segment, hyp_segment in segments:
                reference_annotation[ref_segment] = situation
                hypothesis_annotation[hyp_segment] = situation

            # Obtenir les segments manqués et les fausses alarmes
            missed_detections, false_alarms = sit_get_missed_and_false_alarm_segments(reference_annotation, hypothesis_annotation)
            correct_detections = sit_get_correct_segments(reference_annotation, hypothesis_annotation)

            print(f'Reference segments for Situation {situation} in File {file_id}:')
            print(reference_annotation)
            print(f'Hypothesis segments for Situation {situation} in File {file_id}:')
            print(hypothesis_annotation)

            print(f'Missed detections for Situation {situation} in File {file_id}:')
            if not missed_detections:
                print('There are no missed detections')
            else:
                for segment in missed_detections:
                    print(sit_format_segment(segment[0], file_id))

            print(f'False alarms for Situation {situation} in File {file_id}:')
            if not false_alarms:
                print('There are no false alarms')
            else:
                for segment in false_alarms:
                    print(sit_format_segment(segment[0], file_id))

            print(f'Correct detections for Situation {situation} in File {file_id}:')
            if not correct_detections:
                print('There are no correct segments')
            else:
                for segment in correct_detections:
                    print(sit_format_segment(segment[0], file_id))
            print('\n')

    sys.stdout = original_stdout

    contents = output.getvalue()

    output.close()

    return contents




"""
Ce script concerne les adultes et les enfants
DER pour toutes les classes
fichiers d'entrée : fichier reference converti par eaf2jsonDER et fichier hypothese converti par textgrid2json
sorties : DER par classe avec détails (détails: total missed detection et total false alarm) et segments hypotheses, segments references, segments consideré comme missed alarms et false alarms
"""
# Fonction pour charger les annotations depuis le fichier JSON
def cla_load_annotation_from_json(json_file):
    annotations_by_class_file = {}

    with open(json_file, 'r') as file:
        data = json.load(file)
        for segment_data in data:
            start_time = segment_data.get('start_time', 0)
            end_time = segment_data.get('end_time', 0)
            segment = Segment(start_time, end_time)
            label = str(segment_data.get('file_id', ''))
            class_id = segment_data.get('class_id', '')  
            situation = segment_data.get('situation', '')

            # Créer une structure pour stocker les annotations par classe, fichier et segment
            if class_id not in annotations_by_class_file:
                annotations_by_class_file[class_id] = {}
            if label not in annotations_by_class_file[class_id]:
                annotations_by_class_file[class_id][label] = Annotation()

            annotations_by_class_file[class_id][label][segment] = label

    return annotations_by_class_file

# Fonction pour obtenir les segments manqués et les fausses alarmes
def cla_get_missed_and_false_alarm_segments(reference_annotation, hypothesis_annotation):
    reference_segments = set(reference_annotation.itertracks())
    hypothesis_segments = set(hypothesis_annotation.itertracks())

    missed_detections = reference_segments - hypothesis_segments
    false_alarms = hypothesis_segments - reference_segments

    return missed_detections, false_alarms

# Fonction pour obtenir les segments corrects
def cla_get_correct_segments(reference_annotation, hypothesis_annotation):
    reference_segments = set(reference_annotation.itertracks())
    hypothesis_segments = set(hypothesis_annotation.itertracks())

    correct_detections = reference_segments & hypothesis_segments

    return correct_detections

# Fonction pour formater un segment
def cla_format_segment(segment, file_id):
    start, end = segment
    start_hour, start_min = divmod(start, 3600)
    start_min, start_sec = divmod(start_min, 60)
    end_hour, end_min = divmod(end, 3600)
    end_min, end_sec = divmod(end_min, 60)
    return f"[ {start_hour:02.0f}:{start_min:02.0f}:{start_sec:06.3f} -->  {end_hour:02.0f}:{end_min:02.0f}:{end_sec:06.3f}] _ {file_id}"


def der_process_for_class(ref,hyp):
    output = io.StringIO()

    original_stdout = sys.stdout

    sys.stdout = output
    # Charger les annotations de référence et d'hypothèse
    reference_annotations = cla_load_annotation_from_json(ref)
    hypothesis_annotations = cla_load_annotation_from_json(hyp)

    # Parcourir les annotations par classe
    for class_id, file_annotations in reference_annotations.items():  
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et annotations de référence pour chaque classe
        for file_id, reference_annotation in file_annotations.items():
            hypothesis_annotation = hypothesis_annotations.get(class_id, {}).get(file_id, Annotation())  
            components = der(reference_annotation, hypothesis_annotation, detailed=True)

            total_miss += components['miss']
            total_false_alarm += components['false alarm']
            total_total += components['total']

        # Calculer et afficher le taux d'erreur de détection (DER) pour chaque classe
        if total_total != 0:
            error_rate = (total_miss + total_false_alarm) / total_total
            print(f'Detection Error Rate for Class {class_id}:')  
            print(f'Total Missed Detections: {total_miss:.2f}')
            print(f'Total False Alarms: {total_false_alarm:.2f}')
            print(f'Total References: {total_total:.2f}')
            print(f'Error Rate: {error_rate:.2%}\n')
        else:
            print(f'No annotations found for Class {class_id}\n')

        # Afficher les segments manqués, les fausses alarmes et les segments corrects pour chaque fichier
        for file_id, reference_annotation in file_annotations.items():
            hypothesis_annotation = hypothesis_annotations.get(class_id, {}).get(file_id, Annotation())
            missed_detections, false_alarms = cla_get_missed_and_false_alarm_segments(reference_annotation, hypothesis_annotation)    
            correct_detections = cla_get_correct_segments(reference_annotation, hypothesis_annotation)

            print(f'Reference segments for Class {class_id} in File {file_id}:')
            print(reference_annotation)
            print(f'Hypothesis segments for Class {class_id} in File {file_id}:')
            print(hypothesis_annotation)
            
            print(f'Missed detections for Class {class_id} in File {file_id}:')
            if not missed_detections:
                print('There are no missed detections')
            else:
                for segment in missed_detections:
                    print(cla_format_segment(segment[0], file_id))
            
            print(f'False alarms for Class {class_id} in File {file_id}:')
            if not false_alarms:
                print('There are no false alarms')
            else:
                for segment in false_alarms:
                    print(cla_format_segment(segment[0], file_id))

            print(f'Correct detections for Class {class_id} in File {file_id}:')
            if not correct_detections:
                print('There are no correct segments')
            else:
                for segment in correct_detections:
                    print(cla_format_segment(segment[0], file_id))
            print('\n')

    sys.stdout = original_stdout

    contents = output.getvalue()

    output.close()

    return contents



"""
Ce script concerne les adultes et les enfants
DER pour tous les locuteurs
fichiers d'entrée : fichier reference converti par eaf2jsonDER et fichier hypothese converti par textgrid2json
sorties : DER par locuteur avec détails (détails: total missed detection et total false alarm) et segments hypotheses, segments references, segments consideré comme missed alarms et false alarms
"""
# Fonction pour charger les annotations depuis le fichier JSON
def spe_load_annotation_from_json(json_file):
    annotations_by_speaker_file = {}

    with open(json_file, 'r') as file:
        data = json.load(file)
        for segment_data in data:
            # Extraire les informations du segment
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

            # Ajouter le segment à la structure
            annotations_by_speaker_file[speaker_id][label][segment] = label
    return annotations_by_speaker_file


# Fonction pour obtenir les segments manqués et les fausses alarmes
def spe_get_missed_and_false_alarm_segments(reference_annotation, hypothesis_annotation):
    reference_segments = set(reference_annotation.itertracks())
    hypothesis_segments = set(hypothesis_annotation.itertracks())

    missed_detections = reference_segments - hypothesis_segments
    false_alarms = hypothesis_segments - reference_segments

    return missed_detections, false_alarms

# Fonction pour obtenir les segments corrects
def spe_get_correct_segments(reference_annotation, hypothesis_annotation):
    reference_segments = set(reference_annotation.itertracks())
    hypothesis_segments = set(hypothesis_annotation.itertracks())

    correct_detections = reference_segments & hypothesis_segments

    return correct_detections

# Fonction pour formater un segment
def spe_format_segment(segment, file_id):
    start, end = segment
    start_hour, start_min = divmod(start, 3600)
    start_min, start_sec = divmod(start_min, 60)
    end_hour, end_min = divmod(end, 3600)
    end_min, end_sec = divmod(end_min, 60)
    return f"[ {start_hour:02.0f}:{start_min:02.0f}:{start_sec:06.3f} -->  {end_hour:02.0f}:{end_min:02.0f}:{end_sec:06.3f}] _ {file_id}"

def der_process_for_speaker(ref,hyp):
    output = io.StringIO()

    original_stdout = sys.stdout

    sys.stdout = output

    # Charger les annotations de référence et d'hypothèse
    reference_annotations = spe_load_annotation_from_json(ref)
    hypothesis_annotations = spe_load_annotation_from_json(hyp)
    # Parcourir les annotations par locuteur
    for speaker_id, file_annotations in reference_annotations.items():
        der = DetectionErrorRate()
        total_miss = 0
        total_false_alarm = 0
        total_total = 0

        # Parcourir les fichiers et segments de référence pour chaque locuteur
        for file_id, reference_annotation in file_annotations.items():
            # Obtenir les annotations d'hypothèse pour le locuteur et le fichier spécifiques
            hypothesis_annotation = hypothesis_annotations.get(speaker_id, {}).get(file_id, Annotation())
            
            # Calculer les composants DER pour chaque fichier
            components = der(reference_annotation, hypothesis_annotation, detailed=True)

            # Cumuler les composants pour calculer le DER total
            total_miss += components['miss']
            total_false_alarm += components['false alarm']
            total_total += components['total']

        # Calculer et afficher le taux d'erreur de détection (DER) pour chaque locuteur
        if total_total != 0:
            error_rate = (total_miss + total_false_alarm) / total_total
            print(f'Detection Error Rate for Speaker {speaker_id}:')
            print(f'Total Missed Detections: {total_miss:.2f}')
            print(f'Total False Alarms: {total_false_alarm:.2f}')
            print(f'Total References: {total_total:.2f}')
            print(f'Error Rate: {error_rate:.2%}\n')
        else:
            print(f'No annotations found for Speaker {speaker_id}\n')

        # Afficher les segments manqués, les fausses alarmes et les segments corrects pour chaque fichier
        for file_id, reference_annotation in file_annotations.items():
            # Obtenir les annotations d'hypothèse pour le locuteur et le fichier spécifiques
            hypothesis_annotation = hypothesis_annotations.get(speaker_id, {}).get(file_id, Annotation())
            
            # Obtenir les segments manqués et les fausses alarmes
            missed_detections, false_alarms = spe_get_missed_and_false_alarm_segments(reference_annotation, hypothesis_annotation)
            correct_detections = spe_get_correct_segments(reference_annotation, hypothesis_annotation)

            print(f'Reference segments for Speaker {speaker_id} in File {file_id}:')
            print(reference_annotation)
            print(f'Hypothesis segments for Speaker {speaker_id} in File {file_id}:')
            print(hypothesis_annotation)

            print(f'Missed detections for Speaker {speaker_id} in File {file_id}:')
            if not missed_detections:
                print('There are no missed detections')
            else:
                for segment in missed_detections:
                    print(spe_format_segment(segment[0], file_id))

            print(f'False alarms for Speaker {speaker_id} in File {file_id}:')
            if not false_alarms:
                print('There are no false alarms')
            else:
                for segment in false_alarms:
                    print(spe_format_segment(segment[0], file_id))

            print(f'Correct detections for Speaker {speaker_id} in File {file_id}:')
            if not correct_detections:
                print('There are no correct segments')
            else:
                for segment in correct_detections:
                    print(spe_format_segment(segment[0], file_id))
            print('\n')


    sys.stdout = original_stdout

    contents = output.getvalue()

    output.close()

    return contents