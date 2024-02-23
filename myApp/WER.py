from jiwer import compute_measures, process_words, visualize_alignment
import json

################################SPEAKER_WER#####################################
"""
Cette partie ne concerne que les adultes
WER pour tous les locuteurs
fichiers d'entrée : fichier de référence converti par eaf2jsonWER et fichier d'hypothèse converti par txt2json
sorties : WER par locuteur avec détails (détails: total substitutions, total insertions, total deletions) et segments d'hypothèse, segments de référence avec les insertions, les suppressions et les substitutions
"""
def wer_process_for_speaker(reference_file, hypothesis_file):

    # Lire les fichiers téléchargés
    hypothesis_content = hypothesis_file.read()
    reference_content = reference_file.read()

    # Charger les données de référence et les données d'hypothèse depuis les fichiers JSON
    hypothesis_data = json.loads(hypothesis_content)
    reference_data = json.loads(reference_content)

    # Initialiser des structures pour stocker les mesures par locuteur et les détails par locuteur
    measures_by_speaker = {}
    details_by_speaker = {}

    # Parcourir les segments d'hypothèse
    for h_segment in hypothesis_data:
        # Parcourir les segments de référence
        for r_segment in reference_data:
            # Vérifier si les segments appartiennent au même locuteur et correspondent en termes de fichier et de temps (tolérance de 0.1 seconde)
            if h_segment['speaker_id'] == r_segment['speaker_id']:
                if h_segment['speaker_id'].startswith('1') and r_segment['speaker_id'].startswith('1'):
                    if (h_segment['file_id'] == r_segment['file_id'] and
                        (h_segment['start_time'] == r_segment['start_time'] or abs(h_segment['end_time'] - r_segment['end_time']) < 0.1)):
                            # Extraire des informations spécifiques au segment
                            speaker_id = h_segment['speaker_id']
                            h_text = h_segment['hypothesis']
                            r_text = r_segment['transcript']

                            # Calculer les mesures WER et obtenir l'alignement des mots
                            measures = compute_measures(r_text, h_text)
                            alignment = process_words([r_text], [h_text])
                            details = "{}\nSegment WER: {}, Supressions totales: {}, Insertions totales: {}, Substitutions totales: {}\n{}".format(
                                h_segment['file_id'],
                                measures['wer'],
                                measures['deletions'],
                                measures['insertions'],
                                measures['substitutions'],
                                visualize_alignment(alignment, show_measures=False, skip_correct=False).replace('sentence 1\n', '')
                            )

                            # Stocker les mesures par locuteur
                            if speaker_id not in measures_by_speaker:
                                measures_by_speaker[speaker_id] = {"total_errors": 0, "total_words": 0, "deletions": 0, "insertions": 0, "substitutions": 0}
                                details_by_speaker[speaker_id] = []
                            measures_by_speaker[speaker_id]["total_errors"] += measures["wer"] * len(h_text.split())
                            measures_by_speaker[speaker_id]["total_words"] += len(h_text.split())
                            measures_by_speaker[speaker_id]["deletions"] += measures["deletions"]
                            measures_by_speaker[speaker_id]["insertions"] += measures["insertions"]
                            measures_by_speaker[speaker_id]["substitutions"] += measures["substitutions"]
                            details_by_speaker[speaker_id].append(details)

    # Calculer le WER total pour chaque locuteur
    total_wer_by_speaker = {speaker: {"wer": measures["total_errors"] / measures["total_words"] if measures["total_words"] > 0 else 0, "deletions": measures["deletions"], "insertions": measures["insertions"], "substitutions": measures["substitutions"]} for speaker, measures in measures_by_speaker.items()}
    results=""
    # Afficher les résultats
    for speaker, measures in total_wer_by_speaker.items():
        results += f'Locuteur: {speaker}, WER: {measures["wer"]}, Supressions totales: {measures["deletions"]}, Insertions totales: {measures["insertions"]}, Substitutions totales: {measures["substitutions"]}\n'
        
    # Afficher les détails pour chaque locuteur
    for speaker, details_list in details_by_speaker.items():
        results += f'\nDétails pour Locuteur {speaker}:\n'
        for details in details_list:
            results += details + "\n"
    return results.strip()

