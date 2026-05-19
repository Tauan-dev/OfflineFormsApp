import * as FileSystem from "expo-file-system/legacy";

function docUri(fileName: string): string {
  return (FileSystem.documentDirectory ?? "") + fileName;
}

export async function fileExists(fileName: string): Promise<boolean> {
  const info = await FileSystem.getInfoAsync(docUri(fileName));
  return info.exists;
}

export async function readFileAsText(fileName: string): Promise<string> {
  return FileSystem.readAsStringAsync(docUri(fileName), {
    encoding: FileSystem.EncodingType.UTF8,
  });
}

export async function writeFileAsText(
  fileName: string,
  text: string,
): Promise<void> {
  await FileSystem.writeAsStringAsync(docUri(fileName), text, {
    encoding: FileSystem.EncodingType.UTF8,
  });
}

export function getFileUri(fileName: string): string {
  return docUri(fileName);
}

export async function deleteFile(fileName: string): Promise<void> {
  const info = await FileSystem.getInfoAsync(docUri(fileName));
  if (info.exists) await FileSystem.deleteAsync(docUri(fileName));
}

export async function getShareUri(fileName: string): Promise<string> {
  return docUri(fileName);
}
