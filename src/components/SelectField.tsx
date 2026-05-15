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
              activeOpacity={disabled ? 1 : 0.7}
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
    marginBottom: 10,
  },
  disabledContainer: {
    opacity: 0.5,
  },
  label: {
    ...Typography.label,
  },
  optionsRow: {
    flexDirection: "row",
    gap: 8,
    paddingVertical: 4,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  chipSelected: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  chipDisabled: {
    backgroundColor: Colors.background,
    borderColor: Colors.border,
  },
  chipText: {
    fontSize: 14,
    color: Colors.textPrimary,
    fontWeight: "500",
  },
  chipTextSelected: {
    color: Colors.surface,
    fontWeight: "600",
  },
  chipTextDisabled: {
    color: Colors.textSecondary,
  },
});
