# Capítol 6: Anàlisi dels Requisits Funcionals

Aquest document conté l'**anàlisi formal dels requisits funcionals** del sistema per a la redacció del **Capítol 6** de la memòria del Treball de Fi de Grau (TFG). Inclou el **Diagrama de Classes del Sistema**, l'anàlisi del model de domini i els **Diagrames de Seqüència UML** per a cadascun dels casos d'ús principals.

---

## 6.1. Diagrama de Classes del Sistema

El sistema s'estructura seguint un patró arquitectònic desacoblat en tres capes (**Presentació/Control en Laravel**, **Serveis d'Intel·ligència Artificial en Python Flask** i **Persistència de Dades en SQLite/FAISS**).

### 6.1.1. Diagrama de Classes UML (Mermaid)

```mermaid
classDiagram
    direction TB

    %% Capa de Presentació (Laravel)
    class PatientAnalysisController {
        -PythonApiService apiService
        +index() View
        +show(string id) View
        +analyze(Request request) JsonResponse
        +saveFeedback(Request request) JsonResponse
        +getTimeline(string id) JsonResponse
    }

    class PythonApiService {
        -string baseUrl
        -int timeout
        +getPriorityPatients() array
        +analyzePatient(string patientId) array
        +submitFeedback(array feedbackData) array
        +getPatientHistory(string patientId) array
    }

    class User {
        +int id
        +string name
        +string email
        +string role
        +getProfessionalSignature() string
    }

    class DashboardViewModel {
        +int totalPending
        +int totalMaca
        +int totalPcc
        +array priorityList
        +calculateKpis() void
    }

    %% Capa d'IA (Flask / Python)
    class FlaskAPI {
        +get_priority_patients() Response
        +analyze_patient() Response
        +submit_feedback() Response
        +get_patient_timeline() Response
    }

    class HierarchicalPredictor {
        -Pipeline stage1Model
        -CalibratedClassifierCV stage2Model
        -float thresholdStage1
        -float thresholdStage2
        +predict_patient(DataFrame patientData) dict
        +predict_probabilities(DataFrame patientData) dict
        -evaluate_chronic(DataFrame data) tuple
        -evaluate_complexity(DataFrame data) tuple
    }

    class ShapExplainer {
        -TreeExplainer explainerStage1
        -TreeExplainer explainerStage2
        -ColumnTransformer preprocessor
        +calcular_explicabilitat(DataFrame patientData) list
        -filter_noise(array shapValues) array
        -map_clinical_names(string featureName) string
    }

    class VectorSimilaritySearch {
        -IndexFlatIP faissIndex
        -array metadataRecords
        +find_similar_cases(array patientVector, int k) list
        +calculate_cohort_statistics(list neighbors) dict
    }

    class LLMReportGenerator {
        -string engineType
        -string modelName
        +generar_informe_clinic(dict clinicalContext) string
        -build_rigid_prompt(dict context) string
        -netejar_text_informe(string rawText) string
    }

    %% Capa de Dades (SQLite)
    class PatientRecord {
        +int id_pacient
        +string sexe
        +string grup_edat
        +int diags_totals
        +int farmacs_totals
        +int num_visitas_primaria
        +int visites_urgencies_risc_vital
        +int visites_urgencies_1_121
        +int visites_urgencies_122_242
        +int visites_urgencies_243_365
        +float biomarcadors_risc
    }

    class ClinicalFeedback {
        +int id
        +string timestamp
        +int id_pacient
        +string prediccio_model
        +float confianca_model
        +bool feedback_correcte
        +string classificacio_correcta
        +string comentari
        +string usuari
    }

    %% Relacions i Associacions
    PatientAnalysisController --> PythonApiService : Utilitza
    PatientAnalysisController ..> DashboardViewModel : Instancia
    PatientAnalysisController ..> User : Obté sessió
    
    PythonApiService ..> FlaskAPI : Crides REST JSON

    FlaskAPI --> HierarchicalPredictor : Invoca inferència
    FlaskAPI --> ShapExplainer : Invoca explicabilitat
    FlaskAPI --> VectorSimilaritySearch : Invoca cerca k-NN
    FlaskAPI --> LLMReportGenerator : Sol·licita informe
    FlaskAPI ..> PatientRecord : Consulta SQL
    FlaskAPI ..> ClinicalFeedback : Insereix / Consulta SQL

    HierarchicalPredictor ..> PatientRecord : Processa
    ShapExplainer ..> PatientRecord : Analitza
    VectorSimilaritySearch ..> PatientRecord : Compara vectors L2
    ClinicalFeedback --> PatientRecord : Fa referència
```

