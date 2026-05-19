import React, { useCallback, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  TouchableOpacity,
  LayoutAnimation,
  Platform,
  UIManager,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { Colors } from "../constants/theme";
import { loadParcelaStats, ParcelaStats } from "../analytics/dataLoader";

// Habilitar LayoutAnimation no Android
if (
  Platform.OS === "android" &&
  UIManager.setLayoutAnimationEnabledExperimental
) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

function interpParcela(indicador: number): { text: string; color: string } {
  if (indicador > 50) return { text: "Área saudável", color: "#27AE60" };
  if (indicador >= 0) return { text: "Área em atenção", color: "#D4A017" };
  return { text: "Área em risco", color: "#E74C3C" };
}

function ParcelaCard({
  p,
  isExpanded,
  onToggle,
}: {
  p: ParcelaStats;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const interp = interpParcela(p.indicadorSaude);

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onToggle}
      activeOpacity={0.88}
    >
      {/* Cabeçalho sempre visível */}
      <View style={styles.cardHeader}>
        <View style={styles.cardHeaderLeft}>
          <Text style={styles.cardNome}>{p.parcela}</Text>
          <Text style={[styles.statusText, { color: interp.color }]}>
            {interp.text}
          </Text>
        </View>
        <Text style={[styles.chevron, { color: interp.color }]}>
          {isExpanded ? "▲" : "▼"}
        </Text>
      </View>

      {/* Resumo colapsado */}
      {!isExpanded && (
        <View style={styles.collapsedRow}>
          <Text style={styles.collapsedItem}>
            DAP médio:{" "}
            <Text style={styles.collapsedValue}>
              {p.mediaDap !== null ? `${p.mediaDap.toFixed(1)} cm` : "—"}
            </Text>
          </Text>
          <Text style={styles.collapsedSep}> · </Text>
          <Text style={styles.collapsedItem}>
            Saúde:{" "}
            <Text style={[styles.collapsedValue, { color: interp.color }]}>
              {p.indicadorSaude > 0 ? "+" : ""}
              {p.indicadorSaude}
            </Text>
          </Text>
        </View>
      )}

      {/* Detalhes expandidos */}
      {isExpanded && (
        <View>
          {/* Métricas em grade — sem divisores visuais */}
          <View style={styles.metricsRow}>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>{p.totalArvores}</Text>
              <Text style={styles.metricLabel}>Indivíduos</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>{p.totalEspecies}</Text>
              <Text style={styles.metricLabel}>Espécies</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricValue}>
                {p.mediaDap !== null ? p.mediaDap.toFixed(1) : "—"}
              </Text>
              <Text style={styles.metricLabel}>DAP (cm)</Text>
            </View>
            <View style={styles.metric}>
              <Text style={[styles.metricValue, { color: interp.color }]}>
                {p.indicadorSaude > 0 ? "+" : ""}
                {p.indicadorSaude}
              </Text>
              <Text style={styles.metricLabel}>Saúde</Text>
            </View>
          </View>

          {/* Estado fitossanitário — barra */}
          <Text style={styles.expandSectionLabel}>Estado fitossanitário</Text>
          <View style={styles.healthBar}>
            {p.pctSaudavel > 0 && (
              <View
                style={[
                  styles.healthSegment,
                  { flex: p.pctSaudavel, backgroundColor: "#27AE60" },
                ]}
              />
            )}
            {p.pctDanoLeve > 0 && (
              <View
                style={[
                  styles.healthSegment,
                  { flex: p.pctDanoLeve, backgroundColor: "#F1C40F" },
                ]}
              />
            )}
            {p.pctDanoSevero > 0 && (
              <View
                style={[
                  styles.healthSegment,
                  { flex: p.pctDanoSevero, backgroundColor: "#E67E22" },
                ]}
              />
            )}
            {p.pctMorto > 0 && (
              <View
                style={[
                  styles.healthSegment,
                  { flex: p.pctMorto, backgroundColor: "#7F8C8D" },
                ]}
              />
            )}
          </View>
          <View style={styles.legendRow}>
            {p.pctSaudavel > 0 && (
              <Text style={styles.legendItem}>
                🟢 {p.pctSaudavel}% saudável
              </Text>
            )}
            {p.pctDanoLeve > 0 && (
              <Text style={styles.legendItem}>🟡 {p.pctDanoLeve}% d. leve</Text>
            )}
            {p.pctDanoSevero > 0 && (
              <Text style={styles.legendItem}>
                🔴 {p.pctDanoSevero}% d. severo
              </Text>
            )}
            {p.pctMorto > 0 && (
              <Text style={styles.legendItem}>⚫ {p.pctMorto}% morto</Text>
            )}
          </View>

          {/* Espécie dominante */}
          {p.especieDominante ? (
            <Text style={styles.dominante}>
              Espécie dominante:{" "}
              <Text style={styles.dominanteNome}>{p.especieDominante}</Text>
            </Text>
          ) : null}
        </View>
      )}
    </TouchableOpacity>
  );
}
export default function InventoryParcelaScreen() {
  const [parcelas, setParcelas] = useState<ParcelaStats[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  function toggleCard(nome: string) {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded((prev) => (prev === nome ? null : nome));
  }

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const data = await loadParcelaStats();
      setParcelas(data);
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
        <Text style={styles.loadingText}>Carregando parcelas…</Text>
      </View>
    );
  }

  if (parcelas.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>📍</Text>
        <Text style={styles.emptyText}>Nenhuma parcela encontrada.</Text>
        <Text style={styles.emptySub}>
          Registre árvores com parcelas definidas.
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
      <Text style={styles.headerSub}>
        Ordenado do melhor para o pior estado de conservação
      </Text>
      {parcelas.map((p) => (
        <ParcelaCard
          key={p.parcela}
          p={p}
          isExpanded={expanded === p.parcela}
          onToggle={() => toggleCard(p.parcela)}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F5F5F5" },
  content: { padding: 16, paddingBottom: 32 },
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
  headerSub: { fontSize: 12, color: Colors.textSecondary, marginBottom: 14 },

  // Card acordeão
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    elevation: 3,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 6,
  },
  cardHeaderLeft: { flex: 1, gap: 3 },
  cardNome: { fontSize: 15, fontWeight: "700", color: Colors.primaryDark },
  statusText: { fontSize: 12, fontWeight: "500" },
  chevron: { fontSize: 13, fontWeight: "600", marginLeft: 12, marginTop: 2 },

  // Colapsado
  collapsedRow: { flexDirection: "row", alignItems: "center", marginTop: 6 },
  collapsedItem: { fontSize: 12, color: Colors.textSecondary },
  collapsedValue: { fontWeight: "600", color: Colors.textPrimary },
  collapsedSep: { fontSize: 12, color: Colors.textSecondary },

  // Expandido
  expandSectionLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: Colors.textSecondary,
    marginBottom: 6,
    marginTop: 20,
  },

  // Métricas
  metricsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 16,
    marginBottom: 4,
  },
  metric: { flex: 1, alignItems: "center" },
  metricValue: { fontSize: 20, fontWeight: "700", color: Colors.primaryDark },
  metricLabel: {
    fontSize: 9,
    color: Colors.textSecondary,
    marginTop: 3,
    textAlign: "center",
  },

  // Barra de saúde
  healthBar: {
    flexDirection: "row",
    height: 6,
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 8,
  },
  healthSegment: { height: "100%" },

  // Legenda
  legendRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 8,
  },
  legendItem: { fontSize: 10, color: Colors.textSecondary },

  // Espécie dominante
  dominante: { fontSize: 12, color: Colors.textSecondary, marginTop: 10 },
  dominanteNome: { fontWeight: "600", color: Colors.primaryDark },
});
