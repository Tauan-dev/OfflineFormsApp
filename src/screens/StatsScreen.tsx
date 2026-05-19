/**
 * StatsScreen.tsx
 *
 * Painel de BI Offline — exibe estatísticas calculadas localmente a partir
 * dos arquivos CSV salvos. Funciona 100% sem internet.
 */
import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { Colors, Shadow, Spacing, Typography } from "../constants/theme";
import { fileExists, readFileAsText } from "../storage/fileManager";
import { parseCsv } from "../services/excelService";
import {
  calcDendroStats,
  DendroStats,
  parseDendroRows,
} from "../analytics/dendrometryAnalytics";
import {
  calcPhenologyStats,
  parseFenologiaRows,
  PhenologyStats,
} from "../analytics/phenologyAnalytics";
import {
  calcInventoryStats,
  InventoryStats,
} from "../analytics/inventoryAnalytics";

// ─────────────────────────────────────────────────────────────────────────────
// HELPERS DE FORMATAÇÃO
// ─────────────────────────────────────────────────────────────────────────────

function fmt(value: number | null, decimals = 1, unit = ""): string {
  if (value === null) return "—";
  return value.toFixed(decimals) + (unit ? ` ${unit}` : "");
}

function pct(value: number): string {
  return `${value}%`;
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENTES REUTILIZÁVEIS
// ─────────────────────────────────────────────────────────────────────────────

function SectionHeader({ icon, title }: { icon: string; title: string }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionIcon}>{icon}</Text>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionLine} />
    </View>
  );
}

function MetricCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string; // cor da barra lateral
}) {
  return (
    <View
      style={[styles.metricCard, { borderLeftColor: accent ?? Colors.primary }]}
    >
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
      {sub ? <Text style={styles.metricSub}>{sub}</Text> : null}
    </View>
  );
}

function MetricRow({ children }: { children: React.ReactNode }) {
  return <View style={styles.metricRow}>{children}</View>;
}

function BarItem({
  label,
  count,
  pct: pctVal,
  color,
}: {
  label: string;
  count: number;
  pct: number;
  color?: string;
}) {
  return (
    <View style={styles.barItem}>
      <View style={styles.barLabelRow}>
        <Text style={styles.barLabel} numberOfLines={1}>
          {label}
        </Text>
        <Text style={styles.barCount}>
          {count} · {pctVal}%
        </Text>
      </View>
      <View style={styles.barTrack}>
        <View
          style={[
            styles.barFill,
            {
              width: `${Math.min(pctVal, 100)}%`,
              backgroundColor: color ?? Colors.primary,
            },
          ]}
        />
      </View>
    </View>
  );
}

function AlertChip({ estado, count }: { estado: string; count: number }) {
  return (
    <View style={styles.alertChip}>
      <Text style={styles.alertChipText}>
        ⚠️ {estado} · {count}
      </Text>
    </View>
  );
}

