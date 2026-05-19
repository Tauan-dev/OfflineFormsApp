/**
 * populationDynamicsAnalytics.ts
 *
 * Dinâmica do Povoamento — análises baseadas em ecologia de populações
 * e silvicultura: coortes, recrutamento, mortalidade (via replantio),
 * distribuição temporal.
 *
 * Usa os dados brutos de DendroRow (dendometria.csv).
 *
 * Colunas relevantes:
 *   plantio   → ano/coorte de plantio original
 *   replantio → preenchido = árvore foi replantada (mortalidade + recrutamento)
 *   nomeComum → espécie
 *   parcela   → unidade amostral
 */

import { DendroRow } from "./dendrometryAnalytics";

// ─────────────────────────────────────────────────────────────────────────────
// TIPOS
// ─────────────────────────────────────────────────────────────────────────────

export interface CoorteEntry {
  ano: string; // ex: "2021"
  total: number; // árvores plantadas naquele ano
  pct: number; // % do total
  replantios: number; // replantios ocorridos nesse coorte
  taxaReplantio: number; // % de replantio dentro do coorte
}

export interface ReplantioAno {
  ano: string;
  count: number;
  pct: number;
}

export interface EspecieReplantio {
  nome: string;
  count: number;
  pct: number;
}

export interface ParcelaReplantio {
  parcela: string;
  totalArvores: number;
  replantios: number;
  taxaReplantio: number; // %
}

// ── NOVOS TIPOS ───────────────────────────────────────────────────────────────

export type AdaptacaoNivel = "alta" | "moderada" | "baixa";

export interface EspecieSucesso {
  nome: string;
  total: number;
  replantios: number;
  indiceSucesso: number; // 0.0 – 1.0
  nivel: AdaptacaoNivel;
}

export type ClassificacaoPovoamento =
  | "Jovem"
  | "Em desenvolvimento"
  | "Estabelecido"
  | "Sob estresse"
  | "Degradado";

export interface ClassificacaoPovoamentoResult {
  classificacao: ClassificacaoPovoamento;
  cor: string;
  descricao: string;
}

export interface PopulationDynamicsStats {
  // Totais
  totalArvores: number;
  totalReplantios: number;
  taxaReplantioGlobal: number; // %

  // Coortes
  coortes: CoorteEntry[]; // ordenado por ano
  coortesDominante: string | null; // ano com mais indivíduos
  totalCoortes: number;
  amplitudeTemporal: number | null; // diferença em anos entre menor e maior coorte

  // Replantio por ano
  replantiosPorAno: ReplantioAno[];

  // Espécies mais replantadas
  especiesReplantadas: EspecieReplantio[];

  // Replantio por parcela
  replantiosPorParcela: ParcelaReplantio[];

  // Interpretação
  interpretacao: string;
  interpretacaoColor: string;

