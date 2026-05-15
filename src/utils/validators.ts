export interface ValidationError {
  field: string;
  message: string;
}

// =============================================
// DENDOMETRIA
// =============================================

export interface DendrometryFields {
  parcela: string;
  arv: string;
  nomeComum: string;
  dataMedicao: string;
  dap: string;
  hesg: string;
  hesgcopa: string;
  hc: string;
  ht: string;
}

export function validateDendrometry(
  form: DendrometryFields,
): ValidationError[] {
  const errors: ValidationError[] = [];

  // Campos obrigatórios
  if (!form.parcela.trim()) {
    errors.push({ field: "parcela", message: "Parcela é obrigatória" });
  }
  if (!form.arv.trim()) {
    errors.push({ field: "arv", message: "Árvore é obrigatória" });
  }
  if (!form.nomeComum.trim()) {
    errors.push({ field: "nomeComum", message: "Nome comum é obrigatório" });
  }
  if (!form.dataMedicao.trim()) {
    errors.push({
      field: "dataMedicao",
      message: "Data de medição é obrigatória",
    });
  }

  // Campos numéricos — não podem ser negativos
  const numericFields: Array<{ key: keyof DendrometryFields; label: string }> =
    [
      { key: "dap", label: "DAP" },
      { key: "hesg", label: "Hesg" },
      { key: "hesgcopa", label: "Hesgcopa" },
      { key: "hc", label: "Hc" },
      { key: "ht", label: "Ht" },
    ];

  for (const { key, label } of numericFields) {
    const val = form[key].trim();
    if (val !== "") {
      const num = Number(val);
      if (isNaN(num)) {
        errors.push({
          field: key,
          message: `${label} deve ser um número válido`,
        });
      } else if (num < 0) {
        errors.push({ field: key, message: `${label} não pode ser negativo` });
      }
    }
  }

  return errors;
}

// =============================================
// FENOLOGIA
// =============================================

export interface PhenologyGroupFields {
  presenca: boolean;
  intensidade: string;
  estagio: string;
}

export interface PhenologyFields {
  parcela: string;
  arv: string;
  nomeComum: string;
  flores: PhenologyGroupFields;
  frutos: PhenologyGroupFields;
  folhas: PhenologyGroupFields;
}

export function validatePhenology(form: PhenologyFields): ValidationError[] {
  const errors: ValidationError[] = [];

  // Campos obrigatórios
  if (!form.parcela.trim()) {
    errors.push({ field: "parcela", message: "Parcela é obrigatória" });
  }
  if (!form.arv.trim()) {
    errors.push({ field: "arv", message: "Árvore é obrigatória" });
  }
  if (!form.nomeComum.trim()) {
    errors.push({ field: "nomeComum", message: "Nome comum é obrigatório" });
  }

  // Intensidade: apenas valida se presença = sim
  const groups: Array<{
    key: keyof Pick<PhenologyFields, "flores" | "frutos" | "folhas">;
    label: string;
  }> = [
    { key: "flores", label: "Flores" },
    { key: "frutos", label: "Frutos" },
    { key: "folhas", label: "Folhas" },
  ];

  for (const { key, label } of groups) {
    const group = form[key];
    if (group.presenca && group.intensidade.trim() !== "") {
      const num = Number(group.intensidade);
      if (isNaN(num) || num < 0 || num > 100) {
        errors.push({
          field: `${key}.intensidade`,
          message: `Intensidade de ${label} deve estar entre 0 e 100`,
        });
      }
    }
  }

  return errors;
}

// =============================================
// UTILITÁRIO
// =============================================

/** Retorna a mensagem de erro de um campo específico, ou undefined */
export function getFieldError(
  errors: ValidationError[],
  field: string,
): string | undefined {
  return errors.find((e) => e.field === field)?.message;
}
