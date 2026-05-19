// =============================================
// PALETA DE CORES
// =============================================
export const Colors = {
  // Verdes principais — tons florestais, não saturados
  primary: "#2D6A4F",
  primaryDark: "#1B4332",
  primaryLight: "#52B788",
  primarySoft: "#B7E4C7",
  primaryMuted: "#D8F3DC",

  // Neutras com leve tinte verde
  background: "#F2F5F1",
  surface: "#FFFFFF",
  surfaceAlt: "#EEF3EF",
  border: "rgba(45,106,79,0.14)",
  borderLight: "rgba(45,106,79,0.07)",
  textPrimary: "#1B3327",
  textSecondary: "#4D7260",
  textTertiary: "#8FAD97",

  // Estados
  success: "#2D6A4F",
  successSoft: "#D4EDDA",
  error: "#B71C1C",
  errorSoft: "#FFEBEE",
  warning: "#E65100",
  warningLight: "#FFF3E0",
};

// =============================================
// GRADIENTES
// =============================================
export const Gradients = {
  header: ["#1B4332", "#2D6A4F"] as [string, string],
  headerDiag: ["#163828", "#2D6A4F", "#3A8A63"] as [string, string, string],
  cardAccent: ["#2D6A4F", "#52B788"] as [string, string],
  softGreen: ["#D8F3DC", "#F2F5F1"] as [string, string],
  surface: ["#FFFFFF", "#F7FAF7"] as [string, string],
};

// =============================================
// ESPAÇAMENTO E DIMENSÕES
// =============================================
export const Spacing = {
  paddingScreen: 20,
  paddingCard: 18,
  gapBetweenCards: 14,
  borderRadius: 16,
  borderRadiusInput: 12,
  borderRadiusChip: 22,
  inputHeight: 54,
  buttonHeight: 52,
};

// =============================================
// TIPOGRAFIA
// =============================================
export const Typography = {
  screenTitle: {
    fontSize: 22,
    fontWeight: "bold" as const,
    color: Colors.textPrimary,
  },
  cardTitle: {
    fontSize: 12,
    fontWeight: "700" as const,
    color: Colors.primary,
    textTransform: "uppercase" as const,
    letterSpacing: 1.1,
  },
  label: {
    fontSize: 12,
    fontWeight: "600" as const,
    color: Colors.textSecondary,
    marginBottom: 5,
    letterSpacing: 0.2,
  },
  inputText: {
    fontSize: 16,
    color: Colors.textPrimary,
  },
  buttonText: {
    fontSize: 15,
    fontWeight: "700" as const,
    color: "#FFFFFF",
    letterSpacing: 0.3,
  },
  caption: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  errorText: {
    fontSize: 11,
    color: Colors.error,
    marginTop: 4,
  },
  unit: {
    fontSize: 13,
    fontWeight: "600" as const,
    color: Colors.textTertiary,
  },
};

// =============================================
// SOMBRAS — difusas, estilo iOS premium
// =============================================
export const Shadow = {
  small: {
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  card: {
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 14,
    elevation: 4,
  },
  medium: {
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.14,
    shadowRadius: 20,
    elevation: 8,
  },
  strong: {
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.18,
    shadowRadius: 28,
    elevation: 12,
  },
};
