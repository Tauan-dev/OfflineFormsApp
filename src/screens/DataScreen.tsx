import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import * as Sharing from "expo-sharing";
import { Colors, Spacing, Typography, Shadow } from "../constants/theme";
import {
  fileExists,
  readFileAsText,
  deleteFile,
  getShareUri,
} from "../storage/fileManager";
import { parseCsv } from "../services/excelService";

// ── tipos ──────────────────────────────────────────────────────────────────
interface SheetState {
  headers: string[];
  rows: string[][];
  count: number;
  exists: boolean;
}

const EMPTY_SHEET: SheetState = {
  headers: [],
  rows: [],
  count: 0,
  exists: false,
};

// ── helpers ────────────────────────────────────────────────────────────────
async function readSheet(fileName: string): Promise<SheetState> {
  if (!(await fileExists(fileName))) return EMPTY_SHEET;
  const text = await readFileAsText(fileName);
  const all = parseCsv(text);
  if (all.length === 0) return { ...EMPTY_SHEET, exists: true };
  const [headers, ...rows] = all;
  return { headers, rows, count: rows.length, exists: true };
}

async function compartilhar(fileName: string, label: string) {
  if (!(await fileExists(fileName))) {
    Alert.alert(
      "Arquivo não encontrado",
      `Nenhum dado de ${label} foi salvo ainda.`,
    );
    return;
  }
  const uri = await getShareUri(fileName);
  const canShare = await Sharing.isAvailableAsync();
  if (!canShare) {
    Alert.alert("Compartilhamento indisponível", `Caminho do arquivo:\n${uri}`);
    return;
  }
  try {
    await Sharing.shareAsync(uri, {
      mimeType: "text/csv",
      dialogTitle: `Compartilhar ${label}`,
      UTI: "public.comma-separated-values-text",
    });
  } catch (e: any) {
    Alert.alert("Erro ao compartilhar", e?.message ?? String(e));
  }
}

// ── componente de tabela ───────────────────────────────────────────────────
function DataTable({ sheet }: { sheet: SheetState }) {
  if (!sheet.exists) {
    return (
      <View style={styles.emptyBox}>
        <Text style={styles.emptyIcon}>📭</Text>
        <Text style={styles.emptyText}>Nenhum dado salvo ainda</Text>
      </View>
    );
  }
  if (sheet.rows.length === 0) {
    return (
      <View style={styles.emptyBox}>
        <Text style={styles.emptyIcon}>📋</Text>
        <Text style={styles.emptyText}>Arquivo existe mas está vazio</Text>
      </View>
    );
  }

  return (
    <View>
      <ScrollView horizontal showsHorizontalScrollIndicator persistentScrollbar>
        <View>
          {/* ── cabeçalho ── */}
          <View style={[styles.tableRow, styles.tableHead]}>
            {/* coluna # */}
            <View style={[styles.tableCell, styles.tableCellNumHead]}>
              <Text style={[styles.tableCellHeadText, { textAlign: "center" }]}>
                #
              </Text>
            </View>
            {sheet.headers.map((h, i) => (
              <View key={i} style={[styles.tableCell, styles.tableCellHead]}>
                <Text style={styles.tableCellHeadText} numberOfLines={2}>
                  {h}
                </Text>
              </View>
            ))}
          </View>

          {/* ── linhas de dados ── */}
          {sheet.rows.map((row, ri) => (
            <View
              key={ri}
              style={[
                styles.tableRow,
                ri % 2 === 0 ? styles.tableRowEven : styles.tableRowOdd,
              ]}
            >
              {/* número da linha */}
              <View style={[styles.tableCell, styles.tableCellNum]}>
                <Text style={styles.tableCellNumText}>{ri + 1}</Text>
              </View>
              {sheet.headers.map((_, ci) => (
                <View key={ci} style={styles.tableCell}>
                  <Text style={styles.tableCellText} numberOfLines={2}>
                    {row[ci] ?? "-"}
                  </Text>
                </View>
              ))}
            </View>
          ))}
        </View>
      </ScrollView>

      {/* ── rodapé com contagem ── */}
      <View style={styles.tableFooter}>
        <Text style={styles.tableFooterText}>
          {sheet.count} registro{sheet.count !== 1 ? "s" : ""} encontrado
          {sheet.count !== 1 ? "s" : ""}
        </Text>
      </View>
    </View>
  );
}

