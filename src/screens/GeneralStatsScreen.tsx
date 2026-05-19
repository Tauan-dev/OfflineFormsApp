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
import { loadAllStats, AllStats } from "../analytics/dataLoader";

function KpiCard({
  icon,
  label,
  value,
  unit,
  color,
}: {
  icon: string;
  label: string;
  value: string;
  unit?: string;
  color?: string;
}) {
  return (
    <View style={styles.kpiCard}>
      <Text style={styles.kpiIcon}>{icon}</Text>
      <Text style={styles.kpiLabel}>{label}</Text>
      <View style={styles.kpiRow}>
        <Text style={[styles.kpiValue, color ? { color } : {}]}>{value}</Text>
        {unit ? <Text style={styles.kpiUnit}>{unit}</Text> : null}
      </View>
    </View>
  );
}

function MiniBar({
  label,
  pct,
  color,
}: {
  label: string;
  pct: number;
  color: string;
}) {
  return (
    <View style={styles.miniBarRow}>
      <Text style={styles.miniBarLabel}>{label}</Text>
      <View style={styles.miniBarTrack}>
        <View
          style={[
            styles.miniBarFill,
            { width: `${Math.min(pct, 100)}%`, backgroundColor: color },
          ]}
        />
      </View>
      <Text style={[styles.miniBarPct, { color }]}>{pct}%</Text>
    </View>
  );
}

function fmt(n: number | null, d = 1) {
  return n !== null && n !== undefined ? n.toFixed(d) : "—";
}

