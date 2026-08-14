@extends('layouts.app')

@section('page-title', 'Anàlisi de Pacient')

@section('content')
    <div class="content-card">
        {{-- CAPÇALERA --}}
        <div class="card-header-row">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <h1 class="card-title">Anàlisi de Pacient</h1>
        </div>
        <p class="card-subtitle">Introdueix l'ID del pacient per obtenir l'anàlisi predictiva jeràrquica</p>

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
                <span id="btn-text">Analitzar</span>
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
                            </div>
                        </div>
                    @endif

                    {{-- 4. TARGETA FAMILIARS (HARDCODED) --}}
                    <div
                        style="padding:20px; background:white; border-radius:16px; border:1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
                        <div
                            style="display:flex; align-items:center; gap:10px; margin-bottom:15px; border-bottom:1px solid #f1f5f9; padding-bottom:10px;">
                            <div
                                style="width:36px; height:36px; background:#fff1f2; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#e11d48;">
                                <svg style="width:20px; height:20px;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                    stroke-linejoin="round">
                                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                                    <circle cx="9" cy="7" r="4"></circle>
                                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                                    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                                </svg>
                            </div>
                            <h3 style="font-size:15px; font-weight:700; color:#1e293b; margin:0;">Antecedents familiars</h3>
                        </div>
                        <div style="display:flex; flex-direction:column; gap:12px;">
                            <div>
                                <p>Cap familiar amb antecedents</p>
                            </div>
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
                                    Generat amb DeepSeek-R1:8b via Ollama</p>
                            </div>
                        </div>

                        <div
                            style="background:rgba(255,255,255,0.6); padding:20px; border-radius:14px; border:1px solid rgba(255,255,255,0.8); font-size:15px; color:#0c4a6e; line-height:1.7; white-space:pre-wrap; font-family: inherit;">
                            {{ str_replace(['**', '#'], '', $resultat['informe']) }}</div>
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

                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:24px;">
                            {{-- ESTAT 1: CRONIC VS NO --}}
                            @if(isset($resultat['explicabilitat_shap']['stage1_chronic_vs_no']) && count($resultat['explicabilitat_shap']['stage1_chronic_vs_no']) > 0)
                                <div>
                                    <div style="margin-bottom:12px; border-bottom:1px solid #f1f5f9; padding-bottom:8px;">
                                        <h4 style="font-size:14px; font-weight:700; color:#1e293b; margin:0 0 4px 0;">Estat 1: Decisió
                                            de Cronicitat</h4>
                                        <p style="font-size:11px; color:#64748b; margin:0;">Variables que determinen si el pacient es
                                            considera Crònic o NO.</p>
                                    </div>
                                    <div style="display:flex; flex-direction:column; gap:10px;">
                                        @foreach($resultat['explicabilitat_shap']['stage1_chronic_vs_no'] as $item)
                                            @php
                                                $var_name = $noms_variables[$item['variable']] ?? ucfirst(str_replace('_', ' ', $item['variable']));
                                                $val = $item['shap_value'];
                                                $pct = round((abs($val) / $max_s1) * 100);
                                                $is_pos = $val > 0;
                                                $color = $is_pos ? '#f97316' : '#3b82f6';
                                                $badge_bg = $is_pos ? '#fff7ed' : '#eff6ff';
                                                $badge_text = $is_pos ? '#c2410c' : '#1d4ed8';
                                                $badge_label = $is_pos ? 'Cap a Crònic' : 'Cap a NO';
                                            @endphp
                                            <div
                                                style="display:flex; flex-direction:column; gap:4px; padding:8px; border-radius:8px; background:#f8fafc; border:1px solid #f1f5f9;">
                                                <div
                                                    style="display:flex; justify-content:space-between; align-items:center; font-size:12px;">
                                                    <span style="font-weight:600; color:#334155;">{{ $var_name }}</span>
                                                    <span
                                                        style="padding:2px 6px; border-radius:4px; font-size:10px; font-weight:700; background:{{ $badge_bg }}; color:{{ $badge_text }};">
                                                        {{ $badge_label }} ({{ $val > 0 ? '+' : '' }}{{ number_format($val, 3) }})
                                                    </span>
                                                </div>
                                                <div style="display:flex; align-items:center; gap:8px; margin-top:2px;">
                                                    <div
                                                        style="flex-grow:1; height:6px; background:#e2e8f0; border-radius:3px; overflow:hidden;">
                                                        <div
                                                            style="width:{{ $pct }}%; background:{{ $color }}; height:100%; border-radius:3px;">
                                                        </div>
                                                    </div>
                                                    @if($item['valor_original'] !== null && $item['valor_original'] !== '')
                                                        <span style="font-size:10px; color:#64748b; font-weight:600; flex-shrink:0;">Val:
                                                            {{ $item['valor_original'] }}</span>
                                                    @endif
                                                </div>
                                            </div>
                                        @endforeach
                                    </div>
                                </div>
                            @endif

                            {{-- ESTAT 2: MACA VS PCC --}}
                            @if(isset($resultat['explicabilitat_shap']['stage2_maca_vs_pcc']) && count($resultat['explicabilitat_shap']['stage2_maca_vs_pcc']) > 0 && ($resultat['prediccio_v3']['resultat'] ?? '') !== 'NO')
                                <div>
                                    <div style="margin-bottom:12px; border-bottom:1px solid #f1f5f9; padding-bottom:8px;">
                                        <h4 style="font-size:14px; font-weight:700; color:#1e293b; margin:0 0 4px 0;">Estat 2: Decisió
                                            de Gravetat</h4>
                                        <p style="font-size:11px; color:#64748b; margin:0;">Variables que diferencien si el crònic és
                                            PCC o MACA.</p>
                                    </div>
                                    <div style="display:flex; flex-direction:column; gap:10px;">
                                        @foreach($resultat['explicabilitat_shap']['stage2_maca_vs_pcc'] as $item)
                                            @php
                                                $var_name = $noms_variables[$item['variable']] ?? ucfirst(str_replace('_', ' ', $item['variable']));
                                                $val = $item['shap_value'];
                                                $pct = round((abs($val) / $max_s2) * 100);
                                                $is_pos = $val > 0;
                                                $color = $is_pos ? '#dc2626' : '#d97706';
                                                $badge_bg = $is_pos ? '#fee2e2' : '#fffbeb';
                                                $badge_text = $is_pos ? '#991b1b' : '#92400e';
                                                $badge_label = $is_pos ? 'Cap a MACA' : 'Cap a PCC';
                                            @endphp
                                            <div
                                                style="display:flex; flex-direction:column; gap:4px; padding:8px; border-radius:8px; background:#f8fafc; border:1px solid #f1f5f9;">
                                                <div
                                                    style="display:flex; justify-content:space-between; align-items:center; font-size:12px;">
                                                    <span style="font-weight:600; color:#334155;">{{ $var_name }}</span>
                                                    <span
                                                        style="padding:2px 6px; border-radius:4px; font-size:10px; font-weight:700; background:{{ $badge_bg }}; color:{{ $badge_text }};">
                                                        {{ $badge_label }} ({{ $val > 0 ? '+' : '' }}{{ number_format($val, 3) }})
                                                    </span>
                                                </div>
                                                <div style="display:flex; align-items:center; gap:8px; margin-top:2px;">
                                                    <div
                                                        style="flex-grow:1; height:6px; background:#e2e8f0; border-radius:3px; overflow:hidden;">
                                                        <div
                                                            style="width:{{ $pct }}%; background:{{ $color }}; height:100%; border-radius:3px;">
                                                        </div>
                                                    </div>
                                                    @if($item['valor_original'] !== null && $item['valor_original'] !== '')
                                                        <span style="font-size:10px; color:#64748b; font-weight:600; flex-shrink:0;">Val:
                                                            {{ $item['valor_original'] }}</span>
                                                    @endif
                                                </div>
                                            </div>
                                        @endforeach
                                    </div>
                                </div>
                            @endif
                        </div>
                    </div>
                @endif

                {{-- JSON DEBUG --}}
                <details style="margin-top:24px; border-top:1px solid #f1f5f9; padding-top:16px;">
                    <summary style="font-size:12px; color:#94a3b8; cursor:pointer; font-weight:600;">Detalls tècnics del motor
                        de decisió (JSON)</summary>
                    <pre
                        style="font-size:11px; color:#64748b; background:#f8fafc; padding:16px; border-radius:12px; margin-top:12px; overflow-x:auto; border:1px solid #f1f5f9;">{{ json_encode($resultat, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) }}</pre>
                </details>
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
    </style>

    <script>
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
    </script>
@endsection