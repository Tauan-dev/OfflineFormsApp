import React from "react";
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
} from "react-native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { useNavigation } from "@react-navigation/native";
import { RootStackParamList } from "../navigation/AppNavigator";
import Button from "../components/Button";
import { Colors, Spacing, Typography, Shadow } from "../constants/theme";

type HomeNavProp = NativeStackNavigationProp<RootStackParamList, "Home">;

export default function HomeScreen() {
  const navigation = useNavigation<HomeNavProp>();

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoCircle}>
            <Text style={styles.logoIcon}>🌿</Text>
          </View>
          <Text style={styles.appName}>Coleta Verde</Text>
          <Text style={styles.appSubtitle}>CEPLAC — Formulários de Campo</Text>
        </View>

        {/* Formulários */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Selecione o formulário</Text>

          <View style={styles.card}>
            <Button
              label="Dendometria"
              onPress={() => navigation.navigate("Form1")}
            />
            <View style={styles.divider} />
            <Button
              label="Fenologia"
              onPress={() => navigation.navigate("Form2")}
              variant="secondary"
            />
          </View>
        </View>

        {/* Dados salvos */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.dataBtn}
            onPress={() => navigation.navigate("Data")}
          >
            <Text style={styles.dataBtnIcon}>📊</Text>
            <View>
              <Text style={styles.dataBtnTitle}>Ver Dados Salvos</Text>
              <Text style={styles.dataBtnSub}>
                Visualize e compartilhe os .xlsx
              </Text>
            </View>
            <Text style={styles.dataBtnArrow}>›</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.version}>v1.0.0</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
    paddingHorizontal: Spacing.paddingScreen,
    paddingTop: 32,
    justifyContent: "space-between",
    paddingBottom: 24,
  },
  header: {
    alignItems: "center",
    marginBottom: 40,
  },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.primary,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
    ...Shadow.small,
  },
  logoIcon: {
    fontSize: 38,
  },
  appName: {
    fontSize: 28,
    fontWeight: "bold",
    color: Colors.primary,
    marginBottom: 6,
  },
  appSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: "center",
  },
  section: {
    flex: 1,
    justifyContent: "center",
  },
  sectionTitle: {
    ...Typography.label,
    textAlign: "center",
    marginBottom: 16,
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.paddingCard,
    ...Shadow.small,
  },
  divider: {
    height: 10,
  },
  dataBtn: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: 16,
    gap: 12,
    ...Shadow.small,
  },
  dataBtnIcon: { fontSize: 28 },
  dataBtnTitle: { fontSize: 15, fontWeight: "700", color: Colors.primary },
  dataBtnSub: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  dataBtnArrow: {
    fontSize: 24,
    color: Colors.textSecondary,
    marginLeft: "auto",
  },
  version: {
    textAlign: "center",
    ...Typography.caption,
    marginTop: 8,
  },
});