#####################################################################

################################SITUATION_WER#####################################
"""
Cette partie ne concerne que les adultes
WER pour toutes les situations
fichiers d'entrée : fichier de référence converti par eaf2jsonWER et fichier d'hypothèse converti par txt2json
sorties : WER par situation avec détails (détails: total substitutions, total insertions, total deletions) et segments d'hypothèse, segments de référence avec les insertions, les suppressions et les substitutions
"""
def wer_process_for_situation(reference_file, hypothesis_file):

    # Lire les fichiers téléchargés
    hypothesis_content = hypothesis_file.read()
    reference_content = reference_file.read()

    # Charger les données de référence et les données d'hypothèse depuis les fichiers JSON
    hypothesis_data = json.loads(hypothesis_content)
    reference_data = json.loads(reference_content)

    # Initialiser des structures pour stocker les mesures par situation et les détails par situation
    measures_by_situation = {}
    details_by_situation = {}

    # Parcourir les segments de référence
    for r_segment in reference_data:
        # Parcourir les segments d'hypothèse
        for h_segment in hypothesis_data:
            # Vérifier si les segments appartiennent au même locuteur et correspondent en termes de fichier et de temps (tolérance de 0.1 seconde)
            if h_segment['speaker_id'].startswith('1') and r_segment['speaker_id'].startswith('1'):
                if (h_segment['file_id'] == r_segment['file_id'] and
                    (h_segment['start_time'] == r_segment['start_time'] or abs(h_segment['end_time'] - r_segment['end_time']) < 0.1)):
                    # Extraire des informations spécifiques au segment
                    situation = r_segment['situation']
                    h_text = h_segment['hypothesis']
                    r_text = r_segment['transcript']

                    # Calculer les mesures WER et obtenir l'alignement des mots
                    measures = compute_measures(r_text, h_text)
                    alignment = process_words([r_text], [h_text])

                    # Formater les détails pour l'affichage
                    details = h_segment['file_id'] + "\nSegment WER: " + str(measures['wer']) + ", Supressions totales: " + str(measures['deletions']) + ", Insertions totales: " + str(measures['insertions']) + ", Substitutions totales: " + str(measures['substitutions']) + "\n" + visualize_alignment(alignment, show_measures=False, skip_correct=False).replace('sentence 1\n', '')

                    # Stocker les mesures par situation
                    if situation not in measures_by_situation:
                        measures_by_situation[situation] = {"total_errors": 0, "total_words": 0, "deletions": 0, "insertions": 0, "substitutions": 0}
                        details_by_situation[situation] = []
                    measures_by_situation[situation]["total_errors"] += measures["wer"] * len(h_text.split())
                    measures_by_situation[situation]["total_words"] += len(h_text.split())
                    measures_by_situation[situation]["deletions"] += measures["deletions"]
                    measures_by_situation[situation]["insertions"] += measures["insertions"]
                    measures_by_situation[situation]["substitutions"] += measures["substitutions"]
                    details_by_situation[situation].append(details)

    # Calculer le WER total pour chaque situation
    total_wer_by_situation = {situation: {"wer": measures["total_errors"] / measures["total_words"] if measures["total_words"] > 0 else 0, "deletions": measures["deletions"], "insertions": measures["insertions"], "substitutions": measures["substitutions"]} for situation, measures in measures_by_situation.items()}
    results = ""
    # Afficher les résultats
    for situation, measures in total_wer_by_situation.items():
        results += f'Situation: {situation}, WER: {measures["wer"]}, Supressions totales: {measures["deletions"]}, Insertions totales: {measures["insertions"]}, Substitutions totales: {measures["substitutions"]}\n'
    
    # Afficher les détails pour chaque situation
    for situation, details_list in details_by_situation.items():
        results += f'\nDétails pour Situation "{situation}":\n'
        for details in details_list:
            results += details + "\n"
    return results.strip()

