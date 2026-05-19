/**
 * inventoryAnalytics.ts
 *
 * Estatísticas cruzadas de inventário — combina dados de Dendometria e
 * Fenologia para gerar uma visão consolidada do campo.
 */

import { DendroRow } from "./dendrometryAnalytics";
import { FenologiaRow } from "./phenologyAnalytics";

// ─────────────────────────────────────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────────────────────────────────────

export interface EspecieInventario {
  nome: string;
  totalDendro: number;
  totalFenol: number;
  totalGeral: number;
  pct: number; // % do total geral de árvores
}

export interface InventoryStats {
  totalArvores: number; // registros únicos de dendometria
  totalObservacoesFenol: number;
  totalEspecies: number;
  especieMaisFrequente: string | null;
  especieMaisFrequenteCount: number;
  topEspecies: EspecieInventario[];
  fitossanitarioAlerta: FitoAlerta[]; // estados problemáticos
  parcelasAtivas: string[];
  totalParcelas: number;
  coberturaDados: number; // % de árvores dendro que também têm fenologia
  // Saúde por categoria
  pctSaudavel: number;
  pctDanoLeve: number;
  pctDanoSevero: number;
  pctMorto: number;
  indicadorSaude: number; // pctSaudavel - (pctDanoSevero + pctMorto)
  interacoesFauna: number; // nº de observações fenol não-vazias
  top3Especies: EspecieInventario[];
}

export interface FitoAlerta {
  estado: string;
  count: number;
  pct: number;
}

