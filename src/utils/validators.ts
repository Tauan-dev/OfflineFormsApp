export interface ValidationError {
  field: string;
  message: string;
}

// ───────────────────────────────────────────────────────────────
const CURRENT_YEAR = new Date().getFullYear();

function validateYear(value: string): string | null {
  const t = value.trim();
  if (!t) return null;
  if (!/^\d{4}$/.test(t))
    return "Ano inválido — deve conter exatamente 4 dígitos";
  const yr = Number(t);
  if (yr < 1500 || yr > CURRENT_YEAR)
    return `Ano inválido — deve estar entre 1500 e ${CURRENT_YEAR}`;
  return null;
}

function validateDate(value: string, label = "Data"): string | null {
  const t = value.trim();
  if (!t) return null;
  const m = t.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return `${label} inválida — use o formato DD/MM/AAAA`;
  const day = parseInt(m[1], 10);
  const month = parseInt(m[2], 10);
  const year = parseInt(m[3], 10);
  if (year < 1500 || year > CURRENT_YEAR)
    return `${label} inválida — ano deve estar entre 1500 e ${CURRENT_YEAR}`;
  const date = new Date(year, month - 1, day);
  if (
    date.getFullYear() !== year ||
    date.getMonth() + 1 !== month ||
    date.getDate() !== day
  )
    return `${label} inválida — data não existe no calendário`;
  return null;
}

function validatePositiveNumber(value: string, label: string): string | null {
  const t = value.trim();
  if (!t) return null;
  const num = Number(t);
  if (isNaN(num)) return `${label} deve ser um número válido`;
  if (num < 0) return `${label} não pode ser negativo`;
  return null;
}

// ───────────────────────────────────────────────────────────────
// DENDOMETRIA
// ───────────────────────────────────────────────────────────────
export interface DendrometryFields {
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
}

export function validateDendrometry(
  form: DendrometryFields,
): ValidationError[] {
  const errors: ValidationError[] = [];
  const push = (field: string, msg: string | null) => {
    if (msg) errors.push({ field, message: msg });
  };

  if (!form.parcela.trim()) push("parcela", "Parcela é obrigatória");
  if (!form.arv.trim()) push("arv", "Árvore é obrigatória");
  if (!form.nomeComum.trim()) push("nomeComum", "Nome comum é obrigatório");

  if (!form.dataMedicao.trim())
    push("dataMedicao", "Data de medição é obrigatória");
  else push("dataMedicao", validateDate(form.dataMedicao, "Data de medição"));

  push("plantio", validateYear(form.plantio));

  // Replantio é opcional, mas se preenchido deve ser uma data válida
  // e seu ano deve ser maior que o ano de plantio
  const replantioErr = validateDate(form.replantio, "Replantio");
  if (replantioErr) {
    push("replantio", replantioErr);
  } else if (form.replantio.trim() && form.plantio.trim()) {
    const replantioYear = parseInt(form.replantio.trim().split("/")[2], 10);
    const plantioYear = parseInt(form.plantio.trim(), 10);
    if (
      !isNaN(replantioYear) &&
      !isNaN(plantioYear) &&
      replantioYear <= plantioYear
    ) {
      push("replantio", "Ano do replantio deve ser maior que o ano de plantio");
    }
  }

  push("dap", validatePositiveNumber(form.dap, "DAP"));
  push("hesg", validatePositiveNumber(form.hesg, "Hesg"));
  push("hesgcopa", validatePositiveNumber(form.hesgcopa, "Hesgcopa"));
  push("hc", validatePositiveNumber(form.hc, "Hc"));
  push("ht", validatePositiveNumber(form.ht, "Ht"));

  return errors;
}

// ───────────────────────────────────────────────────────────────
// FENOLOGIA
// ───────────────────────────────────────────────────────────────
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
  fitossanitario: string;
  observacao: string;
}

export function validatePhenology(form: PhenologyFields): ValidationError[] {
  const errors: ValidationError[] = [];
  const push = (field: string, msg: string | null) => {
    if (msg) errors.push({ field, message: msg });
  };

  if (!form.parcela.trim()) push("parcela", "Parcela é obrigatória");
  if (!form.arv.trim()) push("arv", "Árvore é obrigatória");
  if (!form.nomeComum.trim()) push("nomeComum", "Nome comum é obrigatório");

  const groups = [
    { key: "flores" as const, label: "Flores" },
    { key: "frutos" as const, label: "Frutos" },
    { key: "folhas" as const, label: "Folhas" },
  ];

  for (const { key, label } of groups) {
    const g = form[key];
    if (g.presenca && g.intensidade.trim() !== "") {
      const num = Number(g.intensidade);
      if (isNaN(num) || num < 0 || num > 100)
        push(
          `${key}.intensidade`,
          `Intensidade de ${label} deve estar entre 0 e 100`,
        );
    }
  }

  return errors;
}

// ───────────────────────────────────────────────────────────────
export function getFieldError(
  errors: ValidationError[],
  field: string,
): string {
  return errors.find((e) => e.field === field)?.message ?? "";
}
