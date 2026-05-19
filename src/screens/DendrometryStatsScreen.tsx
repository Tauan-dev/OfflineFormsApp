import React, { useCallback, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { Colors } from "../constants/theme";
import { loadDendroStats } from "../analytics/dataLoader";
import { DendroStats } from "../analytics/dendrometryAnalytics";

function fmt(n: number | null, decimals = 1): string {
  if (n === null || n === undefined) return "—";
  return n.toFixed(decimals);
}

function interpDap(dap: number | null): { text: string; color: string } | null {
  if (dap === null) return null;
  if (dap < 10) return { text: "Povoamento jovem", color: "#E67E22" };
  if (dap <= 20)
    return { text: "Povoamento em desenvolvimento", color: "#D4A017" };
  return { text: "Povoamento estabelecido", color: "#27AE60" };
}

function interpAreaBasal(
  ab: number | null,
): { text: string; color: string } | null {
  if (ab === null) return null;
  if (ab < 5) return { text: "Baixa densidade de biomassa", color: "#E67E22" };
  if (ab <= 20) return { text: "Densidade equilibrada", color: "#D4A017" };
  return { text: "Alta densidade de biomassa", color: "#27AE60" };
}

function StatCard({
  label,
  value,
  unit,
  sub,
  interp,
}: {
  label: string;
  value: string;
  unit?: string;
  sub?: string;
  interp?: { text: string; color: string } | null;
}) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statLabel}>{label}</Text>
      <View style={styles.statRow}>
        <Text style={styles.statValue}>{value}</Text>
        {unit ? <Text style={styles.statUnit}>{unit}</Text> : null}
      </View>
      {sub ? <Text style={styles.statSub}>{sub}</Text> : null}
      {interp ? (
        <Text style={[styles.statInterp, { color: interp.color }]}>
          ● {interp.text}
        </Text>
      ) : null}
    </View>
  );
}