  // ── NOVOS CAMPOS ────────────────────────────────────────────────────────
  especiesSucesso: EspecieSucesso[]; // top piores + todas
  classificacaoPovoamento: ClassificacaoPovoamentoResult;
  textoAutomatico: string; // laudo gerado automaticamente
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────────────────────

function isReplanted(val: string): boolean {
  if (!val || val.trim() === "") return false;
  const v = val.trim().toLowerCase();
  if (
    v === "não" ||
    v === "nao" ||
    v === "n" ||
    v === "0" ||
    v === "false" ||
    v === "no"
  )
    return false;
  return true;
}

function extractYear(val: string): string | null {
  if (!val || val.trim() === "") return null;
  const match = val.trim().match(/\b(19|20)\d{2}\b/);
  if (match) return match[0];
  // fallback: se for apenas número com 4 dígitos
  if (/^\d{4}$/.test(val.trim())) return val.trim();
  return val.trim() || null;
}

// ─────────────────────────────────────────────────────────────────────────────
// CÁLCULO PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────

export function calcPopulationDynamics(
  rows: DendroRow[],
): PopulationDynamicsStats {
  if (rows.length === 0) {
    return emptyStats();
  }

  const total = rows.length;
  const replantados = rows.filter((r) => isReplanted(r.replantio));
  const totalReplantios = replantados.length;
  const taxaGlobal =
    total > 0 ? Math.round((totalReplantios / total) * 100) : 0;

  // ── Coortes (por ano de plantio) ─────────────────────────────────────────
  const coorteMap = new Map<string, { total: number; replantios: number }>();
  for (const r of rows) {
    const ano = extractYear(r.plantio) ?? "Sem data";
    if (!coorteMap.has(ano)) coorteMap.set(ano, { total: 0, replantios: 0 });
    const entry = coorteMap.get(ano)!;
    entry.total += 1;
    if (isReplanted(r.replantio)) entry.replantios += 1;
  }

  const coortesRaw = Array.from(coorteMap.entries())
    .sort((a, b) => {
      const ya = parseInt(a[0]) || 0;
      const yb = parseInt(b[0]) || 0;
      return ya - yb;
    })
    .map(([ano, v]) => ({
      ano,
      total: v.total,
      pct: Math.round((v.total / total) * 100),
      replantios: v.replantios,
      taxaReplantio:
        v.total > 0 ? Math.round((v.replantios / v.total) * 100) : 0,
    }));

  const coortesDominante =
    coortesRaw.length > 0
      ? coortesRaw.reduce((a, b) => (a.total >= b.total ? a : b)).ano
      : null;

  // Amplitude temporal
  const anosNum = coortesRaw
    .map((c) => parseInt(c.ano))
    .filter((n) => !isNaN(n));
  const amplitudeTemporal =
    anosNum.length >= 2 ? Math.max(...anosNum) - Math.min(...anosNum) : null;

  // ── Replantio por ano (usando campo replantio como possível ano) ──────────
  const replantioAnoMap = new Map<string, number>();
  for (const r of replantados) {
    const ano =
      extractYear(r.replantio) ?? extractYear(r.plantio) ?? "Sem data";
    replantioAnoMap.set(ano, (replantioAnoMap.get(ano) ?? 0) + 1);
  }
  const replantiosPorAno: ReplantioAno[] = Array.from(replantioAnoMap.entries())
    .sort((a, b) => {
      const ya = parseInt(a[0]) || 0;
      const yb = parseInt(b[0]) || 0;
      return ya - yb;
    })
    .map(([ano, count]) => ({
      ano,
      count,
      pct:
        totalReplantios > 0 ? Math.round((count / totalReplantios) * 100) : 0,
    }));

  // ── Espécies mais replantadas ─────────────────────────────────────────────
  const especieMap = new Map<string, number>();
  for (const r of replantados) {
    const nome = (r.nomeComum || "Desconhecida").trim();
    const key = nome.toLowerCase();
    // armazena com o nome original capitalizado
    if (!especieMap.has(key)) especieMap.set(key, 0);
    especieMap.set(key, especieMap.get(key)! + 1);
  }
  // recupera nome original com capitalização (primeira ocorrência)
  const nomeOriginalMap = new Map<string, string>();
  for (const r of replantados) {
    const nome = (r.nomeComum || "Desconhecida").trim();
    const key = nome.toLowerCase();
    if (!nomeOriginalMap.has(key)) nomeOriginalMap.set(key, nome);
  }
  const especiesReplantadas: EspecieReplantio[] = Array.from(
    especieMap.entries(),
  )
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([key, count]) => ({
      nome: nomeOriginalMap.get(key) ?? key,
      count,
      pct:
        totalReplantios > 0 ? Math.round((count / totalReplantios) * 100) : 0,
    }));

  // ── Replantio por parcela ─────────────────────────────────────────────────
  const parcelaMap = new Map<string, { total: number; replantios: number }>();
  for (const r of rows) {
    const p = r.parcela || "Sem parcela";
    if (!parcelaMap.has(p)) parcelaMap.set(p, { total: 0, replantios: 0 });
    const entry = parcelaMap.get(p)!;
    entry.total += 1;
    if (isReplanted(r.replantio)) entry.replantios += 1;
  }
  const replantiosPorParcela: ParcelaReplantio[] = Array.from(
    parcelaMap.entries(),
  )
    .sort((a, b) => b[1].replantios - a[1].replantios)
    .map(([parcela, v]) => ({
      parcela,
      totalArvores: v.total,
      replantios: v.replantios,
      taxaReplantio:
        v.total > 0 ? Math.round((v.replantios / v.total) * 100) : 0,
    }));

  // ── Interpretação automática ──────────────────────────────────────────────
  const { texto, cor } = interpretarDinamica(
    taxaGlobal,
    amplitudeTemporal,
    coortesRaw.length,
  );

  // ── Índice de sucesso por espécie ─────────────────────────────────────────
  const especieTotalMap = new Map<
    string,
    { total: number; replantios: number; nomeOrig: string }
  >();
  for (const r of rows) {
    const nome = (r.nomeComum || "Desconhecida").trim();
    const key = nome.toLowerCase();
    if (!especieTotalMap.has(key))
      especieTotalMap.set(key, { total: 0, replantios: 0, nomeOrig: nome });
    const e = especieTotalMap.get(key)!;
    e.total += 1;
    if (isReplanted(r.replantio)) e.replantios += 1;
  }
  const especiesSucesso: EspecieSucesso[] = Array.from(especieTotalMap.values())
    .filter((e) => e.total > 0)
    .map((e) => {
      const indiceSucesso = parseFloat((1 - e.replantios / e.total).toFixed(3));
      const nivel: AdaptacaoNivel =
        indiceSucesso > 0.8
          ? "alta"
          : indiceSucesso >= 0.5
            ? "moderada"
            : "baixa";
      return {
        nome: e.nomeOrig,
        total: e.total,
        replantios: e.replantios,
        indiceSucesso,
        nivel,
      };
    })
    .sort((a, b) => a.indiceSucesso - b.indiceSucesso); // piores primeiro

