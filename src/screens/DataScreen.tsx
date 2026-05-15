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
import * as XLSX from "xlsx";
import { Colors, Spacing, Typography, Shadow } from "../constants/theme";
import { fileExists, readFileAsBytes, getFileUri } from "../storage/fileManager";

// ── tipos ──────────────────────────────────────────────────────────────────
interface SheetState {
  headers: string[];
  rows: string[][];
  count: number;
  exists: boolean;
}

const EMPTY_SHEET: SheetState = { headers: [], rows: [], count: 0, exists: false };

// ── helpers ────────────────────────────────────────────────────────────────
function readSheet(fileName: string): SheetState {
  if (!fileExists(fileName)) return EMPTY_SHEET;
  const bytes = readFileAsBytes(fileName);
  const wb = XLSX.read(bytes, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const all: string[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
  if (all.length === 0) return { ...EMPTY_SHEET, exists: true };
  const [headers, ...rows] = all;
  return { headers, rows, count: rows.length, exists: true };
}

async function compartilhar(fileName: string, label: string) {
  if (!fileExists(fileName)) {
    Alert.alert("Arquivo não encontrado", `Nenhum dado de ${label} foi salvo ainda.`);
    return;
  }
  const uri = getFileUri(fileName);
  const canShare = await Sharing.isAvailableAsync();
  if (!canShare) {
    Alert.alert("Compartilhamento indisponível", `Caminho do arquivo:\n${uri}`);
    return;
  }
  await Sharing.shareAsync(uri, {
    mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    dialogTitle: `Compartilhar ${label}`,
    UTI: "com.microsoft.excel.xlsx",
  });
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
    <ScrollView horizontal showsHorizontalScrollIndicator>
      <View>
        {/* cabeçalho */}
        <View style={[styles.tableRow, styles.tableHead]}>
          {sheet.headers.map((h, i) => (
            <Text key={i} style={[styles.tableCell, styles.tableCellHead]}>
              {h}
            </Text>
          ))}
        </View>
        {/* linhas */}
        {sheet.rows.map((row, ri) => (
          <View
            key={ri}
            style={[styles.tableRow, ri % 2 === 1 && styles.tableRowAlt]}
          >
            {sheet.headers.map((_, ci) => (
              <Text key={ci} style={styles.tableCell}>
                {row[ci] ?? ""}
              </Text>
            ))}
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

// ── tela principal ─────────────────────────────────────────────────────────
export default function DataScreen() {
  const [dendro, setDendro] = useState<SheetState>(EMPTY_SHEET);
  const [fenol, setFenol] = useState<SheetState>(EMPTY_SHEET);
  const [tab, setTab] = useState<"dendro" | "fenol">("dendro");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    try {
      setDendro(readSheet("dendometria.xlsx"));
      setFenol(readSheet("fenologia.xlsx"));
    } finally {
      setLoading(false);
    }
  }, []);

  // recarrega sempre que a tela ganhar foco
  useFocusEffect(load);

  const onRefresh = () => {
    setRefreshing(true);
    load();
    setRefreshing(false);
  };

  const activeSheet = tab === "dendro" ? dendro : fenol;
  const activeFile = tab === "dendro" ? "dendometria.xlsx" : "fenologia.xlsx";
  const activeLabel = tab === "dendro" ? "Dendometria" : "Fenologia";

  return (
    <ScrollView
      style={styles.root}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* ── abas ── */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, tab === "dendro" && styles.tabActive]}
          onPress={() => setTab("dendro")}
        >
          <Text style={[styles.tabText, tab === "dendro" && styles.tabTextActive]}>
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
          <Text style={[styles.tabText, tab === "fenol" && styles.tabTextActive]}>
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
        <TouchableOpacity
          style={[styles.shareBtn, !activeSheet.exists && styles.shareBtnDisabled]}
          onPress={() => compartilhar(activeFile, activeLabel)}
          disabled={!activeSheet.exists}
        >
          <Text style={styles.shareBtnText}>📤 Compartilhar</Text>
        </TouchableOpacity>
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
        ↻ Puxe para baixo para atualizar · Toque em Compartilhar para enviar o .xlsx
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
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: "hidden",
    marginBottom: 16,
    ...Shadow.small,
  },
  tab: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    gap: 6,
  },
  tabActive: { backgroundColor: Colors.primary },
  tabText: { fontSize: 14, fontWeight: "600", color: Colors.textSecondary },
  tabTextActive: { color: "#fff" },
  badge: {
    backgroundColor: Colors.primarySoft,
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 1,
    marginLeft: 4,
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

  // botão compartilhar
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
  tableRowAlt: { backgroundColor: "#F9FBF9" },
  tableHead: { backgroundColor: Colors.primary },
  tableCell: {
    width: CELL_W,
    paddingHorizontal: 8,
    paddingVertical: 9,
    fontSize: 12,
    color: Colors.textPrimary,
    borderRightWidth: 1,
    borderRightColor: Colors.border,
  },
  tableCellHead: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 11,
    borderRightColor: "rgba(255,255,255,0.2)",
  },

  // vazio
  emptyBox: { alignItems: "center", padding: 32 },
  emptyIcon: { fontSize: 36, marginBottom: 8 },
  emptyText: { ...Typography.caption, textAlign: "center" },

  // rodapé
  hint: { ...Typography.caption, textAlign: "center", marginTop: 16 },
});
