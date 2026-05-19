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
import { loadInventoryStats } from "../analytics/dataLoader";
import { InventoryStats } from "../analytics/inventoryAnalytics";

function HealthBar({
  label,
  pct,
  color,
}: {
  label: string;
  pct: number;
  color: string;
}) {
  return (
    <View style={styles.healthRow}>
      <Text style={styles.healthLabel}>{label}</Text>
      <View style={styles.barTrack}>
        <View
          style={[
            styles.barFill,
            { width: `${Math.min(pct, 100)}%`, backgroundColor: color },
          ]}
        />
      </View>
      <Text style={[styles.healthPct, { color }]}>{pct}%</Text>
    </View>
  );
}

function EspecieRow({
  rank,
  nome,
  count,
  pct,
}: {
  rank: number;
  nome: string;
  count: number;
  pct: number;
}) {
  const medals = ["🥇", "🥈", "🥉"];
  return (
    <View style={styles.especieRow}>
      <Text style={styles.especieMedal}>{medals[rank] ?? `${rank + 1}°`}</Text>
      <View style={styles.especieInfo}>
        <Text style={styles.especieNome}>{nome}</Text>
        <View style={styles.barTrack}>
          <View
            style={[
              styles.barFill,
              {
                width: `${Math.min(pct, 100)}%`,
                backgroundColor: Colors.primary,
              },
            ]}
          />
        </View>
      </View>
      <Text style={styles.especieCount}>{count}</Text>
    </View>
  );
}

export default function InventoryStatsScreen() {
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const inv = await loadInventoryStats();
      setStats(inv);
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

  if (
    !stats ||
    (stats.totalArvores === 0 && stats.totalObservacoesFenol === 0)
  ) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>🌿</Text>
        <Text style={styles.emptyText}>
          Nenhum dado de inventário encontrado.
        </Text>
        <Text style={styles.emptySub}>
          Registre árvores e fenologia primeiro.
        </Text>
      </View>
    );
  }

  const saudeColor =
    stats.indicadorSaude > 30
      ? "#27AE60"
      : stats.indicadorSaude > -10
        ? "#D4A017"
        : "#E74C3C";

  const interpIndicador =
    stats.indicadorSaude > 30
      ? "Área saudável"
      : stats.indicadorSaude > -10
        ? "Área em equilíbrio"
        : "Área degradada — intervenção recomendada";

  const interpFito =
    stats.pctSaudavel > 80
      ? { text: "Área em boas condições", color: "#27AE60" }
      : stats.pctSaudavel >= 50
        ? { text: "Atenção necessária", color: "#D4A017" }
        : { text: "Área sob estresse", color: "#E74C3C" };

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
      {/* Resumo */}
      <View style={styles.summaryRow}>
        <View style={styles.chip}>
          <Text style={styles.chipValue}>{stats.totalEspecies}</Text>
          <Text style={styles.chipLabel}>Espécies</Text>
        </View>
        <View style={styles.chip}>
          <Text style={styles.chipValue}>{stats.totalParcelas}</Text>
          <Text style={styles.chipLabel}>Parcelas</Text>
        </View>
        <View style={styles.chip}>
          <Text style={styles.chipValue}>{stats.coberturaDados}%</Text>
          <Text style={styles.chipLabel}>Cobertura</Text>
        </View>
      </View>

      {/* Indicador de saúde */}
      <Text style={styles.sectionTitle}>INDICADOR DE SAÚDE</Text>
      <View style={[styles.card, styles.cardCentered]}>
        <Text style={styles.cardLabel}>Condição geral da área</Text>
        <Text style={[styles.cardBigValue, { color: saudeColor }]}>
          {stats.indicadorSaude > 0 ? "+" : ""}
          {stats.indicadorSaude}
        </Text>
        <Text style={[styles.cardInterp, { color: saudeColor }]}>
          ● {interpIndicador}
        </Text>
        <Text style={styles.cardSub}>
          % saudável − (% dano severo + % mortos)
        </Text>
      </View>

      {/* Estado fitossanitário */}
      <Text style={styles.sectionTitle}>ESTADO FITOSSANITÁRIO</Text>
      <View style={styles.card}>
        <HealthBar
          label="🟢 Saudável"
          pct={stats.pctSaudavel}
          color="#27AE60"
        />
        <HealthBar
          label="🟡 Dano Leve"
          pct={stats.pctDanoLeve}
          color="#F1C40F"
        />
        <HealthBar
          label="🔴 Dano Severo"
          pct={stats.pctDanoSevero}
          color="#E67E22"
        />
        <HealthBar label="⚫ Morto" pct={stats.pctMorto} color="#7F8C8D" />
        <Text
          style={[styles.cardInterp, { color: interpFito.color, marginTop: 8 }]}
        >
          ● {interpFito.text}
        </Text>
      </View>

      {/* Top 3 espécies */}
      {stats.top3Especies.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>ESPÉCIES MAIS FREQUENTES</Text>
          <View style={styles.card}>
            {stats.top3Especies.map((esp, i) => (
              <EspecieRow
                key={esp.nome}
                rank={i}
                nome={esp.nome}
                count={esp.totalGeral}
                pct={esp.pct}
              />
            ))}
          </View>
        </>
      )}

      {/* Alertas fitossanitários */}
      {stats.fitossanitarioAlerta.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>ALERTAS FITOSSANITÁRIOS</Text>
          <View style={styles.card}>
            {stats.fitossanitarioAlerta.map((a) => (
              <View key={a.estado} style={styles.alertRow}>
                <Text style={styles.alertEstado}>{a.estado}</Text>
                <Text style={styles.alertCount}>
                  {a.count} ({a.pct}%)
                </Text>
              </View>
            ))}
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

  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  chip: {
    flex: 1,
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    paddingVertical: 12,
    marginHorizontal: 4,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  chipValue: { fontSize: 20, fontWeight: "700", color: Colors.primary },
  chipLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
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

  card: {
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
  cardCentered: { alignItems: "center" },
  cardLabel: { fontSize: 11, color: Colors.textSecondary, marginBottom: 4 },
  cardBigValue: { fontSize: 52, fontWeight: "700", lineHeight: 60 },
  cardInterp: { fontSize: 13, fontWeight: "600", marginTop: 2 },
  cardSub: { fontSize: 11, color: Colors.textSecondary, marginTop: 6 },

  healthRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
    gap: 8,
  },
  healthLabel: {
    width: 100,
    fontSize: 12,
    color: Colors.textPrimary,
    fontWeight: "500",
  },
  barTrack: {
    flex: 1,
    height: 7,
    backgroundColor: "#EEEEEE",
    borderRadius: 4,
    overflow: "hidden",
  },
  barFill: { height: "100%", borderRadius: 4 },
  healthPct: { width: 36, textAlign: "right", fontSize: 12, fontWeight: "600" },

  especieRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
    gap: 8,
  },
  especieMedal: { fontSize: 20, width: 30 },
  especieInfo: { flex: 1 },
  especieNome: {
    fontSize: 12,
    color: Colors.textPrimary,
    fontWeight: "600",
    marginBottom: 5,
  },
  especieCount: {
    fontSize: 14,
    fontWeight: "700",
    color: Colors.primary,
    width: 30,
    textAlign: "right",
  },

  alertRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
  },
  alertEstado: { fontSize: 13, color: Colors.textPrimary, flex: 1 },
  alertCount: { fontSize: 13, color: "#E74C3C", fontWeight: "600" },
});
