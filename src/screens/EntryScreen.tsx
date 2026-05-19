import React from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Dimensions,
  Image,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useNavigation } from "@react-navigation/native";
import { RootStackParamList } from "../navigation/AppNavigator";

type Nav = NativeStackNavigationProp<RootStackParamList>;

const { height } = Dimensions.get("window");

export default function EntryScreen() {
  const navigation = useNavigation<Nav>();

  return (
    <View style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor="#F7FAF7" />

      {/* Fundo — gradiente verde muito suave, quase branco */}
      <LinearGradient
        colors={["#EEF6EE", "#F7FAF7", "#FFFFFF"]}
        start={{ x: 0.3, y: 0 }}
        end={{ x: 0.7, y: 1 }}
        style={StyleSheet.absoluteFill}
      />

      {/* Círculo decorativo de fundo — sutil */}
      <View style={styles.bgCircle1} />
      <View style={styles.bgCircle2} />

      {/* ── Área principal ──────────────────────────────────────────────── */}
      <View style={styles.body}>
        {/* Label institucional */}
        <Text style={styles.orgLabel}>CEPLAC · Sistema de Campo</Text>

        {/* Logo */}
        <Image
          source={require("../../assets/coletaverde.png")}
          style={styles.logoImage}
          resizeMode="contain"
        />

        {/* Subtítulo */}
        <Text style={styles.subtitle}>
          Coleta e monitoramento{"\n"}ambiental em campo
        </Text>

        {/* Linha decorativa */}
        <View style={styles.divider} />

        {/* Features resumidas */}
        <View style={styles.featureRow}>
          <Feature label="Dendometria" />
          <View style={styles.featureSep} />
          <Feature label="Fenologia" />
          <View style={styles.featureSep} />
          <Feature label="Inventário" />
        </View>
      </View>

      {/* ── Rodapé com CTA ──────────────────────────────────────────────── */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.ctaButton}
          onPress={() => navigation.navigate("Home")}
          activeOpacity={0.88}
        >
          <LinearGradient
            colors={["#2D6A4F", "#1B4332"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.ctaGradient}
          >
            <Text style={styles.ctaText}>Iniciar coleta</Text>
            <Text style={styles.ctaArrow}>→</Text>
          </LinearGradient>
        </TouchableOpacity>

        <Text style={styles.footerNote}>Desenvolvido por Tauan Neres Silva</Text>
      </View>
    </View>
  );
}

function Feature({ label }: { label: string }) {
  return <Text style={styles.featureLabel}>{label}</Text>;
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#F7FAF7",
  },

  // Círculos decorativos de fundo
  bgCircle1: {
    position: "absolute",
    width: 360,
    height: 360,
    borderRadius: 180,
    backgroundColor: "#2D6A4F",
    opacity: 0.04,
    top: -100,
    right: -80,
  },
  bgCircle2: {
    position: "absolute",
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: "#52B788",
    opacity: 0.06,
    bottom: height * 0.18,
    left: -60,
  },

  // ── Corpo central ─────────────────────────────────────────────────────────
  body: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
    paddingTop: 40,
  },

  orgLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: "#4D7260",
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 48,
    opacity: 0.7,
  },

  // ── Logo ──────────────────────────────────────────────────────────────────
  logoImage: {
    width: 400,
    height: 330,
    marginBottom: 28,
  },

  // ── Subtítulo ─────────────────────────────────────────────────────────────
  subtitle: {
    fontSize: 15,
    color: "#4D7260",
    textAlign: "center",
    lineHeight: 23,
    fontWeight: "400",
    marginBottom: 36,
    opacity: 0.85,
  },

  divider: {
    width: 40,
    height: 2,
    backgroundColor: "#2D6A4F",
    borderRadius: 1,
    opacity: 0.25,
    marginBottom: 28,
  },

  // ── Features ─────────────────────────────────────────────────────────────
  featureRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },

  featureLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: "#4D7260",
    letterSpacing: 0.4,
    opacity: 0.7,
  },

  featureSep: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: "#2D6A4F",
    opacity: 0.3,
  },

  // ── Rodapé ────────────────────────────────────────────────────────────────
  footer: {
    paddingHorizontal: 28,
    paddingBottom: 44,
    alignItems: "center",
  },

  ctaButton: {
    width: "100%",
    borderRadius: 16,
    overflow: "hidden",
    marginBottom: 14,
    shadowColor: "#1B4332",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.22,
    shadowRadius: 16,
    elevation: 6,
  },

  ctaGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 18,
    gap: 10,
  },

  ctaText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#FFFFFF",
    letterSpacing: 0.3,
  },

  ctaArrow: {
    fontSize: 18,
    color: "rgba(255,255,255,0.75)",
    fontWeight: "300",
  },

  footerNote: {
    fontSize: 11,
    color: "#4D7260",
    opacity: 0.55,
    letterSpacing: 0.2,
  },
});
