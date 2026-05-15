import { File, Paths } from "expo-file-system";

/**
 * Verifica se um arquivo existe no diretório de documentos do app.
 */
export function fileExists(fileName: string): boolean {
  const file = new File(Paths.document, fileName);
  return file.exists;
}

/**
 * Lê um arquivo do diretório de documentos e retorna seu conteúdo como Uint8Array.
 * @throws Error se o arquivo não existir.
 */
export function readFileAsBytes(fileName: string): Uint8Array {
  const file = new File(Paths.document, fileName);
  if (!file.exists) {
    throw new Error(`Arquivo não encontrado: ${fileName}`);
  }
  return file.bytesSync();
}

/**
 * Salva (cria ou sobrescreve) um arquivo no diretório de documentos.
 */
export function writeFileAsBytes(fileName: string, data: Uint8Array): void {
  const file = new File(Paths.document, fileName);
  file.write(data);
}

/**
 * Retorna a URI completa de um arquivo no diretório de documentos.
 */
export function getFileUri(fileName: string): string {
  const file = new File(Paths.document, fileName);
  return file.uri;
}
