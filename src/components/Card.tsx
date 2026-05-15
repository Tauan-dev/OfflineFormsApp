import React from "react";
import { View, Text, StyleSheet, ViewStyle } from "react-native";
import { Colors, Spacing, Typography, Shadow } from "../constants/theme";

interface CardProps {
  title?: string;
  children: React.ReactNode;
  style?: ViewStyle;
}

export default function Card({ title, children, style }: CardProps) {
  return (
    <View style={[styles.card, style]}>
      {title && <Text style={styles.title}>{title}</Text>}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.paddingCard,
    ...Shadow.small,
  },
  title: {
    ...Typography.cardTitle,
    color: Colors.primary,
    marginBottom: 14,
  },
});