// ── tela principal ─────────────────────────────────────────────────────────
export default function DataScreen() {
  const [dendro, setDendro] = useState<SheetState>(EMPTY_SHEET);
  const [fenol, setFenol] = useState<SheetState>(EMPTY_SHEET);
  const [tab, setTab] = useState<"dendro" | "fenol">("dendro");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [d, f] = await Promise.all([
        readSheet("dendometria.csv"),
        readSheet("fenologia.csv"),
      ]);
      setDendro(d);
      setFenol(f);
    } finally {
      setLoading(false);
    }
  }, []);

  // recarrega sempre que a tela ganhar foco
  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const activeSheet = tab === "dendro" ? dendro : fenol;
  const activeFile = tab === "dendro" ? "dendometria.csv" : "fenologia.csv";
  const activeLabel = tab === "dendro" ? "Dendometria" : "Fenologia";

  function handleLimpar() {
    Alert.alert(
      `Limpar ${activeLabel}`,
      `Isso apagará TODOS os registros de ${activeLabel} permanentemente. Deseja continuar?`,
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Apagar",
          style: "destructive",
          onPress: async () => {
            await deleteFile(activeFile);
            load();
          },
        },
      ],
    );
  }

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* ── abas ── */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, tab === "dendro" && styles.tabActive]}
          onPress={() => setTab("dendro")}
        >
          <Text
            style={[styles.tabText, tab === "dendro" && styles.tabTextActive]}
          >
            🌲 Dendometria
          </Text>
          {dendro.exists && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{dendro.count}</Text>
            </View>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.tab, tab === "fenol" && styles.tabActive]}
          onPress={() => setTab("fenol")}
        >
          <Text
            style={[styles.tabText, tab === "fenol" && styles.tabTextActive]}
          >
            🌸 Fenologia
          </Text>
          {fenol.exists && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{fenol.count}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {/* ── info + botão compartilhar ── */}
      <View style={styles.infoRow}>
        <View>
          <Text style={styles.infoTitle}>{activeLabel}</Text>
          <Text style={styles.infoSub}>
            {activeSheet.exists
              ? `${activeSheet.count} registro${activeSheet.count !== 1 ? "s" : ""} salvo${activeSheet.count !== 1 ? "s" : ""}`
              : "Arquivo não criado ainda"}
          </Text>
        </View>
        <View style={styles.btnGroup}>
          <TouchableOpacity
            style={[
              styles.clearBtn,
              !activeSheet.exists && styles.shareBtnDisabled,
            ]}
            onPress={handleLimpar}
            disabled={!activeSheet.exists}
          >
            <Text style={styles.clearBtnText}>🗑️</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.shareBtn,
              !activeSheet.exists && styles.shareBtnDisabled,
            ]}
            onPress={() => compartilhar(activeFile, activeLabel)}
            disabled={!activeSheet.exists}
          >
            <Text style={styles.shareBtnText}>📤 Compartilhar</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* ── tabela ── */}
      <View style={styles.tableCard}>
        {loading ? (
          <ActivityIndicator color={Colors.primary} style={{ padding: 24 }} />
        ) : (
          <DataTable sheet={activeSheet} />
        )}
      </View>

      <Text style={styles.hint}>
        ↻ Puxe para baixo para atualizar · Toque em Compartilhar para enviar o
        .csv
      </Text>
    </ScrollView>
  );
}

// ── estilos ────────────────────────────────────────────────────────────────
const CELL_W = 110;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: Colors.background },
  content: { padding: Spacing.paddingScreen, paddingBottom: 40 },

  // abas
  tabs: {
    flexDirection: "row",
    backgroundColor: Colors.surfaceAlt,
    borderRadius: Spacing.borderRadius,
    borderWidth: 0.5,
    borderColor: "rgba(45,106,79,0.12)",
    overflow: "hidden",
    marginBottom: 16,
    padding: 4,
    gap: 4,
    ...Shadow.small,
  },
  tab: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 11,
    gap: 6,
    borderRadius: 12,
  },
  tabActive: {
    backgroundColor: Colors.surface,
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 2,
  },
  tabText: { fontSize: 14, fontWeight: "600", color: Colors.textTertiary },
  tabTextActive: { color: Colors.primary, fontWeight: "700" },
  badge: {
    backgroundColor: Colors.primaryMuted,
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 1,
    marginLeft: 2,
  },
  badgeText: { fontSize: 11, fontWeight: "700", color: Colors.primary },

  // info
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  infoTitle: { ...Typography.cardTitle, marginBottom: 2 },
  infoSub: { ...Typography.caption },

  // botões da infoRow
  btnGroup: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  clearBtn: {
    backgroundColor: Colors.errorSoft,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: Spacing.borderRadiusInput,
    ...Shadow.small,
  },
  clearBtnText: { fontSize: 16 },
  shareBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: Spacing.borderRadiusInput,
    ...Shadow.small,
  },
  shareBtnDisabled: { backgroundColor: Colors.border },
  shareBtnText: { color: "#fff", fontWeight: "700", fontSize: 13 },

  // tabela
  tableCard: {
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: "hidden",
    ...Shadow.small,
  },
  tableRow: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tableRowEven: { backgroundColor: Colors.surface },
  tableRowOdd: { backgroundColor: "#F2F7F4" },
  tableHead: {
    backgroundColor: Colors.primary,
    borderBottomWidth: 2,
    borderBottomColor: "rgba(0,0,0,0.15)",
  },
  tableCell: {
    width: CELL_W,
    minHeight: 40,
    paddingHorizontal: 10,
    paddingVertical: 8,
    justifyContent: "center",
    borderRightWidth: 1,
    borderRightColor: Colors.border,
  },
  tableCellHead: {
    backgroundColor: "transparent",
    borderRightColor: "rgba(255,255,255,0.2)",
    justifyContent: "center",
  },
  tableCellHeadText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 11,
    textAlign: "center",
    letterSpacing: 0.3,
    textTransform: "uppercase",
  },
  tableCellText: {
    fontSize: 12,
    color: Colors.textPrimary,
    textAlign: "center",
  },
  // coluna de número (#)
  tableCellNum: {
    width: 36,
    backgroundColor: "#EEF5F1",
    borderRightColor: Colors.border,
    justifyContent: "center",
  },
  tableCellNumHead: {
    width: 36,
    borderRightColor: "rgba(255,255,255,0.2)",
    justifyContent: "center",
  },
  tableCellNumText: {
    fontSize: 11,
    color: Colors.textTertiary,
    fontWeight: "600",
    textAlign: "center",
  },
  // rodapé da tabela
  tableFooter: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: "#F7FAF8",
    alignItems: "flex-end",
  },
  tableFooterText: {
    fontSize: 11,
    color: Colors.textTertiary,
    fontWeight: "600",
  },

  // vazio
  emptyBox: { alignItems: "center", padding: 32 },
  emptyIcon: { fontSize: 36, marginBottom: 8 },
  emptyText: { ...Typography.caption, textAlign: "center" },

  // rodapé
  hint: { ...Typography.caption, textAlign: "center", marginTop: 16 },
});