---

### 6.1.2. Descripció dels Components i Classes Principals

#### 1. Capa de Presentació i Control (Laravel)
* **`PatientAnalysisController`**: Controlador principal de la interfície d'usuari. Rep les peticions del navegador web, valida les entrades, invoca el servei `PythonApiService` i injecta les dades a les vistes Blade (`dashboard.blade.php`). Gestiona el flux asíncron (AJAX) d'anàlisi i tramesa de valoracions mèdiques.
* **`PythonApiService`**: Servei d'abstracció HTTP basat en `Illuminate\Support\Facades\Http`. Centralitza la configuració d'adreces de xarxa, capçaleres, gestió de timeouts i serialització/deserialització del format JSON cap a l'API de Python.
* **`User`**: Model d'usuari autenticat a Laravel. Aporta la identitat del facultatiu mèdic (`name`, `role`) per a la traçabilitat clínica obligatòria de les esmenes de diagnòstic.
* **`DashboardViewModel`**: Classe/Estructura de dades de vista que agrega els indicadors clau de rendiment hospitalari (KPIs: pendents totals, alertes MACA, alertes PCC) i la llista de pacients prioritzats.

#### 2. Capa d'Intel·ligència Artificial i Suport a la Decisió (Flask / Python)
* **`FlaskAPI`**: Punt d'entrada de la capa d'IA (`api.py`). Exposa els punts d'accés REST (`/api/patients/priority`, `/api/analyze`, `/api/feedback`, `/api/timeline`), orquestrant els mòduls de càlcul de forma sincronitzada.
* **`HierarchicalPredictor`**: Motor d'aprenentatge automàtic jeràrquic. Executa de manera seqüencial el model d'Estadi 1 (`RandomForestClassifier` per a cronicitat $\ge 0.50$) i l'Estadi 2 (`HistGradientBoostingClassifier` calibrat per a PCC vs. MACA $\ge 0.40$), retornant les probabilitats calibrades de cada classe.
* **`ShapExplainer`**: Mòdul d'explicabilitat basat en SHAP. Executa `TreeExplainer` de forma nativa sobre els arbres de decisió dels models de scikit-learn, filtra el soroll numèric ($|val| > 10^{-5}$) i mapeja els noms tècnics de les columnes a nomenclatura clínica en català.
* **`VectorSimilaritySearch`**: Motor de cerca semàntica i recuperació de casos anàlegs. Utilitza un índex vectorial **FAISS** (`IndexFlatIP` normalitzat amb norma L2) per trobar en pocs mil·lisegons els $k=10$ pacients històrics més semblants al cas actual, extraient estadístiques d'evolució clínica.
* **`LLMReportGenerator`**: Mòdul generador d'informes mèdics (`ollama.py`). Construeix un prompt rígid estructurat en 4 blocs a partir de les dades de ML, SHAP i FAISS, i el transmet a un motor d'inferència local (Ollama amb Gemma/Llama) o al núvol (OpenRouter), aplicant posteriorment regles de neteja textual (*post-processing*).

#### 3. Capa de Dades i Entitats (SQLite)
* **`PatientRecord`**: Representa l'estructura relacional d'un pacient a la base de dades `clinic_data.sqlite` (taula `pacients`), amb índex sobre `id_pacient`. Conté dades demogràfiques, biomarcadors de laboratori, diagnòstics totals, fàrmacs i visites estructurades en 3 finestres temporals.
* **`ClinicalFeedback`**: Entitat de persistència que emmagatzema les decisions dels metges a la taula `feedback`. Enregistra la marca de temps, el pacient analitzat, la predicció de la IA, la conformitat o esmena, el diagnòstic corregit, les observacions textuals i el metge autor.

