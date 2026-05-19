/**
 * phenologyAnalytics.ts
 *
 * Estatísticas calculadas a partir dos registros de Fenologia.
 *
 * Colunas CSV (índices):
 *  0 Parcela | 1 Árvore | 2 Nome Comum
 *  3 Flores Presença | 4 Flores Intensidade | 5 Flores Estágio
 *  6 Frutos Presença | 7 Frutos Intensidade | 8 Frutos Estágio
 *  9 Folhas Presença | 10 Folhas Intensidade | 11 Folhas Estágio
 *  12 Estado Fitossanitário | 13 Observações
 */

// ─────────────────────────────────────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────────────────────────────────────

export interface FenologiaRow {
  parcela: string;
  arv: string;
  nomeComum: string;
  floresPresenca: boolean;
  floresIntensidade: string;
  floresEstagio: string;
  frutosPresenca: boolean;
  frutosIntensidade: string;
  frutosEstagio: string;
  folhasPresenca: boolean;
  folhasIntensidade: string;
  folhasEstagio: string;
  fitossanitario: string;
  observacao: string;
}

export interface PhenologyStats {
  total: number;
  totalEspecies: number;
  // Flores
  pctFlores: number; // % com flores
  floresEstagios: EstagioCount[];
  floresIntensidades: IntensidadeCount[];
  // Frutos
  pctFrutos: number;
  frutosEstagios: EstagioCount[];
  frutosIntensidades: IntensidadeCount[];
  // Folhas
  pctFolhas: number;
  // Fitossanitário
  fitossanitario: FitoCount[];
  // Predominâncias
  estagioPredomFlores: string | null;
  estagioPredomFrutos: string | null;
  intensidadePredomFlores: string | null;
  intensidadePredomFrutos: string | null;
  // Combinações interessantes
  semFloresSemFrutos: number; // árvores sem flores e sem frutos
  comFloresEFrutos: number; // em produção simultânea
}

export interface EstagioCount {
  estagio: string;
  count: number;
  pct: number;
}

export interface IntensidadeCount {
  intensidade: string;
  count: number;
  pct: number;
}

export interface FitoCount {
  estado: string;
  count: number;
  pct: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// PARSING
// ─────────────────────────────────────────────────────────────────────────────

/** Converte linhas CSV (sem cabeçalho) em objetos FenologiaRow. */
export function parseFenologiaRows(rows: string[][]): FenologiaRow[] {
  return rows.map((r) => ({
    parcela: r[0] ?? "",
    arv: r[1] ?? "",
    nomeComum: r[2] ?? "",
    floresPresenca: (r[3] ?? "").toLowerCase() === "sim",
    floresIntensidade: r[4] ?? "",
    floresEstagio: r[5] ?? "",
    frutosPresenca: (r[6] ?? "").toLowerCase() === "sim",
    frutosIntensidade: r[7] ?? "",
    frutosEstagio: r[8] ?? "",
    folhasPresenca: (r[9] ?? "").toLowerCase() === "sim",
    folhasIntensidade: r[10] ?? "",
    folhasEstagio: r[11] ?? "",
    fitossanitario: r[12] ?? "",
    observacao: r[13] ?? "",
  }));
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────

function countDistribution<T extends string>(
  values: T[],
  total: number,
): { value: string; count: number; pct: number }[] {
  const map = new Map<string, number>();
  for (const v of values) {
    const key = v?.trim() || "Não informado";
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return [...map.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([value, count]) => ({
      value,
      count,
      pct: total > 0 ? Math.round((count / total) * 100) : 0,
    }));
}

// ─────────────────────────────────────────────────────────────────────────────
// FUNÇÃO PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────

/** Calcula todos os indicadores de Fenologia. */
export function calcPhenologyStats(rows: FenologiaRow[]): PhenologyStats {
  const total = rows.length;

  const totalEspecies = new Set(rows.map((r) => r.nomeComum).filter(Boolean))
    .size;

  // ── flores ──
  const comFlores = rows.filter((r) => r.floresPresenca).length;
  const pctFlores = total > 0 ? Math.round((comFlores / total) * 100) : 0;

  const floresEstagiosRaw = countDistribution(
    rows.filter((r) => r.floresPresenca).map((r) => r.floresEstagio),
    comFlores,
  );
  const floresEstagios: EstagioCount[] = floresEstagiosRaw.map((e) => ({
    estagio: e.value,
    count: e.count,
    pct: e.pct,
  }));

  const floresIntensidadesRaw = countDistribution(
    rows.filter((r) => r.floresPresenca).map((r) => r.floresIntensidade),
    comFlores,
  );
  const floresIntensidades: IntensidadeCount[] = floresIntensidadesRaw.map(
    (e) => ({ intensidade: e.value, count: e.count, pct: e.pct }),
  );

  // ── frutos ──
  const comFrutos = rows.filter((r) => r.frutosPresenca).length;
  const pctFrutos = total > 0 ? Math.round((comFrutos / total) * 100) : 0;

  const frutosEstagiosRaw = countDistribution(
    rows.filter((r) => r.frutosPresenca).map((r) => r.frutosEstagio),
    comFrutos,
  );
  const frutosEstagios: EstagioCount[] = frutosEstagiosRaw.map((e) => ({
    estagio: e.value,
    count: e.count,
    pct: e.pct,
  }));

  const frutosIntensidadesRaw = countDistribution(
    rows.filter((r) => r.frutosPresenca).map((r) => r.frutosIntensidade),
    comFrutos,
  );
  const frutosIntensidades: IntensidadeCount[] = frutosIntensidadesRaw.map(
    (e) => ({ intensidade: e.value, count: e.count, pct: e.pct }),
  );

  // ── folhas ──
  const comFolhas = rows.filter((r) => r.folhasPresenca).length;
  const pctFolhas = total > 0 ? Math.round((comFolhas / total) * 100) : 0;

  // ── fitossanitário ──
  const fitoRaw = countDistribution(
    rows.map((r) => r.fitossanitario),
    total,
  );
  const fitossanitario: FitoCount[] = fitoRaw.map((e) => ({
    estado: e.value,
    count: e.count,
    pct: e.pct,
  }));

  // ── predominâncias (moda) ──
  const estagioPredomFlores =
    floresEstagios.length > 0 ? floresEstagios[0].estagio : null;
  const estagioPredomFrutos =
    frutosEstagios.length > 0 ? frutosEstagios[0].estagio : null;
  const intensidadePredomFlores =
    floresIntensidades.length > 0 ? floresIntensidades[0].intensidade : null;
  const intensidadePredomFrutos =
    frutosIntensidades.length > 0 ? frutosIntensidades[0].intensidade : null;

  // ── combinações ──
  const semFloresSemFrutos = rows.filter(
    (r) => !r.floresPresenca && !r.frutosPresenca,
  ).length;
  const comFloresEFrutos = rows.filter(
    (r) => r.floresPresenca && r.frutosPresenca,
  ).length;

  return {
    total,
    totalEspecies,
    pctFlores,
    floresEstagios,
    floresIntensidades,
    estagioPredomFlores,
    estagioPredomFrutos,
    intensidadePredomFlores,
    intensidadePredomFrutos,
    pctFrutos,
    frutosEstagios,
    frutosIntensidades,
    pctFolhas,
    fitossanitario,
    semFloresSemFrutos,
    comFloresEFrutos,
  };
}