#####################################################################

################################CLASS_WER#####################################
"""
Ce script ne concerne que les adultes
WER pour toutes les classes
fichiers d'entrée : fichier de référence converti par eaf2jsonWER et fichier d'hypothèse converti par txt2json
sorties : WER par classe avec détails avec détails (détails: total substitutions, total insertions, total deletions) et segments d'hypothèse, segments de référence avec les insertions, les suppressions et les substitutions
"""
def wer_process_for_class(reference_file, hypothesis_file):

    # Lire les fichiers téléchargés
    hypothesis_content = hypothesis_file.read()
    reference_content = reference_file.read()

    # Charger les données de référence et les données d'hypothèse depuis les fichiers JSON
    hypothesis_data = json.loads(hypothesis_content)
    reference_data = json.loads(reference_content)

    # Initialiser des structures pour stocker les mesures par classe et les détails par classe
    measures_by_class = {}
    details_by_class = {}

    # Parcourir les segments d'hypothèse
    for h_segment in hypothesis_data:
        # Parcourir les segments de référence
        for r_segment in reference_data:
            # Vérifier si les segments appartiennent à la même classe et au même locuteur
            if h_segment['class_id'] == r_segment['class_id']:
                if h_segment['speaker_id'].startswith('1') and r_segment['speaker_id'].startswith('1'):
                    # Vérifier si les segments correspondent en termes de fichier et de temps (tolérance de 0.1 seconde)
                    if (h_segment['file_id'] == r_segment['file_id'] and
                        (h_segment['start_time'] == r_segment['start_time'] or abs(h_segment['end_time'] - r_segment['end_time']) < 0.1)):
                            # Extraire des informations spécifiques aux segments
                            class_id = h_segment['class_id']
                            h_text = h_segment['hypothesis']
                            r_text = r_segment['transcript']

                            # Calculer les mesures WER et obtenir l'alignement des mots
                            measures = compute_measures(r_text, h_text)
                            alignment = process_words([r_text], [h_text])
                            details = "{}\nSegment WER: {}, Supressions totales: {}, Insertions totales: {}, Substitutions totales: {}\n{}".format(
                                h_segment['file_id'],
                                measures['wer'],
                                measures['deletions'],
                                measures['insertions'],
                                measures['substitutions'],
                                visualize_alignment(alignment, show_measures=False, skip_correct=False).replace('sentence 1\n', '')
                            )
                            # Stocker les mesures par classe
                            if class_id not in measures_by_class:
                                measures_by_class[class_id] = {"total_errors": 0, "total_words": 0, "deletions": 0, "insertions": 0, "substitutions": 0}
                                details_by_class[class_id] = []
                            measures_by_class[class_id]["total_errors"] += measures["wer"] * len(h_text.split())
                            measures_by_class[class_id]["total_words"] += len(h_text.split())
                            measures_by_class[class_id]["deletions"] += measures["deletions"]
                            measures_by_class[class_id]["insertions"] += measures["insertions"]
                            measures_by_class[class_id]["substitutions"] += measures["substitutions"]
                            details_by_class[class_id].append(details)

    # Calculer le WER total pour chaque classe
    total_wer_by_class = {class_id: {"wer": measures["total_errors"] / measures["total_words"] if measures["total_words"] > 0 else 0, "deletions": measures["deletions"], "insertions": measures["insertions"], "substitutions": measures["substitutions"]} for class_id, measures in measures_by_class.items()}
    results=""

    for class_id, measures in total_wer_by_class.items():
        results += f'Classe: {class_id}, WER: {measures["wer"]}, Supressions totales: {measures["deletions"]}, Insertions totales: {measures["insertions"]}, Substitutions totales: {measures["substitutions"]}\n'

    for class_id, details_list in details_by_class.items():
        results += f'\nDétails pour Classe {class_id}:\n'
        for details in details_list:
            results += details + "\n"
    return results.strip()
#####################################################################