export default function GeneralStatsScreen() {
  const [stats, setStats] = useState<AllStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      setStats(await loadAllStats());
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
        <Text style={styles.loadingText}>Consolidando dados…</Text>
      </View>
    );
  }

  const nenhum =
    !stats || (stats.dendro.total === 0 && stats.phenol.total === 0);
  if (nenhum) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>📊</Text>
        <Text style={styles.emptyText}>Nenhum dado encontrado.</Text>
        <Text style={styles.emptySub}>
          Registre dados de dendometria e fenologia.
        </Text>
      </View>
    );
  }

  const { dendro, phenol, inventory } = stats!;
  const indicadorColor =
    inventory.indicadorSaude >= 60
      ? "#27AE60"
      : inventory.indicadorSaude >= 20
        ? "#F39C12"
        : "#E74C3C";

  const interpSaude =
    inventory.indicadorSaude > 30
      ? { text: "Área saudável", color: "#27AE60" }
      : inventory.indicadorSaude > -10
        ? { text: "Área em equilíbrio", color: "#D4A017" }
        : { text: "Área degradada", color: "#E74C3C" };

  const interpFloresGeral =
    phenol.pctFlores > 50
      ? { text: "Alta atividade reprodutiva", color: "#27AE60" }
      : phenol.pctFlores >= 20
        ? { text: "Atividade reprodutiva moderada", color: "#D4A017" }
        : { text: "Baixa atividade reprodutiva", color: "#E74C3C" };

  const interpFrutosGeral =
    phenol.pctFrutos > 40
      ? {
          text: "Alta disponibilidade de recursos para fauna",
          color: "#27AE60",
        }
      : null;

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
      {/* KPIs principais */}
      <View style={styles.kpiGrid}>
        <KpiCard
          icon="🌳"
          label="Registros de dendometria"
          value={String(dendro.total)}
        />
        <KpiCard
          icon="🌸"
          label="Registros de fenologia"
          value={String(phenol.total)}
        />
        <KpiCard
          icon="🌿"
          label="Diversidade de espécies"
          value={String(inventory.totalEspecies)}
        />
        <KpiCard
          icon="📍"
          label="Parcelas amostradas"
          value={String(inventory.totalParcelas)}
        />
        <KpiCard
          icon="📏"
          label="Diâmetro médio (DAP)"
          value={fmt(dendro.mediaDap)}
          unit="cm"
        />
        <KpiCard
          icon="📐"
          label="Altura média do povoamento"
          value={fmt(dendro.mediaHt)}
          unit="m"
        />
        <KpiCard
          icon="🌲"
          label="Área Basal"
          value={
            dendro.areaBasalTotal !== null
              ? dendro.areaBasalTotal.toFixed(3)
              : "—"
          }
          unit="m²"
        />
        <KpiCard
          icon="🔗"
          label="Cobertura"
          value={`${inventory.coberturaDados}%`}
          color={inventory.coberturaDados >= 70 ? "#27AE60" : "#E67E22"}
        />
      </View>

      {/* Indicador de saúde */}
      <Text style={styles.sectionTitle}>CONDIÇÃO GERAL DA ÁREA</Text>
      <View style={styles.healthBigCard}>
        <Text style={styles.healthBigLabel}>Indicador de saúde</Text>
        <Text style={[styles.healthBigValue, { color: indicadorColor }]}>
          {inventory.indicadorSaude > 0 ? "+" : ""}
          {inventory.indicadorSaude}
        </Text>
        <Text style={[styles.healthBigInterp, { color: interpSaude.color }]}>
          ● {interpSaude.text}
        </Text>
        <View style={styles.healthBarsWrap}>
          <MiniBar
            label="Saudável"
            pct={inventory.pctSaudavel}
            color="#27AE60"
          />
          <MiniBar
            label="Dano Leve"
            pct={inventory.pctDanoLeve}
            color="#F1C40F"
          />
          <MiniBar
            label="Dano Severo"
            pct={inventory.pctDanoSevero}
            color="#E67E22"
          />
          <MiniBar label="Morto" pct={inventory.pctMorto} color="#7F8C8D" />
        </View>
      </View>

      {/* Fenologia resumo */}
      <Text style={styles.sectionTitle}>ATIVIDADE FENOLÓGICA</Text>
      <View style={styles.fenolCard}>
        <MiniBar
          label="🌸 Indivíduos com flores"
          pct={phenol.pctFlores}
          color="#B5338A"
        />
        <MiniBar
          label="🍎 Indivíduos com frutos"
          pct={phenol.pctFrutos}
          color="#E67E22"
        />
        <MiniBar
          label="🍃 Indivíduos com folhas"
          pct={phenol.pctFolhas}
          color="#27AE60"
        />
        <Text style={[styles.fenolInterp, { color: interpFloresGeral.color }]}>
          ● {interpFloresGeral.text}
        </Text>
        {interpFrutosGeral && (
          <Text
            style={[styles.fenolInterp, { color: interpFrutosGeral.color }]}
          >
            ● {interpFrutosGeral.text}
          </Text>
        )}
        <View style={styles.fenolFooter}>
          <Text style={styles.fenolItem}>
            🌸+🍎:{" "}
            <Text style={styles.fenolBold}>{phenol.comFloresEFrutos}</Text> ind.
          </Text>
          <Text style={styles.fenolItem}>
            Inativas:{" "}
            <Text style={styles.fenolBold}>{phenol.semFloresSemFrutos}</Text>{" "}
            ind.
          </Text>
          <Text style={styles.fenolItem}>
            Obs. Fauna:{" "}
            <Text style={styles.fenolBold}>{inventory.interacoesFauna}</Text>
          </Text>
        </View>
      </View>

      {/* Espécie mais frequente */}
      {inventory.especieMaisFrequente && (
        <>
          <Text style={styles.sectionTitle}>ESPÉCIE DOMINANTE</Text>
          <View style={styles.especieCard}>
            <Text style={styles.especieNome}>
              {inventory.especieMaisFrequente}
            </Text>
            <Text style={styles.especieCount}>
              {inventory.especieMaisFrequenteCount} registros
            </Text>
          </View>
        </>
      )}

      {/* Top 3 espécies */}
      {inventory.top3Especies.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>TOP 3 ESPÉCIES</Text>
          <View style={styles.top3Card}>
            {inventory.top3Especies.map((esp, i) => {
              const medals = ["🥇", "🥈", "🥉"];
              return (
                <View key={esp.nome} style={styles.top3Row}>
                  <Text style={styles.top3Medal}>{medals[i]}</Text>
                  <Text style={styles.top3Nome}>{esp.nome}</Text>
                  <Text style={styles.top3Count}>{esp.totalGeral}</Text>
                </View>
              );
            })}
          </View>
        </>
      )}
    </ScrollView>
  );
}

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
  kpiGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 4,
    marginTop: 4,
  },
  kpiCard: {
    width: "47%",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 16,
    alignItems: "flex-start",
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  kpiIcon: { fontSize: 20, marginBottom: 6 },
  kpiLabel: {
    fontSize: 9,
    color: Colors.textSecondary,
    marginBottom: 4,
    lineHeight: 13,
  },
  kpiRow: { flexDirection: "row", alignItems: "baseline", gap: 3 },
  kpiValue: { fontSize: 24, fontWeight: "700", color: Colors.primaryDark },
  kpiUnit: { fontSize: 11, color: Colors.textSecondary },
  healthBigCard: {
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
  healthBigLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 4,
  },
  healthBigValue: { fontSize: 44, fontWeight: "700", marginVertical: 4 },
  healthBigInterp: { fontSize: 13, fontWeight: "600", marginBottom: 12 },
  healthBarsWrap: { marginTop: 4 },
  miniBarRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    gap: 8,
  },
  miniBarLabel: {
    width: 84,
    fontSize: 11,
    color: Colors.textPrimary,
    fontWeight: "500",
  },
  miniBarTrack: {
    flex: 1,
    height: 7,
    backgroundColor: "#EEEEEE",
    borderRadius: 4,
    overflow: "hidden",
  },
  miniBarFill: { height: "100%", borderRadius: 4 },
  miniBarPct: {
    width: 34,
    textAlign: "right",
    fontSize: 11,
    fontWeight: "600",
  },
  fenolCard: {
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
  fenolInterp: {
    fontSize: 11,
    fontWeight: "600",
    marginTop: 8,
    marginBottom: 2,
  },
  fenolFooter: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    marginTop: 10,
  },
  fenolItem: { fontSize: 12, color: Colors.textSecondary },
  fenolBold: { fontWeight: "700", color: Colors.primaryDark },
  especieCard: {
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
  especieNome: { fontSize: 20, fontWeight: "700", color: Colors.primaryDark },
  especieCount: { fontSize: 12, color: Colors.textSecondary, marginTop: 6 },
  top3Card: {
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
  top3Row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    gap: 10,
  },
  top3Medal: { fontSize: 20 },
  top3Nome: {
    flex: 1,
    fontSize: 13,
    fontWeight: "600",
    color: Colors.textPrimary,
  },
  top3Count: { fontSize: 16, fontWeight: "700", color: Colors.primary },
});
