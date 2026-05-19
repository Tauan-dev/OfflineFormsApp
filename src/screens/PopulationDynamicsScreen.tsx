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
import { loadDendroRows } from "../analytics/dataLoader";
import {
  calcPopulationDynamics,
  PopulationDynamicsStats,
  EspecieSucesso,
} from "../analytics/populationDynamicsAnalytics";

// ── Chip de resumo ────────────────────────────────────────────────────────────
function Chip({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <View style={styles.chip}>
      <Text style={[styles.chipValue, color ? { color } : {}]}>{value}</Text>
      <Text style={styles.chipLabel}>{label}</Text>
    </View>
  );
}

// ── Barra horizontal simples ──────────────────────────────────────────────────
function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <View style={styles.barTrack}>
      <View
        style={[
          styles.barFill,
          { width: `${Math.max(pct, 2)}%` as any, backgroundColor: color },
        ]}
      />
    </View>
  );
}

export default function PopulationDynamicsScreen() {
  const [stats, setStats] = useState<PopulationDynamicsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetch = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const rows = await loadDendroRows();
      setStats(calcPopulationDynamics(rows));
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
        <Text style={styles.loadingText}>Calculando dinâmica…</Text>
      </View>
    );
  }

  if (!stats || stats.totalArvores === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyIcon}>🌱</Text>
        <Text style={styles.emptyText}>Sem dados de dendometria.</Text>
        <Text style={styles.emptySub}>
          Registre árvores para analisar a dinâmica do povoamento.
        </Text>
      </View>
    );
  }

  const maxCoorte = Math.max(...stats.coortes.map((c) => c.total), 1);
  const maxReplAno = Math.max(...stats.replantiosPorAno.map((r) => r.count), 1);
  const maxReplParcela = Math.max(
    ...stats.replantiosPorParcela.map((p) => p.replantios),
    1,
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
      {/* ── Chips de resumo ────────────────────────────────────────────── */}
      <View style={styles.chipRow}>
        <Chip label="Árvores" value={String(stats.totalArvores)} />
        <Chip
          label="Replantios"
          value={String(stats.totalReplantios)}
          color={stats.totalReplantios > 0 ? "#E67E22" : Colors.textPrimary}
        />
        <Chip
          label="Taxa"
          value={`${stats.taxaReplantioGlobal}%`}
          color={
            stats.taxaReplantioGlobal > 25
              ? "#E74C3C"
              : stats.taxaReplantioGlobal > 10
                ? "#D4A017"
                : "#27AE60"
          }
        />
        <Chip label="Coortes" value={String(stats.totalCoortes)} />
      </View>

      {/* ── Interpretação automática ────────────────────────────────────── */}
      <View
        style={[
          styles.card,
          { borderLeftWidth: 3, borderLeftColor: stats.interpretacaoColor },
        ]}
      >
        <Text style={styles.cardLabel}>Diagnóstico do Povoamento</Text>
        <Text style={[styles.interpText, { color: stats.interpretacaoColor }]}>
          {stats.interpretacao}
        </Text>
      </View>

      {/* ── Coorte dominante ────────────────────────────────────────────── */}
      {stats.coortesDominante && (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Coorte Dominante</Text>
          <Text style={styles.bigValue}>{stats.coortesDominante}</Text>
          <Text style={styles.cardSub}>
            {stats.amplitudeTemporal !== null
              ? `Amplitude temporal: ${stats.amplitudeTemporal} anos entre o primeiro e último plantio`
              : `${stats.totalCoortes} coorte${stats.totalCoortes > 1 ? "s" : ""} registrada${stats.totalCoortes > 1 ? "s" : ""}`}
          </Text>
        </View>
      )}

      {/* ── Distribuição de coortes ─────────────────────────────────────── */}
      {stats.coortes.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>
            Distribuição por Coorte (Ano de Plantio)
          </Text>
          {stats.coortes.map((c) => (
            <View key={c.ano} style={styles.barRow}>
              <Text style={styles.barLabel}>{c.ano}</Text>
              <View style={styles.barArea}>
                <Bar pct={(c.total / maxCoorte) * 100} color={Colors.primary} />
              </View>
              <Text style={styles.barCount}>{c.total}</Text>
              {c.replantios > 0 && (
                <Text style={[styles.barTag, { color: "#E67E22" }]}>
                  {c.taxaReplantio}% repl.
                </Text>
              )}
            </View>
          ))}
        </View>
      )}

      {/* ── Replantio por ano ───────────────────────────────────────────── */}
      {stats.replantiosPorAno.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Replantios por Ano</Text>
          <Text style={styles.cardSub}>
            Recrutamento de substituição ao longo do tempo
          </Text>
          {stats.replantiosPorAno.map((r) => (
            <View key={r.ano} style={styles.barRow}>
              <Text style={styles.barLabel}>{r.ano}</Text>
              <View style={styles.barArea}>
                <Bar pct={(r.count / maxReplAno) * 100} color="#E67E22" />
              </View>
              <Text style={styles.barCount}>{r.count}</Text>
            </View>
          ))}
        </View>
      )}

      {/* ── Espécies mais replantadas ────────────────────────────────────── */}
      {stats.especiesReplantadas.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Espécies Mais Replantadas</Text>
          {stats.especiesReplantadas.map((e, i) => (
            <View key={e.nome} style={styles.especieRow}>
              <Text style={styles.especieRank}>{i + 1}</Text>
              <View style={{ flex: 1 }}>
                <View style={styles.especieHeader}>
                  <Text style={styles.especieNome}>{e.nome}</Text>
                  <Text style={styles.especiePct}>{e.pct}%</Text>
                </View>
                <Bar pct={e.pct} color="#8E44AD" />
              </View>
            </View>
          ))}
        </View>
      )}

      {/* ── Replantio por parcela ────────────────────────────────────────── */}
      <View style={styles.card}>
        <Text style={styles.cardLabel}>Replantio por Parcela</Text>
        <Text style={styles.cardSub}>
          Parcelas com maior pressão de mortalidade
        </Text>
        {stats.replantiosPorParcela.map((p) => (
          <View key={p.parcela} style={styles.parcelaRow}>
            <View style={styles.parcelaInfo}>
              <Text style={styles.parcelaNome}>Parcela {p.parcela}</Text>
              <Text style={styles.parcelaDetalhe}>
                {p.replantios}/{p.totalArvores} árvores
              </Text>
            </View>
            <View style={styles.parcelaBarArea}>
              <Bar
                pct={
                  maxReplParcela > 0 ? (p.replantios / maxReplParcela) * 100 : 0
                }
                color={
                  p.taxaReplantio > 25
                    ? "#E74C3C"
                    : p.taxaReplantio > 10
                      ? "#E67E22"
                      : "#27AE60"
                }
              />
            </View>
            <Text
              style={[
                styles.parcelaTaxa,
                {
                  color:
                    p.taxaReplantio > 25
                      ? "#E74C3C"
                      : p.taxaReplantio > 10
                        ? "#E67E22"
                        : "#27AE60",
                },
              ]}
            >
              {p.taxaReplantio}%
            </Text>
          </View>
        ))}
      </View>

      {/* ── Classificação do Povoamento ───────────────────────────────── */}
      <View
        style={[
          styles.card,
          styles.classCard,
          { borderColor: stats.classificacaoPovoamento.cor },
        ]}
      >
        <Text style={styles.cardLabel}>Classificação do Povoamento</Text>
        <Text
          style={[
            styles.classLabel,
            { color: stats.classificacaoPovoamento.cor },
          ]}
        >
          {stats.classificacaoPovoamento.classificacao}
        </Text>
        <Text style={styles.classDesc}>
          {stats.classificacaoPovoamento.descricao}
        </Text>
      </View>

      {/* ── Índice de Sucesso por Espécie ──────────────────────────────── */}
      {stats.especiesSucesso.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Índice de Sucesso por Espécie</Text>
          <Text style={styles.cardSub}>
            Adaptabilidade ao sítio — piores resultados primeiro
          </Text>
          {stats.especiesSucesso.slice(0, 6).map((e) => {
            const cor =
              e.nivel === "alta"
                ? "#27AE60"
                : e.nivel === "moderada"
                  ? "#D4A017"
                  : "#E74C3C";
            const nivelLabel =
              e.nivel === "alta"
                ? "Alta adaptação"
                : e.nivel === "moderada"
                  ? "Adaptação moderada"
                  : "Baixa adaptação";
            return (
              <View key={e.nome} style={styles.sucessoRow}>
                <View style={styles.sucessoInfo}>
                  <Text style={styles.sucessoNome}>{e.nome}</Text>
                  <Text style={[styles.sucessoNivel, { color: cor }]}>
                    {nivelLabel}
                  </Text>
                </View>
                <View style={styles.sucessoBarArea}>
                  <Bar pct={e.indiceSucesso * 100} color={cor} />
                </View>
                <Text style={[styles.sucessoVal, { color: cor }]}>
                  {(e.indiceSucesso * 100).toFixed(0)}%
                </Text>
              </View>
            );
          })}
        </View>
      )}

      {/* ── Laudo Automático ──────────────────────────────────────────────── */}
      {stats.textoAutomatico.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Laudo Automático</Text>
          <Text style={styles.laudoText}>{stats.textoAutomatico}</Text>
        </View>
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

  // Chips
  chipRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 16,
    gap: 8,
  },
  chip: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
  },
  chipValue: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.primaryDark,
  },
  chipLabel: {
    fontSize: 9,
    color: Colors.textSecondary,
    marginTop: 2,
    textAlign: "center",
  },

  // Card
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 18,
    marginBottom: 14,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
  },
  cardLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: Colors.textSecondary,
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  cardSub: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: 12,
    marginTop: -6,
  },

  // Interpretação
  interpText: {
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "500",
  },

  // Valor grande
  bigValue: {
    fontSize: 42,
    fontWeight: "800",
    color: Colors.primaryDark,
    lineHeight: 48,
    marginBottom: 6,
  },

  // Barras
  barRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 10,
  },
  barLabel: {
    width: 52,
    fontSize: 11,
    color: Colors.textPrimary,
    fontWeight: "600",
  },
  barArea: { flex: 1, marginHorizontal: 8 },
  barCount: {
    width: 26,
    fontSize: 11,
    color: Colors.textSecondary,
    textAlign: "right",
    fontWeight: "600",
  },
  barTag: {
    fontSize: 9,
    fontWeight: "700",
    marginLeft: 6,
    width: 46,
    textAlign: "right",
  },
  barTrack: {
    height: 7,
    borderRadius: 4,
    backgroundColor: "#EEEEEE",
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    borderRadius: 4,
  },

  // Espécies replantadas
  especieRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 12,
    gap: 10,
  },
  especieRank: {
    fontSize: 13,
    fontWeight: "800",
    color: Colors.primaryDark,
    width: 16,
    marginTop: 2,
  },
  especieHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 5,
  },
  especieNome: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.textPrimary,
    flex: 1,
  },
  especiePct: {
    fontSize: 12,
    fontWeight: "700",
    color: "#8E44AD",
    marginLeft: 8,
  },

  // Parcelas
  parcelaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
    gap: 8,
  },
  parcelaInfo: { width: 90 },
  parcelaNome: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.textPrimary,
  },
  parcelaDetalhe: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  parcelaBarArea: { flex: 1 },
  parcelaTaxa: {
    fontSize: 12,
    fontWeight: "700",
    width: 34,
    textAlign: "right",
  },

  // Classificação do Povoamento
  classCard: {
    borderWidth: 1.5,
    borderColor: "transparent",
  },
  classLabel: {
    fontSize: 28,
    fontWeight: "800",
    marginBottom: 6,
    lineHeight: 34,
  },
  classDesc: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
  },

  // Índice de sucesso
  sucessoRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
    gap: 8,
  },
  sucessoInfo: { width: 110 },
  sucessoNome: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.textPrimary,
  },
  sucessoNivel: {
    fontSize: 10,
    fontWeight: "500",
    marginTop: 1,
  },
  sucessoBarArea: { flex: 1 },
  sucessoVal: {
    fontSize: 12,
    fontWeight: "700",
    width: 34,
    textAlign: "right",
  },

  // Laudo automático
  laudoText: {
    fontSize: 13,
    color: Colors.textPrimary,
    lineHeight: 22,
  },
});
