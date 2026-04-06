# PRD — MentalEval
**Sistema de evaluación de salud mental estudiantil**  
**Versión:** 1.0 · **Fecha:** Abril 2026  
**Autor:** Miller Zamora

---

## 1. Resumen ejecutivo

MentalEval es una plataforma web para instituciones educativas de secundaria en Perú que permite aplicar, gestionar y analizar evaluaciones de salud mental basadas en el cuestionario DASS-42 (Depression Anxiety Stress Scales), combinando la puntuación clínica validada internacionalmente con un modelo de predicción por Machine Learning (Random Forest) ejecutado en el cliente vía ONNX Runtime Web.

El sistema centraliza el ciclo completo: registro de estudiantes → configuración de test → aplicación → predicción → seguimiento clínico → reportes y exportación.

---

## 2. Objetivos del producto

| Objetivo | Indicador de éxito |
|---|---|
| Digitalizar la evaluación DASS-42 en colegios | Tests completados sin soporte técnico |
| Detectar tempranamente casos de riesgo | Casos Moderado/Severo con seguimiento asignado en < 48 h |
| Permitir adaptación del lenguaje sin invalidar el modelo | Texto adaptado con constructo intacto |
| Proveer reportes accionables para directivos | Exportación Excel con un clic |
| Privacidad: predicción 100 % en el cliente | Sin datos enviados a servidores externos |

---

## 3. Roles del sistema

```
Director
  ├── Crea cuentas de psicólogos, tutores y estudiantes
  ├── Ve métricas ejecutivas y gráficos
  └── Exporta reportes Excel

Psicólogo
  ├── Crea y edita configuraciones de test
  │     ├── Adapta lenguaje de las 42 preguntas
  │     ├── Agrega preguntas de contexto extra
  │     └── Asigna test a grados
  ├── Ve casos pendientes de atención
  └── Gestiona seguimiento clínico

Tutor
  ├── Ve reportes de sus estudiantes asignados
  └── Gestiona seguimiento clínico

Estudiante
  ├── Responde tests activos asignados a su grado
  ├── Ve su último resultado
  └── Edita su perfil personal y contraseña
```

---

## 4. Flujo completo del sistema

```
1. Director registra al psicólogo y tutores
2. Director registra estudiantes (asignando grado, sección y tutor)
3. Psicólogo crea configuración de test:
     - Adapta el texto de las 42 preguntas (mismo constructo)
     - Agrega preguntas extra de contexto
     - Activa el test para grados específicos
4. Estudiante inicia sesión → ve tests activos de su grado
5. Estudiante responde el test (42 preguntas DASS + extras)
6. Sistema calcula score clínico + predicción ML localmente
7. Resultado guardado en Firestore
8. Si nivel Moderado o Severo → requiereSeguimiento = true
9. Psicólogo/Tutor ve el caso en "Seguimiento"
10. Psicólogo inicia seguimiento con nota clínica inicial
11. Una vez resuelto → caso marcado como "Resuelto"
12. Director/Psicólogo exportan reportes en Excel
```

---

## 5. Cuestionario DASS-42

### 5.1 Descripción general

El **DASS-42** (Depression Anxiety Stress Scales — 42 ítems) es un instrumento psicométrico desarrollado por **Lovibond & Lovibond (1995)** en la Universidad de New South Wales, Australia. Está validado internacionalmente para medir la severidad de síntomas de depresión, ansiedad y estrés en adultos y adolescentes.

> **Referencia:** Lovibond, S.H. & Lovibond, P.F. (1995). *Manual for the Depression Anxiety Stress Scales* (2nd ed.). Psychology Foundation of Australia.

### 5.2 Estructura del instrumento

| Subescala | N° de ítems | Ítems (numeración del cuestionario) |
|---|---|---|
| **Depresión** | 14 | 3, 5, 10, 13, 16, 17, 21, 24, 26, 29, 32, 34, 37, 38, 42 |
| **Ansiedad**  | 14 | 2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41 |
| **Estrés**    | 14 | 1, 6, 8, 11, 12, 14, 18, 22, 27, 31, 33, 35, 39 |

### 5.3 Escala de respuesta

El instrumento original usa una escala **0–3**:

| Valor | Significado original | Equivalente en el sistema |
|---|---|---|
| 0 | No me ocurrió | Nunca |
| 1 | Me ocurrió en cierta medida o parte del tiempo | A veces |
| 2 | Me ocurrió en una medida considerable | Frecuentemente |
| 3 | Me ocurrió mucho o la mayor parte del tiempo | Casi siempre |

