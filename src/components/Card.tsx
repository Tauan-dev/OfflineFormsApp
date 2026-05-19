import React from "react";
import { View, Text, StyleSheet, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import {
  Colors,
  Gradients,
  Spacing,
  Typography,
  Shadow,
} from "../constants/theme";

interface CardProps {
  title?: string;
  icon?: string;
  subtitle?: string;
  children: React.ReactNode;
  style?: ViewStyle;
  accent?: boolean;
}

export default function Card({
  title,
  icon,
  subtitle,
  children,
  style,
  accent = false,
}: CardProps) {
  const hasHeader = title || icon;
  return (
    <View style={[styles.card, style]}>
      {accent && (
        <LinearGradient
          colors={Gradients.cardAccent}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.accentBar}
        />
      )}
      {hasHeader && (
        <View style={styles.header}>
          {icon && (
            <View style={styles.iconWrap}>
              <Text style={styles.icon}>{icon}</Text>
            </View>
          )}
          <View style={styles.headerText}>
            {title && <Text style={styles.title}>{title}</Text>}
            {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
          </View>
        </View>
      )}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Spacing.borderRadius,
    borderWidth: 0.5,
    borderColor: "rgba(45,106,79,0.09)",
    padding: Spacing.paddingCard,
    overflow: "hidden",
    ...Shadow.card,
  },
  accentBar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
    gap: 12,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.primaryMuted,
    alignItems: "center",
    justifyContent: "center",
  },
  icon: {
    fontSize: 18,
  },
  headerText: {
    flex: 1,
  },
  title: {
    ...Typography.cardTitle,
    color: Colors.primary,
  },
  subtitle: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 1,
    letterSpacing: 0.2,
  },
});
