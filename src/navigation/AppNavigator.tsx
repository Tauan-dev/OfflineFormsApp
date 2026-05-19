import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Colors } from "../constants/theme";

import HomeScreen from "../screens/HomeScreen";
import Form1Screen from "../screens/Form1Screen";
import Form2Screen from "../screens/Form2Screen";
import DataScreen from "../screens/DataScreen";
import StatsHomeScreen from "../screens/StatsHomeScreen";
import DendrometryStatsScreen from "../screens/DendrometryStatsScreen";
import PhenologyStatsScreen from "../screens/PhenologyStatsScreen";
import InventoryStatsScreen from "../screens/InventoryStatsScreen";
import InventoryStatsHomeScreen from "../screens/InventoryStatsHomeScreen";
import InventoryParcelaScreen from "../screens/InventoryParcelaScreen";
import GeneralStatsScreen from "../screens/GeneralStatsScreen";
import PopulationDynamicsScreen from "../screens/PopulationDynamicsScreen";

export type RootStackParamList = {
  Home: undefined;
  Form1: undefined;
  Form2: undefined;
  Form3: undefined;
  Data: undefined;
  StatsHome: undefined;
  DendrometryStats: undefined;
  PhenologyStats: undefined;
  InventoryStats: undefined;
  InventoryStatsHome: undefined;
  InventoryParcela: undefined;
  GeneralStats: undefined;
  PopulationDynamics: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerStyle: { backgroundColor: Colors.primaryDark },
          headerTintColor: "#FFFFFF",
          headerTitleStyle: {
            fontWeight: "700",
            fontSize: 17,
          },
          headerShadowVisible: false,
          headerBackTitle: "Voltar",
          contentStyle: { backgroundColor: Colors.background },
        }}
      >
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Form1"
          component={Form1Screen}
          options={{ title: "Dendometria" }}
        />
        <Stack.Screen
          name="Form2"
          component={Form2Screen}
          options={{ title: "Fenologia" }}
        />
        <Stack.Screen
          name="Data"
          component={DataScreen}
          options={{ title: "Dados Salvos" }}
        />
        <Stack.Screen
          name="StatsHome"
          component={StatsHomeScreen}
          options={{ title: "Análises" }}
        />
        <Stack.Screen
          name="DendrometryStats"
          component={DendrometryStatsScreen}
          options={{ title: "🌳 Dendometria" }}
        />
        <Stack.Screen
          name="PhenologyStats"
          component={PhenologyStatsScreen}
          options={{ title: "🌸 Fenologia" }}
        />
        <Stack.Screen
          name="InventoryStats"
          component={InventoryStatsScreen}
          options={{ title: "🌿 Visão Geral" }}
        />
        <Stack.Screen
          name="InventoryStatsHome"
          component={InventoryStatsHomeScreen}
          options={{ title: "🌿 Inventário" }}
        />
        <Stack.Screen
          name="InventoryParcela"
          component={InventoryParcelaScreen}
          options={{ title: "📍 Análise por Parcela" }}
        />
        <Stack.Screen
          name="PopulationDynamics"
          component={PopulationDynamicsScreen}
          options={{ title: "🌱 Dinâmica do Povoamento" }}
        />
        <Stack.Screen
          name="GeneralStats"
          component={GeneralStatsScreen}
          options={{ title: "📊 Visão Geral" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
