# Importations nécessaires pour les réponses HTTP, la gestion des fichiers et le traitement des données
from django.http import JsonResponse, HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.timezone import now
import uuid
import json

# Importations des modules spécifiques au projet pour le traitement des données
from .DER import der_process_for_class, der_process_for_situation, der_process_for_speaker
from .WER import wer_process_for_class, wer_process_for_situation, wer_process_for_speaker
from .DERWER_ADULT import adult_class, adult_speaker, adult_situation
from .DERWER_ENFANT import enfant_class, enfant_speaker, enfant_situation
from .conversion import eaf2jsonDER, textgrid2json, eaf2jsonWER, txt2json

# Vue pour la page d'accueil
def home(request):
    # Rendu de la page d'accueil
    return render(request, 'home.html')

# Vue pour la conversion des fichiers
def conversion_view(request):
    # Traitement de la requête POST pour la conversion des fichiers
    if request.method == 'POST':
        conversion_type = request.POST.get('conversion_type', '')
        uploaded_files = request.FILES.getlist('file')  
        results = []

        # Boucle sur tous les fichiers téléchargés pour les convertir selon le type demandé
        for uploaded_file in uploaded_files:
            file_name = uploaded_file.name
            temp_file_path = default_storage.save(file_name, uploaded_file)

            # Sélection du type de conversion et traitement du fichier
            if conversion_type == 'eaf2jsonDER':
                result = eaf2jsonDER(temp_file_path)
            elif conversion_type == 'textgrid2json':
                result = textgrid2json(temp_file_path)
            elif conversion_type == 'eaf2jsonWER':
                result = eaf2jsonWER(temp_file_path)
            elif conversion_type == 'txt2json':
                result = txt2json(temp_file_path)
            else:
                # Suppression du fichier temporaire si le type de conversion n'est pas supporté
                default_storage.delete(temp_file_path)
                return JsonResponse({"error": "Unsupported conversion type"}, status=400)

            results.extend(result)
            default_storage.delete(temp_file_path)

        # Préparation et sauvegarde du fichier JSON résultant
        timestamp = now().strftime('%Y%m%d%H%M%S')
        json_file_name = f"converted_{file_name}_{timestamp}.json"
        json_file_path = default_storage.save(json_file_name, ContentFile(json.dumps(results, indent=2).encode('utf-8')))

        # Génération de l'URL pour télécharger le fichier converti
        download_url = f'/download/{json_file_name}'
        return JsonResponse({"success": "Files converted successfully", "download_url": download_url})

    # Rendu de la page de conversion pour une requête GET
    return render(request, 'conversion.html')

# Vue pour télécharger un fichier
def download_file(request, file_name):
    file_path = default_storage.path(file_name)
    with open(file_path, 'rb') as fh:
        # Préparation de la réponse HTTP pour télécharger le fichier
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=' + file_name
        return response

# Vue pour l'analyse DER
def DER_view(request):
    # Traitement de la requête POST pour l'analyse DER
    if request.method == 'POST':
        reference_file = request.FILES.get('referenceFile')
        hypothesis_file = request.FILES.get('hypothesisFile')
        analysis_type = request.POST.get('analysisType')

        # Vérification de la présence des fichiers nécessaires
        if not reference_file or not hypothesis_file:
            return HttpResponse("Please upload both reference and hypothesis files.", status=400)
        if reference_file and hypothesis_file:

            re_file_name = reference_file.name
            hy_file_name = hypothesis_file.name
            re_path = default_storage.save(re_file_name, reference_file)
            hy_path = default_storage.save(hy_file_name, hypothesis_file)
        try:
            # Sélection du type d'analyse et traitement
            if analysis_type == 'class':
                results = der_process_for_class(re_path, hy_path)
            elif analysis_type == 'situation':
                results = der_process_for_situation(re_path, hy_path)
            elif analysis_type == 'speaker':
                results = der_process_for_speaker(re_path, hy_path)
            else:
                return HttpResponse("Invalid analysis type", status=400)

        except Exception as e:

            return HttpResponse(f"Error processing files: {str(e)}", status=500)

        default_storage.delete(re_path)
        default_storage.delete(hy_path)

        return render(request, 'DER.html', {'results': results})
    else:
        return render(request, 'DER.html')

