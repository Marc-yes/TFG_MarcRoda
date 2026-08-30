<?php

namespace App\Http\Controllers;

use App\Services\PythonApiService;
use Illuminate\Http\Request;

class PatientAnalysisController extends Controller
{
    /**
     * Mostra el formulari d'anàlisi de pacient.
     */
    public function index(PythonApiService $api)
    {
        $priorityResult = $api->getPriorityReviewList(50);
        $priorityPatients = $priorityResult['success'] ? ($priorityResult['data']['patients'] ?? []) : [];

        return view('dashboard', [
            'priorityPatients' => $priorityPatients
        ]);
    }

    /**
     * Envia el DNI a l'API Python i retorna els resultats.
     */
    public function analyze(Request $request, PythonApiService $api)
    {
        $request->validate([
            'dni' => ['required', 'string', 'max:20'],
        ], [
            'dni.required' => 'El DNI/NIE és obligatori.',
        ]);

        $result = $api->analyzePatient($request->input('dni'));
        $priorityResult = $api->getPriorityReviewList(50);
        $priorityPatients = $priorityResult['success'] ? ($priorityResult['data']['patients'] ?? []) : [];

        if ($result['success']) {
            $historyResult = $api->getPatientFeedbackHistory((int)$request->input('dni'));
            $history = $historyResult['success'] ? ($historyResult['data']['history'] ?? []) : [];

            return view('dashboard', [
                'dni'      => $request->input('dni'),
                'resultat' => $result['data'],
                'historial' => $history,
                'priorityPatients' => $priorityPatients,
            ]);
        }

        return back()
            ->withInput()
            ->withErrors(['api' => $result['error']])
            ->with('priorityPatients', $priorityPatients);
    }

    /**
     * Desa el feedback de l'usuari sobre una predicció.
     */
    public function saveFeedback(Request $request, PythonApiService $api)
    {
        $validated = $request->validate([
            'id_pacient'             => ['required', 'integer'],
            'prediccio_model'        => ['required', 'string'],
            'confianca_model'        => ['required', 'numeric'],
            'feedback_correcte'      => ['required', 'boolean'],
            'classificacio_correcta' => ['nullable', 'string'],
            'comentari'              => ['nullable', 'string'],
        ]);

        // Afegim l'usuari professional autenticat
        $validated['usuari'] = auth()->user()->name ?? 'professional';

        // Enviem el feedback a l'API de Python
        $result = $api->submitFeedback($validated);

        if ($result['success']) {
            return response()->json([
                'success' => true,
                'message' => 'Feedback registrat correctament.',
            ]);
        }

        return response()->json([
            'success' => false,
            'message' => $result['error'] ?? 'Error en enviar el feedback.',
        ], 500);
    }


}
