import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
} from "react-native";
import { Colors, Spacing, Typography } from "../constants/theme";

interface SelectFieldProps {
  label: string;
  options: string[];
  value: string;
  onChange: (val: string) => void;
  disabled?: boolean;
}

export default function SelectField({
  label,
  options,
  value,
  onChange,
  disabled = false,
}: SelectFieldProps) {
  return (
    <View style={[styles.container, disabled && styles.disabledContainer]}>
      <Text style={styles.label}>{label}</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.optionsRow}
      >
        {options.map((opt) => {
          const isSelected = value === opt;
          return (
            <TouchableOpacity
              key={opt}
              style={[
                styles.chip,
                isSelected && styles.chipSelected,
                disabled && styles.chipDisabled,
              ]}
              onPress={() => !disabled && onChange(opt)}
              activeOpacity={disabled ? 1 : 0.65}
            >
              <Text
                style={[
                  styles.chipText,
                  isSelected && styles.chipTextSelected,
                  disabled && styles.chipTextDisabled,
                ]}
              >
                {opt}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
  },
  disabledContainer: {
    opacity: 0.45,
  },
  label: {
    ...Typography.label,
  },
  optionsRow: {
    flexDirection: "row",
    gap: 8,
    paddingVertical: 6,
    paddingHorizontal: 2,
  },
  chip: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: Spacing.borderRadiusChip,
    borderWidth: 1,
    borderColor: "rgba(45,106,79,0.18)",
    backgroundColor: Colors.surface,
    shadowColor: "#0D2B1E",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  chipSelected: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 3,
  },
  chipDisabled: {
    backgroundColor: Colors.surfaceAlt,
    borderColor: "rgba(45,106,79,0.08)",
  },
  chipText: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: "500",
    letterSpacing: 0.1,
  },
  chipTextSelected: {
    color: "#FFFFFF",
    fontWeight: "700",
    letterSpacing: 0.2,
  },
  chipTextDisabled: {
    color: Colors.textTertiary,
  },
});
