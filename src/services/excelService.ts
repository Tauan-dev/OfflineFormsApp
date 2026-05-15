import * as XLSX from "xlsx";
import {
  fileExists,
  readFileAsBytes,
  writeFileAsBytes,
  getFileUri,
} from "../storage/fileManager";

// =============================================
// DENDOMETRIA
// =============================================

const DENDOMETRY_FILE = "dendometria.xlsx";

const DENDOMETRY_HEADERS = [
  "PARCELA",
  "ARV",
  "PLANTIO",
  "REPLANTIO",
  "NOME COMUM",
  "DATA MEDICAO",
  "DAP",
  "HESG",
  "HESGCOPA",
  "HC",
  "HT",
  "OBSERVACAO",
];

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

function base64ToUint8Array(base64: string): Uint8Array {
  const binaryStr = atob(base64);
  const bytes = new Uint8Array(binaryStr.length);
  for (let i = 0; i < binaryStr.length; i++) {
    bytes[i] = binaryStr.charCodeAt(i);
  }
  return bytes;
}

function saveToExcel(
  fileName: string,
  sheetName: string,
  headers: string[],
  newRow: string[],
): void {
  let workbook: XLSX.WorkBook;
  let worksheet: XLSX.WorkSheet;

  if (fileExists(fileName)) {
    const bytes = readFileAsBytes(fileName);
    workbook = XLSX.read(bytes, { type: "array" });
    const existingSheet = workbook.SheetNames[0];
    worksheet = workbook.Sheets[existingSheet];
    const existing: any[][] = XLSX.utils.sheet_to_json(worksheet, {
      header: 1,
    });
    existing.push(newRow);
    worksheet = XLSX.utils.aoa_to_sheet(existing);
    workbook.Sheets[existingSheet] = worksheet;
  } else {
    const rows = [headers, newRow];
    worksheet = XLSX.utils.aoa_to_sheet(rows);
    workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
  }

  const wbout: Uint8Array = XLSX.write(workbook, {
    type: "buffer",
    bookType: "xlsx",
  });
  writeFileAsBytes(fileName, wbout);
  console.log(`Salvo em: ${getFileUri(fileName)}`);
}

// =============================================
// DENDOMETRIA — salvar
// =============================================

export async function saveDendrometryData(
  data: DendrometryData,
): Promise<void> {
  try {
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
    saveToExcel(DENDOMETRY_FILE, "Dendometria", DENDOMETRY_HEADERS, row);
  } catch (error) {
    console.error("Erro ao salvar dendometria:", error);
    throw error;
  }
}

export function getDendrometryFilePath(): string {
  return getFileUri(DENDOMETRY_FILE);
}

// =============================================
// FENOLOGIA
// =============================================

const PHENOLOGY_FILE = "fenologia.xlsx";

const PHENOLOGY_HEADERS = [
  "PARCELA",
  "ARV",
  "NOME COMUM",
  "FLORES_PRESENCA",
  "FLORES_INTENSIDADE",
  "FLORES_ESTAGIO",
  "FRUTOS_PRESENCA",
  "FRUTOS_INTENSIDADE",
  "FRUTOS_ESTAGIO",
  "FOLHAS_PRESENCA",
  "FOLHAS_INTENSIDADE",
  "FOLHAS_ESTAGIO",
];

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
}

export async function savePhenologyData(data: PhenologyData): Promise<void> {
  try {
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
    ];
    saveToExcel(PHENOLOGY_FILE, "Fenologia", PHENOLOGY_HEADERS, row);
  } catch (error) {
    console.error("Erro ao salvar fenologia:", error);
    throw error;
  }
}

export function getPhenologyFilePath(): string {
  return getFileUri(PHENOLOGY_FILE);
}