# Vue pour l'analyse WER
def WER_view(request):
    # Traitement de la requête POST pour l'analyse WER
    if request.method == 'POST':
        reference_file = request.FILES.get('referenceFile')
        hypothesis_file = request.FILES.get('hypothesisFile')
        analysis_type = request.POST.get('analysisType')

        # Vérification de la présence des fichiers et sélection du type d'analyse
        if not reference_file or not hypothesis_file:
            return HttpResponse("Veuillez télécharger les fichiers de référence et les fichiers hypothétiques.", status=400)

        try:
            reference_file.seek(0)
            hypothesis_file.seek(0)
            
            # Traitement selon le type d'analyse sélectionné
            if analysis_type == 'class':
                results = wer_process_for_class(reference_file, hypothesis_file)

            elif analysis_type == 'situation':
                results = wer_process_for_situation(reference_file, hypothesis_file)
            elif analysis_type == 'speaker':
                results = wer_process_for_speaker(reference_file, hypothesis_file)
            else:
                return HttpResponse("Invalid analysis type", status=400)
        except json.JSONDecodeError as e:
            return HttpResponse(f"Erreur lors de l'analyse du fichier JSON: {str(e)}", status=500)
        except KeyError as e:
            return HttpResponse(f"Clé nécessaire manquante: {str(e)}", status=500)
        except Exception as e:
            return HttpResponse(f"Erreur lors du traitement du fichier: {str(e)}", status=500)

        return render(request, 'WER.html', {'results': results})
    else:
        return render(request, 'WER.html')


# Vue pour l'analyse combinée DER et WER
def DERWER_view(request):
    # Traitement de la requête POST pour l'analyse combinée
    if request.method == 'POST':

        reference_file_WER = request.FILES.get('referenceFileWER')
        hypothesis_file_WER = request.FILES.get('hypothesisFileWER')
        reference_file_DER = request.FILES.get('referenceFileDER')
        hypothesis_file_DER = request.FILES.get('hypothesisFileDER')
        analysis_type = request.POST.get('analysisType')
        target_group = request.POST.get('targetGroup')

        # Vérification de la présence des fichiers selon le groupe cible
        if target_group == 'adult':
            if not all([reference_file_WER, hypothesis_file_WER, reference_file_DER, hypothesis_file_DER]):
                return HttpResponse("Please upload all required files.", status=400)
        elif target_group == 'enfant':
            if not all([reference_file_DER, hypothesis_file_DER]):
                return HttpResponse("Please upload all required files.", status=400)

        try:
            func_map = {
                'adult': {
                    'class': adult_class,
                    'situation': adult_situation,
                    'speaker': adult_speaker
                },
                'enfant': {
                    'class': enfant_class,
                    'situation': enfant_situation,
                    'speaker': enfant_speaker
                }
            }
            func = func_map[target_group].get(analysis_type)
            if func:
                if target_group == 'adult':
                    resultat, chart_data, scatter_data = func(hypothesis_file_WER, reference_file_WER, hypothesis_file_DER, reference_file_DER)  
                else: 
                    resultat, chart_data, scatter_data = func(hypothesis_file_DER, reference_file_DER)
                
        except Exception as e:
            print("Error:", e)  
            return HttpResponse(f"Error processing files: {str(e)}", status=500)

        context = {
            'resultat': resultat,
            'chart_data': json.dumps(chart_data),
            'scatter_data': json.dumps(scatter_data),
        }
        return render(request, 'DERWER.html', context)

    else:
        return render(request, 'DERWER.html')