> **Nota de implementación:** El sistema almacena las respuestas en escala **1–4** para evitar valores nulos. El worker de predicción normaliza restando 1 antes de calcular el score: `score_item = respuesta - 1`.

### 5.4 Cálculo del score clínico de ansiedad

Este sistema evalúa únicamente la subescala de **ansiedad** (14 ítems).

**Fórmula:**
```
score_clínico = Σ (respuesta_item - 1)  para cada uno de los 14 ítems de ansiedad
```

**Rango:** 0 a 42 (14 ítems × valor máximo 3)

**Implementación exacta en `predict-worker.js`:**
```javascript
const ANXIETY_ITEMS = new Set([2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]);

let score = 0;
for (const item of ANXIETY_ITEMS) {
  score += Math.max(0, (answers[`Q${item}A`] ?? 1) - 1);
}
```

### 5.5 Umbrales de clasificación clínica

Los umbrales originales de Lovibond & Lovibond (1995) para la subescala de **ansiedad** (escala 0–3, 14 ítems, máximo 42) son:

| Nivel original | Rango de score |
|---|---|
| Normal | 0 – 7 |
| Leve (Mild) | 8 – 9 |
| Moderado (Moderate) | 10 – 14 |
| Severo (Severe) | 15 – 19 |
| Extremadamente severo (Extremely Severe) | ≥ 20 |

**Simplificación aplicada en este sistema** (3 niveles para uso escolar):

| Nivel del sistema | Rango de score | Niveles originales agrupados |
|---|---|---|
| **Leve** | 0 – 9 | Normal + Leve |
| **Moderado** | 10 – 14 | Moderado |
| **Severo** | ≥ 15 | Severo + Extremadamente severo |

**Implementación exacta:**
```javascript
const nivelClinico = score <= 9 ? "Leve" : score <= 14 ? "Moderado" : "Severo";
```

El porcentaje mostrado en el resultado se calcula sobre el máximo posible:
```javascript
porcentaje = Math.round((score / 42) * 1000) / 10  // un decimal
```

---

## 6. Modelo de Machine Learning

### 6.1 Algoritmo

**Random Forest** entrenado con datos del cuestionario DASS-42 combinados con datos de personalidad (TIPI — Ten-Item Personality Inventory) y variables demográficas. El modelo se ejecuta en el **navegador del cliente** mediante ONNX Runtime Web — ningún dato sale del dispositivo.

### 6.2 Features de entrada (49 variables)

```javascript
const FEATURE_COLS = [
  // 28 ítems DASS seleccionados por importancia estadística
  "Q1A","Q3A","Q5A","Q6A","Q8A","Q10A","Q11A","Q12A",
  "Q13A","Q14A","Q16A","Q17A","Q18A","Q21A","Q22A","Q24A",
  "Q26A","Q27A","Q29A","Q31A","Q32A","Q33A","Q34A","Q35A",
  "Q37A","Q38A","Q39A","Q42A",
  // 10 ítems TIPI (personalidad)
  "TIPI1","TIPI2","TIPI3","TIPI4","TIPI5",
  "TIPI6","TIPI7","TIPI8","TIPI9","TIPI10",
  // 11 variables demográficas
  "age","gender","education","urban","religion",
  "orientation","race","married","familysize"
];
```

> **Nota:** El modelo usa 28 de los 42 ítems DASS (los de mayor importancia en el entrenamiento). Los ítems no incluidos en `FEATURE_COLS` reciben `NaN` y el modelo los trata como datos faltantes.

### 6.3 Optimización del umbral para "Severo"

Se aplica un umbral optimizado para la clase Severo:

```javascript
const SEVERO_IDX = 2;
const SEVERO_THR = 0.38;  // umbral ajustado para mayor sensibilidad

if (probs[SEVERO_IDX] >= SEVERO_THR) {
  nivelIdx = SEVERO_IDX;  // clasifica como Severo si p(Severo) ≥ 38%
} else {
  // De las clases restantes elige la de mayor probabilidad
  const copy = [...probs];
  copy[SEVERO_IDX] = 0;
  nivelIdx = copy.indexOf(Math.max(...copy));
}
```

