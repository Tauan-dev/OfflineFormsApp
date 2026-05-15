import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Colors } from "../constants/theme";

import HomeScreen from "../screens/HomeScreen";
import Form1Screen from "../screens/Form1Screen";
import Form2Screen from "../screens/Form2Screen";
import DataScreen from "../screens/DataScreen";

export type RootStackParamList = {
  Home: undefined;
  Form1: undefined;
  Form2: undefined;
  Form3: undefined;
  Data: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Home"
        screenOptions={{
          headerStyle: { backgroundColor: Colors.primary },
          headerTintColor: "#fff",
          headerTitleStyle: { fontWeight: "bold", fontSize: 17 },
          headerBackTitle: "Voltar",
        }}
      >
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: "Coleta Verde", headerShown: false }}
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
      </Stack.Navigator>
    </NavigationContainer>
  );
}
