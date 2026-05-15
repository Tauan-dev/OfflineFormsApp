import AsyncStorage from "expo-sqlite/kv-store";
import { DEFAULT_SPECIES } from "../constants/species";

const STORAGE_KEY = "@coleta_verde:custom_species";

/**
 * Retorna a lista completa de espécies (padrão + salvas pelo usuário)
 */
export async function getSpeciesList(): Promise<string[]> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const custom: string[] = raw ? JSON.parse(raw) : [];
    const combined = [...DEFAULT_SPECIES, ...custom];
    // Remove duplicatas e ordena
    const unique = Array.from(new Set(combined)).sort((a, b) =>
      a.localeCompare(b, "pt-BR"),
    );
    return unique;
  } catch (error) {
    console.error("Erro ao recuperar espécies:", error);
    return DEFAULT_SPECIES;
  }
}

/**
 * Adiciona uma nova espécie à lista personalizada (evita duplicatas)
 */
export async function addNewSpecies(name: string): Promise<void> {
  const trimmed = name.trim();
  if (!trimmed) return;

  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    const custom: string[] = raw ? JSON.parse(raw) : [];

    const allExisting = [...DEFAULT_SPECIES, ...custom].map((s) =>
      s.toLowerCase(),
    );

    if (!allExisting.includes(trimmed.toLowerCase())) {
      custom.push(trimmed);
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(custom));
    }
  } catch (error) {
    console.error("Erro ao salvar nova espécie:", error);
  }
}
