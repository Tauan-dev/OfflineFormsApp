// ─────────────────────────────────────────────────────────────────────────────
// FEATURE FLAGS — controle de versão do APK
//
//  showStats: true  → APK para gestores/técnicos (com Estatísticas de Campo)
//  showStats: false → APK para coletores de campo (sem Estatísticas de Campo)
//
// Para gerar o APK dos coletores: deixe false e build
// Para gerar o APK dos gestores:  mude para true e build
// ─────────────────────────────────────────────────────────────────────────────

export const FEATURES = {
  showStats: true,
};