function EmptyCard({ message }: { message: string }) {
  return (
    <View style={styles.emptyCard}>
      <Text style={styles.emptyCardIcon}>📭</Text>
      <Text style={styles.emptyCardText}>{message}</Text>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SEÇÕES
// ─────────────────────────────────────────────────────────────────────────────

function DendroSection({ stats }: { stats: DendroStats | null }) {
  if (!stats || stats.total === 0) {
    return (
      <>
        <SectionHeader icon="🌲" title="Dendometria" />
        <EmptyCard message="Nenhum registro de dendometria encontrado" />
      </>
    );
  }
  return (
    <>
      <SectionHeader icon="🌲" title="Dendometria" />

      {/* Totais */}
      <MetricRow>
        <MetricCard
          label="Árvores"
          value={String(stats.total)}
          sub="registros"
          accent={Colors.primary}
        />
        <MetricCard
          label="Parcelas"
          value={String(stats.totalParcelas)}
          sub="ativas"
          accent={Colors.primaryLight}
        />
        <MetricCard
          label="Espécies"
          value={String(stats.totalEspecies)}
          sub="distintas"
          accent="#52B788"
        />
      </MetricRow>

      {/* DAP */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>
          📏 DAP — Diâmetro à Altura do Peito
        </Text>
        <MetricRow>
          <MetricCard
            label="Média"
            value={fmt(stats.mediaDap, 1, "cm")}
            accent={Colors.primary}
          />
          <MetricCard
            label="Máximo"
            value={fmt(stats.maxDap, 1, "cm")}
            accent="#2E8B57"
          />
          <MetricCard
            label="Mínimo"
            value={fmt(stats.minDap, 1, "cm")}
            accent={Colors.primaryLight}
          />
        </MetricRow>
      </View>

      {/* Alturas */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📐 Alturas</Text>
        <MetricRow>
          <MetricCard
            label="HT Média"
            value={fmt(stats.mediaHt, 1, "m")}
            sub="total"
            accent={Colors.primary}
          />
          <MetricCard
            label="HT Máxima"
            value={fmt(stats.maxHt, 1, "m")}
            accent="#2E8B57"
          />
          <MetricCard
            label="HC Média"
            value={fmt(stats.mediaHc, 1, "m")}
            sub="comercial"
            accent={Colors.primaryLight}
          />
        </MetricRow>
      </View>

      {/* Maior árvore */}
      {stats.maiorArvore && (
        <View style={[styles.card, styles.highlightCard]}>
          <Text style={styles.cardTitle}>🏆 Maior Árvore por DAP</Text>
          <View style={styles.highlightRow}>
            <View style={styles.highlightBigVal}>
              <Text style={styles.highlightBigNum}>
                {fmt(stats.maiorArvore.dap, 1, "cm")}
              </Text>
              <Text style={styles.highlightBigLabel}>DAP</Text>
            </View>
            <View style={styles.highlightInfo}>
              <Text style={styles.highlightSpecies}>
                {stats.maiorArvore.nomeComum || "Espécie não informada"}
              </Text>
              <Text style={styles.highlightMeta}>
                Parcela {stats.maiorArvore.parcela} · Árvore{" "}
                {stats.maiorArvore.arv}
              </Text>
              {stats.maiorArvore.ht !== null && (
                <Text style={styles.highlightMeta}>
                  HT: {fmt(stats.maiorArvore.ht, 1, "m")}
                </Text>
              )}
            </View>
          </View>
        </View>
      )}

      {/* Top espécies */}
      {stats.topEspecies.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>🌿 Espécies Mais Frequentes</Text>
          {stats.topEspecies.map((e, i) => (
            <BarItem
              key={i}
              label={e.nome}
              count={e.count}
              pct={e.pct}
              color={i === 0 ? Colors.primary : Colors.primaryLight}
            />
          ))}
        </View>
      )}
    </>
  );
}

function PhenologySection({ stats }: { stats: PhenologyStats | null }) {
  if (!stats || stats.total === 0) {
    return (
      <>
        <SectionHeader icon="🌸" title="Fenologia" />
        <EmptyCard message="Nenhum registro de fenologia encontrado" />
      </>
    );
  }
  return (
    <>
      <SectionHeader icon="🌸" title="Fenologia" />

      {/* Totais */}
      <MetricRow>
        <MetricCard
          label="Observações"
          value={String(stats.total)}
          accent="#C084FC"
        />
        <MetricCard
          label="Espécies"
          value={String(stats.totalEspecies)}
          accent="#A855F7"
        />
        <MetricCard
          label="Em produção"
          value={pct(
            stats.pctFlores > 0 || stats.pctFrutos > 0
              ? Math.max(stats.pctFlores, stats.pctFrutos)
              : 0,
          )}
          sub="flores ou frutos"
          accent="#7C3AED"
        />
      </MetricRow>

      {/* Barras flores / frutos / folhas */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>🔬 Presença por Fenofase</Text>
        <BarItem
          label="🌸 Flores"
          count={Math.round((stats.pctFlores * stats.total) / 100)}
          pct={stats.pctFlores}
          color="#F472B6"
        />
        <BarItem
          label="🍈 Frutos"
          count={Math.round((stats.pctFrutos * stats.total) / 100)}
          pct={stats.pctFrutos}
          color="#FB923C"
        />
        <BarItem
          label="🍃 Folhas"
          count={Math.round((stats.pctFolhas * stats.total) / 100)}
          pct={stats.pctFolhas}
          color="#4ADE80"
        />
      </View>

      {/* Detalhes flores */}
      {stats.floresEstagios.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>🌸 Estágios das Flores</Text>
          {stats.floresEstagios.map((e, i) => (
            <BarItem
              key={i}
              label={e.estagio}
              count={e.count}
              pct={e.pct}
              color="#F472B6"
            />
          ))}
        </View>
      )}

      {/* Detalhes frutos */}
      {stats.frutosEstagios.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>🍈 Estágios dos Frutos</Text>
          {stats.frutosEstagios.map((e, i) => (
            <BarItem
              key={i}
              label={e.estagio}
              count={e.count}
              pct={e.pct}
              color="#FB923C"
            />
          ))}
        </View>
      )}

      {/* Combinações */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>⚡ Cruzamentos</Text>
        <MetricRow>
          <MetricCard
            label="Flores + Frutos"
            value={String(stats.comFloresEFrutos)}
            sub="simultâneos"
            accent="#7C3AED"
          />
          <MetricCard
            label="Sem flores/frutos"
            value={String(stats.semFloresSemFrutos)}
            sub="vegetativo"
            accent={Colors.textTertiary}
          />
        </MetricRow>
      </View>

      {/* Fitossanitário */}
      {stats.fitossanitario.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>🩺 Estado Fitossanitário</Text>
          {stats.fitossanitario.slice(0, 5).map((e, i) => (
            <BarItem
              key={i}
              label={e.estado}
              count={e.count}
              pct={e.pct}
              color={
                e.estado.toLowerCase().includes("bom") ||
                e.estado.toLowerCase().includes("boa")
                  ? "#22C55E"
                  : Colors.warning
              }
            />
          ))}
        </View>
      )}
    </>
  );
}

function InventorySection({ stats }: { stats: InventoryStats | null }) {
  if (
    !stats ||
    (stats.totalArvores === 0 && stats.totalObservacoesFenol === 0)
  ) {
    return (
      <>
        <SectionHeader icon="🌳" title="Inventário" />
        <EmptyCard message="Registre dados para ver o inventário consolidado" />
      </>
    );
  }
  return (
    <>
      <SectionHeader icon="🌳" title="Inventário Consolidado" />

      <MetricRow>
        <MetricCard
          label="Parcelas"
          value={String(stats.totalParcelas)}
          accent={Colors.primary}
        />
        <MetricCard
          label="Espécies"
          value={String(stats.totalEspecies)}
          accent="#2E8B57"
        />
        <MetricCard
          label="Cobertura"
          value={pct(stats.coberturaDados)}
          sub="dendro + fenol"
          accent={stats.coberturaDados >= 70 ? "#22C55E" : Colors.warning}
        />
      </MetricRow>

      {/* Espécie campeã */}
      {stats.especieMaisFrequente && (
        <View style={[styles.card, styles.highlightCard]}>
          <Text style={styles.cardTitle}>🥇 Espécie Mais Frequente</Text>
          <View style={styles.highlightRow}>
            <View style={styles.highlightBigVal}>
              <Text style={styles.highlightBigNum}>
                {stats.especieMaisFrequenteCount}
              </Text>
              <Text style={styles.highlightBigLabel}>registros</Text>
            </View>
            <View style={styles.highlightInfo}>
              <Text style={styles.highlightSpecies}>
                {stats.especieMaisFrequente}
              </Text>
              <Text style={styles.highlightMeta}>
                {stats.totalEspecies} espécies no total
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Top espécies cruzadas */}
      {stats.topEspecies.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📋 Inventário por Espécie</Text>
          {stats.topEspecies.map((e, i) => (
            <View key={i} style={styles.especieRow}>
              <Text style={styles.especieRank}>{i + 1}</Text>
              <View style={styles.especieInfo}>
                <Text style={styles.especieNome} numberOfLines={1}>
                  {e.nome}
                </Text>
                <Text style={styles.especieSub}>
                  🌲 {e.totalDendro} dendro · 🌸 {e.totalFenol} fenol
                </Text>
              </View>
              <View style={styles.especieBadge}>
                <Text style={styles.especieBadgeText}>{e.totalGeral}</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Parcelas ativas */}
      {stats.parcelasAtivas.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>📍 Parcelas Ativas</Text>
          <View style={styles.chipWrap}>
            {stats.parcelasAtivas.map((p, i) => (
              <View key={i} style={styles.parcelaChip}>
                <Text style={styles.parcelaChipText}>{p}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Alertas fitossanitários */}
      {stats.fitossanitarioAlerta.length > 0 && (
        <View style={[styles.card, styles.alertCard]}>
          <Text style={[styles.cardTitle, { color: Colors.warning }]}>
            ⚠️ Alertas Fitossanitários
          </Text>
          <View style={styles.chipWrap}>
            {stats.fitossanitarioAlerta.slice(0, 6).map((a, i) => (
              <AlertChip key={i} estado={a.estado} count={a.count} />
            ))}
          </View>
        </View>
      )}
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// TELA PRINCIPAL
// ─────────────────────────────────────────────────────────────────────────────

async function loadAllStats() {
  const [dendroExists, fenolExists] = await Promise.all([
    fileExists("dendometria.csv"),
    fileExists("fenologia.csv"),
  ]);

  const [dendroText, fenolText] = await Promise.all([
    dendroExists ? readFileAsText("dendometria.csv") : Promise.resolve(""),
    fenolExists ? readFileAsText("fenologia.csv") : Promise.resolve(""),
  ]);

  const dendroAllRows = dendroText ? parseCsv(dendroText) : [];
  const fenolAllRows = fenolText ? parseCsv(fenolText) : [];

  const dendroData =
    dendroAllRows.length > 1 ? parseDendroRows(dendroAllRows.slice(1)) : [];
  const fenolData =
    fenolAllRows.length > 1 ? parseFenologiaRows(fenolAllRows.slice(1)) : [];

  return {
    dendro: calcDendroStats(dendroData),
    phenol: calcPhenologyStats(fenolData),
    inventory: calcInventoryStats(dendroData, fenolData),
  };
}

interface StatsState {
  dendro: DendroStats | null;
  phenol: PhenologyStats | null;
  inventory: InventoryStats | null;
}

export default function StatsScreen() {
  const [stats, setStats] = useState<StatsState>({
    dendro: null,
    phenol: null,
    inventory: null,
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const result = await loadAllStats();
      setStats(result);
    } catch (e) {
      console.error("[StatsScreen] Erro ao carregar:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      setLoading(true);
      load();
    }, [load]),
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={styles.loadingWrap}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>Calculando estatísticas…</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={Colors.primary}
          colors={[Colors.primary]}
        />
      }
    >
      {/* Banner */}
      <View style={styles.banner}>
        <Text style={styles.bannerIcon}>📊</Text>
        <View>
          <Text style={styles.bannerTitle}>Painel de Campo</Text>
          <Text style={styles.bannerSub}>
            {stats.inventory
              ? `${stats.inventory.totalArvores} dendro · ${stats.inventory.totalObservacoesFenol} fenol`
              : "Dados offline"}
          </Text>
        </View>
        <View style={styles.offlineBadge}>
          <View style={styles.offlineDot} />
          <Text style={styles.offlineBadgeText}>Offline</Text>
        </View>
      </View>

      {/* Seções */}
      <InventorySection stats={stats.inventory} />
      <DendroSection stats={stats.dendro} />
      <PhenologySection stats={stats.phenol} />

      <Text style={styles.footer}>
        ↻ Puxe para atualizar · Dados calculados localmente
      </Text>
    </ScrollView>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// ESTILOS
// ─────────────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.paddingScreen, paddingBottom: 48 },

  loadingWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    backgroundColor: Colors.background,
  },
  loadingText: { ...Typography.caption, fontSize: 14 },

  // Banner topo
  banner: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.primaryDark,
    borderRadius: Spacing.borderRadius,
    padding: 16,
    gap: 12,
    marginBottom: 24,
    ...Shadow.card,
  },
  bannerIcon: { fontSize: 32 },
  bannerTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#fff",
  },
  bannerSub: { fontSize: 12, color: "rgba(255,255,255,0.65)", marginTop: 2 },
  offlineBadge: {
    marginLeft: "auto",
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.12)",
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 5,
    gap: 5,
  },
  offlineDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#4ADE80",
  },
  offlineBadgeText: { fontSize: 11, color: "#fff", fontWeight: "600" },

  // Section header
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 8,
    marginBottom: 12,
  },
  sectionIcon: { fontSize: 18 },
  sectionTitle: {
    fontSize: 13,
    fontWeight: "800",
    color: Colors.textSecondary,
    textTransform: "uppercase",
    letterSpacing: 1.2,
  },
  sectionLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border,
    marginLeft: 4,
  },

  // Cards genéricos
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 16,
    marginBottom: 12,
    ...Shadow.small,
  },
  cardTitle: {
    ...Typography.cardTitle,
    marginBottom: 12,
  },
  highlightCard: {
    borderColor: Colors.primarySoft,
    backgroundColor: "#F0FBF4",
  },
  alertCard: {
    borderColor: Colors.warningLight,
    backgroundColor: Colors.warningLight,
  },

  // MetricRow / MetricCard
  metricRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 12,
  },
  metricCard: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.border,
    borderLeftWidth: 4,
    padding: 12,
    alignItems: "center",
    ...Shadow.small,
  },
  metricValue: {
    fontSize: 22,
    fontWeight: "800",
    color: Colors.textPrimary,
    textAlign: "center",
  },
  metricLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: Colors.textTertiary,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    textAlign: "center",
    marginTop: 2,
  },
  metricSub: {
    fontSize: 10,
    color: Colors.textTertiary,
    textAlign: "center",
    marginTop: 1,
  },

  // Barra de progresso
  barItem: { marginBottom: 10 },
  barLabelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  barLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontWeight: "600",
    flex: 1,
  },
  barCount: { fontSize: 11, color: Colors.textTertiary, fontWeight: "600" },
  barTrack: {
    height: 8,
    backgroundColor: Colors.surfaceAlt,
    borderRadius: 4,
    overflow: "hidden",
  },
  barFill: { height: 8, borderRadius: 4 },

  // Highlight card
  highlightRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  highlightBigVal: { alignItems: "center", minWidth: 72 },
  highlightBigNum: {
    fontSize: 34,
    fontWeight: "900",
    color: Colors.primary,
  },
  highlightBigLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: Colors.primaryLight,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  highlightInfo: { flex: 1 },
  highlightSpecies: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  highlightMeta: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 2,
  },

  // Inventário — row de espécie
  especieRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: 10,
  },
  especieRank: {
    width: 22,
    fontSize: 12,
    fontWeight: "800",
    color: Colors.primaryLight,
    textAlign: "center",
  },
  especieInfo: { flex: 1 },
  especieNome: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.textPrimary,
  },
  especieSub: { fontSize: 11, color: Colors.textTertiary, marginTop: 1 },
  especieBadge: {
    backgroundColor: Colors.primaryMuted,
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  especieBadgeText: {
    fontSize: 12,
    fontWeight: "800",
    color: Colors.primary,
  },

  // Chips
  chipWrap: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 4 },
  parcelaChip: {
    backgroundColor: Colors.primaryMuted,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 5,
  },
  parcelaChipText: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.primary,
  },
  alertChip: {
    backgroundColor: Colors.warningLight,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderWidth: 1,
    borderColor: "rgba(230,81,0,0.2)",
  },
  alertChipText: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.warning,
  },

  // Empty
  emptyCard: {
    alignItems: "center",
    padding: 28,
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 12,
    ...Shadow.small,
  },
  emptyCardIcon: { fontSize: 30, marginBottom: 8 },
  emptyCardText: { ...Typography.caption, textAlign: "center", fontSize: 13 },

  footer: {
    ...Typography.caption,
    textAlign: "center",
    marginTop: 8,
  },
});
