export type Subscale = "Depresion" | "Ansiedad" | "Estres";

export interface Question {
  id: number;       // 1-42
  key: string;      // "Q1A"
  text: string;
  subscale: Subscale;
  isAnxiety: boolean; // true = ítem de ansiedad DASS
}

// Ítems de ansiedad DASS-42
export const ANXIETY_ITEMS = new Set([2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41]);

export const SCALE_LABELS = [
  { value: 1, label: "Nunca" },
  { value: 2, label: "A veces" },
  { value: 3, label: "Frecuentemente" },
  { value: 4, label: "Casi siempre" },
];

export const QUESTIONS: Question[] = [
  { id: 1,  key: "Q1A",  subscale: "Estres",    isAnxiety: false, text: "Me costó mucho desactivarme (relajarme)." },
  { id: 2,  key: "Q2A",  subscale: "Ansiedad",  isAnxiety: true,  text: "Me di cuenta de que mi boca estaba seca." },
  { id: 3,  key: "Q3A",  subscale: "Depresion", isAnxiety: false, text: "No podía experimentar ningún sentimiento positivo." },
  { id: 4,  key: "Q4A",  subscale: "Ansiedad",  isAnxiety: true,  text: "Tuve dificultad para respirar (p. ej., respiración excesivamente rápida, falta de aliento sin haber hecho esfuerzo físico)." },
  { id: 5,  key: "Q5A",  subscale: "Depresion", isAnxiety: false, text: "Me resultó difícil tomar iniciativa para hacer cosas." },
  { id: 6,  key: "Q6A",  subscale: "Estres",    isAnxiety: false, text: "Tuve tendencia a reaccionar exageradamente en ciertas situaciones." },
  { id: 7,  key: "Q7A",  subscale: "Ansiedad",  isAnxiety: true,  text: "Tuve temblores (p. ej., en las manos)." },
  { id: 8,  key: "Q8A",  subscale: "Estres",    isAnxiety: false, text: "Sentí que utilizaba mucha energía nerviosa." },
  { id: 9,  key: "Q9A",  subscale: "Ansiedad",  isAnxiety: true,  text: "Estaba preocupado por situaciones en las que podía entrar en pánico y hacer el ridículo." },
  { id: 10, key: "Q10A", subscale: "Depresion", isAnxiety: false, text: "Sentí que no tenía nada que esperar." },
  { id: 11, key: "Q11A", subscale: "Estres",    isAnxiety: false, text: "Me encontré agitado." },
  { id: 12, key: "Q12A", subscale: "Estres",    isAnxiety: false, text: "Me resultó difícil relajarme." },
  { id: 13, key: "Q13A", subscale: "Depresion", isAnxiety: false, text: "Me sentí triste y deprimido." },
  { id: 14, key: "Q14A", subscale: "Estres",    isAnxiety: false, text: "Fui intolerante con las cosas que me impedían continuar con lo que estaba haciendo." },
  { id: 15, key: "Q15A", subscale: "Ansiedad",  isAnxiety: true,  text: "Sentí que estaba al borde del pánico." },
  { id: 16, key: "Q16A", subscale: "Depresion", isAnxiety: false, text: "No pude sentir entusiasmo por nada." },
  { id: 17, key: "Q17A", subscale: "Depresion", isAnxiety: false, text: "Sentí que no valía mucho como persona." },
  { id: 18, key: "Q18A", subscale: "Estres",    isAnxiety: false, text: "Sentí que era bastante susceptible." },
  { id: 19, key: "Q19A", subscale: "Ansiedad",  isAnxiety: true,  text: "Noté que mi corazón latía sin haber realizado esfuerzo físico (p. ej., sensación de aumento de la frecuencia cardíaca, latido irregular)." },
  { id: 20, key: "Q20A", subscale: "Ansiedad",  isAnxiety: true,  text: "Me sentí atemorizado sin razón." },
  { id: 21, key: "Q21A", subscale: "Depresion", isAnxiety: false, text: "Sentí que la vida no tenía ningún sentido." },
  { id: 22, key: "Q22A", subscale: "Estres",    isAnxiety: false, text: "Me costó relajarme." },
  { id: 23, key: "Q23A", subscale: "Ansiedad",  isAnxiety: true,  text: "Tuve dificultad para deglutir." },
  { id: 24, key: "Q24A", subscale: "Depresion", isAnxiety: false, text: "No podía obtener ningún disfrute de las cosas que hacía." },
  { id: 25, key: "Q25A", subscale: "Ansiedad",  isAnxiety: true,  text: "No logré experimentar ningún sentimiento positivo ante ninguna actividad." },
  { id: 26, key: "Q26A", subscale: "Depresion", isAnxiety: false, text: "Fui incapaz de sentir entusiasmo por nada." },
  { id: 27, key: "Q27A", subscale: "Estres",    isAnxiety: false, text: "Sentí que no era digno de nada como persona." },
  { id: 28, key: "Q28A", subscale: "Ansiedad",  isAnxiety: true,  text: "Sentí que me faltaba el aliento." },
  { id: 29, key: "Q29A", subscale: "Depresion", isAnxiety: false, text: "Sentí que no había nada que pudiera esperar." },
  { id: 30, key: "Q30A", subscale: "Ansiedad",  isAnxiety: true,  text: "Tuve miedo sin razón aparente." },
  { id: 31, key: "Q31A", subscale: "Estres",    isAnxiety: false, text: "Me encontré en situaciones que me producían tanta ansiedad que me sentí muy aliviado cuando terminaron." },
  { id: 32, key: "Q32A", subscale: "Depresion", isAnxiety: false, text: "Sentí que no valía nada." },
  { id: 33, key: "Q33A", subscale: "Estres",    isAnxiety: false, text: "Tuve dificultad para tolerar las interrupciones en lo que estaba haciendo." },
  { id: 34, key: "Q34A", subscale: "Depresion", isAnxiety: false, text: "Me sentí muy triste y afligido." },
  { id: 35, key: "Q35A", subscale: "Estres",    isAnxiety: false, text: "Fui incapaz de esperar que las cosas siguieran su camino." },
  { id: 36, key: "Q36A", subscale: "Ansiedad",  isAnxiety: true,  text: "Sentí terror." },
  { id: 37, key: "Q37A", subscale: "Depresion", isAnxiety: false, text: "Vi que no había futuro para mí." },
  { id: 38, key: "Q38A", subscale: "Depresion", isAnxiety: false, text: "Sentí que la vida no valía la pena." },
  { id: 39, key: "Q39A", subscale: "Estres",    isAnxiety: false, text: "Me encontré irritable." },
  { id: 40, key: "Q40A", subscale: "Ansiedad",  isAnxiety: true,  text: "Estuve preocupado por situaciones en que podía ser objeto de pánico o en que me podría poner en ridículo." },
  { id: 41, key: "Q41A", subscale: "Ansiedad",  isAnxiety: true,  text: "Experimenté temblores (p. ej., en las manos)." },
  { id: 42, key: "Q42A", subscale: "Depresion", isAnxiety: false, text: "Me costó encontrar energía para iniciar actividades." },
];

export const QUESTIONS_PER_PAGE = 7;
export const TOTAL_PAGES = Math.ceil(QUESTIONS.length / QUESTIONS_PER_PAGE);
