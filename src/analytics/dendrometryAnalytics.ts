/**
 * dendrometryAnalytics.ts
 *
 * Estatísticas calculadas a partir dos registros de Dendometria.
 * Trabalha com os dados já parseados do CSV (array de objetos).
 *
 * Colunas CSV (índices):
 *  0 Parcela | 1 Árvore | 2 Plantio | 3 Replantio | 4 Nome Comum
 *  5 Data Medição | 6 DAP (cm) | 7 HESG (m) | 8 HESGCOPA (m)
 *  9 HC (m) | 10 HT (m) | 11 Observação
 */

// ─────────────────────────────────────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────────────────────────────────────

export interface DendroRow {
  parcela: string;
  arv: string;
  plantio: string;
  replantio: string;
  nomeComum: string;
  dataMedicao: string;
  dap: number | null;
  hesg: number | null;
  hesgcopa: number | null;
  hc: number | null;
  ht: number | null;
  observacao: string;
}

export interface DendroStats {
  total: number;
  totalParcelas: number;
  totalEspecies: number;
  mediaDap: number | null; // cm
  maxDap: number | null;
  minDap: number | null;
  mediaHt: number | null; // m
  maxHt: number | null;
  mediaHc: number | null; // m
  maiorArvore: MaiorArvore | null;
  topEspecies: EspecieCount[]; // top 5
  porParcela: ParcelaCount[];
  areaBasalTotal: number | null; // m²
  distribuicaoDiametrica: ClasseDiametrica[];
}

export interface ClasseDiametrica {
  classe: string; // ex: "10-20"
  minCm: number;
  maxCm: number;
  count: number;
  pct: number;
}

export interface MaiorArvore {
  parcela: string;
  arv: string;
  nomeComum: string;
  dap: number;
  ht: number | null;
}

export interface EspecieCount {
  nome: string;
  count: number;
  pct: number; // %
}

export interface ParcelaCount {
  parcela: string;
  count: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// PARSING
// ─────────────────────────────────────────────────────────────────────────────

function toNum(v: string): number | null {
  const n = parseFloat(v?.replace(",", ".") ?? "");
  return isNaN(n) ? null : n;
}

/** Converte linhas CSV (sem cabeçalho) em objetos DendroRow. */
export function parseDendroRows(rows: string[][]): DendroRow[] {
  return rows.map((r) => ({
    parcela: r[0] ?? "",
    arv: r[1] ?? "",
    plantio: r[2] ?? "",
    replantio: r[3] ?? "",
    nomeComum: r[4] ?? "",
    dataMedicao: r[5] ?? "",
    dap: toNum(r[6]),
    hesg: toNum(r[7]),
    hesgcopa: toNum(r[8]),
    hc: toNum(r[9]),
    ht: toNum(r[10]),
    observacao: r[11] ?? "",
  }));
}

// ─────────────────────────────────────────────────────────────────────────────
// FUNÇÕES ESTATÍSTICAS
// ─────────────────────────────────────────────────────────────────────────────

function avg(values: number[]): number | null {
  if (values.length === 0) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function max(values: number[]): number | null {
  if (values.length === 0) return null;
  return Math.max(...values);
}

function min(values: number[]): number | null {
  if (values.length === 0) return null;
  return Math.min(...values);
}

/** Calcula todos os indicadores de Dendometria. */
export function calcDendroStats(rows: DendroRow[]): DendroStats {
  const total = rows.length;

  // Parcelas únicas
  const parcelasSet = new Set(rows.map((r) => r.parcela).filter(Boolean));
  const totalParcelas = parcelasSet.size;

  // Espécies únicas
  const especiesSet = new Set(rows.map((r) => r.nomeComum).filter(Boolean));
  const totalEspecies = especiesSet.size;

  // DAP
  const daps = rows.map((r) => r.dap).filter((v): v is number => v !== null);
  const mediaDap = avg(daps);
  const maxDap = max(daps);
  const minDap = min(daps);

  // HT
  const hts = rows.map((r) => r.ht).filter((v): v is number => v !== null);
  const mediaHt = avg(hts);
  const maxHt = max(hts);

  // HC
  const hcs = rows.map((r) => r.hc).filter((v): v is number => v !== null);
  const mediaHc = avg(hcs);

  // Maior árvore por DAP
  let maiorArvore: MaiorArvore | null = null;
  if (daps.length > 0) {
    const best = rows
      .filter((r) => r.dap !== null)
      .sort((a, b) => (b.dap ?? 0) - (a.dap ?? 0))[0];
    maiorArvore = {
      parcela: best.parcela,
      arv: best.arv,
      nomeComum: best.nomeComum,
      dap: best.dap!,
      ht: best.ht,
    };
  }

  // Top espécies — chave normalizada (case-insensitive), preserva originalCase
  const especieMap = new Map<string, { nome: string; count: number }>();
  for (const r of rows) {
    const raw = r.nomeComum.trim();
    if (!raw) continue;
    const key = raw.toLowerCase();
    const entry = especieMap.get(key) ?? { nome: raw, count: 0 };
    entry.count += 1;
    especieMap.set(key, entry);
  }
  const topEspecies: EspecieCount[] = [...especieMap.values()]
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)
    .map(({ nome, count }) => ({
      nome,
      count,
      pct: total > 0 ? Math.round((count / total) * 100) : 0,
    }));

  // Por parcela
  const parcelaMap = new Map<string, number>();
  for (const r of rows) {
    const p = r.parcela.trim();
    if (p) parcelaMap.set(p, (parcelaMap.get(p) ?? 0) + 1);
  }
  const porParcela: ParcelaCount[] = [...parcelaMap.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([parcela, count]) => ({ parcela, count }));

  // Área basal total: soma de π*(DAP_m/2)² para DAP válido (0 < DAP ≤ 300 cm)
  const dapsValidos = daps.filter((d) => d > 0 && d <= 300);
  const areaBasalTotal =
    dapsValidos.length > 0
      ? dapsValidos.reduce(
          (acc, d) => acc + Math.PI * Math.pow(d / 100 / 2, 2),
          0,
        )
      : null;

  // Distribuição diamétrica em classes de 10 cm
  const CLASSES: { classe: string; min: number; max: number }[] = [
    { classe: "0-10", min: 0, max: 10 },
    { classe: "10-20", min: 10, max: 20 },
    { classe: "20-30", min: 20, max: 30 },
    { classe: "30-40", min: 30, max: 40 },
    { classe: "40+", min: 40, max: Infinity },
  ];
  const distribuicaoDiametrica: ClasseDiametrica[] = CLASSES.map(
    ({ classe, min, max }) => {
      const count = dapsValidos.filter(
        (d) => d > min && d <= (max === Infinity ? 99999 : max),
      ).length;
      return {
        classe,
        minCm: min,
        maxCm: max === Infinity ? 999 : max,
        count,
        pct:
          dapsValidos.length > 0
            ? Math.round((count / dapsValidos.length) * 100)
            : 0,
      };
    },
  );

  return {
    total,
    totalParcelas,
    totalEspecies,
    mediaDap,
    maxDap,
    minDap,
    mediaHt,
    maxHt,
    mediaHc,
    maiorArvore,
    topEspecies,
    porParcela,
    areaBasalTotal,
    distribuicaoDiametrica,
  };
}