export interface ParcelaStats {
  parcela: string;
  totalArvores: number; // dendometria
  totalFenol: number; // fenologia
  totalEspecies: number;
  especieDominante: string | null;
  mediaDap: number | null; // cm
  pctSaudavel: number;
  pctDanoLeve: number;
  pctDanoSevero: number;
  pctMorto: number;
  indicadorSaude: number; // pctSaudavel - (pctDanoSevero + pctMorto)
  interacoesFauna: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// FUNÇÕES
// ─────────────────────────────────────────────────────────────────────────────

/** Contagem de espécies cruzando dendometria + fenologia.
 *  - Chave normalizada para lowercase (evita duplicatas por capitalização)
 *  - Conta indivíduos únicos: mesma árvore (parcela+arv) é contada apenas 1x
 *  - Percentual calculado sobre total de árvores únicas (não sobre a soma bruta)
 */
function countEspecies(
  dendroRows: DendroRow[],
  fenolRows: FenologiaRow[],
): EspecieInventario[] {
  // Mapa lowercase → { originalCase, totalDendro, totalFenol }
  const map = new Map<string, { nome: string; td: number; tf: number }>();

  for (const r of dendroRows) {
    const raw = r.nomeComum.trim();
    if (!raw) continue;
    const key = raw.toLowerCase();
    const entry = map.get(key) ?? { nome: raw, td: 0, tf: 0 };
    entry.td += 1;
    map.set(key, entry);
  }

  for (const r of fenolRows) {
    const raw = r.nomeComum.trim();
    if (!raw) continue;
    const key = raw.toLowerCase();
    const entry = map.get(key) ?? { nome: raw, td: 0, tf: 0 };
    entry.tf += 1;
    map.set(key, entry);
  }

  // Total de indivíduos únicos: árvores únicas em dendro + as que só estão em fenol
  // Usa dendro como base (censo principal); fenol enriquece sp. sem dendro
  const keysFenolOnly = new Set(
    fenolRows
      .map((r) => r.nomeComum.trim().toLowerCase())
      .filter(
        (k) =>
          k && !dendroRows.some((d) => d.nomeComum.trim().toLowerCase() === k),
      ),
  );
  const totalIndividuos =
    dendroRows.filter((r) => r.nomeComum.trim()).length +
      fenolRows.filter((r) =>
        keysFenolOnly.has(r.nomeComum.trim().toLowerCase()),
      ).length || 1;

  return [...map.entries()]
    .map(([, entry]) => {
      const tg = entry.td + entry.tf;
      return {
        nome: entry.nome,
        totalDendro: entry.td,
        totalFenol: entry.tf,
        totalGeral: tg,
        pct: Math.round(
          (entry.td /
            (dendroRows.filter((r) => r.nomeComum.trim()).length || 1)) *
            100,
        ),
      };
    })
    .filter((e) => e.totalGeral > 0)
    .sort(
      (a, b) => b.totalDendro - a.totalDendro || b.totalFenol - a.totalFenol,
    );
}

/** Estados fitossanitários com presença > 0, excluindo "Bom" / "Normal". */
const ESTADOS_OK = ["bom", "boa", "normal", "saudável", "saudavel"];

function alertasFito(fenolRows: FenologiaRow[]): FitoAlerta[] {
  const map = new Map<string, number>();
  for (const r of fenolRows) {
    const e = r.fitossanitario?.trim();
    if (!e) continue;
    map.set(e, (map.get(e) ?? 0) + 1);
  }
  const total = fenolRows.length || 1;
  return [...map.entries()]
    .filter(([estado]) => !ESTADOS_OK.includes(estado.toLowerCase()))
    .sort((a, b) => b[1] - a[1])
    .map(([estado, count]) => ({
      estado,
      count,
      pct: Math.round((count / total) * 100),
    }));
}

/** Calcula cobertura: % de árvores que aparecem em AMBAS as planilhas. */
function calcCobertura(
  dendroRows: DendroRow[],
  fenolRows: FenologiaRow[],
): number {
  if (dendroRows.length === 0) return 0;
  const keysFenol = new Set(fenolRows.map((r) => `${r.parcela}|${r.arv}`));
  const cruzadas = dendroRows.filter((r) =>
    keysFenol.has(`${r.parcela}|${r.arv}`),
  ).length;
  return Math.round((cruzadas / dendroRows.length) * 100);
}

// ─── Classificação de saúde por palavras-chave ───────────────────────────────
const KW_SAUDAVEL = [
  "bom",
  "boa",
  "saudável",
  "saudavel",
  "normal",
  "ótimo",
  "otimo",
];
const KW_DANO_LEVE = [
  "leve",
  "médio",
  "medio",
  "moderado",
  "amarelo",
  "atacado",
];
const KW_DANO_SEV = ["severo", "grave", "crítico", "critico", "seco", "doente"];
const KW_MORTO = ["morto", "morta", "dead", "seco"];

function classificarFito(
  estado: string,
): "saudavel" | "danoLeve" | "danoSevero" | "morto" | "outro" {
  const e = estado.toLowerCase().trim();
  if (KW_MORTO.some((k) => e.includes(k))) return "morto";
  if (KW_DANO_SEV.some((k) => e.includes(k))) return "danoSevero";
  if (KW_DANO_LEVE.some((k) => e.includes(k))) return "danoLeve";
  if (KW_SAUDAVEL.some((k) => e.includes(k))) return "saudavel";
  return "outro";
}

/**
 * Calcula estatísticas por parcela (dendometria + fenologia filtradas).
 * Retorna array ordenado pelo indicador de saúde decrescente.
 */
export function calcParcelaStats(
  dendroRows: DendroRow[],
  fenolRows: FenologiaRow[],
): ParcelaStats[] {
  // Coletar todas as parcelas presentes em qualquer dataset
  const allParcelas = new Set([
    ...dendroRows.map((r) => r.parcela.trim()).filter(Boolean),
    ...fenolRows.map((r) => r.parcela.trim()).filter(Boolean),
  ]);

  return [...allParcelas]
    .sort()
    .map((parcela): ParcelaStats => {
      const dRows = dendroRows.filter((r) => r.parcela.trim() === parcela);
      const fRows = fenolRows.filter((r) => r.parcela.trim() === parcela);

      // Espécies únicas
      const especiesSet = new Set([
        ...dRows.map((r) => r.nomeComum).filter(Boolean),
        ...fRows.map((r) => r.nomeComum).filter(Boolean),
      ]);

      // Espécie dominante (dendometria, case-insensitive)
      const especieMap = new Map<string, { nome: string; count: number }>();
      for (const r of dRows) {
        const raw = r.nomeComum.trim();
        if (!raw) continue;
        const key = raw.toLowerCase();
        const entry = especieMap.get(key) ?? { nome: raw, count: 0 };
        entry.count += 1;
        especieMap.set(key, entry);
      }
      const especieDominante =
        especieMap.size > 0
          ? [...especieMap.values()].sort((a, b) => b.count - a.count)[0].nome
          : null;

      // DAP médio
      const daps = dRows
        .map((r) => r.dap)
        .filter((v): v is number => v !== null && v > 0 && v <= 300);
      const mediaDap =
        daps.length > 0 ? daps.reduce((a, b) => a + b, 0) / daps.length : null;

      // Saúde (baseada em fenologia)
      const totalFenol = fRows.length || 1;
      let cS = 0,
        cL = 0,
        cSv = 0,
        cM = 0;
      for (const r of fRows) {
        const cat = classificarFito(r.fitossanitario);
        if (cat === "saudavel") cS++;
        else if (cat === "danoLeve") cL++;
        else if (cat === "danoSevero") cSv++;
        else if (cat === "morto") cM++;
      }
      const pctSaudavel = Math.round((cS / totalFenol) * 100);
      const pctDanoLeve = Math.round((cL / totalFenol) * 100);
      const pctDanoSevero = Math.round((cSv / totalFenol) * 100);
      const pctMorto = Math.round((cM / totalFenol) * 100);
      const indicadorSaude = pctSaudavel - (pctDanoSevero + pctMorto);

      // Interações fauna
      const interacoesFauna = fRows.filter(
        (r) => r.observacao.trim().length > 0,
      ).length;

      return {
        parcela,
        totalArvores: dRows.length,
        totalFenol: fRows.length,
        totalEspecies: especiesSet.size,
        especieDominante,
        mediaDap,
        pctSaudavel,
        pctDanoLeve,
        pctDanoSevero,
        pctMorto,
        indicadorSaude,
        interacoesFauna,
      };
    })
    .sort((a, b) => b.indicadorSaude - a.indicadorSaude);
}

/** Calcula estatísticas consolidadas de inventário. */
export function calcInventoryStats(
  dendroRows: DendroRow[],
  fenolRows: FenologiaRow[],
): InventoryStats {
  const allEspeciesOrdered = countEspecies(dendroRows, fenolRows);
  const topEspecies = allEspeciesOrdered.slice(0, 8);
  const top3Especies = allEspeciesOrdered.slice(0, 3);

  const especieMaisFrequente =
    topEspecies.length > 0 ? topEspecies[0].nome : null;
  const especieMaisFrequenteCount =
    topEspecies.length > 0 ? topEspecies[0].totalGeral : 0;

  const allEspecies = new Set([
    ...dendroRows.map((r) => r.nomeComum).filter(Boolean),
    ...fenolRows.map((r) => r.nomeComum).filter(Boolean),
  ]);

  const allParcelas = new Set([
    ...dendroRows.map((r) => r.parcela).filter(Boolean),
    ...fenolRows.map((r) => r.parcela).filter(Boolean),
  ]);

  // Saúde por categoria
  const totalFenol = fenolRows.length || 1;
  let cntSaudavel = 0,
    cntDanoLeve = 0,
    cntDanoSevero = 0,
    cntMorto = 0;
  for (const r of fenolRows) {
    const cat = classificarFito(r.fitossanitario);
    if (cat === "saudavel") cntSaudavel++;
    else if (cat === "danoLeve") cntDanoLeve++;
    else if (cat === "danoSevero") cntDanoSevero++;
    else if (cat === "morto") cntMorto++;
  }
  const pctSaudavel = Math.round((cntSaudavel / totalFenol) * 100);
  const pctDanoLeve = Math.round((cntDanoLeve / totalFenol) * 100);
  const pctDanoSevero = Math.round((cntDanoSevero / totalFenol) * 100);
  const pctMorto = Math.round((cntMorto / totalFenol) * 100);
  const indicadorSaude = pctSaudavel - (pctDanoSevero + pctMorto);

  // Interações fauna = observações fenol não-vazias
  const interacoesFauna = fenolRows.filter(
    (r) => r.observacao.trim().length > 0,
  ).length;

  return {
    totalArvores: dendroRows.length,
    totalObservacoesFenol: fenolRows.length,
    totalEspecies: allEspecies.size,
    especieMaisFrequente,
    especieMaisFrequenteCount,
    topEspecies,
    top3Especies,
    fitossanitarioAlerta: alertasFito(fenolRows),
    parcelasAtivas: [...allParcelas].sort(),
    totalParcelas: allParcelas.size,
    coberturaDados: calcCobertura(dendroRows, fenolRows),
    pctSaudavel,
    pctDanoLeve,
    pctDanoSevero,
    pctMorto,
    indicadorSaude,
    interacoesFauna,
  };
}
