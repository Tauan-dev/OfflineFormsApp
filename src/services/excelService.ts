/**
 * excelService.ts
 *
 * Usa CSV (Comma-Separated Values) com BOM UTF-8.
 * Formato texto puro — abre corretamente em Excel, Google Sheets e LibreOffice.
 * Sem bibliotecas externas, sem binário, sem compressão.
 */
import {
  fileExists,
  readFileAsText,
  writeFileAsText,
  getFileUri,
} from "../storage/fileManager";

// ───────────────────────────────────────────────────────────────
// INTERFACES
// ───────────────────────────────────────────────────────────────

export interface DendrometryData {
  parcela: string;
  arv: string;
  plantio: string;
  replantio: string;
  nomeComum: string;
  dataMedicao: string;
  dap: string;
  hesg: string;
  hesgcopa: string;
  hc: string;
  ht: string;
  observacao: string;
}

export interface PhenologyGroupData {
  presenca: boolean;
  intensidade: string;
  estagio: string;
}

export interface PhenologyData {
  parcela: string;
  arv: string;
  nomeComum: string;
  flores: PhenologyGroupData;
  frutos: PhenologyGroupData;
  folhas: PhenologyGroupData;
  fitossanitario: string;
  observacao: string;
}

// ───────────────────────────────────────────────────────────────
// XML SPREADSHEET 2003 — GERADOR E PARSER
// ───────────────────────────────────────────────────────────────

// ───────────────────────────────────────────────────────────────
// CSV — GERADOR E PARSER
// ───────────────────────────────────────────────────────────────

/** Escapa um campo CSV: envolve em aspas se contiver vírgula, aspas ou quebra de linha. */
function csvField(value: string): string {
  const s = String(value ?? "");
  if (
    s.includes(",") ||
    s.includes('"') ||
    s.includes("\n") ||
    s.includes("\r")
  ) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

/** Converte array de linhas para string CSV com BOM UTF-8. */
function buildCsv(rows: string[][]): string {
  // BOM UTF-8 garante que Excel abre com acentos corretamente
  const BOM = "\uFEFF";
  return BOM + rows.map((row) => row.map(csvField).join(",")).join("\r\n");
}

/** Lê CSV e retorna array de linhas/colunas. */
export function parseCsv(csv: string): string[][] {
  // Remove BOM se presente
  const text = csv.startsWith("\uFEFF") ? csv.slice(1) : csv;
  const lines = text.split(/\r?\n/).filter((l) => l.trim() !== "");
  return lines.map((line) => {
    const fields: string[] = [];
    let i = 0;
    while (i < line.length) {
      if (line[i] === '"') {
        let field = "";
        i++;
        while (i < line.length) {
          if (line[i] === '"' && line[i + 1] === '"') {
            field += '"';
            i += 2;
          } else if (line[i] === '"') {
            i++;
            break;
          } else {
            field += line[i++];
          }
        }
        fields.push(field);
        if (line[i] === ",") i++;
      } else {
        const end = line.indexOf(",", i);
        if (end === -1) {
          fields.push(line.slice(i));
          break;
        } else {
          fields.push(line.slice(i, end));
          i = end + 1;
        }
      }
    }
    return fields;
  });
}

// ───────────────────────────────────────────────────────────────
// MOTOR PRINCIPAL
// ───────────────────────────────────────────────────────────────

async function saveToCsv(
  fileName: string,
  headers: string[],
  newRow: string[],
): Promise<void> {
  let allRows: string[][] = [headers, newRow];

  if (await fileExists(fileName)) {
    try {
      const existing = await readFileAsText(fileName);
      const parsed = parseCsv(existing);
      const dataOnly = parsed.length > 1 ? parsed.slice(1) : [];
      allRows = [headers, ...dataOnly, newRow];
    } catch {
      allRows = [headers, newRow];
    }
  }

  const csv = buildCsv(allRows);
  await writeFileAsText(fileName, csv);
  console.log(
    `[excelService] ✅ Salvo: ${getFileUri(fileName)} — ${allRows.length - 1} registro(s)`,
  );
}

// ───────────────────────────────────────────────────────────────
// DENDOMETRIA
// ───────────────────────────────────────────────────────────────

const DENDOMETRY_FILE = "dendometria.csv";

const DENDOMETRY_HEADERS = [
  "Parcela",
  "Árvore",
  "Plantio",
  "Replantio",
  "Nome Comum",
  "Data Medição",
  "DAP (cm)",
  "HESG (m)",
  "HESGCOPA (m)",
  "HC (m)",
  "HT (m)",
  "Observação",
];

export async function saveDendrometryData(
  data: DendrometryData,
): Promise<void> {
  const row = [
    data.parcela,
    data.arv,
    data.plantio,
    data.replantio,
    data.nomeComum,
    data.dataMedicao,
    data.dap,
    data.hesg,
    data.hesgcopa,
    data.hc,
    data.ht,
    data.observacao,
  ];
  await saveToCsv(DENDOMETRY_FILE, DENDOMETRY_HEADERS, row);
}

export function getDendrometryFilePath(): string {
  return getFileUri(DENDOMETRY_FILE);
}

// ───────────────────────────────────────────────────────────────
// FENOLOGIA
// ───────────────────────────────────────────────────────────────

const PHENOLOGY_FILE = "fenologia.csv";

const PHENOLOGY_HEADERS = [
  "Parcela",
  "Árvore",
  "Nome Comum",
  "Flores Presença",
  "Flores Intensidade",
  "Flores Estágio",
  "Frutos Presença",
  "Frutos Intensidade",
  "Frutos Estágio",
  "Folhas Presença",
  "Folhas Intensidade",
  "Folhas Estágio",
  "Estado Fitossanitário",
  "Observações",
];

export async function savePhenologyData(data: PhenologyData): Promise<void> {
  const row = [
    data.parcela,
    data.arv,
    data.nomeComum,
    data.flores.presenca ? "Sim" : "Não",
    data.flores.intensidade,
    data.flores.estagio,
    data.frutos.presenca ? "Sim" : "Não",
    data.frutos.intensidade,
    data.frutos.estagio,
    data.folhas.presenca ? "Sim" : "Não",
    data.folhas.intensidade,
    data.folhas.estagio,
    data.fitossanitario,
    data.observacao,
  ];
  await saveToCsv(PHENOLOGY_FILE, PHENOLOGY_HEADERS, row);
}

export function getPhenologyFilePath(): string {
  return getFileUri(PHENOLOGY_FILE);
}
