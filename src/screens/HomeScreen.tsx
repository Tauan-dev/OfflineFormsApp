import React from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useNavigation } from "@react-navigation/native";
import { RootStackParamList } from "../navigation/AppNavigator";
import {
  Colors,
  Gradients,
  Shadow,
  Spacing,
  Typography,
} from "../constants/theme";

type HomeNavProp = NativeStackNavigationProp<RootStackParamList, "Home">;

const FORMS = [
  {
    key: "Form1" as const,
    icon: "🌲",
    label: "Dendometria",
    desc: "DAP, alturas, medições estruturais",
    tag: "ESTRUTURAL",
  },
  {
    key: "Form2" as const,
    icon: "🌸",
    label: "Fenologia",
    desc: "Flores, frutos e folhas",
    tag: "FENOLÓGICO",
  },
];

export default function HomeScreen() {
  const navigation = useNavigation<HomeNavProp>();

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header com gradiente diagonal */}
      <LinearGradient
        colors={Gradients.headerDiag}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        {/* Círculos decorativos */}
        <View style={styles.decorCircle1} />
        <View style={styles.decorCircle2} />

        <View style={styles.headerTop}>
          <View style={styles.logoWrap}>
            <Text style={styles.logoIcon}>🌿</Text>
          </View>
          <View style={styles.headerTextWrap}>
            <Text style={styles.appName}>Coleta Verde</Text>
            <Text style={styles.appOrg}>CEPLAC · Sistema de Campo</Text>
          </View>
          <View style={styles.headerBadge}>
            <Text style={styles.headerBadgeText}>v1.0</Text>
          </View>
        </View>

        <View style={styles.headerDivider} />

        <View style={styles.headerBottom}>
          <Text style={styles.headerHint}>MÓDULOS DE COLETA</Text>
          <View style={styles.headerStatus}>
            <View style={styles.statusDot} />
            <Text style={styles.headerStatusText}>Offline Ready</Text>
          </View>
        </View>
      </LinearGradient>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Cards de formulários */}
        {FORMS.map((form) => (
          <TouchableOpacity
            key={form.key}
            style={styles.formCard}
            onPress={() => navigation.navigate(form.key)}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={Gradients.cardAccent}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={styles.formCardAccent}
            />
            <View style={styles.formIconWrap}>
              <Text style={styles.formIcon}>{form.icon}</Text>
            </View>
            <View style={styles.formInfo}>
              <View style={styles.formLabelRow}>
                <Text style={styles.formLabel}>{form.label}</Text>
                <View style={styles.formTag}>
                  <Text style={styles.formTagText}>{form.tag}</Text>
                </View>
              </View>
              <Text style={styles.formDesc}>{form.desc}</Text>
            </View>
            <View style={styles.formArrow}>
              <Text style={styles.formArrowText}>›</Text>
            </View>
          </TouchableOpacity>
        ))}

        {/* Divisor */}
        <View style={styles.sectionDivider}>
          <View style={styles.sectionDividerLine} />
          <Text style={styles.sectionDividerLabel}>DADOS</Text>
          <View style={styles.sectionDividerLine} />
        </View>

        {/* Ver dados */}
        <TouchableOpacity
          style={styles.dataCard}
          onPress={() => navigation.navigate("Data")}
          activeOpacity={0.82}
        >
          <View style={styles.dataIconWrap}>
            <Text style={styles.dataIcon}>📊</Text>
          </View>
          <View style={styles.dataInfo}>
            <Text style={styles.dataLabel}>Ver Dados Salvos</Text>
            <Text style={styles.dataDesc}>
              Visualize e compartilhe os arquivos .csv
            </Text>
          </View>
          <Text style={styles.dataArrow}>›</Text>
        </TouchableOpacity>

        {/* Estatísticas */}
        <TouchableOpacity
          style={[styles.dataCard, styles.statsCard]}
          onPress={() => navigation.navigate("StatsHome")}
          activeOpacity={0.82}
        >
          <View style={[styles.dataIconWrap, styles.statsIconWrap]}>
            <Text style={styles.dataIcon}>📈</Text>
          </View>
          <View style={styles.dataInfo}>
            <Text style={styles.dataLabel}>Estatísticas de Campo</Text>
            <Text style={styles.dataDesc}>
              BI offline — médias, rankings e insights
            </Text>
          </View>
          <Text style={styles.dataArrow}>›</Text>
        </TouchableOpacity>
      </ScrollView>

      <Text style={styles.version}>Desenvolvido por Tauan Neres Silva</Text>
      <Text style={styles.version}>Coleta Verde v1.0.0 · CEPLAC</Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: Colors.background,
  },

  // Header
  header: {
    paddingHorizontal: Spacing.paddingScreen,
    paddingTop: 22,
    paddingBottom: 24,
    overflow: "hidden",
  },
  decorCircle1: {
    position: "absolute",
    width: 180,
    height: 180,
    borderRadius: 90,
    backgroundColor: "rgba(255,255,255,0.05)",
    top: -60,
    right: -40,
  },
  decorCircle2: {
    position: "absolute",
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: "rgba(255,255,255,0.04)",
    bottom: -20,
    left: 30,
  },
  headerTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    marginBottom: 18,
  },
  logoWrap: {
    width: 50,
    height: 50,
    borderRadius: 15,
    backgroundColor: "rgba(255,255,255,0.14)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.2)",
  },
  logoIcon: { fontSize: 26 },
  headerTextWrap: { flex: 1 },
  appName: {
    fontSize: 22,
    fontWeight: "800",
    color: "#FFFFFF",
    letterSpacing: 0.4,
  },
  appOrg: {
    fontSize: 11,
    color: "rgba(255,255,255,0.60)",
    marginTop: 2,
    letterSpacing: 0.5,
  },
  headerBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.13)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.2)",
  },
  headerBadgeText: {
    fontSize: 11,
    fontWeight: "700",
    color: "rgba(255,255,255,0.85)",
    letterSpacing: 0.3,
  },
  headerDivider: {
    height: 1,
    backgroundColor: "rgba(255,255,255,0.12)",
    marginBottom: 14,
  },
  headerBottom: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  headerHint: {
    fontSize: 11,
    color: "rgba(255,255,255,0.55)",
    textTransform: "uppercase",
    letterSpacing: 1.4,
    fontWeight: "700",
  },
  headerStatus: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: "#74C69D",
  },
  headerStatusText: {
    fontSize: 11,
    color: "rgba(255,255,255,0.6)",
    fontWeight: "600",
    letterSpacing: 0.3,
  },

  // Scroll
  scroll: { flex: 1 },
  scrollContent: {
    padding: Spacing.paddingScreen,
    gap: 14,
    paddingBottom: 36,
  },

  // Form cards
  formCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 0.5,
    borderColor: "rgba(45,106,79,0.09)",
    paddingVertical: 18,
    paddingRight: 16,
    paddingLeft: 0,
    gap: 14,
    overflow: "hidden",
    ...Shadow.card,
  },
  formCardAccent: {
    width: 4,
    alignSelf: "stretch",
    borderRadius: 2,
    marginLeft: 0,
    marginRight: 2,
  },
  formIconWrap: {
    width: 52,
    height: 52,
    borderRadius: 14,
    backgroundColor: Colors.primaryMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  formIcon: { fontSize: 26 },
  formInfo: { flex: 1 },
  formLabelRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 4,
  },
  formLabel: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.textPrimary,
  },
  formTag: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 5,
    backgroundColor: Colors.primaryMuted,
  },
  formTagText: {
    fontSize: 9,
    fontWeight: "800",
    color: Colors.primary,
    letterSpacing: 0.8,
    textTransform: "uppercase",
  },
  formDesc: {
    fontSize: 12,
    color: Colors.textTertiary,
    lineHeight: 17,
  },
  formArrow: {
    width: 32,
    height: 32,
    borderRadius: 9,
    backgroundColor: Colors.primaryMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  formArrowText: {
    fontSize: 22,
    lineHeight: 30,
    fontWeight: "300",
    color: Colors.primary,
  },

  // Divisor
  sectionDivider: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginVertical: 2,
  },
  sectionDividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border,
  },
  sectionDividerLabel: {
    ...Typography.caption,
    letterSpacing: 1.4,
    fontWeight: "700",
    textTransform: "uppercase",
    fontSize: 10,
  },

  // Data card
  dataCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surfaceAlt,
    borderRadius: Spacing.borderRadius,
    borderWidth: 0.5,
    borderColor: "rgba(45,106,79,0.09)",
    padding: 16,
    gap: 14,
    ...Shadow.small,
  },
  dataIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Colors.primaryMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  dataIcon: { fontSize: 20 },
  dataInfo: { flex: 1 },
  dataLabel: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.primary,
    marginBottom: 2,
  },
  dataDesc: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  dataArrow: {
    fontSize: 24,
    color: Colors.textTertiary,
    fontWeight: "300",
  },

  statsCard: {
    borderColor: Colors.primarySoft,
    backgroundColor: "#F0FBF4",
  },
  statsIconWrap: {
    backgroundColor: Colors.primaryMuted,
  },

  version: {
    textAlign: "center",
    ...Typography.caption,
    paddingVertical: 10,
    backgroundColor: Colors.background,
    letterSpacing: 0.3,
  },
});