---

## 6.2. Diagrames de Seqüència dels Casos d'Ús (UML)

A continuació es presenten els diagrames de seqüència detallats que modelen la interacció dinàmica dels objectes per a cadascun dels casos d'ús del sistema.

---

### 6.2.1. DS-01: Consultar la llista de pacients prioritzats (CU-01)

Aquest diagrama descriu el procés mitjançant el qual el facultatiu accedeix al portal mèdic i el sistema recupera i renderitza la llista de pacients pendents de revisió ordenats per severitat clínica.

```mermaid
sequenceDiagram
    autonumber
    actor M as Facultatiu Mèdic
    participant V as Vista: dashboard.blade.php
    participant C as Controller: PatientAnalysisController
    participant S as Service: PythonApiService
    participant API as Flask API: api.py
    participant DB as SQLite: clinic_data.sqlite

    M->>V: Accedeix al Portal Sanitari (GET /)
    V->>C: Invocació index()
    C->>S: getPriorityPatients()
    S->>API: GET /api/patients/priority (HTTP REST)
    
    activate API
    API->>DB: Consulta SQL (Pendents sense feedback)
    DB-->>API: Registres de pacients no revisats
    API->>API: Ordena per severitat (MACA primer, PCC després)
    API-->>S: JSON [ pacients prioritaris ]
    deactivate API

    S-->>C: Array de pacients prioritaris
    C->>C: Calcula KPIs (Pendents totals, MACA, PCC)
    C-->>V: Renderitza vista amb DashboardViewModel
    V-->>M: Visualitza Tauler amb Taula de Prioritat i Targetes KPI
```

---

### 6.2.2. DS-02: Analitzar un pacient i consultar el suport a la decisió CDSS (CU-02)

Aquest diagrama reflecteix el flux unificat d'alta eficiència on, en una única sol·licitud asíncrona, s'executa el motor de Machine Learning jeràrquic, l'explicabilitat SHAP, la cerca FAISS i la generació de l'informe clínic assistit per LLM.

```mermaid
sequenceDiagram
    autonumber
    actor M as Facultatiu Mèdic
    participant V as Vista: dashboard.blade.php (AJAX)
    participant C as Controller: PatientAnalysisController
    participant S as Service: PythonApiService
    participant API as Flask API: api.py
    participant DB as SQLite: clinic_data.sqlite
    participant ML as HierarchicalPredictor
    participant SHAP as ShapExplainer (TreeExplainer)
    participant FAISS as VectorSimilaritySearch
    participant LLM as LLMReportGenerator (Ollama/Cloud)

    M->>V: Clica sobre un pacient (ex. ID: 24954)
    V->>V: Mostra indicador de càrrega
    V->>C: POST /analyze { patient_id: "24954" } (AJAX)
    C->>S: analyzePatient("24954")
    S->>API: POST /api/analyze { id_pacient: "24954" }

    activate API
    API->>DB: SELECT * FROM pacients WHERE id_pacient = "24954"
    DB-->>API: Registre clínic del pacient

    par Execució del Motor Predictiu Jeràrquic
        API->>ML: predict_patient(patientData)
        ML->>ML: Stage 1: RandomForest (Crònic vs NO)
        alt És Crònic (Prob >= 0.50)
            ML->>ML: Stage 2: HistGradientBoosting Calibrat (PCC vs MACA)
        end
        ML-->>API: Predicció ("MACA") + Probabilitats
    and Càlcul d'Explicabilitat SHAP
        API->>SHAP: calcular_explicabilitat(patientData)
        SHAP->>SHAP: TreeExplainer sobre Stage 1 i Stage 2
        SHAP->>SHAP: Filtra soroll (|val| > 1e-5) i tradueix a termes mèdics
        SHAP-->>API: Top 10 variables explicatives
    and Cerca de Casos Similars (FAISS)
        API->>FAISS: find_similar_cases(patientVector, k=10)
        FAISS-->>API: 10 veïns més propers + Estadístiques de cohort
    end

    API->>LLM: generar_informe_clinic(Context: ML + SHAP + FAISS)
    activate LLM
    LLM->>LLM: Construeix prompt rígid (4 blocs)
    LLM->>LLM: Executa inferència local (Ollama) / Cloud
    LLM->>LLM: netejar_text_informe()
    LLM-->>API: Text de l'Informe Mèdic Estructurat
    deactivate LLM

    API-->>S: JSON consolidat
    deactivate API

    S-->>C: Dades d'anàlisi completes
    C-->>V: Resposta JSON HTTP 200
    V->>V: Actualitza DOM en calent (Badges, barres SHAP CSS, Informe)
    V-->>M: Presenta la Fitxa de Decisió Clínica (CDSS Card)
```