function BarRow({
  label,
  pct,
  count,
}: {
  label: string;
  pct: number;
  count: number;
}) {
  return (
    <View style={styles.barRow}>
      <Text style={styles.barLabel}>{label}</Text>
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${Math.min(pct, 100)}%` }]} />
      </View>
      <Text style={styles.barPct}>
        {count} ({pct}%)
      </Text>
    </View>
  );
}

export default function DendrometryStatsScreen() {
  const [stats, setStats] = useState<DendroStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const data = await loadDendroStats();
      setStats(data);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetch();
    }, [fetch]),
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.primary} />
        <Text style={styles.loadingText}>Calculando estatísticas…</Text>
      </View>
    );
  }

  if (!stats || stats.total === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>🌳</Text>
        <Text style={styles.emptyText}>
          Nenhum registro de dendometria encontrado.
        </Text>
        <Text style={styles.emptySub}>
          Registre árvores no formulário de Dendometria.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => fetch(true)}
          tintColor={Colors.primary}
          colors={[Colors.primary]}
        />
      }
    >
      {/* Métricas principais */}
      <Text style={styles.sectionTitle}>MÉTRICAS PRINCIPAIS</Text>
      <View style={styles.cardGrid}>
        <StatCard
          label="Total de árvores medidas"
          value={String(stats.total)}
        />
        <StatCard
          label="Parcelas amostradas"
          value={String(stats.totalParcelas)}
        />
        <StatCard
          label="Riqueza de espécies"
          value={String(stats.totalEspecies)}
        />
        <StatCard
          label="Diâmetro médio (DAP)"
          value={fmt(stats.mediaDap)}
          unit="cm"
          sub={`Mín: ${fmt(stats.minDap)} · Máx: ${fmt(stats.maxDap)}`}
          interp={interpDap(stats.mediaDap)}
        />
        <StatCard
          label="Altura média do povoamento"
          value={fmt(stats.mediaHt)}
          unit="m"
          sub={`Máx: ${fmt(stats.maxHt)} m`}
        />
        <StatCard
          label="Altura do fuste (HC)"
          value={fmt(stats.mediaHc)}
          unit="m"
        />
      </View>

      {/* Área basal */}
      <Text style={styles.sectionTitle}>ÁREA BASAL</Text>
      <View style={styles.highlightCard}>
        <Text style={styles.highlightLabel}>Área basal total da parcela</Text>
        <Text style={styles.highlightValue}>
          {stats.areaBasalTotal !== null
            ? stats.areaBasalTotal.toFixed(4)
            : "—"}
          <Text style={styles.highlightUnit}> m²</Text>
        </Text>
        <Text style={styles.highlightSub}>
          Σ π·(DAP/2)² de todos os indivíduos
        </Text>
        {interpAreaBasal(stats.areaBasalTotal) && (
          <Text
            style={[
              styles.highlightInterp,
              { color: interpAreaBasal(stats.areaBasalTotal)!.color },
            ]}
          >
            ● {interpAreaBasal(stats.areaBasalTotal)!.text}
          </Text>
        )}
      </View>

      {/* Maior árvore */}
      {stats.maiorArvore && (
        <>
          <Text style={styles.sectionTitle}>MAIOR INDIVÍDUO</Text>
          <View style={styles.highlightCard}>
            <Text style={styles.highlightLabel}>
              {stats.maiorArvore.nomeComum || "Espécie não identificada"}
            </Text>
            <Text style={styles.highlightValue}>
              {fmt(stats.maiorArvore.dap)}{" "}
              <Text style={styles.highlightUnit}>cm DAP</Text>
            </Text>
            <Text style={styles.highlightSub}>
              Parcela {stats.maiorArvore.parcela} · Árv. {stats.maiorArvore.arv}
              {stats.maiorArvore.ht !== null
                ? ` · HT ${fmt(stats.maiorArvore.ht)} m`
                : ""}
            </Text>
          </View>
        </>
      )}

      {/* Distribuição diamétrica */}
      {stats.distribuicaoDiametrica.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>DISTRIBUIÇÃO DIAMÉTRICA</Text>
          <View style={styles.barsCard}>
            {stats.distribuicaoDiametrica.map((cl) => (
              <BarRow
                key={cl.classe}
                label={`${cl.classe} cm`}
                pct={cl.pct}
                count={cl.count}
              />
            ))}
          </View>
        </>
      )}

      {/* Top espécies */}
      {stats.topEspecies.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>ESPÉCIES MAIS FREQUENTES</Text>
          <View style={styles.barsCard}>
            {stats.topEspecies.map((esp) => (
              <BarRow
                key={esp.nome}
                label={esp.nome}
                pct={esp.pct}
                count={esp.count}
              />
            ))}
          </View>
        </>
      )}
    </ScrollView>
  );
}

const BAR_COLOR = "#2D6A4F";

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F5F5F5" },
  content: { padding: 16, paddingBottom: 40 },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  loadingText: { marginTop: 12, color: Colors.textSecondary, fontSize: 14 },
  emptyIcon: { fontSize: 48, marginBottom: 12 },
  emptyText: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.textPrimary,
    textAlign: "center",
  },
  emptySub: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 6,
    textAlign: "center",
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: Colors.textSecondary,
    letterSpacing: 0.8,
    marginBottom: 10,
    marginTop: 16,
  },
  cardGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 4,
  },
  statCard: {
    width: "47%",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 16,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  statLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 6,
    lineHeight: 16,
  },
  statRow: { flexDirection: "row", alignItems: "baseline", gap: 4 },
  statValue: { fontSize: 28, fontWeight: "700", color: Colors.primaryDark },
  statUnit: { fontSize: 13, color: Colors.textSecondary },
  statSub: { fontSize: 10, color: Colors.textSecondary, marginTop: 4 },
  statInterp: { fontSize: 10, fontWeight: "600", marginTop: 6 },
  highlightCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 20,
    marginBottom: 4,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  highlightLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 6,
  },
  highlightValue: {
    fontSize: 34,
    fontWeight: "700",
    color: Colors.primaryDark,
  },
  highlightUnit: {
    fontSize: 15,
    fontWeight: "400",
    color: Colors.textSecondary,
  },
  highlightSub: { fontSize: 11, color: Colors.textSecondary, marginTop: 6 },
  highlightInterp: { fontSize: 11, fontWeight: "600", marginTop: 8 },
  barsCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 18,
    marginBottom: 4,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  barRow: { marginBottom: 12 },
  barLabel: {
    fontSize: 12,
    color: Colors.textPrimary,
    marginBottom: 5,
    fontWeight: "500",
  },
  barTrack: {
    height: 7,
    backgroundColor: "#EEEEEE",
    borderRadius: 4,
    overflow: "hidden",
    marginBottom: 3,
  },
  barFill: { height: "100%", backgroundColor: BAR_COLOR, borderRadius: 4 },
  barPct: { fontSize: 10, color: Colors.textSecondary },
});
