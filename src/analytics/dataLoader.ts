/**
 * dataLoader.ts
 *
 * Utilitário compartilhado para leitura dos arquivos CSV e conversão
 * para os tipos de dados dos analytics. Usado por todas as telas de BI.
 */
import { fileExists, readFileAsText } from "../storage/fileManager";
import { parseCsv } from "../services/excelService";
import {
  parseDendroRows,
  DendroRow,
  calcDendroStats,
  DendroStats,
} from "./dendrometryAnalytics";
import {
  parseFenologiaRows,
  FenologiaRow,
  calcPhenologyStats,
  PhenologyStats,
} from "./phenologyAnalytics";
import {
  calcInventoryStats,
  InventoryStats,
  calcParcelaStats,
  ParcelaStats,
} from "./inventoryAnalytics";

const DENDRO_FILE = "dendometria.csv";
const FENOL_FILE = "fenologia.csv";

// ─────────────────────────────────────────────────────────────────────────────
// LEITURA INDIVIDUAL
// ─────────────────────────────────────────────────────────────────────────────

/** Lê e retorna os dados brutos de dendometria. Retorna [] se o arquivo não existir. */
export async function loadDendroRows(): Promise<DendroRow[]> {
  if (!(await fileExists(DENDRO_FILE))) return [];
  try {
    const text = await readFileAsText(DENDRO_FILE);
    const all = parseCsv(text);
    return all.length > 1 ? parseDendroRows(all.slice(1)) : [];
  } catch {
    return [];
  }
}

/** Lê e retorna os dados brutos de fenologia. Retorna [] se o arquivo não existir. */
export async function loadFenolRows(): Promise<FenologiaRow[]> {
  if (!(await fileExists(FENOL_FILE))) return [];
  try {
    const text = await readFileAsText(FENOL_FILE);
    const all = parseCsv(text);
    return all.length > 1 ? parseFenologiaRows(all.slice(1)) : [];
  } catch {
    return [];
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CARREGAMENTO DE STATS
// ─────────────────────────────────────────────────────────────────────────────

export async function loadDendroStats(): Promise<DendroStats> {
  const rows = await loadDendroRows();
  return calcDendroStats(rows);
}

export async function loadPhenologyStats(): Promise<PhenologyStats> {
  const rows = await loadFenolRows();
  return calcPhenologyStats(rows);
}

export async function loadInventoryStats(): Promise<InventoryStats> {
  const [dendro, fenol] = await Promise.all([
    loadDendroRows(),
    loadFenolRows(),
  ]);
  return calcInventoryStats(dendro, fenol);
}

export async function loadParcelaStats(): Promise<ParcelaStats[]> {
  const [dendro, fenol] = await Promise.all([
    loadDendroRows(),
    loadFenolRows(),
  ]);
  return calcParcelaStats(dendro, fenol);
}

export type { ParcelaStats };

export interface AllStats {
  dendro: DendroStats;
  phenol: PhenologyStats;
  inventory: InventoryStats;
}

export async function loadAllStats(): Promise<AllStats> {
  const [dendroRows, fenolRows] = await Promise.all([
    loadDendroRows(),
    loadFenolRows(),
  ]);
  return {
    dendro: calcDendroStats(dendroRows),
    phenol: calcPhenologyStats(fenolRows),
    inventory: calcInventoryStats(dendroRows, fenolRows),
  };
}