---

### 6.2.3. DS-03: Registrar feedback clínic (Validar o Corregir diagnòstic) (CU-03)

Aquest diagrama detalla el cicle de retroalimentació mèdica (*Active Learning*), il·lustrant com la decisió s'enregistra de forma atòmica a la base de dades i provoca l'exclusió automàtica del pacient de la llista de pendents sense recarregar la pàgina.

```mermaid
sequenceDiagram
    autonumber
    actor M as Facultatiu Mèdic
    participant V as Vista: dashboard.blade.php
    participant C as Controller: PatientAnalysisController
    participant S as Service: PythonApiService
    participant API as Flask API: api.py
    participant Lock as Concurrency Lock (threading.Lock)
    participant DB as SQLite: clinic_data.sqlite

    M->>V: Selecciona "No" (Esmena) -> Tria "PCC" + Introdueix Observacions
    M->>V: Prem "Desar valoració"
    V->>V: Deshabilita botons i activa indicador d'enviament
    V->>C: POST /feedback { id_pacient, correcte: false, nova_classe: "PCC", comentari: "..." }
    
    activate C
    C->>C: Valida camps del formulari
    C->>C: Extreu nom del facultatiu autenticat: auth()->user()->name
    C->>S: submitFeedback(feedbackPayload)
    S->>API: POST /api/feedback (JSON)
    
    activate API
    API->>Lock: acquire()
    Note over Lock,API: Protecció contra concurrència d'escriptura
    API->>DB: INSERT INTO feedback (...) VALUES (...)
    DB-->>API: Confirmació d'inserció
    API->>Lock: release()
    API-->>S: JSON { status: "success", message: "Feedback registrat" }
    deactivate API

    S-->>C: Confirmació de recepció
    C-->>V: JSON HTTP 200 { success: true }
    deactivate C

    V->>V: Mostra missatge d'èxit
    V->>V: Elimina el pacient de la barra lateral de prioritat (DOM)
    V->>V: Afegeix la nova entrada a la línia temporal (Timeline)
    V-->>M: Interfície actualitzada de forma instantània
```

---

### 6.2.4. DS-04: Consultar l'historial de decisions clíniques (*Timeline*) (CU-04)

Aquest diagrama descriu la consulta de la traçabilitat clínica i l'historial d'esmenes realitzades prèviament sobre un pacient.

```mermaid
sequenceDiagram
    autonumber
    actor M as Facultatiu Mèdic
    participant V as Vista: dashboard.blade.php
    participant C as Controller: PatientAnalysisController
    participant S as Service: PythonApiService
    participant API as Flask API: api.py
    participant DB as SQLite: clinic_data.sqlite

    M->>V: Obre la pestanya "Historial de Decisions" del pacient
    V->>C: GET /patients/{id}/timeline (AJAX)
    C->>S: getPatientHistory(patientId)
    S->>API: GET /api/patients/{id}/timeline
    
    activate API
    API->>DB: SELECT * FROM feedback WHERE id_pacient = ? ORDER BY timestamp DESC
    DB-->>API: Llistat històric de valoracions i esmenes
    API-->>S: JSON [ {timestamp, usuari, prediccio, correcte, correccio, comentari}, ... ]
    deactivate API

    S-->>C: Llista històrica
    C-->>V: JSON HTTP 200
    V->>V: Renderitza l'arbre vertical d'esdeveniments
    V-->>M: Visualitza l'historial complet de decisions mèdiques
```