  // ── Classificação do povoamento ───────────────────────────────────────────
  // Precisa de DAP médio — calcula a partir das linhas
  const dapsValidos = rows
    .map((r) => r.dap)
    .filter((d): d is number => d !== null && d > 0);
  const mediaDapGeral =
    dapsValidos.length > 0
      ? dapsValidos.reduce((a, b) => a + b, 0) / dapsValidos.length
      : null;
  const totalEspecies = especieTotalMap.size;
  const classificacaoPovoamento = classificarPovoamento(
    mediaDapGeral,
    taxaGlobal,
    totalEspecies,
    coortesRaw.length,
  );

  // ── Texto automático ──────────────────────────────────────────────────────
  const textoAutomatico = gerarTextoAutomatico(
    total,
    totalEspecies,
    mediaDapGeral,
    taxaGlobal,
    especiesSucesso,
    classificacaoPovoamento.classificacao,
    coortesDominante,
  );

  return {
    totalArvores: total,
    totalReplantios,
    taxaReplantioGlobal: taxaGlobal,
    coortes: coortesRaw,
    coortesDominante,
    totalCoortes: coortesRaw.length,
    amplitudeTemporal,
    replantiosPorAno,
    especiesReplantadas,
    replantiosPorParcela,
    interpretacao: texto,
    interpretacaoColor: cor,
    especiesSucesso,
    classificacaoPovoamento,
    textoAutomatico,
  };
}

function interpretarDinamica(
  taxa: number,
  amplitude: number | null,
  numCoortes: number,
): { texto: string; cor: string } {
  if (taxa === 0) {
    return {
      texto:
        "Nenhum replantio registrado. O povoamento está estável, sem histórico de mortalidade ou os dados de replantio ainda não foram informados.",
      cor: "#27AE60",
    };
  }
  if (taxa <= 10) {
    return {
      texto: `Taxa de replantio de ${taxa}% indica baixa mortalidade. O povoamento apresenta boa estabilidade com recrutamento pontual.`,
      cor: "#27AE60",
    };
  }
  if (taxa <= 25) {
    return {
      texto: `Taxa de replantio de ${taxa}% é moderada. Recomenda-se monitorar as parcelas com maior índice para identificar causas de mortalidade recorrente.`,
      cor: "#D4A017",
    };
  }
  if (taxa <= 50) {
    return {
      texto: `Taxa de replantio de ${taxa}% é alta. O povoamento apresenta mortalidade significativa — avaliar pragas, doenças ou condições edafoclimáticas adversas.`,
      cor: "#E67E22",
    };
  }
  return {
    texto: `Taxa de replantio de ${taxa}% é crítica. Mais da metade das árvores foi substituída, indicando instabilidade severa do povoamento. Investigação urgente recomendada.`,
    cor: "#E74C3C",
  };
}

function classificarPovoamento(
  mediaDap: number | null,
  taxaReplantio: number,
  numEspecies: number,
  numCoortes: number,
): ClassificacaoPovoamentoResult {
  // Degradado: replantio alto + dap baixo
  if (taxaReplantio > 50) {
    return {
      classificacao: "Degradado",
      cor: "#E74C3C",
      descricao:
        "Mortalidade severa comprometendo a integridade do sistema produtivo.",
    };
  }
  // Sob estresse: replantio moderado-alto ou dap baixo com baixa diversidade
  if (
    taxaReplantio > 25 ||
    (mediaDap !== null && mediaDap < 8 && numEspecies < 3)
  ) {
    return {
      classificacao: "Sob estresse",
      cor: "#E67E22",
      descricao:
        "Sinais de mortalidade ou crescimento reduzido. Monitoramento intensificado recomendado.",
    };
  }
  // Jovem: dap pequeno, poucos coortes
  if (mediaDap !== null && mediaDap < 10 && numCoortes <= 2) {
    return {
      classificacao: "Jovem",
      cor: "#2980B9",
      descricao:
        "Povoamento recente em fase inicial de estabelecimento. DAP ainda reduzido.",
    };
  }
  // Estabelecido: dap alto, baixo replantio, boa diversidade
  if (
    (mediaDap === null || mediaDap >= 15) &&
    taxaReplantio <= 10 &&
    numEspecies >= 3
  ) {
    return {
      classificacao: "Estabelecido",
      cor: "#27AE60",
      descricao:
        "Estrutura consolidada com baixa mortalidade e boa diversidade de espécies.",
    };
  }
  // Em desenvolvimento: demais casos
  return {
    classificacao: "Em desenvolvimento",
    cor: "#D4A017",
    descricao:
      "Crescimento ativo com estrutura em formação. Acompanhamento periódico recomendado.",
  };
}

