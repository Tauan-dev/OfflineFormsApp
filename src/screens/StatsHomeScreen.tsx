import React, { useCallback, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { RootStackParamList } from "../navigation/AppNavigator";
import { Colors } from "../constants/theme";
import { loadAllStats, AllStats } from "../analytics/dataLoader";

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, "StatsHome">;
};

const CARDS = [
  {
    icon: "🌳",
    label: "Dendometria",
    sub: "DAP, altura, área basal",
    route: "DendrometryStats" as keyof RootStackParamList,
    color: "#2D6A4F",
  },
  {
    icon: "🌸",
    label: "Fenologia",
    sub: "Flores, frutos, folhas",
    route: "PhenologyStats" as keyof RootStackParamList,
    color: "#B5338A",
  },
  {
    icon: "🌿",
    label: "Inventário",
    sub: "Espécies e fitossanidade",
    route: "InventoryStatsHome" as keyof RootStackParamList,
    color: "#1B6CA8",
  },
  {
    icon: "📊",
    label: "Visão Geral",
    sub: "Consolidado da área",
    route: "GeneralStats" as keyof RootStackParamList,
    color: "#7B5EA7",
  },
];

export default function StatsHomeScreen({ navigation }: Props) {
  const [stats, setStats] = useState<AllStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const data = await loadAllStats();
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
      {/* Cabeçalho */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>📈 Análises de Campo</Text>
        <Text style={styles.headerSub}>
          Selecione uma categoria para detalhar
        </Text>
      </View>

      {/* Resumo rápido */}
      {loading ? (
        <ActivityIndicator
          color={Colors.primary}
          style={{ marginVertical: 20 }}
        />
      ) : stats ? (
        <View style={styles.summaryRow}>
          <SummaryChip label="Reg. Dendro" value={String(stats.dendro.total)} />
          <SummaryChip label="Reg. Fenol" value={String(stats.phenol.total)} />
          <SummaryChip
            label="Espécies"
            value={String(stats.inventory.totalEspecies)}
          />
          <SummaryChip
            label="Parcelas"
            value={String(stats.inventory.totalParcelas)}
          />
        </View>
      ) : null}

      {/* Grid 2×2 */}
      <View style={styles.grid}>
        {CARDS.map((card) => (
          <TouchableOpacity
            key={card.route}
            style={styles.card}
            activeOpacity={0.82}
            onPress={() => navigation.navigate(card.route as any)}
          >
            <View
              style={[styles.cardIcon, { backgroundColor: card.color + "18" }]}
            >
              <Text style={styles.cardIconText}>{card.icon}</Text>
            </View>
            <Text style={[styles.cardLabel, { color: card.color }]}>
              {card.label}
            </Text>
            <Text style={styles.cardSub}>{card.sub}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Indicador saúde geral */}
      {stats && (
        <View style={styles.healthCard}>
          <Text style={styles.healthTitle}>🩺 Indicador de Saúde da Área</Text>
          <Text
            style={[
              styles.healthValue,
              {
                color:
                  stats.inventory.indicadorSaude >= 60
                    ? "#27AE60"
                    : stats.inventory.indicadorSaude >= 30
                      ? "#F39C12"
                      : "#E74C3C",
              },
            ]}
          >
            {stats.inventory.indicadorSaude > 0 ? "+" : ""}
            {stats.inventory.indicadorSaude}
          </Text>
          <Text style={styles.healthSub}>
            {stats.inventory.pctSaudavel}% saudáveis − (
            {stats.inventory.pctDanoSevero}% severo + {stats.inventory.pctMorto}
            % mortos)
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

function SummaryChip({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.chip}>
      <Text style={styles.chipValue}>{value}</Text>
      <Text style={styles.chipLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F5F5F5" },
  content: { padding: 16, paddingBottom: 32 },
  header: { marginBottom: 16 },
  headerTitle: { fontSize: 22, fontWeight: "800", color: Colors.primaryDark },
  headerSub: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  chip: {
    flex: 1,
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    paddingVertical: 10,
    marginHorizontal: 3,
    elevation: 1,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
  },
  chipValue: { fontSize: 20, fontWeight: "800", color: Colors.primary },
  chipLabel: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 2,
    textAlign: "center",
  },
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 20,
  },
  card: {
    width: "47.5%",
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 18,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  cardIcon: {
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 10,
  },
  cardIconText: { fontSize: 24 },
  cardLabel: { fontSize: 15, fontWeight: "800", marginBottom: 4 },
  cardSub: { fontSize: 11, color: Colors.textSecondary, lineHeight: 16 },
  healthCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 18,
    alignItems: "center",
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  healthTitle: { fontSize: 14, color: Colors.textSecondary, fontWeight: "600" },
  healthValue: { fontSize: 48, fontWeight: "900", marginVertical: 6 },
  healthSub: { fontSize: 12, color: Colors.textSecondary, textAlign: "center" },
});