---

### 6.2.5. DS-05: Executar reentrenament dels models (*Active Learning*) (CU-05)

Aquest diagrama il·lustra el cicle d'enginyeria de dades i aprenentatge actiu, on les valoracions clíniques acumulades s'utilitzen per reajustar i calibrar els models predictius.

```mermaid
sequenceDiagram
    autonumber
    actor E as Enginyer/a de Dades i IA
    participant NB as Notebook: trainIA_V3.ipynb
    participant DB as SQLite: clinic_data.sqlite
    participant NCV as Nested Cross-Validation (4 Folds)
    participant GS as GridSearchCV (5 Folds interns)
    participant FS as File System: ai/models/

    E->>NB: Inicia procés de reentrenament periòdic
    NB->>DB: Carrega dades amb etiquetes validades
    DB-->>NB: Dataset actualitzat amb esmenes clíniques
    
    activate NB
    NB->>NB: Preprocessament i separació de característiques (X, y)
    
    loop Bucle Extern de Nested CV (4 Folds)
        NB->>NCV: Partició estratificada (Train / Test)
        NCV->>NCV: clone(preprocessor) -> Evita Data Leakage
        
        par Optimització Estadi 1 (Random Forest)
            NCV->>GS: Cerca hiperparàmetres Estadi 1
            GS-->>NCV: Millor configuració Estadi 1
        and Optimització Estadi 2 (HistGradientBoosting)
            NCV->>GS: Cerca hiperparàmetres Estadi 2 (Només pacients crònics)
            GS-->>NCV: Millor configuració Estadi 2
        end
        
        NCV->>NCV: Genera prediccions Out-of-Fold (OOF) i Probabilitats
    end

    NB->>NB: Avalua mètriques OOF reals (PR-AUC, Recall, F2-Score, Brier Score)
    NB->>NB: Reentrena models finals amb el 100% de les dades optimitzades
    
    NB->>FS: joblib.dump(model_stage1, "model_stage1_v3.joblib")
    NB->>FS: joblib.dump(model_stage2, "model_stage2_v3.joblib")
    deactivate NB
    
    FS-->>E: Binaris de producció actualitzats correctament
```

---

## 6.3. Diagrama de Transició d'Estats del Pacient (State Machine)

Com a complement de l'anàlisi dinàmica, el següent diagrama descriu els canvis d'estat d'un registre de pacient al llarg del flux assistencial i d'intel·ligència artificial:

```mermaid
stateDiagram-v2
    [*] --> Ingestat: Ingestió ETL de dades hospitalàries
    
    Ingestat --> PendentRevisio: Càrrega a SQLite (Sense Feedback)
    
    state PendentRevisio {
        [*] --> PrioritzatMACA: Predicció MACA (Risc Crític)
        [*] --> PrioritzatPCC: Predicció PCC (Risc Moderat)
        [*] --> PrioritzatNO: Predicció NO Crònic (Baix Risc)
    }

    PendentRevisio --> EnAnalisi: Facultatiu selecciona el pacient
    
    state EnAnalisi {
        [*] --> InferènciaJeràrquica
        InferènciaJeràrquica --> CàlculSHAP
        CàlculSHAP --> CercaFAISS
        CercaFAISS --> GeneracióInformeLLM
        GeneracióInformeLLM --> [*]
    }

    EnAnalisi --> Validat: Facultatiu confirma diagnòstic ("Sí")
    EnAnalisi --> Corregit: Facultatiu esmena diagnòstic ("No" + Nova Classe)

    Validat --> ExclosDePendents: Enregistrament a taula feedback
    Corregit --> ExclosDePendents: Enregistrament a taula feedback

    ExclosDePendents --> IndexatFAISS: Actualització de vectors històrics
    ExclosDePendents --> DatasetReentrenament: Incorporació al cicle d'Active Learning
    
    DatasetReentrenament --> [*]: Model reentrenat i actualitzat
```
