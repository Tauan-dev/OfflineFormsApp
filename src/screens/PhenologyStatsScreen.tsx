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
import { loadPhenologyStats } from "../analytics/dataLoader";
import { PhenologyStats } from "../analytics/phenologyAnalytics";

function PresenceBar({
  icon,
  label,
  pct,
  color,
  predom,
  intensidade,
  interp,
}: {
  icon: string;
  label: string;
  pct: number;
  color: string;
  predom?: string | null;
  intensidade?: string | null;
  interp?: { text: string; color: string } | null;
}) {
  return (
    <View style={styles.presenceRow}>
      <View style={styles.presenceHeader}>
        <Text style={styles.presenceLabel}>
          {icon} {label}
        </Text>
        <Text style={[styles.presencePct, { color }]}>{pct}%</Text>
      </View>
      <View style={styles.barTrack}>
        <View
          style={[
            styles.barFill,
            { width: `${Math.min(pct, 100)}%`, backgroundColor: color },
          ]}
        />
      </View>
      {interp && (
        <Text style={[styles.presenceInterp, { color: interp.color }]}>
          ● {interp.text}
        </Text>
      )}
      {(predom || intensidade) && (
        <Text style={styles.presenceSub}>
          {predom ? `Est. fenológico predominante: ${predom}` : ""}
          {predom && intensidade ? " · " : ""}
          {intensidade ? `Intensidade: ${intensidade}` : ""}
        </Text>
      )}
    </View>
  );
}

function interpFlores(pct: number): { text: string; color: string } {
  if (pct > 50) return { text: "Alta atividade reprodutiva", color: "#27AE60" };
  if (pct >= 20)
    return { text: "Atividade reprodutiva moderada", color: "#D4A017" };
  return { text: "Baixa atividade reprodutiva", color: "#E74C3C" };
}

function interpFrutos(pct: number): { text: string; color: string } | null {
  if (pct > 40)
    return {
      text: "Alta disponibilidade de recursos para fauna",
      color: "#27AE60",
    };
  if (pct > 0)
    return { text: "Disponibilidade moderada de recursos", color: "#D4A017" };
  return null;
}

function DistRow({
  label,
  count,
  pct,
}: {
  label: string;
  count: number;
  pct: number;
}) {
  return (
    <View style={styles.barRow}>
      <Text style={styles.barLabel}>{label}</Text>
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
      <Text style={styles.barPct}>
        {count} ({pct}%)
      </Text>
    </View>
  );
}

export default function PhenologyStatsScreen() {
  const [stats, setStats] = useState<PhenologyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      setStats(await loadPhenologyStats());
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
        <Text style={styles.emptyIcon}>🌸</Text>
        <Text style={styles.emptyText}>
          Nenhum registro de fenologia encontrado.
        </Text>
        <Text style={styles.emptySub}>
          Registre observações no formulário de Fenologia.
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
      {/* Totais */}
      <View style={styles.summaryRow}>
        <View style={styles.chip}>
          <Text style={styles.chipValue}>{stats.total}</Text>
          <Text style={styles.chipLabel}>Registros</Text>
        </View>
        <View style={styles.chip}>
          <Text style={styles.chipValue}>{stats.totalEspecies}</Text>
          <Text style={styles.chipLabel}>Espécies</Text>
        </View>
        <View style={styles.chip}>
          <Text style={styles.chipValue}>{stats.comFloresEFrutos}</Text>
          <Text style={styles.chipLabel}>Flores e Frutos</Text>
        </View>
        <View style={styles.chip}>
          <Text style={styles.chipValue}>{stats.semFloresSemFrutos}</Text>
          <Text style={styles.chipLabel}>Sem flores/frutos</Text>
        </View>
      </View>

      {/* Presença fenológica */}
      <Text style={styles.sectionTitle}>PRESENÇA FENOLÓGICA</Text>
      <View style={styles.presenceCard}>
        <PresenceBar
          icon="🌸"
          label="Indivíduos com flores"
          pct={stats.pctFlores}
          color="#B5338A"
          predom={stats.estagioPredomFlores}
          intensidade={stats.intensidadePredomFlores}
          interp={interpFlores(stats.pctFlores)}
        />
        <View style={styles.divider} />
        <PresenceBar
          icon="🍎"
          label="Indivíduos com frutos"
          pct={stats.pctFrutos}
          color="#E67E22"
          predom={stats.estagioPredomFrutos}
          intensidade={stats.intensidadePredomFrutos}
          interp={interpFrutos(stats.pctFrutos)}
        />
        <View style={styles.divider} />
        <PresenceBar
          icon="🍃"
          label="Indivíduos com folhas"
          pct={stats.pctFolhas}
          color="#27AE60"
        />
      </View>

      {/* Estágios de flores */}
      {stats.floresEstagios.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>ESTÁGIOS DAS FLORES</Text>
          <View style={styles.barsCard}>
            {stats.floresEstagios.map((e) => (
              <DistRow
                key={e.estagio}
                label={e.estagio}
                count={e.count}
                pct={e.pct}
              />
            ))}
          </View>
        </>
      )}

      {/* Estágios de frutos */}
      {stats.frutosEstagios.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>ESTÁGIOS DOS FRUTOS</Text>
          <View style={styles.barsCard}>
            {stats.frutosEstagios.map((e) => (
              <DistRow
                key={e.estagio}
                label={e.estagio}
                count={e.count}
                pct={e.pct}
              />
            ))}
          </View>
        </>
      )}

      {/* Fitossanitário */}
      {stats.fitossanitario.length > 0 && (
        <>
          <Text style={styles.sectionTitle}>ESTADO FITOSSANITÁRIO</Text>
          <View style={styles.barsCard}>
            {stats.fitossanitario.map((f) => (
              <DistRow
                key={f.estado}
                label={f.estado}
                count={f.count}
                pct={f.pct}
              />
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
    marginHorizontal: 3,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  chipValue: { fontSize: 20, fontWeight: "700", color: Colors.primary },
  chipLabel: {
    fontSize: 9,
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
  presenceCard: {
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
  presenceRow: { marginBottom: 4 },
  presenceHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  presenceLabel: { fontSize: 13, fontWeight: "600", color: Colors.textPrimary },
  presencePct: { fontSize: 20, fontWeight: "700" },
  barTrack: {
    height: 7,
    backgroundColor: "#EEEEEE",
    borderRadius: 4,
    overflow: "hidden",
    marginBottom: 4,
  },
  barFill: { height: "100%", borderRadius: 4 },
  presenceInterp: {
    fontSize: 11,
    fontWeight: "600",
    marginTop: 4,
    marginBottom: 2,
  },
  presenceSub: { fontSize: 11, color: Colors.textSecondary },
  divider: { height: 1, backgroundColor: "#F5F5F5", marginVertical: 14 },
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
  barPct: { fontSize: 10, color: Colors.textSecondary },
});
