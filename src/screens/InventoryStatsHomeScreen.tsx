import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { RootStackParamList } from "../navigation/AppNavigator";
import { Colors } from "../constants/theme";

type Nav = NativeStackNavigationProp<RootStackParamList>;

const CARDS = [
  {
    route: "InventoryStats" as keyof RootStackParamList,
    icon: "📊",
    title: "Visão Geral",
    sub: "Resumo do inventário da área",
    desc: "Riqueza de espécies, estado fitossanitário e indicador de saúde da área.",
  },
  {
    route: "InventoryParcela" as keyof RootStackParamList,
    icon: "📍",
    title: "Por Parcela",
    sub: "Análise detalhada por unidade amostral",
    desc: "Condição individual de cada parcela, DAP médio e espécie dominante.",
  },
  {
    route: "PopulationDynamics" as keyof RootStackParamList,
    icon: "🌱",
    title: "Dinâmica do Povoamento",
    sub: "Coortes, recrutamento e mortalidade",
    desc: "Distribuição temporal de plantios, taxa de replantio e espécies mais substituídas.",
  },
];

export default function InventoryStatsHomeScreen() {
  const navigation = useNavigation<Nav>();

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>Inventário Florestal</Text>
      <Text style={styles.headingSub}>
        Selecione o tipo de análise desejada
      </Text>

      {CARDS.map((c) => (
        <TouchableOpacity
          key={c.route}
          style={styles.card}
          onPress={() => navigation.navigate(c.route as any)}
          activeOpacity={0.75}
        >
          <Text style={styles.cardIcon}>{c.icon}</Text>
          <View style={styles.cardBody}>
            <Text style={styles.cardTitle}>{c.title}</Text>
            <Text style={styles.cardSub}>{c.sub}</Text>
            <Text style={styles.cardDesc}>{c.desc}</Text>
          </View>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F5F5F5" },
  content: { padding: 20, paddingBottom: 40 },

  heading: {
    fontSize: 22,
    fontWeight: "800",
    color: Colors.primaryDark,
    marginBottom: 4,
  },
  headingSub: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginBottom: 28,
  },

  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 18,
    marginBottom: 14,
    elevation: 2,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  cardIcon: {
    fontSize: 36,
    marginRight: 16,
  },
  cardBody: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.primaryDark,
    marginBottom: 2,
  },
  cardSub: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginBottom: 6,
  },
  cardDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    lineHeight: 16,
  },
  chevron: {
    fontSize: 28,
    color: Colors.textSecondary,
    marginLeft: 8,
  },
});
