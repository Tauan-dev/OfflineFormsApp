// =============================================
// PALETA DE CORES
// =============================================
export const Colors = {
  // Cores principais
  primary: "#2E7D32",
  primaryLight: "#66BB6A",
  primarySoft: "#A5D6A7",

  // Neutras
  background: "#F5F5F5",
  surface: "#FFFFFF",
  border: "#E0E0E0",
  textPrimary: "#424242",
  textSecondary: "#9E9E9E",

  // Estado
  success: "#2E7D32",
  error: "#D32F2F",
  warning: "#F9A825",
  errorSoft: "#FFEBEE",
  successSoft: "#E8F5E9",
};

// =============================================
// ESPAÇAMENTO E DIMENSÕES
// =============================================
export const Spacing = {
  paddingScreen: 16,
  paddingCard: 16,
  gapBetweenCards: 12,
  borderRadius: 12,
  borderRadiusInput: 8,
  inputHeight: 48,
  buttonHeight: 50,
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
    fontSize: 15,
    fontWeight: "700" as const,
    color: Colors.textPrimary,
    textTransform: "uppercase" as const,
    letterSpacing: 0.6,
  },
  label: {
    fontSize: 13,
    fontWeight: "500" as const,
    color: Colors.textSecondary,
    marginBottom: 4,
  },
  inputText: {
    fontSize: 16,
    color: Colors.textPrimary,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: "600" as const,
    color: "#FFFFFF",
  },
  caption: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  errorText: {
    fontSize: 12,
    color: Colors.error,
    marginTop: 3,
  },
};

// =============================================
// SOMBRA PADRÃO (leve)
// =============================================
export const Shadow = {
  small: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 2,
  },
};
