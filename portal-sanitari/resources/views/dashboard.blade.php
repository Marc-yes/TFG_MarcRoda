@extends('layouts.app')

@section('page-title', 'Anàlisi de Pacient')

@section('content')
    <style>
        .dashboard-layout {
            display: flex;
            gap: 30px;
            align-items: flex-start;
            max-width: 1400px;
            margin: 0 auto;
        }
        .priority-sidebar {
            flex: 0 0 350px;
            background: #ffffff;
            border: 1px solid rgba(200, 225, 255, 0.5);
            border-radius: 20px;
            padding: 24px;
            max-height: 800px;
            overflow-y: auto;
            box-shadow: 0 4px 24px rgba(0, 100, 200, 0.05);
        }
        .priority-title {
            font-size: 15px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #eef3fa;
            padding-bottom: 12px;
        }
        .priority-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .priority-item {
            display: flex;
            flex-direction: column;
            padding: 12px 14px;
            background: #f8fafc;
            border: 1.5px solid #e2e8f0;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: inherit;
        }
        .priority-item:hover {
            border-color: #3b82f6;
            background: #f0f7ff;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.06);
            transform: translateY(-1px);
        }
        .priority-item.active {
            border-color: #3b82f6;
            background: #eff6ff;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.08);
        }
        .priority-badge-maca {
            background: #fee2e2;
            color: #991b1b;
            font-weight: 700;
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 6px;
            letter-spacing: 0.05em;
        }
        .priority-badge-pcc {
            background: #fef3c7;
            color: #92400e;
            font-weight: 700;
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 6px;
            letter-spacing: 0.05em;
        }
        .main-analysis-panel {
            flex: 1;
            min-width: 0;
        }
        
        /* Estadístiques de la vista de llista */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 4px 24px rgba(0, 100, 200, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 100, 200, 0.06);
        }
        .stat-icon-maca {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: #fee2e2;
            color: #ef4444;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .stat-icon-pcc {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: #fef3c7;
            color: #f59e0b;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .stat-icon-total {
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: #eff6ff;
            color: #3b82f6;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 800;
            color: #1e293b;
            line-height: 1;
        }
        .stat-label {
            font-size: 13px;
            color: #64748b;
            font-weight: 600;
            margin-top: 6px;
        }

        /* Taula premium per pacients */
        .premium-table-container {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 100, 200, 0.02);
            margin-top: 15px;
        }
        .premium-table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }
        .premium-table th {
            background: #f8fafc;
            padding: 16px 20px;
            font-size: 11px;
            font-weight: 700;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1.5px solid #e2e8f0;
        }
        .premium-table td {
            padding: 16px 20px;
            font-size: 13px;
            color: #334155;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
        }
        .premium-table tr:last-child td {
            border-bottom: none;
        }
        .premium-table tr:hover td {
            background: #f8fafc;
        }
        .progress-bar-container {
            width: 100px;
            height: 6px;
            background: #e2e8f0;
            border-radius: 3px;
            overflow: hidden;
            display: inline-block;
            vertical-align: middle;
            margin-right: 8px;
        }
        .progress-bar-maca {
            height: 100%;
            background: #ef4444;
        }
        .progress-bar-pcc {
            height: 100%;
            background: #f59e0b;
        }
        .review-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: #3b82f6;
            color: #ffffff;
            font-weight: 600;
            font-size: 12px;
            border-radius: 10px;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15);
        }
        .review-btn:hover {
            background: #2563eb;
            box-shadow: 0 4px 6px rgba(59, 130, 246, 0.25);
            transform: translateY(-1px);
        }
        .btn-back {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            color: #475569;
            font-weight: 600;
            font-size: 12px;
            padding: 8px 16px;
            border: 1.5px solid #cbd5e1;
            border-radius: 10px;
            background: white;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            cursor: pointer;
        }
        .btn-back:hover {
            background: #f8fafc;
            border-color: #94a3b8;
            color: #1e293b;
        }
    </style>

    <div class="dashboard-layout">
        {{-- SIDEBAR DE PRIORITATS --}}
        @if (isset($resultat))
        <div class="priority-sidebar">
            <div class="priority-title">
                <svg style="width: 18px; height: 18px; color: #ef4444;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>Revisions Prioritàries</span>
            </div>
            <div class="priority-list">
                @forelse($priorityPatients ?? [] as $p)
                    <a href="#" class="priority-item {{ ($dni ?? '') == $p['id_pacient'] ? 'active' : '' }}" onclick="event.preventDefault(); selectPatient('{{ $p['id_pacient'] }}')">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                            <span style="font-weight:700; color:#1e293b; font-size: 13px;">Pacient #{{ $p['id_pacient'] }}</span>
                            <span class="{{ $p['prediccio_estat'] == 'MACA' ? 'priority-badge-maca' : 'priority-badge-pcc' }}">
                                {{ $p['prediccio_estat'] }}
                            </span>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size: 11px; color: #64748b;">
                            <span>{{ $p['grup_edat'] }} anys | {{ $p['sexe'] == 'H' ? 'Masculí' : 'Femenina' }}</span>
                            <span style="font-weight: 600; color: #3b82f6;">
                                {{ number_format(($p['prediccio_estat'] == 'MACA' ? $p['prob_maca'] : $p['prob_pcc']) * 100, 1) }}%
                            </span>
                        </div>
                    </a>
                @empty
                    <p style="font-size:12px; color:#94a3b8; text-align:center; padding: 20px 0; font-style: italic;">No hi ha pacients pendents.</p>
                @endforelse
            </div>
        </div>
        @endif

        {{-- COLUMNA DE CONTINGUT PRINCIPAL --}}
        <div class="main-analysis-panel" style="max-width: none;">
            @if (isset($resultat))
                <div style="margin-bottom: 20px;">
                    <a href="{{ route('dashboard') }}" class="btn-back">
                        <svg style="width: 16px; height: 16px;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                        </svg>
                        <span>Tornar al llistat de pacients</span>
                    </a>
                </div>
            @endif

            <div class="content-card" style="max-width: none;">
        {{-- CAPÇALERA --}}
        <div class="card-header-row">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <h1 class="card-title">
                @if (isset($resultat))
                    Anàlisi de Pacient
                @else
                    Tauler de Decisions Clíniques
                @endif
            </h1>
        </div>
        <p class="card-subtitle">
            @if (isset($resultat))
                Consulta els detalls predictius, l'explicabilitat SHAP i l'informe clínic generat per la IA.
            @else
                Pacients d'alta prioritat de revisió, ordenats per urgència clínica de MACA a PCC.
            @endif
        </p>

        {{-- ERRORS --}}
        @if ($errors->has('api'))
            <div
                style="background:#fef2f2; border:1px solid #fecaca; border-radius:12px; padding:12px 16px; margin-bottom:20px; font-size:13px; color:#991b1b; font-weight:500;">
                <svg style="width:16px; height:16px; display:inline; margin-right:4px; vertical-align:text-bottom;"
                    xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                    stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                {{ $errors->first('api') }}
            </div>
        @endif

        {{-- FORMULARI --}}
        <form method="POST" action="{{ route('analyze') }}" id="analysis-form"
            style="display:flex; gap:16px; align-items: flex-end; margin-bottom: 30px; max-width: 500px;">
            @csrf
            <div style="flex:1;">
                <label class="form-label" for="dni" style="margin-bottom: 10px;">ID Pacient (Test Set)</label>
                <input type="text" class="form-input" id="dni" name="dni" placeholder="Ex: 24954, 22644..."
                    value="{{ old('dni', $dni ?? '') }}" required autofocus style="margin-bottom:0;">
            </div>
            <button type="submit" class="btn-primary" id="btn-analyze"
                style="height:48px; padding: 0 32px; flex: 0 0 auto; width: auto; min-width: 140px; margin-top:0; position: relative;">
                <span id="btn-text">Cercar</span>
                <span id="btn-spinner"
                    style="display: none; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);">
                    <svg style="animation: spin 1s linear infinite; width: 20px; height: 20px;"
                        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
                        </path>
                    </svg>
                </span>
            </button>
        </form>

        {{-- RESULTATS --}}
        @if (isset($resultat))
            <div class="results-container" style="animation: fadeInUp 0.5s ease-out;">
                <div style="display:flex; align-items:center; justify-content:between; margin-bottom:20px;">
                    <h2 style="font-size:20px; font-weight:800; color:#0f172a; margin:0;">Resultats de l'Anàlisi</h2>
                    <span
                        style="margin-left:auto; padding:4px 12px; background:#e2e8f0; border-radius:20px; font-size:12px; font-weight:600; color:#475569;">Pacient
                        #{{ $resultat['pacient']['id_pacient'] }}</span>
                </div>

                {{-- GRAELLA DE TARGETES (3 COLUMNE) --}}
                <div
                    style="display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:20px; margin-bottom:24px;">

                    {{-- 1. TARGETA PERFIL --}}
                    <div
                        style="padding:20px; background:white; border-radius:16px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                        <div
                            style="display:flex; align-items:center; gap:10px; margin-bottom:15px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                            <div
                                style="width:36px; height:36px; background:#eff6ff; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#2563eb;">
                                <svg style="width:20px; height:20px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="12" cy="7" r="4"></circle>
                                </svg>
                            </div>
                            <h3 style="font-size:15px; font-weight:700; color:#1e293b; margin:0;">Perfil del Pacient</h3>
                        </div>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
                            <div>
                                <p style="font-size:11px; color:#64748b; margin:0; text-transform: uppercase; font-weight:700;">
                                    Edat / Sexe</p>
                                <p style="font-size:14px; color:#1e293b; font-weight:600; margin:4px 0 0 0;">
                                    {{ $resultat['pacient']['grup_edat'] }} anys /
                                    {{ $resultat['pacient']['sexe'] == 'H' ? 'Masculí' : 'Femenina' }}</p>
                            </div>
                            <div>
                                <p style="font-size:11px; color:#64748b; margin:0; text-transform: uppercase; font-weight:700;">
                                    Estat Actual</p>
                                <span
                                    style="display:inline-block; margin-top:4px; padding:2px 8px; border-radius:6px; font-size:12px; font-weight:700; background: {{ $resultat['pacient']['cronic_actual'] == 'NO' ? '#f1f5f9' : ($resultat['pacient']['cronic_actual'] == 'PCC' ? '#fef3c7' : '#fee2e2') }}; color: {{ $resultat['pacient']['cronic_actual'] == 'NO' ? '#475569' : ($resultat['pacient']['cronic_actual'] == 'PCC' ? '#92400e' : '#991b1b') }};">
                                    {{ $resultat['pacient']['cronic_actual'] }}
                                </span>
                            </div>
                            <div>
                                <p style="font-size:11px; color:#64748b; margin:0; text-transform: uppercase; font-weight:700;">
                                    Diagnòstics</p>
                                <p style="font-size:14px; color:#1e293b; font-weight:600; margin:4px 0 0 0;">
                                    {{ $resultat['pacient']['diags_totals'] }} totals</p>
                            </div>
                            <div>
                                <p style="font-size:11px; color:#64748b; margin:0; text-transform: uppercase; font-weight:700;">
                                    Fàrmacs</p>
                                <p style="font-size:14px; color:#1e293b; font-weight:600; margin:4px 0 0 0;">
                                    {{ $resultat['pacient']['farmacs_totals'] }} actius</p>
                            </div>
                        </div>
                    </div>

                    {{-- 2. TARGETA SIMILITUD (FAISS) --}}
                    <div
                        style="padding:20px; background:white; border-radius:16px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                        <div
                            style="display:flex; align-items:center; gap:10px; margin-bottom:15px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                            <div
                                style="width:36px; height:36px; background:#f0fdf4; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#16a34a;">
                                <svg style="width:20px; height:20px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="9" cy="7" r="4"></circle>
                                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                                </svg>
                            </div>
                            <h3 style="font-size:15px; font-weight:700; color:#1e293b; margin:0;">Casos Similars (FAISS)</h3>
                        </div>
                        <div style="margin-bottom:12px;">
                            <p style="font-size:12px; color:#475569; margin-bottom:8px;">Distribució de
                                {{ $resultat['pacient']['n_veins'] }} veïns reals:</p>
                            <div style="display:flex; height:8px; border-radius:4px; overflow:hidden; background:#e2e8f0;">
                                <div style="width:{{ $resultat['pacient']['pct_pcc'] }}%; background:#f59e0b;" title="PCC">
                                </div>
                                <div style="width:{{ $resultat['pacient']['pct_maca'] }}%; background:#ef4444;" title="MACA">
                                </div>
                                <div style="width:{{ $resultat['pacient']['pct_no'] }}%; background:#94a3b8;" title="NO"></div>
                            </div>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; font-weight:600;">
                            <span style="color:#b45309;">PCC: {{ $resultat['pacient']['pct_pcc'] }}%</span>
                            <span style="color:#b91c1c;">MACA: {{ $resultat['pacient']['pct_maca'] }}%</span>
                            <span style="color:#475569;">NO: {{ $resultat['pacient']['pct_no'] }}%</span>
                        </div>
                    </div>

                    {{-- 3. TARGETA PREDICCIÓ (ML V3) --}}
                    @if(isset($resultat['prediccio_v3']))
                        <div
                            style="padding:20px; background:white; border-radius:16px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                            <div
                                style="display:flex; align-items:center; gap:10px; margin-bottom:15px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                                <div
                                    style="width:36px; height:36px; background:#f5f3ff; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#7c3aed;">
                                    <svg style="width:20px; height:20px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                        stroke-linejoin="round">
                                        <path
                                            d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z">
                                        </path>
                                        <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                                        <line x1="12" y1="22.08" x2="12" y2="12"></line>
                                    </svg>
                                </div>
                                <h3 style="font-size:15px; font-weight:700; color:#1e293b; margin:0;">Model Predictiu (ML V3)</h3>
                                @php
                                    $estat = $resultat['prediccio_v3']['estat'] ?? 'Nova / Pendent de revisar';
                                    $estatColor = 'background:#fef3c7; color:#d97706;'; // Groc
                                    if (str_contains($estat, 'Validada')) {
                                        $estatColor = 'background:#dcfce7; color:#16a34a;'; // Verd
                                    } elseif (str_contains($estat, 'Corregida')) {
                                        $estatColor = 'background:#dbeafe; color:#2563eb;'; // Blau
                                    }
                                @endphp
                                <span id="badge-estat-prediccio" style="margin-left:auto; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:700; {{ $estatColor }}">{{ $estat }}</span>
                            </div>
                            <div style="text-align:center; padding:10px 0;">
                                <p style="font-size:11px; color:#64748b; margin:0; text-transform: uppercase; font-weight:700;">
                                    Suggereix Classificar com</p>
                                @php
                                    $pred = $resultat['prediccio_v3']['resultat'];
                                    $color = $pred == 'NO' ? '#64748b' : (($pred == 'MACA' || $pred == 'ERROR') ? '#ef4444' : '#f59e0b');
                                    $confRaw = $resultat['prediccio_v3']['confianca'];
                                    $conf = is_numeric($confRaw) ? $confRaw * 100 : 0;
                                @endphp
                                <p style="font-size:32px; font-weight:900; color: {{ $color }}; margin:5px 0;">{{ $pred }}</p>
                                <div style="margin-top:12px;">
                                    @if(is_numeric($confRaw))
                                        <p style="font-size:11px; color:#64748b; margin-bottom:4px; font-weight:700;">CONFIANÇA:
                                            {{ number_format($conf, 1) }}%</p>
                                        <div style="height:6px; background:#f1f5f9; border-radius:3px; overflow:hidden;">
                                            <div style="width:{{ $conf }}%; background:{{ $color }}; height:100%;"></div>
                                        </div>
                                    @else
                                        <p style="font-size:11px; color:#ef4444; margin-bottom:4px; font-weight:700;">{{ $confRaw }}</p>
                                    @endif
                                </div>

                                {{-- SECCIÓ DE FEEDBACK DE PREDICCIÓ --}}
                                <div style="margin-top: 20px; border-top: 1px dashed #e2e8f0; padding-top: 15px; text-align: left;" id="feedback-section">
                                    <p style="font-size:12px; font-weight:700; color:#475569; margin-bottom:10px; text-align: center;">És correcta aquesta predicció?</p>
                                    <div style="display:flex; gap:10px; justify-content:center;" id="feedback-initial-buttons">
                                        <button type="button" class="feedback-btn feedback-yes" onclick="showFeedbackDetails(true)" style="display:flex; align-items:center; gap:6px; padding:6px 16px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; font-size:12px; font-weight:600; color:#16a34a; cursor:pointer; transition:all 0.2s;">
                                            <svg style="width:14px; height:14px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                                <polyline points="20 6 9 17 4 12"></polyline>
                                            </svg>
                                            Sí
                                        </button>
                                        <button type="button" class="feedback-btn feedback-no" onclick="showFeedbackDetails(false)" style="display:flex; align-items:center; gap:6px; padding:6px 16px; background:#fef2f2; border:1px solid #fecaca; border-radius:8px; font-size:12px; font-weight:600; color:#dc2626; cursor:pointer; transition:all 0.2s;">
                                            <svg style="width:14px; height:14px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                                <line x1="6" y1="6" x2="18" y2="18"></line>
                                            </svg>
                                            No
                                        </button>
                                    </div>
                                    
                                    {{-- DESPLEGABLE DE DETALLS DE FEEDBACK --}}
                                    <div id="feedback-details" style="display:none; margin-top:15px; animation: fadeIn 0.3s ease-out;">
                                        {{-- Classificació correcta (només visible si tria "No") --}}
                                        <div id="correct-classification-group" style="margin-bottom:12px;">
                                            <label style="display:block; font-size:11px; font-weight:700; color:#64748b; margin-bottom:6px; text-transform:uppercase;">Classificació correcta:</label>
                                            <div style="display:flex; gap:8px;">
                                                <button type="button" class="class-choice-btn" data-class="NO" onclick="selectCorrectClass('NO')" style="flex:1; padding:6px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-size:11px; font-weight:700; color:#64748b; cursor:pointer; transition:all 0.2s;">NO</button>
                                                <button type="button" class="class-choice-btn" data-class="PCC" onclick="selectCorrectClass('PCC')" style="flex:1; padding:6px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-size:11px; font-weight:700; color:#64748b; cursor:pointer; transition:all 0.2s;">PCC</button>
                                                <button type="button" class="class-choice-btn" data-class="MACA" onclick="selectCorrectClass('MACA')" style="flex:1; padding:6px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; font-size:11px; font-weight:700; color:#64748b; cursor:pointer; transition:all 0.2s;">MACA</button>
                                            </div>
                                        </div>
                                        
                                        <div style="margin-bottom:12px;">
                                            <label for="feedback-comentari" style="display:block; font-size:11px; font-weight:700; color:#64748b; margin-bottom:6px; text-transform:uppercase;">Comentaris / Observacions clíniques:</label>
                                            <textarea id="feedback-comentari" rows="2" style="width:100%; padding:8px; border:1.5px solid #e2e8f0; border-radius:8px; font-size:12px; font-family:inherit; outline:none; resize:none; background:#f8fafc; transition:all 0.2s;" placeholder="Escriu una breu justificació si cal..."></textarea>
                                        </div>
                                        
                                        <div style="display:flex; gap:8px;">
                                            <button type="button" onclick="cancelFeedback()" style="flex:1; padding:8px; border:1px solid #e2e8f0; border-radius:8px; font-size:12px; font-weight:600; color:#64748b; background:white; cursor:pointer; transition:all 0.2s;">Cancel·lar</button>
                                            <button type="button" id="btn-submit-feedback" onclick="submitFeedback()" style="flex:2; padding:8px; background:linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%); border:none; border-radius:8px; font-size:12px; font-weight:600; color:white; cursor:pointer; transition:all 0.2s; box-shadow:0 2px 4px rgba(124,58,237,0.2); position:relative; overflow:hidden;">
                                                <span id="feedback-btn-text">Desar Feedback</span>
                                                <span id="feedback-btn-spinner" style="display: none; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);">
                                                    <svg style="animation: spin 1s linear infinite; width: 16px; height: 16px;" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity: 0.25;"></circle>
                                                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" style="opacity: 0.75;"></path>
                                                    </svg>
                                                </span>
                                            </button>
                                        </div>
                                    </div>
                                    
                                    {{-- MISSATGE D'ÈXIT --}}
                                    <div id="feedback-success" style="display:none; text-align:center; padding:10px 0; animation: scaleUp 0.3s ease-out;">
                                        <div style="width:36px; height:36px; background:#dcfce7; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#15803d; margin:0 auto 8px auto;">
                                            <svg style="width:20px; height:20px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                                <polyline points="20 6 9 17 4 12"></polyline>
                                            </svg>
                                        </div>
                                        <p style="font-size:12px; font-weight:700; color:#15803d; margin:0;">Feedback registrat!</p>
                                        <p style="font-size:10px; color:#16a34a; margin-top:2px;">Gràcies per ajudar a millorar el model.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    @endif

                    {{-- 4. TARGETA HISTORIAL DE REVISIONS --}}
                    <div id="card-historial-feedback"
                        style="padding:20px; background:white; border-radius:16px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                        <div
                            style="display:flex; align-items:center; gap:10px; margin-bottom:15px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                            <div
                                style="width:36px; height:36px; background:#f0f9ff; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#0284c7;">
                                <svg style="width:20px; height:20px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <polyline points="12 6 12 12 16 14"></polyline>
                                </svg>
                            </div>
                            <h3 style="font-size:15px; font-weight:700; color:#1e293b; margin:0;">Historial de Revisions</h3>
                        </div>
                        <div id="timeline-feedback-list" style="display:flex; flex-direction:column; gap:15px; max-height:220px; overflow-y:auto; padding-right:5px;">
                            @if(isset($historial) && count($historial) > 0)
                                @foreach($historial as $h)
                                    @php
                                        $isVal = $h['feedback_correcte'];
                                        $bulletColor = $isVal ? '#16a34a' : '#2563eb';
                                        $titleText = $isVal ? 'Validada' : 'Corregida a ' . ($h['classificacio_correcta'] ?? 'Altra');
                                    @endphp
                                    <div style="position:relative; padding-left:18px; border-left:2px solid #e2e8f0; font-size:12px;">
                                        <div style="position:absolute; left:-6px; top:4px; width:10px; height:10px; border-radius:50%; background:{{ $bulletColor }}; border:2px solid white; box-shadow:0 0 0 1px #cbd5e1;"></div>
                                        <div style="display:flex; justify-content:space-between; font-weight:700; color:#1e293b;">
                                            <span>{{ $titleText }}</span>
                                            <span style="font-size:10px; color:#94a3b8; font-weight:500;">{{ \Carbon\Carbon::parse($h['timestamp'])->format('d/m H:i') }}</span>
                                        </div>
                                        <div style="color:#64748b; font-size:11px; margin-top:2px;">
                                            Per: <span style="font-weight:600; color:#475569;">{{ $h['usuari'] }}</span>
                                        </div>
                                        @if(!empty($h['comentari']))
                                            <div style="margin-top:4px; padding:4px 8px; background:#f8fafc; border-radius:6px; border-left:2px solid #cbd5e1; font-style:italic; color:#475569; font-size:11px; word-break:break-word;">
                                                "{{ $h['comentari'] }}"
                                            </div>
                                        @endif
                                    </div>
                                @endforeach
                            @else
                                <p id="no-feedback-text" style="font-size:12px; color:#64748b; text-align:center; margin:20px 0;">No hi ha cap interacció registrada.</p>
                            @endif
                        </div>
                    </div>
                </div>

                {{-- INFORME GENERATIU --}}
                @if (isset($resultat['informe']))
                    <div
                        style="padding:24px; background:linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius:20px; border:1px solid #bae6fd; position:relative; overflow:hidden;">
                        <div style="position:absolute; top:-20px; right:-20px; opacity:0.1; color:#0369a1;">
                            <svg style="width:120px; height:120px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                            </svg>
                        </div>

                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
                            <div
                                style="width:40px; height:40px; background:#0369a1; border-radius:12px; display:flex; align-items:center; justify-content:center; color:white; box-shadow: 0 4px 6px -1px rgb(3 105 161 / 0.3);">
                                <svg style="width:22px; height:22px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
                                    <path d="M12 2a10 10 0 0 1 10 10h-10V2z"></path>
                                    <path d="M12 12L2.8 7.3"></path>
                                    <path d="M12 12l9.2 4.7"></path>
                                </svg>
                            </div>
                            <div>
                                <h3 style="font-size:16px; font-weight:800; color:#0369a1; margin:0;">Informe de Decisió Clínica
                                    (IA)</h3>
                                <p
                                    style="font-size:11px; color:#0ea5e9; font-weight:600; margin:0; text-transform:uppercase; letter-spacing:0.5px;">
                                    Generat amb {{ $resultat['model_informe'] ?? 'DeepSeek-R1:8b via Ollama' }}</p>
                            </div>
                        </div>

                        <div
                            style="background:rgba(255,255,255,0.6); padding:20px; border-radius:14px; border:1px solid rgba(255,255,255,0.8); font-size:15px; color:#0c4a6e; line-height:1.7; white-space:pre-wrap; font-family: inherit; max-height: 380px; overflow-y: auto;">{!! preg_replace('/\*\*(.*?)\*\*/', '<strong>$1</strong>', e(trim($resultat['informe']))) !!}</div>
                    </div>
                @endif

                {{-- EXPLICABILITAT SHAP --}}
                @if (isset($resultat['explicabilitat_shap']))
                    @php
                        $noms_variables = [
                            'num_visitas_primaria' => 'Visites atenció primària',
                            'farmacs_totals' => 'Fàrmacs prescrits',
                            'diags_totals' => 'Diagnòstics totals',
                            'grup_edat_70-75' => 'Edat (70-75)',
                            'grup_edat_75-80' => 'Edat (75-80)',
                            'grup_edat_80-85' => 'Edat (80-85)',
                            'grup_edat_85-90' => 'Edat (85-90)',
                            'grup_edat_90>' => 'Edat (Major de 90)',
                            'antiinfecciosos_per_a_us_sistemic' => 'Antiinfecciosos (ús sistèmic)',
                            'sistema_nervios' => 'Patologia: Sistema Nerviós',
                            'sang_i_organs_hematopoetics' => 'Patologia: Sang i òrgans hematopoètics',
                            'visites_urgencies_risc_vital' => 'Visites urgències (risc vital)',
                            'sistema_digestiu_i_metabolisme' => 'Patologia: Sistema digestiu/metabolisme',
                            'sistema_cardiovascular' => 'Patologia: Sistema cardiovascular',
                            'visites_hosp_243_365' => 'Hospitalitzacions (fa 243-365 dies)',
                            'visites_inter_243_365' => 'Visites intermèdies (fa 243-365 dies)',
                            'sistema_musculoesqueletic' => 'Patologia: Sistema musculoesquelètic',
                            'signes_i_sintomes' => 'Signes i símptomes clínics',
                            'sexe_D' => 'Gènere femení',
                            'altres' => 'Altres diagnòstics/fàrmacs'
                        ];

                        $max_s1 = 0.0001;
                        if (isset($resultat['explicabilitat_shap']['stage1_chronic_vs_no'])) {
                            foreach ($resultat['explicabilitat_shap']['stage1_chronic_vs_no'] as $item) {
                                $max_s1 = max($max_s1, abs($item['shap_value']));
                            }
                        }

                        $max_s2 = 0.0001;
                        if (isset($resultat['explicabilitat_shap']['stage2_maca_vs_pcc'])) {
                            foreach ($resultat['explicabilitat_shap']['stage2_maca_vs_pcc'] as $item) {
                                $max_s2 = max($max_s2, abs($item['shap_value']));
                            }
                        }
                    @endphp

                    <div
                        style="margin-top:24px; padding:24px; background:white; border-radius:20px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); animation: fadeInUp 0.5s ease-out;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:20px;">
                            <div
                                style="width:40px; height:40px; background:#eff6ff; border-radius:12px; display:flex; align-items:center; justify-content:center; color:#2563eb;">
                                <svg style="width:22px; height:22px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <line x1="18" y1="20" x2="18" y2="10"></line>
                                    <line x1="12" y1="20" x2="12" y2="4"></line>
                                    <line x1="6" y1="20" x2="6" y2="14"></line>
                                </svg>
                            </div>
                            <div>
                                <h3 style="font-size:16px; font-weight:800; color:#1e293b; margin:0;">Explicabilitat de les
                                    Decisions (SHAP)</h3>
                                <p style="font-size:12px; color:#64748b; margin:0;">Factors clínics individuals que pesen més en la
                                    classificació realitzada pel model.</p>
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:24px; margin-top:20px;">
                            {{-- ESTAT 1: CRONIC VS NO --}}
                            @if(isset($resultat['explicabilitat_shap']['stage1_chronic_vs_no']) && count($resultat['explicabilitat_shap']['stage1_chronic_vs_no']) > 0)
                                <div>
                                    <div style="margin-bottom:12px; border-bottom:1px solid #f1f5f9; padding-bottom:8px;">
                                        <h4 style="font-size:14px; font-weight:700; color:#1e293b; margin:0 0 4px 0;">Estat 1: Decisió de Cronicitat</h4>
                                        <p style="font-size:11px; color:#64748b; margin:0;">Variables que determinen si el pacient es considera Crònic o NO.</p>
                                    </div>
                                    <div style="display:flex; flex-direction:column; gap:4px;">
                                        <!-- Header row for the plot -->
                                        <div style="display: flex; align-items: center; margin-bottom: 8px; border-bottom: 2px solid #cbd5e1; padding-bottom: 6px;">
                                            <div style="width: 32%; font-size: 10px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">Variable</div>
                                            <div style="width: 13%; font-size: 10px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; text-align: right; padding-right: 15px;">Valor</div>
                                            <div style="width: 55%; display: flex; justify-content: space-between; font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; position: relative;">
                                                <span style="color: #2563eb;">← Disminueix Cronicitat</span>
                                                <span style="color: #ef4444;">Incrementa Cronicitat →</span>
                                            </div>
                                        </div>
                                        @foreach($resultat['explicabilitat_shap']['stage1_chronic_vs_no'] as $item)
                                            @php
                                                $var_name = $noms_variables[$item['variable']] ?? ucfirst(str_replace('_', ' ', $item['variable']));
                                                $val = $item['shap_value'];
                                                $pct = round((abs($val) / $max_s1) * 100);
                                            @endphp
                                            <div style="display: flex; align-items: center; padding: 6px 0; border-bottom: 1px solid #f1f5f9; position: relative;">
                                                <!-- Variable Name -->
                                                <div style="width: 32%; font-size: 12px; font-weight: 600; color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{{ $var_name }}">
                                                    {{ $var_name }}
                                                </div>
                                                <!-- Patient Value -->
                                                <div style="width: 13%; font-size: 11px; color: #64748b; font-weight: 500; text-align: right; padding-right: 15px;">
                                                    {{ $item['valor_original'] !== null && $item['valor_original'] !== '' ? $item['valor_original'] : '-' }}
                                                </div>
                                                <!-- Plot Area -->
                                                <div style="width: 55%; height: 20px; position: relative; display: flex; align-items: center;">
                                                    <!-- Center line -->
                                                    <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 1.5px; background: #cbd5e1; z-index: 1;"></div>
                                                    @if($val >= 0)
                                                        <!-- Positive Red Bar -->
                                                        <div style="position: absolute; left: 50%; width: {{ min(44, $pct * 0.44) }}%; height: 10px; background: #ef4444; border-radius: 0 3px 3px 0; z-index: 2;"></div>
                                                        <!-- Label -->
                                                        <div style="position: absolute; left: calc(50% + {{ min(44, $pct * 0.44) }}% + 4px); font-size: 10px; font-weight: 700; color: #b91c1c;">
                                                            +{{ number_format($val, 3) }}
                                                        </div>
                                                    @else
                                                        <!-- Negative Blue Bar -->
                                                        <div style="position: absolute; right: 50%; width: {{ min(44, $pct * 0.44) }}%; height: 10px; background: #3b82f6; border-radius: 3px 0 0 3px; z-index: 2;"></div>
                                                        <!-- Label -->
                                                        <div style="position: absolute; right: calc(50% + {{ min(44, $pct * 0.44) }}% + 4px); font-size: 10px; font-weight: 700; color: #1d4ed8;">
                                                            {{ number_format($val, 3) }}
                                                        </div>
                                                    @endif
                                                </div>
                                            </div>
                                        @endforeach
                                        <!-- Bottom scale axis -->
                                        <div style="display: flex; align-items: center; margin-top: 6px; padding-top: 6px; border-top: 1px solid #cbd5e1;">
                                            <div style="width: 45%;"></div>
                                            <div style="width: 55%; position: relative; display: flex; justify-content: space-between; font-size: 8px; color: #94a3b8; font-weight: 700;">
                                                <span style="position: absolute; left: 6%; transform: translateX(-50%);">-{{ number_format($max_s1, 1) }}</span>
                                                <span style="position: absolute; left: 50%; transform: translateX(-50%);">0.0</span>
                                                <span style="position: absolute; left: 94%; transform: translateX(-50%);">+{{ number_format($max_s1, 1) }}</span>
                                            </div>
                                        </div>
                                        <div style="text-align: center; font-size: 9px; color: #94a3b8; font-weight: 700; margin-top: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Contribució SHAP (impacte en la cronicitat)
                                        </div>
                                    </div>
                                </div>
                            @endif

                            {{-- ESTAT 2: MACA VS PCC --}}
                            @if(isset($resultat['explicabilitat_shap']['stage2_maca_vs_pcc']) && count($resultat['explicabilitat_shap']['stage2_maca_vs_pcc']) > 0 && ($resultat['prediccio_v3']['resultat'] ?? '') !== 'NO')
                                <div>
                                    <div style="margin-bottom:12px; border-bottom:1px solid #f1f5f9; padding-bottom:8px;">
                                        <h4 style="font-size:14px; font-weight:700; color:#1e293b; margin:0 0 4px 0;">Estat 2: Decisió de Gravetat</h4>
                                        <p style="font-size:11px; color:#64748b; margin:0;">Variables que diferencien si el crònic és PCC o MACA.</p>
                                    </div>
                                    <div style="display:flex; flex-direction:column; gap:4px;">
                                        <!-- Header row for the plot -->
                                        <div style="display: flex; align-items: center; margin-bottom: 8px; border-bottom: 2px solid #cbd5e1; padding-bottom: 6px;">
                                            <div style="width: 32%; font-size: 10px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;">Variable</div>
                                            <div style="width: 13%; font-size: 10px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; text-align: right; padding-right: 15px;">Valor</div>
                                            <div style="width: 55%; display: flex; justify-content: space-between; font-size: 9px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; position: relative;">
                                                <span style="color: #d97706;">← Afavoreix PCC</span>
                                                <span style="color: #dc2626;">Afavoreix MACA →</span>
                                            </div>
                                        </div>
                                        @foreach($resultat['explicabilitat_shap']['stage2_maca_vs_pcc'] as $item)
                                            @php
                                                $var_name = $noms_variables[$item['variable']] ?? ucfirst(str_replace('_', ' ', $item['variable']));
                                                $val = $item['shap_value'];
                                                $pct = round((abs($val) / $max_s2) * 100);
                                            @endphp
                                            <div style="display: flex; align-items: center; padding: 6px 0; border-bottom: 1px solid #f1f5f9; position: relative;">
                                                <!-- Variable Name -->
                                                <div style="width: 32%; font-size: 12px; font-weight: 600; color: #334155; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{{ $var_name }}">
                                                    {{ $var_name }}
                                                </div>
                                                <!-- Patient Value -->
                                                <div style="width: 13%; font-size: 11px; color: #64748b; font-weight: 500; text-align: right; padding-right: 15px;">
                                                    {{ $item['valor_original'] !== null && $item['valor_original'] !== '' ? $item['valor_original'] : '-' }}
                                                </div>
                                                <!-- Plot Area -->
                                                <div style="width: 55%; height: 20px; position: relative; display: flex; align-items: center;">
                                                    <!-- Center line -->
                                                    <div style="position: absolute; left: 50%; top: 0; bottom: 0; width: 1.5px; background: #cbd5e1; z-index: 1;"></div>
                                                    @if($val >= 0)
                                                        <!-- Positive Red Bar (MACA) -->
                                                        <div style="position: absolute; left: 50%; width: {{ min(44, $pct * 0.44) }}%; height: 10px; background: #dc2626; border-radius: 0 3px 3px 0; z-index: 2;"></div>
                                                        <!-- Label -->
                                                        <div style="position: absolute; left: calc(50% + {{ min(44, $pct * 0.44) }}% + 4px); font-size: 10px; font-weight: 700; color: #991b1b;">
                                                            +{{ number_format($val, 3) }}
                                                        </div>
                                                    @else
                                                        <!-- Negative Amber Bar (PCC) -->
                                                        <div style="position: absolute; right: 50%; width: {{ min(44, $pct * 0.44) }}%; height: 10px; background: #d97706; border-radius: 3px 0 0 3px; z-index: 2;"></div>
                                                        <!-- Label -->
                                                        <div style="position: absolute; right: calc(50% + {{ min(44, $pct * 0.44) }}% + 4px); font-size: 10px; font-weight: 700; color: #92400e;">
                                                            {{ number_format($val, 3) }}
                                                        </div>
                                                    @endif
                                                </div>
                                            </div>
                                        @endforeach
                                        <!-- Bottom scale axis -->
                                        <div style="display: flex; align-items: center; margin-top: 6px; padding-top: 6px; border-top: 1px solid #cbd5e1;">
                                            <div style="width: 45%;"></div>
                                            <div style="width: 55%; position: relative; display: flex; justify-content: space-between; font-size: 8px; color: #94a3b8; font-weight: 700;">
                                                <span style="position: absolute; left: 6%; transform: translateX(-50%);">-{{ number_format($max_s2, 1) }}</span>
                                                <span style="position: absolute; left: 50%; transform: translateX(-50%);">0.0</span>
                                                <span style="position: absolute; left: 94%; transform: translateX(-50%);">+{{ number_format($max_s2, 1) }}</span>
                                            </div>
                                        </div>
                                        <div style="text-align: center; font-size: 9px; color: #94a3b8; font-weight: 700; margin-top: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Contribució SHAP (impacte en la gravetat)
                                        </div>
                                    </div>
                                </div>
                            @endif
                        </div>
                    </div>
                @endif
            </div>
        @else
            @php
                $totalPending = count($priorityPatients);
                $macaCount = 0;
                $pccCount = 0;
                foreach ($priorityPatients as $p) {
                    if (($p['prediccio_estat'] ?? '') === 'MACA') {
                        $macaCount++;
                    } elseif (($p['prediccio_estat'] ?? '') === 'PCC') {
                        $pccCount++;
                    }
                }
            @endphp

            {{-- KPIs / Targetes de resum --}}
            <div class="stats-grid" style="animation: fadeInUp 0.5s ease-out;">
                <div class="stat-card">
                    <div class="stat-icon-total">
                        <svg style="width: 24px; height: 24px;" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                        </svg>
                    </div>
                    <div>
                        <div class="stat-value">{{ $totalPending }}</div>
                        <div class="stat-label">Pendents de Revisió</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon-maca">
                        <svg style="width: 24px; height: 24px;" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                        </svg>
                    </div>
                    <div>
                        <div class="stat-value">{{ $macaCount }}</div>
                        <div class="stat-label">Urgents (MACA)</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon-pcc">
                        <svg style="width: 24px; height: 24px;" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                    </div>
                    <div>
                        <div class="stat-value">{{ $pccCount }}</div>
                        <div class="stat-label">Crònics Complexos (PCC)</div>
                    </div>
                </div>
            </div>

            <div style="border-top: 1px solid #eef3fa; padding-top: 25px; margin-top: 25px; animation: fadeInUp 0.5s ease-out;">
                <h3 style="font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
                    <svg style="width: 20px; height: 20px; color: #3b82f6;" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>
                    </svg>
                    <span>Llistat de Prioritats Clíniques</span>
                </h3>

                {{-- Taula Premium de Pacients --}}
                <div class="premium-table-container">
                    <table class="premium-table">
                        <thead>
                            <tr>
                                <th>ID Pacient</th>
                                <th>Perfil</th>
                                <th>Estat Suggerit</th>
                                <th>Nivell d'Urgència / Probabilitat</th>
                                <th style="text-align: center;">Estat Revisió</th>
                                <th style="text-align: right;">Acció</th>
                            </tr>
                        </thead>
                        <tbody>
                            @forelse ($priorityPatients as $p)
                                @php
                                    $isMaca = ($p['prediccio_estat'] ?? '') === 'MACA';
                                    $prob = $isMaca ? ($p['prob_maca'] ?? 0.0) : ($p['prob_pcc'] ?? 0.0);
                                @endphp
                                <tr>
                                    <td>
                                        <span style="font-weight: 700; color: #1e293b;">#{{ $p['id_pacient'] }}</span>
                                    </td>
                                    <td>
                                        <span style="font-size: 13px; color: #64748b;">
                                            {{ $p['grup_edat'] }} anys | {{ ($p['sexe'] ?? '') === 'H' ? 'Home' : 'Dona' }}
                                        </span>
                                    </td>
                                    <td>
                                        <span class="{{ $isMaca ? 'priority-badge-maca' : 'priority-badge-pcc' }}">
                                            {{ $p['prediccio_estat'] }}
                                        </span>
                                    </td>
                                    <td>
                                        <div style="display: flex; align-items: center;">
                                            <div class="progress-bar-container">
                                                <div class="{{ $isMaca ? 'progress-bar-maca' : 'progress-bar-pcc' }}" style="width: {{ $prob * 100 }}%"></div>
                                            </div>
                                            <span style="font-size: 13px; font-weight: 700; color: {{ $isMaca ? '#ef4444' : '#f59e0b' }};">
                                                {{ number_format($prob * 100, 1) }}%
                                            </span>
                                        </div>
                                    </td>
                                    <td style="text-align: center;">
                                        <span style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #b45309; background: #fffbeb; padding: 4px 10px; border-radius: 9999px; border: 1px solid #fde68a;">
                                            <span style="width: 6px; height: 6px; background: #f59e0b; border-radius: 50%;"></span>
                                            Pendent
                                        </span>
                                    </td>
                                    <td style="text-align: right;">
                                        <button class="review-btn" onclick="selectPatient('{{ $p['id_pacient'] }}')">
                                            <span>Revisar Cas</span>
                                            <svg style="width: 14px; height: 14px;" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"></path>
                                            </svg>
                                        </button>
                                    </td>
                                </tr>
                            @empty
                                <tr>
                                    <td colspan="6" style="text-align: center; color: #94a3b8; padding: 40px 0; font-style: italic;">
                                        No hi ha cap pacient pendent de revisió en aquests moments.
                                    </td>
                                </tr>
                            @endforelse
                        </tbody>
                    </table>
                </div>
            </div>
        @endif
    </div>

    <style>
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }

        .form-input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
        }

        @media (max-width: 600px) {
            #analysis-form {
                flex-direction: column !important;
                align-items: stretch !important;
                gap: 12px !important;
            }

            #btn-analyze {
                margin-top: 8px !important;
                width: 100% !important;
                min-width: auto !important;
            }
        }

        /* Estils de Feedback */
        .feedback-yes:hover {
            background: #dcfce7 !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(22, 163, 74, 0.1);
        }
        .feedback-no:hover {
            background: #fee2e2 !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(220, 38, 38, 0.1);
        }
        .class-choice-btn.selected {
            background: #f5f3ff !important;
            border-color: #7c3aed !important;
            color: #7c3aed !important;
            box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.1);
        }
        .class-choice-btn:hover:not(.selected) {
            border-color: #cbd5e1 !important;
            background: #f1f5f9 !important;
        }
        #feedback-comentari:focus {
            border-color: #7c3aed;
            background: white;
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes scaleUp {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
    </style>

    <script>
        function selectPatient(id) {
            document.getElementById('dni').value = id;
            document.getElementById('analysis-form').submit();
        }

        document.getElementById('analysis-form').addEventListener('submit', function () {
            // Desactiva el botó i canvia el text pel spinner per donar feedback dinàmic de UX
            const btn = document.getElementById('btn-analyze');
            document.getElementById('btn-text').style.opacity = '0';
            document.getElementById('btn-spinner').style.display = 'block';
            btn.style.pointerEvents = 'none';
            btn.style.opacity = '0.9';

            // Atenuar els resultats existents si l'usuari fa una nova consulta
            const resultsContainer = document.querySelector('.results-container');
            if (resultsContainer) {
                resultsContainer.style.opacity = '0.4';
                resultsContainer.style.transition = 'opacity 0.3s';
            }
        });

        @if (isset($resultat))
            // Variables globals per gestionar el feedback i la pestanya SHAP
            let feedbackCorrecte = null;
            let classCorrectaSeleccionada = null;

            
            const pacientIdVal = {{ $resultat['pacient']['id_pacient'] }};
            const predModelVal = "{{ $resultat['prediccio_v3']['resultat'] ?? 'NO' }}";
            const confModelVal = {{ is_numeric($resultat['prediccio_v3']['confianca'] ?? null) ? $resultat['prediccio_v3']['confianca'] : 0 }};



            function showFeedbackDetails(isCorrect) {
                feedbackCorrecte = isCorrect;
                document.getElementById('feedback-initial-buttons').style.display = 'none';
                
                const classificationGroup = document.getElementById('correct-classification-group');
                if (isCorrect) {
                    classificationGroup.style.display = 'none';
                    classCorrectaSeleccionada = predModelVal; // si és correcte, coincideix
                } else {
                    classificationGroup.style.display = 'block';
                    classCorrectaSeleccionada = null; // cal que triï una
                    // Netejar selecció prèvia de botons
                    document.querySelectorAll('.class-choice-btn').forEach(btn => btn.classList.remove('selected'));
                }
                
                document.getElementById('feedback-details').style.display = 'block';
            }

            function selectCorrectClass(classChoice) {
                classCorrectaSeleccionada = classChoice;
                document.querySelectorAll('.class-choice-btn').forEach(btn => {
                    if (btn.getAttribute('data-class') === classChoice) {
                        btn.classList.add('selected');
                    } else {
                        btn.classList.remove('selected');
                    }
                });
            }

            function cancelFeedback() {
                document.getElementById('feedback-details').style.display = 'none';
                document.getElementById('feedback-initial-buttons').style.display = 'flex';
                document.getElementById('feedback-comentari').value = '';
                classCorrectaSeleccionada = null;
                feedbackCorrecte = null;
            }

            function submitFeedback() {
                if (feedbackCorrecte === false && !classCorrectaSeleccionada) {
                    alert('Si us plau, selecciona quina hauria de ser la classificació correcta.');
                    return;
                }
                
                const btnSubmit = document.getElementById('btn-submit-feedback');
                const btnText = document.getElementById('feedback-btn-text');
                const btnSpinner = document.getElementById('feedback-btn-spinner');
                
                // Mostrar spinner i desactivar botó
                btnText.style.opacity = '0';
                btnSpinner.style.display = 'block';
                btnSubmit.disabled = true;
                btnSubmit.style.pointerEvents = 'none';
                
                const comentari = document.getElementById('feedback-comentari').value;
                const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                
                const payload = {
                    id_pacient: pacientIdVal,
                    prediccio_model: predModelVal,
                    confianca_model: confModelVal,
                    feedback_correcte: feedbackCorrecte ? 1 : 0,
                    classificacio_correcta: classCorrectaSeleccionada,
                    comentari: comentari
                };
                
                fetch('{{ route("feedback.save") }}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': token,
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('feedback-details').style.display = 'none';
                        document.getElementById('feedback-success').style.display = 'block';
                        
                        // Actualitzar el Badge en calent
                        const badge = document.getElementById('badge-estat-prediccio');
                        if (badge) {
                            if (feedbackCorrecte) {
                                badge.innerText = 'Validada';
                                badge.style.cssText = 'margin-left:auto; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:700; background:#dcfce7; color:#16a34a;';
                            } else {
                                const corregidaClass = classCorrectaSeleccionada || 'Altra';
                                badge.innerText = 'Corregida a ' + corregidaClass;
                                badge.style.cssText = 'margin-left:auto; padding:2px 8px; border-radius:6px; font-size:10px; font-weight:700; background:#dbeafe; color:#2563eb;';
                            }
                        }
                        
                        // Afegir l'entrada a la línia de temps de l'historial en calent
                        const timeline = document.getElementById('timeline-feedback-list');
                        const noFbText = document.getElementById('no-feedback-text');
                        if (noFbText) noFbText.remove();
                        
                        if (timeline) {
                            const now = new Date();
                            const formatTime = String(now.getDate()).padStart(2, '0') + '/' + String(now.getMonth()+1).padStart(2, '0') + ' ' + String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
                            
                            const isVal = feedbackCorrecte;
                            const bulletColor = isVal ? '#16a34a' : '#2563eb';
                            const titleText = isVal ? 'Validada' : 'Corregida a ' + (classCorrectaSeleccionada || 'Altra');
                            const comentariEscrit = comentari ? comentari.replace(/"/g, '&quot;') : '';
                            
                            const newItem = document.createElement('div');
                            newItem.style.cssText = 'position:relative; padding-left:18px; border-left:2px solid #e2e8f0; font-size:12px; animation: fadeIn 0.3s ease-out;';
                            
                            let comentariHTML = '';
                            if (comentariEscrit) {
                                comentariHTML = `
                                    <div style="margin-top:4px; padding:4px 8px; background:#f8fafc; border-radius:6px; border-left:2px solid #cbd5e1; font-style:italic; color:#475569; font-size:11px; word-break:break-word;">
                                        "${comentariEscrit}"
                                    </div>
                                `;
                            }
                            
                            newItem.innerHTML = `
                                <div style="position:absolute; left:-6px; top:4px; width:10px; height:10px; border-radius:50%; background:${bulletColor}; border:2px solid white; box-shadow:0 0 0 1px #cbd5e1;"></div>
                                <div style="display:flex; justify-content:space-between; font-weight:700; color:#1e293b;">
                                    <span>${titleText}</span>
                                    <span style="font-size:10px; color:#94a3b8; font-weight:500;">${formatTime}</span>
                                </div>
                                <div style="color:#64748b; font-size:11px; margin-top:2px;">
                                    Per: <span style="font-weight:600; color:#475569;">{{ auth()->user()->name ?? 'professional' }}</span>
                                </div>
                                ${comentariHTML}
                            `;
                            
                            timeline.insertBefore(newItem, timeline.firstChild);
                        }
                    } else {
                        alert('Error: ' + data.message);
                        resetSubmitButton();
                    }
                })
                .catch(error => {
                    console.error('Error enviant feedback:', error);
                    alert('S\'ha produït un error de xarxa en enviar el feedback.');
                    resetSubmitButton();
                });
                
                function resetSubmitButton() {
                    btnText.style.opacity = '1';
                    btnSpinner.style.display = 'none';
                    btnSubmit.disabled = false;
                    btnSubmit.style.pointerEvents = 'auto';
                }
            }
        @endif
    </script>
            </div> {{-- content-card --}}
        </div> {{-- main-analysis-panel --}}
    </div> {{-- dashboard-layout --}}
@endsection