Esto **aumenta la sensibilidad** para detectar casos severos: si el modelo estima ≥ 38 % de probabilidad de ser Severo, se clasifica como tal aunque no sea la clase con mayor probabilidad absoluta. Esto es preferible en un contexto de salud mental (mejor detectar un caso severo que dejarlo pasar).

### 6.4 Salida del modelo

```typescript
{
  clinico: {
    score:      number,   // suma de 14 ítems (0–42)
    nivel:      string,   // "Leve" | "Moderado" | "Severo"
    max_score:  42,
    porcentaje: number,   // score/42 × 100, un decimal
  },
  ml: {
    nivel:          string,                   // clase predicha
    probabilidades: Record<string, number>,   // { Leve: %, Moderado: %, Severo: % }
  },
  coinciden: boolean,  // clinico.nivel === ml.nivel
}
```

### 6.5 Interpretación de la comparativa

| Escenario | Significado | Acción recomendada |
|---|---|---|
| Ambos coinciden en **Leve** | Bajo riesgo confirmado por dos métodos | Seguimiento rutinario |
| Ambos coinciden en **Moderado/Severo** | Riesgo confirmado, alta confianza | Atención prioritaria |
| Clínico: Leve — ML: Moderado/Severo | El modelo detecta patrones cruzados no capturados por el score puro | El psicólogo evalúa manualmente |
| Clínico: Moderado/Severo — ML: Leve | Score alto pero ML no encuentra patrón consistente | El criterio clínico tiene prioridad |

> **Principio rector:** El diagnóstico clínico (DASS-42) siempre tiene prioridad sobre el ML. El modelo es un segundo criterio de alerta, especialmente útil en casos borderline cerca de los umbrales.

---

## 7. Estructura de datos (Firestore)

### `users/{uid}`
```typescript
{
  uid:                  string,
  email:                string,
  nombre:               string,
  apellido:             string,
  rol:                  "director" | "psicologo" | "tutor" | "estudiante",
  createdAt:            Timestamp,
  // Solo estudiantes
  dni?:                 string,
  edad?:                number,
  genero?:              "M" | "F" | "otro",
  grado?:               "1ro" | "2do" | "3ro" | "4to" | "5to",
  seccion?:             string,
  institucionEducativa?: string,
  tutorId?:             string,   // uid del tutor asignado
  // Solo psicólogos
  especialidad?:        string,
  // Solo tutores
  departamento?:        string,
}
```

### `test_configs/{configId}`
```typescript
{
  titulo:        string,
  instrucciones: string,
  preguntas: [   // siempre 42 items, key fijo
    {
      key:          string,  // "Q3A" — nunca cambia
      textOriginal: string,  // texto DASS-42 oficial
      textAdaptado: string,  // texto que ve el estudiante (mismo constructo)
    }
  ],
  datosExtra: [  // preguntas adicionales — NO van al modelo
    {
      id:        string,
      pregunta:  string,
      tipo:      "texto" | "opciones",
      opciones?: string[],
    }
  ],
  grados:    string[],   // ["3ro", "4to"]
  activo:    boolean,
  creadoPor: string,     // uid del psicólogo
  creadoEn:  string,     // ISO 8601
}
```

### `resultados/{resultadoId}`
```typescript
{
  estudianteId:          string,
  estudianteNombre:      string,
  fecha:                 string,           // ISO 8601
  respuestas:            Record<string, number>,  // { Q1A: 2, Q2A: 3, ... }
  clinico: {
    score:      number,
    nivel:      string,
    max_score:  number,
    porcentaje: number,
  },
  ml: {
    nivel:          string,
    probabilidades: Record<string, number>,
  },
  coinciden:             boolean,
  requiereSeguimiento:   boolean,          // Moderado o Severo
  estado:                "pendiente" | "en_seguimiento" | "resuelto",
  testConfigId?:         string,
  datosExtraRespuestas?: Record<string, string>,
}
```

### `seguimientos/{seguimientoId}`
```typescript
{
  estudianteId: string,
  resultadoId:  string,
  asignadoPor:  string,   // uid del psicólogo/tutor
  nota:         string,
  estado:       "activo" | "cerrado",
  fecha:        string,
}
```

---

## 8. Stack técnico

| Capa | Tecnología |
|---|---|
| Frontend | React 19 + TypeScript + Vite 8 |
| Estilos | Tailwind CSS v4 + shadcn/ui |
| Enrutamiento | React Router v7 |
| Auth | Firebase Authentication (email/password) |
| Base de datos | Firestore (NoSQL) |
| Predicción ML | ONNX Runtime Web (Web Worker) |
| Gráficos | Chart.js + react-chartjs-2 |
| Exportación | ExcelJS |
| Deploy | Firebase Hosting |

