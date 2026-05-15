/**
 * DateInput — campo de data com máscara automática DD/MM/AAAA.
 * Ao digitar apenas números, as barras são inseridas automaticamente.
 */
import React from "react";
import { View, Text, TextInput, StyleSheet } from "react-native";
import { Colors, Spacing, Typography } from "../constants/theme";

interface DateInputProps {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
  error?: string;
}

/** Aplica máscara DD/MM/AAAA removendo tudo que não for dígito */
function applyMask(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 2) return digits;
  if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
}

export default function DateInput({
  label,
  value,
  onChangeText,
  placeholder = "DD/MM/AAAA",
  error,
}: DateInputProps) {
  const handleChange = (text: string) => {
    onChangeText(applyMask(text));
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, !!error && styles.inputError]}
        value={value}
        onChangeText={handleChange}
        placeholder={placeholder}
        placeholderTextColor={Colors.textSecondary}
        keyboardType="numeric"
        maxLength={10}
      />
      {!!error && <Text style={styles.errorText}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: 10 },
  label: { ...Typography.label },
  input: {
    height: Spacing.inputHeight,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Spacing.borderRadiusInput,
    paddingHorizontal: 12,
    fontSize: 16,
    color: Colors.textPrimary,
    backgroundColor: Colors.surface,
    letterSpacing: 1,
  },
  inputError: { borderColor: Colors.error },
  errorText: { ...Typography.errorText },
});
