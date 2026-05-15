import React from "react";
import { ScrollView, StyleSheet, ViewStyle } from "react-native";
import { Colors, Spacing } from "../constants/theme";

interface FormContainerProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export default function FormContainer({ children, style }: FormContainerProps) {
  return (
    <ScrollView
      style={[styles.scroll, style]}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      {children}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scroll: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    padding: Spacing.paddingScreen,
    gap: Spacing.gapBetweenCards,
    paddingBottom: 130,
  },
});