---

## 9. Reglas de negocio críticas

### 9.1 Invariante del modelo ML

> **El `key` de cada pregunta (Q1A, Q2A, … Q42A) es fijo e inmutable.**  
> El psicólogo puede adaptar el texto (`textAdaptado`) para hacerlo más comprensible, pero el constructo psicológico que mide cada ítem NO puede cambiar. Reemplazar el concepto invalida el modelo.

| Acción del psicólogo | Válido | Motivo |
|---|---|---|
| Adaptar lenguaje para adolescentes | Sí | Mismo constructo |
| Cambiar orden de presentación | Sí | No afecta al modelo |
| Agregar preguntas de contexto (`datosExtra`) | Sí | No van al modelo |
| Reemplazar un ítem por uno de concepto distinto | No | Invalida la predicción |

### 9.2 Privacidad de datos

- La predicción se ejecuta íntegramente en el navegador del estudiante (Web Worker).
- Los datos de respuestas se envían únicamente a Firestore del proyecto propio.
- No se usan servicios de terceros para procesamiento de respuestas.

### 9.3 Umbral de seguimiento

Un resultado activa `requiereSeguimiento = true` cuando el nivel clínico es **Moderado o Severo**. El nivel ML no determina este umbral — solo el clínico.

---

## 10. Limitaciones conocidas

| Limitación | Detalle |
|---|---|
| El modelo fue entrenado con población general | Puede no generalizar perfectamente a adolescentes peruanos de secundaria |
| Variables demográficas faltantes | El test no recoge TIPI ni todas las demográficas del entrenamiento — el modelo recibe `NaN` para esas features |
| Solo subescala de ansiedad | El sistema no calcula scores de depresión ni estrés (aunque las respuestas se almacenan) |
| Sin validación de retest | No hay control de tiempo mínimo entre evaluaciones del mismo estudiante |
| Modelo no actualizable en cliente | Cambiar el modelo requiere reemplazar `rf_anxiety.onnx` y redesplegar |

---

## 11. Índices de Firestore requeridos

```json
[
  { "collectionGroup": "test_configs",
    "fields": [
      { "fieldPath": "grados",   "arrayConfig": "CONTAINS" },
      { "fieldPath": "activo",   "order": "ASCENDING" },
      { "fieldPath": "creadoEn", "order": "DESCENDING" }
    ]
  },
  { "collectionGroup": "resultados",
    "fields": [
      { "fieldPath": "estudianteId", "order": "ASCENDING" },
      { "fieldPath": "fecha",        "order": "DESCENDING" }
    ]
  },
  { "collectionGroup": "resultados",
    "fields": [
      { "fieldPath": "requiereSeguimiento", "order": "ASCENDING" },
      { "fieldPath": "estado",             "order": "ASCENDING" },
      { "fieldPath": "fecha",              "order": "DESCENDING" }
    ]
  }
]
```

---

## 12. Glosario

| Término | Definición |
|---|---|
| **DASS-42** | Depression Anxiety Stress Scales, 42 ítems. Instrumento de screening psicométrico validado internacionalmente (Lovibond & Lovibond, 1995) |
| **Score clínico** | Suma de los 14 ítems de ansiedad normalizados a escala 0–3. Rango: 0–42 |
| **Random Forest** | Algoritmo de ML basado en ensamble de árboles de decisión, usado para clasificar el nivel de ansiedad |
| **ONNX** | Open Neural Network Exchange — formato portable para modelos de ML. Permite ejecutar el modelo RF en el navegador sin backend |
| **Web Worker** | Hilo JavaScript en segundo plano que ejecuta la predicción sin bloquear la interfaz de usuario |
| **TIPI** | Ten-Item Personality Inventory — instrumento de 10 ítems para medir los Big Five de personalidad (no incluido en el test actual) |
| **requiereSeguimiento** | Flag booleano en Firestore que activa el flujo de seguimiento clínico. Se establece en `true` cuando nivel clínico ≥ Moderado |
| **textAdaptado** | Versión del texto de una pregunta DASS adaptada por el psicólogo para mayor comprensión, manteniendo el constructo original |
| **datosExtra** | Preguntas adicionales de contexto definidas por el psicólogo. Se almacenan en el resultado pero no se pasan al modelo ML |