function gerarTextoAutomatico(
  totalArvores: number,
  totalEspecies: number,
  mediaDap: number | null,
  taxaReplantio: number,
  especiesSucesso: EspecieSucesso[],
  classificacao: ClassificacaoPovoamento,
  coortesDominante: string | null,
): string {
  const partes: string[] = [];

  // 1. Condição geral
  const condicao =
    classificacao === "Estabelecido"
      ? "em boas condições estruturais"
      : classificacao === "Jovem"
        ? "em fase inicial de desenvolvimento"
        : classificacao === "Em desenvolvimento"
          ? "em processo ativo de crescimento"
          : classificacao === "Sob estresse"
            ? "com sinais de pressão ecológica"
            : "com comprometimento estrutural significativo";
  partes.push(
    `O povoamento (${totalArvores} indivíduos) encontra-se ${condicao}.`,
  );

  // 2. Estrutura diamétrica
  if (mediaDap !== null) {
    const estrutura =
      mediaDap >= 20
        ? "estrutura diamétrica robusta, indicando maturidade silvicultural"
        : mediaDap >= 12
          ? "diâmetros em fase intermediária de desenvolvimento"
          : "diâmetros ainda reduzidos, característicos de plantios jovens";
    partes.push(
      `Com DAP médio de ${mediaDap.toFixed(1)} cm, apresenta ${estrutura}.`,
    );
  }

  // 3. Replantio / mortalidade
  if (taxaReplantio === 0) {
    partes.push(
      "Não há registros de replantio, sugerindo ausência de mortalidade documentada.",
    );
  } else {
    const grau =
      taxaReplantio <= 10
        ? "baixa"
        : taxaReplantio <= 25
          ? "moderada"
          : taxaReplantio <= 50
            ? "alta"
            : "crítica";
    partes.push(
      `A taxa de replantio de ${taxaReplantio}% indica mortalidade ${grau}, com necessidade de${
        taxaReplantio > 25 ? " investigação das causas e" : ""
      } acompanhamento continuado.`,
    );
  }

  // 4. Espécies
  const baixaAdaptacao = especiesSucesso.filter((e) => e.nivel === "baixa");
  if (totalEspecies === 1) {
    partes.push(
      "O sistema é monospecífico, o que aumenta a vulnerabilidade a pragas e doenças.",
    );
  } else if (baixaAdaptacao.length > 0) {
    const nomes = baixaAdaptacao
      .slice(0, 2)
      .map((e) => e.nome)
      .join(" e ");
    partes.push(
      `Das ${totalEspecies} espécies registradas, ${nomes} apresenta${baixaAdaptacao.length > 1 ? "m" : ""} baixa adaptação ao sítio (índice de sucesso < 0,5).`,
    );
  } else {
    partes.push(
      `As ${totalEspecies} espécies registradas demonstram adaptação adequada às condições do sítio.`,
    );
  }

  // 5. Conclusão
  const recomendacao =
    classificacao === "Degradado"
      ? "Recomenda-se intervenção imediata com diagnóstico fitossanitário e revisão do manejo."
      : classificacao === "Sob estresse"
        ? "Recomenda-se monitoramento mensal e avaliação das condições edafoclimáticas e fitossanitárias."
        : classificacao === "Estabelecido"
          ? "Manter o plano de manejo vigente e realizar monitoramento semestral."
          : "Continuar o acompanhamento regular e registrar novos eventos de replantio e medição.";
  partes.push(recomendacao);

  return partes.join(" ");
}

function emptyStats(): PopulationDynamicsStats {
  return {
    totalArvores: 0,
    totalReplantios: 0,
    taxaReplantioGlobal: 0,
    coortes: [],
    coortesDominante: null,
    totalCoortes: 0,
    amplitudeTemporal: null,
    replantiosPorAno: [],
    especiesReplantadas: [],
    replantiosPorParcela: [],
    interpretacao: "Sem dados de dendometria.",
    interpretacaoColor: "#7F8C8D",
    especiesSucesso: [],
    classificacaoPovoamento: {
      classificacao: "Jovem",
      cor: "#7F8C8D",
      descricao: "Sem dados suficientes para classificação.",
    },
    textoAutomatico: "",
  };
}
